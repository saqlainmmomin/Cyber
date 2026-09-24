"""Seed and measure the P4-3 performance benchmark dataset."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import sqlite3
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Callable, Iterator
from unittest.mock import patch

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.frameworks.registry import FrameworkRegistry
from app.models.action import Action
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.finding import Finding
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.initiative import Initiative
from app.routers import analysis
from app.services import approved_report, conclusion_review, findings, report_content, workpaper
from app.services.evidence import map_evidence
from app.utils import pdf_export


REPO_ROOT = Path(__file__).resolve().parents[1]
THRESHOLD_SECONDS = 2.0
TIMED_RUNS = 5
SEARCH_TERM = "retention schedule"
BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
BODY_PARAGRAPH = (
    "This policy defines the controls used to collect, classify, protect, review, "
    "and retire business information. Owners record each processing purpose, limit "
    "access to approved roles, review exceptions, and retain evidence of every "
    "control check. The retention schedule is reviewed with the data owner, changes "
    "are approved before release, and obsolete records are securely removed. "
    "Operational teams report missed checks, preserve supporting records, and test "
    "restoration procedures at a documented interval."
)
PLAN_COUNTS = {
    "clients": 5,
    "engagements": 10,
    "assessments": 30,
    "evidence_versions": 500,
    "conclusion_revisions": 3000,
}
FRAMEWORK_IDS = ("dpdpa", "iso27001", "nist_csf")
QUESTION_ANSWERS = (
    "fully_implemented",
    "partially_implemented",
    "planned",
    "not_implemented",
    "not_applicable",
)


@dataclass(frozen=True)
class SeedHandle:
    a0_id: str
    e0_id: str
    seed_seconds: float
    counts: dict[str, int]


class _SeedClock:
    def __init__(self) -> None:
        self._offset = 0

    def next(self) -> datetime:
        value = BASE + timedelta(seconds=self._offset)
        self._offset += 1
        return value


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def build_database(db_path: Path) -> tuple[str, object]:
    """Build a fresh Alembic-backed SQLite database and return its engine."""
    db_path = Path(db_path)
    if db_path.exists():
        raise FileExistsError(f"refusing to reuse existing database: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(_alembic_config(db_path), "head")

    url = f"sqlite:///{db_path}"
    bench_engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(bench_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return url, bench_engine


def evidence_text(global_index: int, version_number: int, markers: list[str]) -> str:
    """Return the deterministic extracted text stored on a benchmark version."""
    lines = [
        f"Benchmark policy document {global_index:03d}, version {version_number}."
    ]
    lines.extend(f"Section {section}. {BODY_PARAGRAPH}" for section in range(1, 21))
    lines.extend(
        f"Requirement marker {control_id} is implemented under this policy."
        for control_id in markers
    )
    return "\n".join(lines)


def _add_audit(
    db: Session,
    clock: _SeedClock,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=json.dumps(metadata, sort_keys=True),
            created_at=clock.next(),
        )
    )


def _build_analysis_items() -> dict[str, list[dict]]:
    items: dict[str, list[dict]] = {}
    global_index = 0
    for framework_id in FRAMEWORK_IDS:
        framework_items = []
        for control in FrameworkRegistry.get_all_controls(framework_id):
            requirement_id = control.id
            framework_items.append(
                {
                    "requirement_id": requirement_id,
                    "compliance_status": (
                        "non_compliant",
                        "partially_compliant",
                        "compliant",
                    )[global_index % 3],
                    "current_state": f"Benchmark current state for {requirement_id}.",
                    "gap_description": f"Benchmark gap for {requirement_id}.",
                    "risk_level": ("critical", "high", "medium", "low")[global_index % 4],
                    "remediation_action": f"Benchmark remediation for {requirement_id}.",
                    "remediation_priority": (global_index % 4) + 1,
                    "remediation_effort": "medium",
                    "timeline_weeks": 6,
                    "maturity_level": 2,
                    "root_cause_category": "process",
                    "needs_review": False,
                    "evidence_quote": (
                        f"Requirement marker {requirement_id} is implemented under this policy."
                        if global_index % 2 == 0
                        else ""
                    ),
                }
            )
            global_index += 1
        items[framework_id] = framework_items
    if global_index != 228:
        raise RuntimeError(f"benchmark framework catalog has {global_index} controls, expected 228")
    return items


def _insert_hierarchy_and_fillers(
    db: Session,
    clock: _SeedClock,
) -> tuple[Assessment, Engagement, list[tuple[Assessment, AnalysisRun, list[Conclusion]]]]:
    clients: list[Client] = []
    engagements: list[Engagement] = []
    assessments: list[Assessment] = []
    engagement_assessments: dict[str, list[Assessment]] = {}

    for client_number in range(1, 6):
        client_time = clock.next()
        client = Client(
            name=f"Benchmark Client {client_number}",
            industry="Technology",
            size="medium",
            created_at=client_time,
            updated_at=clock.next(),
        )
        db.add(client)
        db.flush()
        clients.append(client)
        for engagement_number in range(1, 3):
            engagement_time = clock.next()
            engagement = Engagement(
                client_id=client.id,
                name=f"Benchmark Client {client_number} engagement {engagement_number}",
                status="active",
                type="gap_assessment",
                created_at=engagement_time,
                updated_at=clock.next(),
            )
            db.add(engagement)
            db.flush()
            engagements.append(engagement)
            engagement_assessments[engagement.id] = []
            for assessment_number in range(1, 4):
                is_a0 = len(assessments) == 0
                filler_index = len(assessments) - 1
                selected = list(FRAMEWORK_IDS) if is_a0 else ["dpdpa"]
                assessment_time = clock.next()
                assessment = Assessment(
                    company_name=client.name,
                    industry=client.industry,
                    company_size=client.size,
                    description=(
                        "Benchmark 3-framework assessment" if is_a0 else None
                    ),
                    status=(
                        "created"
                        if is_a0
                        else ("completed", "questionnaire_done", "documents_uploaded")[
                            filler_index % 3
                        ]
                    ),
                    applicable_requirements=None,
                    selected_frameworks=json.dumps(selected),
                    engagement_id=engagement.id,
                    created_at=assessment_time,
                    updated_at=clock.next(),
                )
                db.add(assessment)
                db.flush()
                assessments.append(assessment)
                engagement_assessments[engagement.id].append(assessment)
                for framework_id in selected:
                    db.add(
                        AssessmentPack(
                            assessment_id=assessment.id,
                            framework_id=framework_id,
                            pack_version=FrameworkRegistry.get(framework_id).version,
                            created_at=clock.next(),
                        )
                    )

    a0 = assessments[0]
    e0 = engagements[0]
    a0_items = _build_analysis_items()
    a0_requirement_ids = [
        item["requirement_id"]
        for framework_id in FRAMEWORK_IDS
        for item in a0_items[framework_id]
    ]
    markers_by_document = {
        document_number: [
            requirement_id
            for global_index, requirement_id in enumerate(a0_requirement_ids)
            if global_index % 40 == document_number
        ]
        for document_number in range(40)
    }

    for engagement_index, engagement in enumerate(engagements):
        linked_assessments = engagement_assessments[engagement.id]
        document_count = 70 if engagement_index == 0 else 20
        for document_number in range(document_count):
            if engagement_index == 0:
                if document_number < 40:
                    assessment_id = a0.id
                    markers = markers_by_document[document_number]
                elif document_number < 55:
                    assessment_id = linked_assessments[1].id
                    markers = []
                else:
                    assessment_id = linked_assessments[2].id
                    markers = []
            else:
                assessment_id = linked_assessments[document_number % 3].id
                markers = []

            global_index = sum(70 if index == 0 else 20 for index in range(engagement_index))
            global_index += document_number
            evidence_time = clock.next()
            evidence = Evidence(
                engagement_id=engagement.id,
                assessment_id=assessment_id,
                document_category="policy",
                original_filename="pending",
                storage_path="pending",
                file_hash_sha256="pending",
                file_size_bytes=0,
                mime_type="application/pdf",
                status="active",
                uploaded_by="consultant:Bench Reviewer",
                created_at=evidence_time,
            )
            db.add(evidence)
            db.flush()

            versions: list[EvidenceVersion] = []
            for version_number in (1, 2):
                filename = (
                    f"benchmark-e{engagement_index:02d}-doc{document_number:03d}"
                    f"-v{version_number}.pdf"
                )
                text = evidence_text(global_index, version_number, markers)
                digest = hashlib.sha256(
                    f"{global_index}:{version_number}".encode()
                ).hexdigest()
                version = EvidenceVersion(
                    evidence_id=evidence.id,
                    version_number=version_number,
                    storage_path=f"benchmark/{evidence.id}/v{version_number}.pdf",
                    file_hash_sha256=digest,
                    file_size_bytes=len(text),
                    change_reason=None if version_number == 1 else "benchmark revision",
                    status="superseded" if version_number == 1 else "active",
                    original_filename=filename,
                    mime_type="application/pdf",
                    extracted_text=text,
                    created_at=clock.next(),
                )
                db.add(version)
                versions.append(version)

            evidence.original_filename = versions[0].original_filename
            evidence.storage_path = versions[0].storage_path
            evidence.file_hash_sha256 = versions[0].file_hash_sha256
            evidence.file_size_bytes = versions[0].file_size_bytes
            db.flush()

            _add_audit(
                db,
                clock,
                actor="consultant:Bench Reviewer",
                action="evidence.created",
                entity_type="evidence",
                entity_id=evidence.id,
                metadata={"evidence_id": evidence.id},
            )
            for version in versions:
                _add_audit(
                    db,
                    clock,
                    actor="consultant:Bench Reviewer",
                    action="evidence_version.created",
                    entity_type="evidence_version",
                    entity_id=version.id,
                    metadata={"evidence_id": evidence.id},
                )
                _add_audit(
                    db,
                    clock,
                    actor="system:scan-placeholder",
                    action="evidence_version.status_changed",
                    entity_type="evidence_version",
                    entity_id=version.id,
                    metadata={"evidence_id": evidence.id},
                )
            _add_audit(
                db,
                clock,
                actor="system:scan-placeholder",
                action="evidence_version.status_changed",
                entity_type="evidence_version",
                entity_id=versions[0].id,
                metadata={"evidence_id": evidence.id},
            )

    fillers: list[tuple[Assessment, AnalysisRun, list[Conclusion]]] = []
    dpdpa_controls = FrameworkRegistry.get_all_controls("dpdpa")[:20]
    for filler_index, assessment in enumerate(assessments[1:]):
        for question_index, control in enumerate(dpdpa_controls):
            db.add(
                QuestionnaireResponse(
                    assessment_id=assessment.id,
                    question_id=control.id,
                    answer=QUESTION_ANSWERS[question_index % len(QUESTION_ANSWERS)],
                    submitted_at=clock.next(),
                )
            )
        started_at = clock.next()
        completed_at = clock.next()
        run = AnalysisRun(
            assessment_id=assessment.id,
            framework_id="dpdpa",
            status="completed",
            model_id="benchmark",
            started_at=started_at,
            completed_at=completed_at,
            claims_json=json.dumps(
                {
                    "schema_version": 1,
                    "trigger_id": "benchmark-filler",
                    "framework_id": "dpdpa",
                    "model_tiers": {},
                    "inputs": {
                        "evidence_versions": [],
                        "legacy_document_ids": [],
                        "questionnaire_response_count": 20,
                        "applicable_requirements": None,
                    },
                    "gap_report_id": None,
                    "desk_review_used": False,
                    "claims": [],
                    "error": None,
                },
                sort_keys=True,
            ),
        )
        db.add(run)
        db.flush()
        conclusions: list[Conclusion] = []
        for control in dpdpa_controls:
            conclusion = Conclusion(
                assessment_id=assessment.id,
                requirement_id=control.id,
                framework_id="dpdpa",
                outcome="partially_compliant",
                rationale="Benchmark filler rationale",
                evidence_summary="",
                gaps_identified="Benchmark gap",
                risk_level="medium",
                recommended_action="Benchmark action",
                ai_proposed=True,
                version=2,
                cluster_id=None,
                created_at=clock.next(),
                updated_at=clock.next(),
            )
            db.add(conclusion)
            conclusions.append(conclusion)
        db.flush()
        fillers.append((assessment, run, conclusions))

    db.commit()
    return a0, e0, fillers


def _add_a0_inputs(db: Session, clock: _SeedClock, a0: Assessment) -> None:
    requirement_ids = [
        control.id
        for framework_id in FRAMEWORK_IDS
        for control in FrameworkRegistry.get_all_controls(framework_id)
    ]
    a0_evidence = (
        db.query(Evidence)
        .filter(Evidence.assessment_id == a0.id)
        .order_by(Evidence.created_at, Evidence.id)
        .all()
    )
    for global_index, requirement_id in enumerate(requirement_ids):
        db.add(
            QuestionnaireResponse(
                assessment_id=a0.id,
                question_id=requirement_id,
                answer=QUESTION_ANSWERS[global_index % len(QUESTION_ANSWERS)],
                notes=f"Benchmark response {global_index}",
                submitted_at=clock.next(),
            )
        )
        if global_index % 2 == 0:
            map_evidence(
                db,
                evidence_id=a0_evidence[(global_index // 2) % 40].id,
                assessment_id=a0.id,
                framework_id=(
                    "dpdpa"
                    if global_index < 41
                    else "iso27001"
                    if global_index < 134
                    else "nist_csf"
                ),
                requirement_id=requirement_id,
                relevance="primary",
                actor="consultant:Bench Reviewer",
            )
    db.commit()


def _patch_analysis(items: dict[str, list[dict]]):
    from app.frameworks import questionnaire_builder

    def stub_multi(**_kwargs):
        return {
            "frameworks": {
                framework_id: {
                    "parsed": {
                        "executive_summary": f"{framework_id} benchmark summary",
                        "assessments": copy.deepcopy(framework_items),
                    },
                    "raw": "{}",
                }
                for framework_id, framework_items in items.items()
            },
            "synthesis": None,
            "total_usage": {},
        }

    return (
        patch.object(analysis, "run_multi_framework_analysis", stub_multi),
        patch.object(analysis, "generate_multi_framework_initiatives", lambda *_args: []),
        patch.object(analysis, "generate_initiatives", lambda *_args: []),
        patch.object(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "Q1"}]),
        patch.object(
            questionnaire_builder,
            "build_multi_questionnaire",
            lambda *_args, **_kwargs: [],
        ),
    )


def _seed_a0(db: Session, clock: _SeedClock, a0: Assessment) -> int:
    items = _build_analysis_items()
    a0.applicable_requirements = json.dumps(
        sorted(
            item["requirement_id"]
            for framework_items in items.values()
            for item in framework_items
        )
    )
    db.flush()
    patches = _patch_analysis(items)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        analysis.trigger_analysis(a0.id, db)

    ordered_ids = [
        (framework_id, item["requirement_id"])
        for framework_id in FRAMEWORK_IDS
        for item in items[framework_id]
    ]
    conclusions_by_key = {
        (conclusion.framework_id, conclusion.requirement_id): conclusion
        for conclusion in db.query(Conclusion)
        .filter(Conclusion.assessment_id == a0.id)
        .all()
    }
    reviewer = conclusion_review.reviewer_actor("Bench Reviewer")
    for global_index, (framework_id, requirement_id) in enumerate(ordered_ids):
        conclusion = conclusions_by_key[(framework_id, requirement_id)]
        if global_index % 4 == 0:
            action = "approved"
            edits = None
        elif global_index % 4 == 1:
            action = "edited"
            edits = {
                "outcome": "non_compliant",
                "rationale": f"Consultant rationale for {requirement_id}.",
                "gaps_identified": "Consultant-identified gap",
                "risk_level": "high",
                "recommended_action": "Consultant action",
            }
        elif global_index % 4 == 2:
            action = "rejected"
            edits = None
        else:
            continue
        conclusion_review.decide(
            db,
            assessment_id=a0.id,
            conclusion_id=conclusion.id,
            action=action,
            expected_version=conclusion.version,
            actor=reviewer,
            edits=edits,
        )
    db.commit()

    conclusions_by_key = {
        (conclusion.framework_id, conclusion.requirement_id): conclusion
        for conclusion in db.query(Conclusion)
        .filter(Conclusion.assessment_id == a0.id)
        .all()
    }
    for global_index, (framework_id, requirement_id) in enumerate(ordered_ids):
        conclusion = conclusions_by_key[(framework_id, requirement_id)]
        card = conclusion_review.conclusion_card(
            db,
            assessment_id=a0.id,
            conclusion_id=conclusion.id,
        )
        if (
            card.state in ("approved", "edited")
            and conclusion.outcome in conclusion_review.GAP_OUTCOMES
        ):
            findings.create_finding(
                db,
                assessment_id=a0.id,
                conclusion_id=conclusion.id,
                conclusion_version=conclusion.version,
                title=f"Finding for {requirement_id}",
                description=f"Benchmark finding description for {requirement_id}.",
                severity=conclusion.risk_level,
                priority=findings.PRIORITY_BY_SEVERITY[conclusion.risk_level],
                action_title=f"Remediate {requirement_id}",
                action_owner=("Owner A", "Owner B", None)[global_index % 3],
                action_target_date=date(2026, 12, 31),
                notes=None,
                actor=reviewer,
                now=BASE,
            )
    db.commit()

    for framework_id, requirement_id in ordered_ids:
        conclusion = conclusions_by_key[(framework_id, requirement_id)]
        card = conclusion_review.conclusion_card(
            db,
            assessment_id=a0.id,
            conclusion_id=conclusion.id,
        )
        if card.state in ("pending", "rejected"):
            conclusion_review.decide(
                db,
                assessment_id=a0.id,
                conclusion_id=conclusion.id,
                action="approved",
                expected_version=conclusion.version,
                actor=reviewer,
            )
    db.commit()

    for _ in range(3):
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            analysis.trigger_analysis(a0.id, db)

    return (
        db.query(ConclusionRevision)
        .join(Conclusion, Conclusion.id == ConclusionRevision.conclusion_id)
        .filter(Conclusion.assessment_id == a0.id)
        .count()
    )


def _insert_filler_revisions(
    db: Session,
    clock: _SeedClock,
    fillers: list[tuple[Assessment, AnalysisRun, list[Conclusion]]],
    remaining: int,
) -> None:
    base_revisions = remaining // len(
        [conclusion for _assessment, _run, conclusions in fillers for conclusion in conclusions]
    )
    remainder = remaining % len(
        [conclusion for _assessment, _run, conclusions in fillers for conclusion in conclusions]
    )
    conclusion_index = 0
    for _assessment, run, conclusions in fillers:
        for conclusion in conclusions:
            revision_count = base_revisions + (1 if conclusion_index < remainder else 0)
            actions = ["proposed", "approved", "proposal_withheld", "proposal_withheld"][:revision_count]
            for revision_index, action in enumerate(actions):
                is_human = action == "approved"
                db.add(
                    ConclusionRevision(
                        conclusion_id=conclusion.id,
                        actor="consultant:Bench Reviewer" if is_human else "system:analysis",
                        action=action,
                        previous_outcome=(None if revision_index == 0 else conclusion.outcome),
                        previous_rationale=(None if revision_index == 0 else conclusion.rationale),
                        citations_json=None if is_human else "[]",
                        analysis_run_id=None if is_human else run.id,
                        created_at=clock.next(),
                    )
                )
            conclusion_index += 1
    db.commit()


def seed_counts(db: Session) -> dict[str, int]:
    models = (
        ("clients", Client),
        ("engagements", Engagement),
        ("assessments", Assessment),
        ("assessment_packs", AssessmentPack),
        ("evidence", Evidence),
        ("evidence_versions", EvidenceVersion),
        ("conclusions", Conclusion),
        ("conclusion_revisions", ConclusionRevision),
        ("analysis_runs", AnalysisRun),
        ("findings", Finding),
        ("actions", Action),
        ("evidence_uses", EvidenceUse),
        ("questionnaire_responses", QuestionnaireResponse),
        ("audit_events", AuditEvent),
        ("gap_reports", GapReport),
        ("gap_items", GapItem),
    )
    return {
        name: db.execute(select(func.count()).select_from(model)).scalar_one()
        for name, model in models
    }


def seed_benchmark_dataset(bench_engine) -> SeedHandle:
    """Seed the complete benchmark dataset into an already-built database."""
    started = time.perf_counter()
    db = sessionmaker(bind=bench_engine)()
    clock = _SeedClock()
    try:
        a0, e0, fillers = _insert_hierarchy_and_fillers(db, clock)
        _add_a0_inputs(db, clock, a0)
        actual_a0_revisions = _seed_a0(db, clock, a0)
        _insert_filler_revisions(
            db,
            clock,
            fillers,
            PLAN_COUNTS["conclusion_revisions"] - actual_a0_revisions,
        )
        approved_report.record_release(db, a0, actor="consultant:Bench Reviewer")
        db.commit()
        counts = seed_counts(db)
        counts["a0_conclusion_revisions"] = actual_a0_revisions
        counts["a0_findings"] = db.query(Finding).filter(Finding.assessment_id == a0.id).count()
        for key, expected in PLAN_COUNTS.items():
            if counts[key] != expected:
                raise AssertionError(f"benchmark count {key}={counts[key]}, expected {expected}")
        return SeedHandle(
            a0_id=a0.id,
            e0_id=e0.id,
            seed_seconds=time.perf_counter() - started,
            counts=counts,
        )
    finally:
        db.close()


def search_engagement_evidence(
    db: Session, engagement_id: str, term: str
) -> list[tuple[Evidence, EvidenceVersion]]:
    """P4-3 reference query for engagement-wide evidence search."""
    pattern = f"%{term}%"
    return db.execute(
        select(Evidence, EvidenceVersion)
        .join(EvidenceVersion, EvidenceVersion.evidence_id == Evidence.id)
        .where(
            Evidence.engagement_id == engagement_id,
            Evidence.status != "archived",
            EvidenceVersion.status == "active",
            or_(
                EvidenceVersion.original_filename.ilike(pattern),
                EvidenceVersion.extracted_text.ilike(pattern),
            ),
        )
        .order_by(Evidence.created_at, Evidence.id)
    ).all()


@contextmanager
def benchmark_client(url: str, bench_engine) -> Iterator[TestClient]:
    """Yield a TestClient whose requests each receive a fresh benchmark session."""
    from app.routers import web
    from app.template_config import configure_templates
    from app.main import app

    configure_templates(web.templates)
    factory = sessionmaker(bind=bench_engine)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with patch.object(settings, "database_url", url):
        try:
            with TestClient(app, raise_server_exceptions=False) as client:
                yield client
        finally:
            app.dependency_overrides.clear()


def _observe_response(response, expected: Callable) -> dict:
    body = response.content
    return {
        "status_code": response.status_code,
        "bytes": len(body),
        "valid": expected(response, body),
    }


def _run_http_operation(client: TestClient, path: str, expected: Callable) -> dict:
    return _observe_response(client.get(path), expected)


def _run_search_operation(factory, engagement_id: str) -> dict:
    db = factory()
    try:
        rows = search_engagement_evidence(db, engagement_id, SEARCH_TERM)
        return {"status_code": None, "bytes": 0, "valid": len(rows) == 70}
    finally:
        db.close()


def _pdf_arguments(db: Session, assessment_id: str):
    assessment = db.get(Assessment, assessment_id)
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .one()
    )
    items = db.query(GapItem).filter(GapItem.report_id == report.id).all()
    initiatives = (
        db.query(Initiative)
        .filter(Initiative.report_id == report.id)
        .order_by(Initiative.priority)
        .all()
    )
    answer_source_map = {
        response.question_id: response.answer_source or "human"
        for response in db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    }
    selected_frameworks = ["dpdpa"]
    if assessment and assessment.selected_frameworks:
        try:
            selected_frameworks = json.loads(assessment.selected_frameworks)
        except json.JSONDecodeError:
            pass
    return (
        report,
        items,
        assessment.company_name if assessment else "Unknown",
        initiatives,
        answer_source_map,
        selected_frameworks,
        assessment,
    )


def _breakdowns(bench_engine, handle: SeedHandle) -> dict[str, dict[str, float]]:
    factory = sessionmaker(bind=bench_engine)
    db = factory()
    try:
        assessment = db.get(Assessment, handle.a0_id)
        started = time.perf_counter()
        workpaper.build_workpaper(db, assessment)
        workpaper_seconds = time.perf_counter() - started
    finally:
        db.close()

    db = factory()
    try:
        assessment = db.get(Assessment, handle.a0_id)
        started = time.perf_counter()
        report_findings = report_content.assessment_findings(db, assessment)
        findings_seconds = time.perf_counter() - started
    finally:
        db.close()

    db = factory()
    try:
        arguments = _pdf_arguments(db, handle.a0_id)
        started = time.perf_counter()
        pdf_export.generate_pdf(
            *arguments[:5],
            selected_frameworks=arguments[5],
            assessment=arguments[6],
            report_findings=report_findings,
        )
        pdf_seconds = time.perf_counter() - started
    finally:
        db.close()
    return {
        "workpaper_3_framework": {"build_workpaper_seconds": workpaper_seconds},
        "gap_report_pdf_3_framework": {
            "assessment_findings_seconds": findings_seconds,
            "generate_pdf_seconds": pdf_seconds,
        },
    }


def run_benchmarks(url: str, bench_engine, handle: SeedHandle) -> dict:
    """Warm, time, and summarize the four P4-3 operations."""
    from app.main import app

    factory = sessionmaker(bind=bench_engine)
    operations: list[dict] = []
    breakdowns = _breakdowns(bench_engine, handle)

    def dashboard(client):
        return _run_http_operation(client, "/", lambda response, body: response.status_code == 200)

    def workpaper_operation(client):
        return _run_http_operation(
            client,
            f"/assessments/{handle.a0_id}/workpaper",
            lambda response, body: response.status_code == 200,
        )

    def report_operation(client):
        return _run_http_operation(
            client,
            f"/api/assessments/{handle.a0_id}/report/pdf",
            lambda response, body: (
                response.status_code == 200
                and response.headers.get("content-type", "").startswith("application/pdf")
                and body.startswith(b"%PDF")
            ),
        )

    operation_specs = (
        ("portfolio_dashboard", "GET /", dashboard),
        (
            "workpaper_3_framework",
            f"GET /assessments/{handle.a0_id}/workpaper",
            workpaper_operation,
        ),
        (
            "gap_report_pdf_3_framework",
            f"GET /api/assessments/{handle.a0_id}/report/pdf",
            report_operation,
        ),
    )

    with benchmark_client(url, bench_engine) as client:
        for name, target, runner in operation_specs:
            statement_total = 0

            def counter(*_args):
                nonlocal statement_total
                statement_total += 1

            event.listen(bench_engine, "before_cursor_execute", counter)
            try:
                warm_observation = runner(client)
            finally:
                event.remove(bench_engine, "before_cursor_execute", counter)
            runs_seconds = []
            observations = []
            for _ in range(TIMED_RUNS):
                started = time.perf_counter()
                observation = runner(client)
                runs_seconds.append(time.perf_counter() - started)
                observations.append(observation)
            final_observation = observations[-1] if observations else warm_observation
            operations.append(
                {
                    "name": name,
                    "target": target,
                    "status_code": final_observation["status_code"],
                    "bytes": final_observation["bytes"],
                    "runs_seconds": runs_seconds,
                    "median_seconds": median(runs_seconds),
                    "max_seconds": max(runs_seconds),
                    "statements": statement_total,
                    "breakdown": breakdowns.get(name, {}),
                    "passed": bool(final_observation["valid"])
                    and median(runs_seconds) < THRESHOLD_SECONDS,
                }
            )

        statement_total = 0

        def counter(*_args):
            nonlocal statement_total
            statement_total += 1

        event.listen(bench_engine, "before_cursor_execute", counter)
        try:
            warm_observation = _run_search_operation(factory, handle.e0_id)
        finally:
            event.remove(bench_engine, "before_cursor_execute", counter)
        runs_seconds = []
        observations = []
        for _ in range(TIMED_RUNS):
            started = time.perf_counter()
            observation = _run_search_operation(factory, handle.e0_id)
            runs_seconds.append(time.perf_counter() - started)
            observations.append(observation)
        final_observation = observations[-1] if observations else warm_observation
        operations.append(
            {
                "name": "evidence_search_engagement",
                "target": "search_engagement_evidence(db, E0.id, 'retention schedule')",
                "status_code": final_observation["status_code"],
                "bytes": final_observation["bytes"],
                "runs_seconds": runs_seconds,
                "median_seconds": median(runs_seconds),
                "max_seconds": max(runs_seconds),
                "statements": statement_total,
                "breakdown": {},
                "passed": bool(final_observation["valid"])
                and median(runs_seconds) < THRESHOLD_SECONDS,
            }
        )

    return {
        "threshold_seconds": THRESHOLD_SECONDS,
        "environment": {
            "python": sys.version,
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
        },
        "seed_seconds": handle.seed_seconds,
        "counts": handle.counts,
        "operations": operations,
    }


def format_table(results: dict) -> str:
    headers = ("name", "median_s", "max_s", "statements", "status", "PASS/FAIL")
    rows = []
    for operation in results["operations"]:
        rows.append(
            (
                operation["name"],
                f"{operation['median_seconds']:.6f}",
                f"{operation['max_seconds']:.6f}",
                str(operation["statements"]),
                str(operation["status_code"]),
                "PASS" if operation["passed"] else "FAIL",
            )
        )
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    lines = [" | ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))]
    lines.append("-+-".join("-" * width for width in widths))
    lines.extend(
        " | ".join(row[index].ljust(widths[index]) for index in range(len(headers)))
        for row in rows
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the CyberAssess P4-3 performance benchmark.")
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None, dest="json_path")
    args = parser.parse_args(argv)

    db_path = args.db or Path(tempfile.mkdtemp(prefix="cyberassess-bench-")) / "benchmark.sqlite3"
    if db_path.exists():
        print(f"refusing to reuse existing database: {db_path}", file=sys.stderr)
        return 2
    json_path = args.json_path or db_path.parent / "benchmark-results.json"
    upload_dir = Path(tempfile.mkdtemp(prefix="cyberassess-bench-uploads-"))

    from app.main import _register_frameworks

    _register_frameworks()
    url, bench_engine = build_database(db_path)
    try:
        with patch.object(settings, "upload_dir", str(upload_dir)):
            handle = seed_benchmark_dataset(bench_engine)
            results = run_benchmarks(url, bench_engine, handle)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        print(format_table(results))
        return 0 if all(operation["passed"] for operation in results["operations"]) else 1
    finally:
        bench_engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
