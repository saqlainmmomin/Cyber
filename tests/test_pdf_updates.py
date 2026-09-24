"""Contract suite for P3-3 PDF and integrated report updates."""

from __future__ import annotations

import copy
import hashlib
import inspect
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import pdfplumber
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.config import settings
from app.database import get_db
from app.dpdpa.framework import get_all_requirements
from app.frameworks.registry import FrameworkRegistry
from app.main import app
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceVersion
from app.models.finding import Finding
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.report_snapshot import ReportSnapshot
from app.routers import web
from app.services import report_content, report_snapshots
from app.services.scoring import report_framework_scores
from app.utils import pdf_export

REPO_ROOT = Path(__file__).resolve().parents[1]
REQS = [row["id"] for row in get_all_requirements()][:3]


@pytest.fixture(scope="module", autouse=True)
def _register_frameworks():
    from app.main import _register_frameworks as register

    register()


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "pdf-updates.sqlite3"
    command.upgrade(_alembic_config(path), "head")
    return path


@pytest.fixture()
def engine(db_path):
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    yield engine
    engine.dispose()


@pytest.fixture()
def db(engine):
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def http(db, db_path, monkeypatch):
    from app.routers.web import templates
    from app.template_config import configure_templates

    configure_templates(templates)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_path}")

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setattr(settings, "upload_dir", str(root))
    return root


@pytest.fixture()
def gate(monkeypatch):
    from app.frameworks import questionnaire_builder
    from app.routers import analysis

    monkeypatch.setattr(analysis, "build_questionnaire", lambda **_kwargs: [{"id": "Q1"}])
    monkeypatch.setattr(analysis, "generate_initiatives", lambda *_args: [])
    monkeypatch.setattr(analysis, "generate_multi_framework_initiatives", lambda *_args: [])
    monkeypatch.setattr(questionnaire_builder, "build_multi_questionnaire", lambda *_a, **_k: [])
    return analysis


def _seed(
    db,
    *,
    applicable=None,
    frameworks=None,
    client_name="Acme Corp",
    engagement=None,
    description=None,
):
    frameworks = frameworks or ["dpdpa"]
    if engagement is None:
        client = Client(name=client_name, industry="Technology", size="medium")
        db.add(client)
        db.flush()
        engagement = Engagement(
            client_id=client.id, name=f"{client_name} gap", status="active"
        )
        db.add(engagement)
        db.flush()
    else:
        client = db.get(Client, engagement.client_id)
    assessment = Assessment(
        company_name=client.name,
        industry="Technology",
        company_size="medium",
        description=description,
        selected_frameworks=json.dumps(frameworks),
        engagement_id=engagement.id,
        applicable_requirements=json.dumps(applicable or [REQS[0]]),
    )
    db.add(assessment)
    db.flush()
    db.add(
        QuestionnaireResponse(
            assessment_id=assessment.id,
            question_id="Q1",
            answer="fully_implemented",
        )
    )
    db.commit()
    return assessment


def _item(
    requirement_id,
    status="partially_compliant",
    *,
    current="Current state",
    gap="Gap exists",
    risk="medium",
    action="Fix the gap",
    quote="",
):
    return {
        "requirement_id": requirement_id,
        "compliance_status": status,
        "current_state": current,
        "gap_description": gap,
        "risk_level": risk,
        "remediation_action": action,
        "remediation_priority": 2,
        "remediation_effort": "medium",
        "timeline_weeks": 6,
        "maturity_level": 2,
        "root_cause_category": "process",
        "evidence_quote": quote,
        "needs_review": False,
    }


def _stub_single(monkeypatch, items):
    from app.routers import analysis

    monkeypatch.setattr(
        analysis,
        "run_gap_analysis",
        lambda **_kwargs: {
            "parsed": {
                "executive_summary": "Synthetic summary",
                "assessments": copy.deepcopy(items),
            },
            "raw": "{}",
        },
    )


def _stub_multi(monkeypatch, per_framework):
    from app.routers import analysis

    def _fake(**_kwargs):
        return {
            "frameworks": {
                framework_id: {
                    "parsed": {
                        "executive_summary": f"{framework_id} summary",
                        "assessments": copy.deepcopy(items),
                    },
                    "raw": "{}",
                }
                for framework_id, items in per_framework.items()
            },
            "synthesis": None,
            "total_usage": {},
        }

    monkeypatch.setattr(analysis, "run_multi_framework_analysis", _fake)


def _revisions(db, conclusion_id):
    db.expire_all()
    return (
        db.query(ConclusionRevision)
        .filter_by(conclusion_id=conclusion_id)
        .order_by(ConclusionRevision.created_at, text("conclusion_revisions.rowid"))
        .all()
    )


def _url(assessment, conclusion, route):
    return f"/api/assessments/{assessment.id}/conclusions/{conclusion.id}/{route}"


def _decide(http, assessment, conclusion, route, **overrides):
    payload = {
        "expected_version": conclusion.version,
        "reviewer_name": "Priya",
    }
    if route == "edit":
        payload.update(
            {
                "outcome": "non_compliant",
                "rationale": "Consultant rationale",
                "gaps_identified": "Consultant gap",
                "risk_level": "high",
                "recommended_action": "Consultant action",
            }
        )
    payload.update(overrides)
    return http.post(_url(assessment, conclusion, route), data=payload)


def _approve(http, db, assessment, conclusion):
    response = _decide(http, assessment, conclusion, "approve")
    assert response.status_code == 200
    db.refresh(conclusion)
    return response


def _create(http, assessment, conclusion, **overrides):
    payload = {
        "conclusion_id": conclusion.id,
        "conclusion_version": conclusion.version,
        "title": "Finding title",
        "description": "Finding description",
        "severity": "high",
        "priority": 1,
        "action_title": "First action",
        "reviewer_name": "Priya",
    }
    for key, value in overrides.items():
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = value
    return http.post(f"/api/assessments/{assessment.id}/findings", data=payload)


def _human_revision(db, conclusion, action, *, actor="consultant:Priya"):
    conclusion.version += 1
    if action == "edited":
        conclusion.ai_proposed = False
    revision = ConclusionRevision(
        conclusion_id=conclusion.id,
        actor=actor,
        action=action,
        previous_outcome=conclusion.outcome,
        previous_rationale=conclusion.rationale,
        citations_json=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(revision)
    db.commit()
    return revision


def _add_evidence(db, assessment, *, filename="policy.pdf", text_value="Grounded quote"):
    evidence = Evidence(
        engagement_id=assessment.engagement_id,
        assessment_id=assessment.id,
        original_filename=filename,
        storage_path=filename,
        file_hash_sha256="a" * 64,
        file_size_bytes=10,
        mime_type="application/pdf",
        status="active",
        uploaded_by="consultant",
    )
    db.add(evidence)
    db.flush()
    version = EvidenceVersion(
        evidence_id=evidence.id,
        version_number=1,
        storage_path=filename,
        file_hash_sha256="a" * 64,
        file_size_bytes=10,
        status="active",
        original_filename=filename,
        mime_type="application/pdf",
        extracted_text=text_value,
    )
    db.add(version)
    db.flush()
    return evidence, version


def _cite_revision(db, conclusion, version, *, excerpt="Grounded quote"):
    proposal = next(row for row in _revisions(db, conclusion.id) if row.action == "proposed")
    proposal.citations_json = json.dumps(
        [
            {
                "evidence_version_id": version.id,
                "location_type": "text_span",
                "location_ref": f"chars:0-{len(excerpt)}",
                "excerpt": excerpt,
            }
        ]
    )
    db.commit()
    return proposal


def _approved_finding(
    db,
    http,
    gate,
    monkeypatch,
    assessment,
    conclusion,
    *,
    excerpt="Grounded quote",
    title=None,
    description=None,
    severity=None,
):
    _evidence, version = _add_evidence(
        db, assessment, text_value=excerpt or "Grounded quote"
    )
    _cite_revision(db, conclusion, version, excerpt=excerpt)
    _approve(http, db, assessment, conclusion)
    overrides = {}
    if title is not None:
        overrides["title"] = title
    if description is not None:
        overrides["description"] = description
    if severity is not None:
        overrides["severity"] = severity
    response = _create(http, assessment, conclusion, **overrides)
    assert response.status_code == 200
    return db.get(Finding, response.json()["finding_id"])


def _run_one(
    db,
    gate,
    monkeypatch,
    *,
    item=None,
    client_name="Acme Corp",
    applicable=None,
    frameworks=None,
    engagement=None,
    description=None,
    approved=False,
):
    assessment = _seed(
        db,
        client_name=client_name,
        applicable=applicable,
        frameworks=frameworks,
        engagement=engagement,
        description=description,
    )
    items = item or _item((applicable or [REQS[0]])[0])
    _stub_single(monkeypatch, [items])
    gate.trigger_analysis(assessment.id, db)
    if approved:
        assessment.review_status = "approved"
        db.commit()
    conclusion = db.query(Conclusion).filter_by(assessment_id=assessment.id).one()
    return assessment, conclusion


def _pdf_text(content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        text_value = " ".join((page.extract_text() or "") for page in pdf.pages)
    return " ".join(text_value.split())


def _page_count(content: bytes) -> int:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return len(pdf.pages)


def _assessment_pdf(db, assessment, report_findings=None):
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    items = db.query(GapItem).filter_by(report_id=report.id).all()
    return pdf_export.generate_pdf(
        report,
        items,
        assessment.company_name,
        selected_frameworks=assessment.frameworks,
        assessment=assessment,
        report_findings=report_findings,
    )


def _set_scores(db, assessment, scores):
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    report.framework_scores = json.dumps(
        {
            framework_id: {
                "overall_score": score,
                "overall_rating": "Partially Compliant",
                "domain_scores": {},
            }
            for framework_id, score in scores.items()
        }
    )
    db.commit()


def _generate_integrated(http, engagement, reviewer="Priya"):
    return http.post(
        f"/api/engagements/{engagement.id}/integrated-reports",
        data={"reviewer_name": reviewer},
    )


def _issue_integrated(http, engagement, snapshot_id, reviewer="Priya"):
    return http.post(
        f"/api/engagements/{engagement.id}/integrated-reports/{snapshot_id}/issue",
        data={"reviewer_name": reviewer},
    )


def _setup_integrated(db, http, gate, monkeypatch):
    first = _seed(
        db,
        applicable=[REQS[0], REQS[1]],
        frameworks=["dpdpa"],
        client_name="Integrated Client",
        description="Assessment A",
    )
    engagement = db.get(Engagement, first.engagement_id)
    _stub_single(
        monkeypatch,
        [
            _item(REQS[0], "non_compliant", risk="high"),
            _item(REQS[1], "partially_compliant", risk="medium"),
        ],
    )
    gate.trigger_analysis(first.id, db)
    first_conclusions = (
        db.query(Conclusion)
        .filter_by(assessment_id=first.id)
        .order_by(Conclusion.requirement_id)
        .all()
    )
    _approved_finding(
        db,
        http,
        gate,
        monkeypatch,
        first,
        next(row for row in first_conclusions if row.requirement_id == REQS[0]),
        title="Assessment A finding",
    )
    first.review_status = "approved"
    db.commit()

    iso_req = FrameworkRegistry.get_all_controls("iso27001")[0].id
    second = _seed(
        db,
        applicable=[REQS[0], iso_req],
        frameworks=["dpdpa", "iso27001"],
        engagement=engagement,
        description="Assessment B",
    )
    _stub_multi(
        monkeypatch,
        {
            "dpdpa": [_item(REQS[0], "non_compliant", risk="high")],
            "iso27001": [_item(iso_req, "partially_compliant", risk="medium")],
        },
    )
    gate.trigger_analysis(second.id, db)
    second_conclusion = (
        db.query(Conclusion)
        .filter_by(assessment_id=second.id, framework_id="dpdpa")
        .one()
    )
    _approved_finding(
        db,
        http,
        gate,
        monkeypatch,
        second,
        second_conclusion,
        title="Assessment B finding",
    )
    second.review_status = "approved"
    db.commit()

    third = _seed(
        db,
        applicable=[REQS[0]],
        frameworks=["dpdpa"],
        engagement=engagement,
        description="Assessment C",
    )
    _stub_single(monkeypatch, [_item(REQS[0], "non_compliant")])
    gate.trigger_analysis(third.id, db)
    third.review_status = "pending"
    db.commit()

    _set_scores(db, first, {"dpdpa": 100.0})
    _set_scores(db, second, {"dpdpa": 40.0, "iso27001": 60.0})
    return engagement, first, second, third, first_conclusions


def _state(db, upload_root):
    rows = db.execute(
        text(
            "SELECT id, is_issued, storage_path FROM report_snapshots "
            "ORDER BY rowid"
        )
    ).all()
    audit_count = db.execute(text("SELECT COUNT(*) FROM audit_events")).scalar_one()
    root = upload_root / "reports"
    files = (
        sorted(str(path.relative_to(upload_root)) for path in root.rglob("*") if path.is_file())
        if root.exists()
        else []
    )
    return audit_count, rows, files


def test_scenario_1_multiframework_pdf_has_findings_and_no_blend(
    db, http, gate, monkeypatch
):
    """Scenario 1: multi-framework assessment PDF with scores, citations and no blended score."""
    iso_req = FrameworkRegistry.get_all_controls("iso27001")[0].id
    assessment = _seed(
        db,
        frameworks=["dpdpa", "iso27001"],
        applicable=[REQS[0], iso_req],
    )
    _stub_multi(
        monkeypatch,
        {
            "dpdpa": [_item(REQS[0], "non_compliant", risk="high")],
            "iso27001": [_item(iso_req, "partially_compliant", risk="medium")],
        },
    )
    gate.trigger_analysis(assessment.id, db)
    conclusions = db.query(Conclusion).filter_by(assessment_id=assessment.id).all()
    dpdpa_conclusion = next(row for row in conclusions if row.framework_id == "dpdpa")
    iso_conclusion = next(row for row in conclusions if row.framework_id == "iso27001")
    _approved_finding(
        db, http, gate, monkeypatch, assessment, dpdpa_conclusion, excerpt="Grounded quote", title="DPDPA finding"
    )
    _evidence, second_version = _add_evidence(
        db, assessment, text_value="Second quote"
    )
    second_version.file_hash_sha256 = "b" * 64
    db.commit()
    _cite_revision(db, iso_conclusion, second_version, excerpt="Second quote")
    _approve(http, db, assessment, iso_conclusion)
    created = _create(http, assessment, iso_conclusion, title="ISO finding")
    assert created.status_code == 200
    assessment.review_status = "approved"
    db.commit()

    response = http.get(f"/api/assessments/{assessment.id}/report/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    text_value = _pdf_text(response.content)
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    for framework_id, scores in report_framework_scores(report, assessment).items():
        assert f"{scores['overall_score']:.0f}%" in text_value
    assert "Framework Scores" in text_value
    assert FrameworkRegistry.get("dpdpa").name in text_value
    assert FrameworkRegistry.get("iso27001").name in text_value
    assert "Approved Findings" in text_value
    assert "DPDPA finding" in text_value
    assert "ISO finding" in text_value
    assert REQS[0] in text_value and iso_req in text_value
    assert "Grounded quote" in text_value and "Second quote" in text_value
    assert "a" * 16 in text_value and "b" * 16 in text_value
    assert "policy.pdf v1" in text_value
    assert f"Workpaper ref: wp-dpdpa-{REQS[0]}" in text_value
    assert "Approved by Priya" in text_value
    assert "Overall Score" not in text_value
    assert text_value.index("Approved Findings") > text_value.index("Detailed Gap Findings")
    assert text_value.index("Approved Findings") < text_value.index("Scope & Limitations")
    assert text_value.index("DPDPA finding") < text_value.index("ISO finding")


def test_scenario_2_reopened_findings_are_omitted(db, http, gate, monkeypatch):
    """Scenario 2: reopened source decisions are omitted and counted."""
    assessment, conclusion = _run_one(
        db, gate, monkeypatch, item=_item(REQS[0], "non_compliant")
    )
    _approved_finding(db, http, gate, monkeypatch, assessment, conclusion)
    assessment.review_status = "approved"
    db.commit()
    reopened = _decide(http, assessment, conclusion, "reopen")
    assert reopened.status_code == 200
    result = report_content.assessment_findings(db, assessment)
    assert result.findings == []
    assert result.omitted_count == 1
    text_value = _pdf_text(_assessment_pdf(db, assessment, result))
    assert "1 finding(s) not shown" in text_value
    assert "Finding title" not in text_value


def test_scenario_2_legacy_bulk_and_edited_sources_follow_inclusion_rules(
    db, http, gate, monkeypatch
):
    """Scenario 2: legacy bulk approvals are omitted while edited sources are included."""
    assessment, conclusion = _run_one(
        db, gate, monkeypatch, item=_item(REQS[0], "non_compliant")
    )
    _human_revision(db, conclusion, "approved", actor="Manager Review")
    legacy = Finding(
        assessment_id=assessment.id,
        conclusion_id=conclusion.id,
        title="Legacy Finding",
        description="Migrated description",
        severity="high",
        priority=1,
        status="open",
    )
    db.add(legacy)
    db.commit()
    result = report_content.assessment_findings(db, assessment)
    assert result.findings == []
    assert result.omitted_count == 1

    edited_assessment, edited_conclusion = _run_one(
        db,
        gate,
        monkeypatch,
        item=_item(REQS[1], "non_compliant"),
        client_name="Edited Client",
    )
    _evidence, edited_version = _add_evidence(db, edited_assessment)
    _cite_revision(db, edited_conclusion, edited_version)
    edited = _decide(http, edited_assessment, edited_conclusion, "edit")
    assert edited.status_code == 200
    db.refresh(edited_conclusion)
    included = _create(http, edited_assessment, edited_conclusion)
    assert included.status_code == 200
    result = report_content.assessment_findings(db, edited_assessment)
    assert len(result.findings) == 1
    assert result.findings[0].decision_label == "Edited and approved"


def test_scenario_2_findings_reader_has_one_call_and_severity_order(
    db, http, gate, monkeypatch
):
    """Scenario 2: the reader calls findings_page once and sorts critical before low."""
    assessment = _seed(db, applicable=[REQS[0], REQS[1]])
    _stub_single(
        monkeypatch,
        [
            _item(REQS[0], "non_compliant", risk="low"),
            _item(REQS[1], "non_compliant", risk="critical"),
        ],
    )
    gate.trigger_analysis(assessment.id, db)
    first_conclusion = db.query(Conclusion).filter_by(
        assessment_id=assessment.id, requirement_id=REQS[0]
    ).one()
    second_conclusion = db.query(Conclusion).filter_by(
        assessment_id=assessment.id, requirement_id=REQS[1]
    ).one()
    _approved_finding(
        db, http, gate, monkeypatch, assessment, first_conclusion, severity="low", title="Low finding"
    )
    _approved_finding(
        db, http, gate, monkeypatch, assessment, second_conclusion, severity="critical", title="Critical finding"
    )
    calls = []
    original = report_content.finding_service.findings_page

    def spy(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(report_content.finding_service, "findings_page", spy)
    result = report_content.assessment_findings(db, assessment)
    assert len(calls) == 1
    assert [row.title for row in result.findings] == ["Critical finding", "Low finding"]


def test_scenario_3_empty_findings_preserve_existing_pdf_pages(db, http, gate, monkeypatch):
    """Scenario 3: no findings means no new section and existing PDF pages remain additive."""
    assessment, _conclusion = _run_one(db, gate, monkeypatch)
    report = db.query(GapReport).filter_by(assessment_id=assessment.id).one()
    items = db.query(GapItem).filter_by(report_id=report.id).all()
    baseline = pdf_export.generate_pdf(
        report, items, assessment.company_name,
        selected_frameworks=assessment.frameworks, assessment=assessment,
    )
    empty = _assessment_pdf(db, assessment, report_content.AssessmentFindings([], 0))
    without = _assessment_pdf(db, assessment, None)
    assert "Approved Findings" not in _pdf_text(empty)
    assert "Approved Findings" not in _pdf_text(without)
    assert _page_count(baseline) == _page_count(empty) == _page_count(without)
    assert list(inspect.signature(pdf_export.generate_pdf).parameters) == [
        "report", "gap_items", "company_name", "initiatives", "answer_source_map",
        "selected_frameworks", "assessment", "report_findings",
    ]
    assert inspect.signature(pdf_export.generate_pdf).parameters["report_findings"].default is None

    _approved_finding(db, http, gate, monkeypatch, assessment, _conclusion)
    included = report_content.assessment_findings(db, assessment)
    with_finding = _assessment_pdf(db, assessment, included)
    assert _page_count(with_finding) > _page_count(baseline)


def test_scenario_4_gap_snapshots_capture_new_findings_without_changing_old_bytes(
    db, http, gate, monkeypatch
):
    """Scenario 4: gap snapshots render the new section while preserving old bytes."""
    assessment, conclusion = _run_one(
        db, gate, monkeypatch, item=_item(REQS[0], "non_compliant"), approved=True
    )
    first_response = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "gap_report", "reviewer_name": "Priya"},
    )
    assert first_response.status_code == 200
    first_id = first_response.json()["snapshot_id"]
    first_file = http.get(f"/api/assessments/{assessment.id}/snapshots/{first_id}/file")
    assert "Approved Findings" not in _pdf_text(first_file.content)
    first_hash = first_file.headers["X-Snapshot-Sha256"]
    _approved_finding(db, http, gate, monkeypatch, assessment, conclusion)
    second_response = http.post(
        f"/api/assessments/{assessment.id}/snapshots",
        data={"type": "gap_report", "reviewer_name": "Priya"},
    )
    second_id = second_response.json()["snapshot_id"]
    second_file = http.get(f"/api/assessments/{assessment.id}/snapshots/{second_id}/file")
    assert "Finding title" in _pdf_text(second_file.content)
    assert "Grounded quote" in _pdf_text(second_file.content)
    assert first_file.content == http.get(
        f"/api/assessments/{assessment.id}/snapshots/{first_id}/file"
    ).content
    assert first_file.headers["X-Snapshot-Sha256"] == first_hash
    assert first_hash != second_file.headers["X-Snapshot-Sha256"]


def test_scenario_5_integrated_report_happy_path(db, http, gate, monkeypatch, upload_root):
    """Scenario 5: integrated report includes approved assessments as separate sections."""
    engagement, first, second, third, _first_conclusions = _setup_integrated(
        db, http, gate, monkeypatch
    )
    response = _generate_integrated(http, engagement)
    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == f"/engagements/{engagement.id}/integrated-reports"
    assert response.json()["type"] == "integrated_report"
    assert response.json()["is_issued"] is False
    snapshot = db.get(ReportSnapshot, response.json()["snapshot_id"])
    assert snapshot.assessment_id is None
    assert snapshot.engagement_id == engagement.id
    assert snapshot.format == "pdf"
    assert snapshot.storage_path == f"reports/engagements/{engagement.id}/{snapshot.id}.pdf"
    assert (upload_root / snapshot.storage_path).is_file()
    metadata = report_snapshots.generated_event(db, snapshot.id)
    assert set(metadata) == {
        "schema_version", "type", "format", "storage_path", "sha256", "size_bytes",
        "assessment_id", "engagement_id", "review_status", "source",
    }
    assert metadata["assessment_id"] is None
    assert metadata["review_status"] is None
    event_row = db.query(AuditEvent).filter_by(entity_id=snapshot.id, action=report_snapshots.GENERATED_ACTION).one()
    assert event_row.actor == "consultant:Priya"
    data = report_content.integrated_report(db, engagement)
    expected_ids = sorted([first.id, second.id])
    assert [row["assessment_id"] for row in metadata["source"]["assessments"]] == sorted(
        expected_ids
    )
    for row in metadata["source"]["assessments"]:
        assessment = db.get(Assessment, row["assessment_id"])
        assert row == {"assessment_id": assessment.id, **report_snapshots.source_manifest(db, assessment)}
    assert metadata["source"]["excluded_assessment_ids"] == [third.id]
    assert metadata["source"]["finding_ids"] == sorted(
        finding.finding_id for section in data.sections for finding in section.findings.findings
    )
    file_response = http.get(
        f"/api/engagements/{engagement.id}/integrated-reports/{snapshot.id}/file"
    )
    assert file_response.status_code == 200
    assert file_response.headers["content-type"] == "application/pdf"
    assert file_response.headers["X-Snapshot-Sha256"] == hashlib.sha256(file_response.content).hexdigest()
    text_value = _pdf_text(file_response.content)
    assert "Integrated Engagement Report" in text_value
    assert "Assessment A" in text_value and "Assessment B" in text_value
    assert "Framework Scores (this assessment only)" in text_value
    assert all(value in text_value for value in ("100%", "40%", "60%"))
    assert "Assessment A finding" in text_value and "Assessment B finding" in text_value
    assert "Assessments Not Included" in text_value
    assert "Assessment C" in text_value and "Not approved for release" in text_value
    assert "Assessment period and evidence cut-off: not recorded" in text_value
    assert all(value not in text_value for value in ("67%", "50%", "70%", "Overall"))
    first_label = next(section.label for section in data.sections if section.assessment_id == first.id)
    second_label = next(section.label for section in data.sections if section.assessment_id == second.id)
    assert text_value.index("Assessment A finding") > text_value.rindex(first_label)
    assert text_value.index("Assessment A finding") < text_value.rindex(second_label)


def test_scenario_6_integrated_lifecycle_release_gate_and_source_change(
    db, http, gate, monkeypatch, upload_root
):
    """Scenario 6: integrated versions are newest-only issuable and release-gated."""
    engagement, first, _second, _third, first_conclusions = _setup_integrated(
        db, http, gate, monkeypatch
    )
    first_response = _generate_integrated(http, engagement)
    second_response = _generate_integrated(http, engagement)
    first_id = first_response.json()["snapshot_id"]
    second_id = second_response.json()["snapshot_id"]
    rows = report_snapshots.engagement_snapshot_rows(db, engagement, current_source=None)
    assert [row.state for row in rows] == ["draft", "superseded_draft"]
    before = _state(db, upload_root)
    old_issue = _issue_integrated(http, engagement, first_id)
    assert old_issue.status_code == 409
    assert _state(db, upload_root) == before
    assert _issue_integrated(http, engagement, second_id).status_code == 200

    third_response = _generate_integrated(http, engagement)
    third_id = third_response.json()["snapshot_id"]
    first.review_status = "pending"
    db.commit()
    before = _state(db, upload_root)
    blocked = _issue_integrated(http, engagement, third_id)
    assert blocked.status_code == 403
    assert "Every assessment in this version must still be approved" in unquote(
        blocked.headers["X-Toast-Message"]
    )
    assert _state(db, upload_root) == before
    first.review_status = "approved"
    db.commit()
    assert _issue_integrated(http, engagement, third_id).status_code == 200
    rows = report_snapshots.engagement_snapshot_rows(db, engagement, current_source=None)
    assert [row.snapshot.id for row in rows if row.is_current_issue] == [third_id]
    third_bytes = (upload_root / next(row for row in rows if row.snapshot.id == third_id).snapshot.storage_path).read_bytes()

    second_conclusion = next(
        row for row in first_conclusions if row.requirement_id == REQS[1]
    )
    _approved_finding(
        db, http, gate, monkeypatch, first, second_conclusion, title="Later finding"
    )
    data = report_content.integrated_report(db, engagement)
    later_rows = report_snapshots.engagement_snapshot_rows(
        db, engagement, current_source=data.source
    )
    third_row = next(row for row in later_rows if row.snapshot.id == third_id)
    assert third_row.source_changed is True
    assert (upload_root / third_row.snapshot.storage_path).read_bytes() == third_bytes


def test_scenario_7_validation_and_snapshot_scoping(db, http, gate, monkeypatch):
    """Scenario 7: unknown, excluded, missing-report and cross-scope requests write nothing."""
    unknown = "missing-engagement"
    assert http.get(f"/engagements/{unknown}/integrated-reports").status_code == 404
    assert http.post(f"/api/engagements/{unknown}/integrated-reports").status_code == 404
    assert http.post(f"/api/engagements/{unknown}/integrated-reports/x/issue").status_code == 404
    assert http.get(f"/api/engagements/{unknown}/integrated-reports/x/file").status_code == 404

    pending, _ = _run_one(db, gate, monkeypatch, approved=False)
    pending_engagement = db.get(Engagement, pending.engagement_id)
    response = _generate_integrated(http, pending_engagement)
    assert response.status_code == 400
    assert response.json()["detail"] == report_content.NOT_RELEASED or response.json()["detail"] == (
        "No assessment in this engagement is approved for release with a report. Nothing was generated."
    )

    no_report = _seed(db, client_name="No Report Client")
    no_report.review_status = "approved"
    db.commit()
    no_report_engagement = db.get(Engagement, no_report.engagement_id)
    assert _generate_integrated(http, no_report_engagement).status_code == 400
    page = http.get(f"/engagements/{no_report_engagement.id}/integrated-reports")
    assert "No analysis report yet" in page.text

    first, _ = _run_one(db, gate, monkeypatch, approved=True, client_name="Scope A")
    first_engagement = db.get(Engagement, first.engagement_id)
    generated = _generate_integrated(http, first_engagement)
    first_snapshot = generated.json()["snapshot_id"]
    second, _ = _run_one(db, gate, monkeypatch, approved=True, client_name="Scope B")
    second_engagement = db.get(Engagement, second.engagement_id)
    assert _issue_integrated(http, second_engagement, first_snapshot).status_code == 404
    assert http.get(
        f"/api/engagements/{second_engagement.id}/integrated-reports/{first_snapshot}/file"
    ).status_code == 404
    assessment_snapshot = http.post(
        f"/api/assessments/{first.id}/snapshots",
        data={"type": "gap_report", "reviewer_name": "Priya"},
    ).json()["snapshot_id"]
    assert http.get(
        f"/api/engagements/{second_engagement.id}/integrated-reports/{assessment_snapshot}/file"
    ).status_code == 404


def test_scenario_8_integrated_page_states_and_escaping(db, http, gate, monkeypatch):
    """Scenario 8: the page lists included/excluded assessments and snapshot lifecycle states."""
    engagement, _first, _second, third, _ = _setup_integrated(db, http, gate, monkeypatch)
    empty = http.get(f"/engagements/{engagement.id}/integrated-reports")
    assert empty.status_code == 200
    assert "No versions generated yet." in empty.text
    assert empty.text.count("data-included-assessment") == 2
    assert empty.text.count("data-excluded-assessment") == 1
    first = _generate_integrated(http, engagement)
    second = _generate_integrated(http, engagement)
    assert _issue_integrated(http, engagement, second.json()["snapshot_id"]).status_code == 200
    _generate_integrated(http, engagement)
    page = http.get(f"/engagements/{engagement.id}/integrated-reports")
    assert page.text.count("data-integrated-row") == 3
    assert "Issued (current)" in page.text
    assert "Draft (superseded)" in page.text
    assert page.text.count("/file") == 3
    assert page.text.count("data-issue-control") == 1
    assert "consultant:Priya" not in page.text
    assert "Priya" in page.text
    engagement.name = "<script>x</script>"
    db.commit()
    escaped = http.get(f"/engagements/{engagement.id}/integrated-reports")
    assert "<script>x</script>" not in escaped.text
    assert "&lt;script&gt;" in escaped.text
    detail = http.get(f"/engagements/{engagement.id}")
    assert f'href="/engagements/{engagement.id}/integrated-reports"' in detail.text


def test_scenario_9_snapshot_failure_cleanup(db, http, gate, monkeypatch, upload_root):
    """Scenario 9: event and commit failures leave no row or stored integrated file."""
    engagement, _first, _second, _third, _ = _setup_integrated(db, http, gate, monkeypatch)
    original_record_event = report_snapshots._record_event

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(report_snapshots, "_record_event", boom)
    with pytest.raises(RuntimeError, match="boom"):
        _generate_integrated(http, engagement)
    db.rollback()
    assert db.query(ReportSnapshot).filter_by(engagement_id=engagement.id).count() == 0
    root = upload_root / "reports" / "engagements"
    assert not root.exists() or not any(path.is_file() for path in root.rglob("*"))

    monkeypatch.setattr(report_snapshots, "_record_event", original_record_event)
    calls = []
    original_commit = db.commit

    def fail_once():
        if not calls:
            calls.append(1)
            raise RuntimeError("commit failed")
        return original_commit()

    monkeypatch.setattr(db, "commit", fail_once)
    response = _generate_integrated(http, engagement)
    assert response.status_code == 500
    assert response.json()["detail"] == "The report version could not be saved. Try again."
    db.rollback()
    assert db.query(ReportSnapshot).filter_by(engagement_id=engagement.id).count() == 0
    assert not root.exists() or not any(path.is_file() for path in root.rglob("*"))
    with pytest.raises(report_snapshots.InvalidSnapshot):
        report_snapshots.create_engagement_snapshot(
            db, engagement=engagement, content=b"", actor="consultant:Priya", source={}
        )


def test_scenario_10_structural_guards():
    """Scenario 10: route, read-only, storage and legacy-consumer guards stay exact."""
    route_set = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        if "/integrated-reports" in path:
            route_set.update((method, path) for method in (route.methods or set()))
    assert route_set == {
        ("GET", "/engagements/{engagement_id}/integrated-reports"),
        ("POST", "/api/engagements/{engagement_id}/integrated-reports"),
        ("POST", "/api/engagements/{engagement_id}/integrated-reports/{snapshot_id}/issue"),
        ("GET", "/api/engagements/{engagement_id}/integrated-reports/{snapshot_id}/file"),
    }
    router_source = Path("app/routers/integrated_reports.py").read_text()
    assert router_source.count(".unlink(") == 1
    assert "delete" not in router_source.lower()
    assert not re.search(r"\.is_issued\s*=(?!=)", router_source)
    assert not re.search(r"SET\s+is_issued\s*=\s*0", router_source, re.I)
    assert ".commit(" in router_source
    content_source = Path("app/services/report_content.py").read_text()
    assert not any(token in content_source for token in ("db.add(", "db.add_all(", "db.merge(", ".flush(", ".commit(", "delete"))
    snapshots_source = Path("app/services/report_snapshots.py").read_text()
    assert snapshots_source.count(".open(") == 1
    assert snapshots_source.count(".unlink(") == 1
    assert not re.search(r"Conclusion|AnalysisRun|analysis_pipeline", Path("app/utils/pdf_export.py").read_text() + Path("app/routers/reports.py").read_text())
    template_source = Path("app/templates/pages/integrated_reports.html").read_text()
    assert not re.search(r"overall_score|CyberAssess|\|\s*safe\b", template_source)
    assert ".commit(" not in inspect.getsource(web.integrated_reports_page)


def test_scenario_11_pdf_sanitizes_and_wraps_long_finding_text(db, http, gate, monkeypatch):
    """Scenario 11: Unicode punctuation and long descriptions/excerpts render safely."""
    assessment, conclusion = _run_one(
        db, gate, monkeypatch, item=_item(REQS[0], "non_compliant")
    )
    excerpt = "Grounded quote " + ("x" * 2500)
    finding = _approved_finding(
        db,
        http,
        gate,
        monkeypatch,
        assessment,
        conclusion,
        excerpt=excerpt,
        title="Policy “review” – owner’s sign-off…",
        description="d" * 2500,
    )
    assessment.review_status = "approved"
    db.commit()
    text_value = _pdf_text(
        _assessment_pdf(db, assessment, report_content.assessment_findings(db, assessment))
    )
    assert 'Policy "review"' in text_value
    assert excerpt[:100] in text_value
    assert "..." in text_value


# Scenario 12 is the full-suite verification required by the handoff. The existing
# P3-1, P3-2, scoring, pipeline, golden, white-label, and workpaper files remain
# unmodified and are run by the implementation verification command.
