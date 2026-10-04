"""Seed deterministic S4 screen data into a throwaway SQLite database.

This harness deliberately does not start the app, access the network, or create
report/evidence blobs. The orchestrator can point its app process at the
resulting database and choose the matching screen/state from ``SCREEN_STATES``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.models  # noqa: F401 - register every model before create_all()
from app.database import Base
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion
from app.models.conclusion import ConclusionRevision
from app.models.engagement import Engagement
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.firm_settings import FirmSettings
from app.models.magic_link import MagicLink
from app.models.report_snapshot import ReportSnapshot


FROZEN_NOW = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
SEED_ACTOR = "consultant:Priya Sharma"
SCREEN_STATES = {
    "engagement_list": ("default", "empty", "loading", "error"),
    "new_engagement": ("default", "new-client", "empty", "error"),
    "engagement_detail": (
        "default",
        "archived",
        "archiving",
        "empty",
        "loading",
        "error",
        "blocked",
    ),
    "remediation_tracker": ("default", "empty", "loading", "error", "embedded"),
    "integrated_reports": (
        "default",
        "issue",
        "empty",
        "none-approved",
        "loading",
        "error",
    ),
    "engagement_purge": ("default", "blocked", "confirm", "error"),
}


def _time(days: int = 0) -> datetime:
    return FROZEN_NOW + timedelta(days=days)


def _client(client_id: str, name: str, industry: str, size: str) -> Client:
    return Client(
        id=client_id,
        name=name,
        industry=industry,
        size=size,
        retention_years=7,
        created_at=_time(-90),
        updated_at=_time(-2),
    )


def _engagement(
    engagement_id: str,
    client_id: str,
    name: str,
    *,
    status: str = "active",
    days=-30,
) -> Engagement:
    return Engagement(
        id=engagement_id,
        client_id=client_id,
        name=name,
        type="gap_assessment",
        status=status,
        created_at=_time(days),
        updated_at=_time(-2 if status != "archived" else -30),
    )


def _assessment(
    assessment_id: str,
    engagement_id: str,
    company_name: str,
    name: str,
    frameworks: tuple[str, ...] = ("dpdpa", "iso27001"),
    *,
    status: str = "created",
    days=-28,
) -> Assessment:
    return Assessment(
        id=assessment_id,
        engagement_id=engagement_id,
        company_name=company_name,
        name=name,
        industry="Technology",
        company_size="medium",
        description="Primary operating environment and supporting systems",
        status=status,
        selected_frameworks=json.dumps(list(frameworks)),
        created_at=_time(days),
        updated_at=_time(-3),
    )


def _audit(
    event_id: str,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    created_at: datetime,
    metadata: dict | None = None,
    actor: str = SEED_ACTOR,
) -> AuditEvent:
    return AuditEvent(
        id=event_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        metadata_json=json.dumps(metadata or {}, sort_keys=True),
        created_at=created_at,
    )


def _report_snapshot(
    snapshot_id: str,
    *,
    assessment_id: str | None = None,
    engagement_id: str | None = None,
    generated_at: datetime,
    issued: bool = True,
    issued_at: datetime | None = None,
    size_bytes: int = 184320,
    source: dict | None = None,
) -> tuple[ReportSnapshot, list[AuditEvent]]:
    storage_path = (
        f"reports/assessments/{assessment_id}/{snapshot_id}.pdf"
        if assessment_id
        else f"reports/engagements/{engagement_id}/{snapshot_id}.pdf"
    )
    snapshot = ReportSnapshot(
        id=snapshot_id,
        assessment_id=assessment_id,
        engagement_id=engagement_id,
        type="gap_report" if assessment_id else "integrated_report",
        format="pdf",
        storage_path=storage_path,
        generated_at=generated_at,
        is_issued=issued,
    )
    metadata = {
        "schema_version": 1,
        "sha256": ("s4" + snapshot_id.replace("-", ""))[:64].ljust(64, "0"),
        "size_bytes": size_bytes,
    }
    if source is not None:
        metadata["source"] = source
    events = [
        _audit(
            f"audit-generated-{snapshot_id}",
            action="report_snapshot.generated",
            entity_type="report_snapshot",
            entity_id=snapshot_id,
            created_at=generated_at,
            metadata=metadata,
        )
    ]
    if issued:
        events.append(
            _audit(
                f"audit-issued-{snapshot_id}",
                action="report_snapshot.issued",
                entity_type="report_snapshot",
                entity_id=snapshot_id,
                created_at=issued_at or generated_at + timedelta(hours=2),
            )
        )
    return snapshot, events


def _add_actions(db: Session, assessment: Assessment) -> None:
    conclusion = Conclusion(
        id=f"conclusion-{assessment.id}",
        assessment_id=assessment.id,
        framework_id="dpdpa",
        requirement_id="CH2.SECURITY.1",
        outcome="partially_compliant",
        rationale="The control is partly implemented and needs operating evidence.",
        evidence_summary="Access review evidence is incomplete.",
        gaps_identified="Quarterly review evidence is not retained consistently.",
        risk_level="high",
        recommended_action="Document and test the access review process.",
        ai_proposed=False,
        created_at=_time(-20),
        updated_at=_time(-4),
    )
    finding = Finding(
        id=f"finding-{assessment.id}",
        assessment_id=assessment.id,
        conclusion_id=conclusion.id,
        title="Access reviews need retained evidence",
        description="The access review process is not consistently evidenced.",
        business_impact="Unreviewed access can remain active longer than intended.",
        recommendation="Retain quarterly review evidence and track exceptions.",
        severity="high",
        priority=1,
        status="open",
        created_at=_time(-18),
        updated_at=_time(-4),
    )
    action = Action(
        id=f"action-{assessment.id}",
        finding_id=finding.id,
        title="Retain quarterly access review evidence",
        owner="Security operations",
        responsibility="owner",
        target_date=_time(-3),
        status="open",
        history_json="[]",
        created_at=_time(-18),
        updated_at=_time(-3),
    )
    db.add_all(
        [
            conclusion,
            finding,
            action,
            ConclusionRevision(
                id=f"revision-{assessment.id}",
                conclusion_id=conclusion.id,
                actor=SEED_ACTOR,
                action="proposed",
                created_at=_time(-4),
            ),
        ]
    )


def _seed_portfolio(db: Session, *, state: str, screen: str) -> dict:
    clients = [
        _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large"),
        _client("client-loomwire", "Loomwire Labs", "IT services", "medium"),
        _client("client-kestrel", "Kestrel Advisory", "Professional services", "small"),
    ]
    db.add_all(clients)
    if state == "empty" and screen in {"engagement_list", "new_engagement"}:
        return {"clients": [], "engagements": []}

    # The detail/remediation/report specimens all use the same canonical
    # engagement. Keep it on the Meridian client so every linked surface has
    # identical copy and never falls through to the single-assessment redirect.
    kestrel = _engagement("eng-kestrel", clients[0].id, "FY2026 privacy readiness")
    meridian = _engagement("eng-meridian", clients[0].id, "Payments security gap assessment")
    loomwire = _engagement("eng-loomwire", clients[1].id, "NIST CSF baseline")
    gdpr = _engagement("eng-loomwire-gdpr", clients[1].id, "GDPR readiness")
    vendor = _engagement("eng-loomwire-vendor", clients[1].id, "Vendor risk review")
    prior = _engagement("eng-meridian-fy2025", clients[0].id, "FY2025 DPDPA assessment")
    engagements = [kestrel, meridian, loomwire, gdpr, vendor, prior]
    db.add_all(engagements)
    assessments = [
        _assessment("assessment-head-office", kestrel.id, clients[0].name, "Head office", ("dpdpa", "iso27001")),
        _assessment("assessment-payments", kestrel.id, clients[0].name, "Payments subsidiary", ("iso27001",)),
        _assessment("assessment-meridian-payments", meridian.id, clients[0].name, "Payments security", ("iso27001", "nist_csf")),
        _assessment("assessment-loomwire-nist", loomwire.id, clients[1].name, "NIST baseline", ("nist_csf",)),
        _assessment("assessment-loomwire-gdpr", gdpr.id, clients[1].name, "GDPR readiness", ("gdpr",)),
        _assessment("assessment-loomwire-vendor", vendor.id, clients[1].name, "Vendor risk", ("iso27001",)),
        _assessment("assessment-meridian-fy2025", prior.id, clients[0].name, "FY2025 DPDPA", ("dpdpa",), status="completed", days=-220),
    ]
    db.add_all(assessments)
    if screen == "remediation_tracker" and state != "default":
        _add_actions(db, assessments[0])
    return {"clients": clients, "engagements": engagements, "assessments": assessments}


def _seed_archived(
    db: Session,
    *,
    eligible: bool,
    dependency: bool,
    invalid: bool = False,
    detail_date: bool = False,
) -> dict:
    client = _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large")
    engagement = _engagement(
        "eng-meridian-archive",
        client.id,
        "FY2026 privacy readiness",
        status="archived",
        days=-400,
    )
    assessments = [
        _assessment("assessment-archive-head-office", engagement.id, client.name, "Head office", ("dpdpa", "iso27001")),
        _assessment("assessment-archive-payments", engagement.id, client.name, "Payments subsidiary", ("iso27001",)),
    ]
    db.add_all([client, engagement, *assessments])
    metadata = (
        {"schema_version": 1, "client_id": client.id, "previous_status": "active"}
        if invalid
        else {
            "schema_version": 1,
            "client_id": client.id,
            "previous_status": "active",
            "retention_years": 7,
            "retention_source": "firm",
        }
    )
    archive_at = (
        datetime(2026, 2, 3, 12, tzinfo=timezone.utc)
        if detail_date or not eligible
        else datetime(2019, 1, 14, 12, tzinfo=timezone.utc)
    )
    db.add(
        _audit(
            "audit-archive-meridian",
            action="engagement.archived",
            entity_type="engagement",
            entity_id=engagement.id,
            created_at=archive_at,
            metadata=metadata,
        )
    )
    if dependency:
        # Sorts after the archived engagement so the harness (first engagement id) opens the
        # archived one, not this dependency.
        other = _engagement("eng-other-dependency", client.id, "Loomwire dependency")
        db.add(other)
        db.add(
            Evidence(
                id="evidence-external-dependency",
                engagement_id=other.id,
                assessment_id=assessments[0].id,
                original_filename="shared-review.pdf",
                storage_path=f"evidence/{engagement.id}/shared-review.pdf",
                file_hash_sha256="0" * 64,
                file_size_bytes=1024,
                mime_type="application/pdf",
                status="available",
                uploaded_by=SEED_ACTOR,
                created_at=_time(-10),
            )
        )
    return {"clients": [client], "engagements": [engagement], "assessments": assessments}


def _seed_purge_inventory(db: Session, data: dict) -> None:
    """Give purge states the same record volumes shown in the specimen."""
    engagement = data["engagements"][0]
    assessments = data["assessments"]
    if len(assessments) < 3:
        extra = _assessment(
            "assessment-archive-legacy",
            engagement.id,
            "Meridian Ledger Technologies",
            "Legacy records",
            ("dpdpa",),
            days=-410,
        )
        db.add(extra)
        assessments.append(extra)

    for index in range(148):
        evidence_id = f"purge-evidence-{index:03d}"
        assessment = assessments[index % len(assessments)]
        db.add(
            Evidence(
                id=evidence_id,
                engagement_id=engagement.id,
                assessment_id=assessment.id,
                original_filename=f"evidence-{index:03d}.pdf",
                storage_path=f"evidence/{engagement.id}/evidence-{index:03d}.pdf",
                file_hash_sha256=(f"{index:064x}")[-64:],
                file_size_bytes=1024,
                mime_type="application/pdf",
                status="available",
                uploaded_by=SEED_ACTOR,
                created_at=_time(-30),
            )
        )
    for index in range(64):
        assessment = assessments[index % len(assessments)]
        conclusion_id = f"purge-conclusion-{index:03d}"
        finding_id = f"purge-finding-{index:03d}"
        db.add(
            Conclusion(
                id=conclusion_id,
                assessment_id=assessment.id,
                framework_id="dpdpa",
                requirement_id=f"S4.PURGE.{index:03d}",
                outcome="partially_compliant",
                rationale="Seeded purge record.",
                evidence_summary="Seeded evidence.",
                gaps_identified="Seeded gap.",
                risk_level="medium",
                recommended_action="Resolve the seeded finding.",
                ai_proposed=False,
                created_at=_time(-30),
                updated_at=_time(-4),
            )
        )
        db.add(
            Finding(
                id=finding_id,
                assessment_id=assessment.id,
                conclusion_id=conclusion_id,
                title=f"Seeded purge finding {index + 1}",
                description="Seeded finding for the permanent purge specimen.",
                business_impact="Seeded impact.",
                recommendation="Resolve the finding.",
                severity="medium",
                priority=index + 1,
                status="open",
                created_at=_time(-30),
                updated_at=_time(-4),
            )
        )
    for index in range(31):
        db.add(
            Action(
                id=f"purge-action-{index:03d}",
                finding_id=f"purge-finding-{index:03d}",
                title=f"Seeded remediation action {index + 1}",
                owner="Meridian IT security",
                responsibility="owner",
                target_date=_time(-3),
                status="open",
                history_json="[]",
                created_at=_time(-30),
                updated_at=_time(-3),
            )
        )
    for index in range(6):
        db.add(
            ReportSnapshot(
                id=f"purge-report-{index:03d}",
                engagement_id=engagement.id,
                type="integrated_report",
                format="pdf",
                storage_path=f"reports/engagements/{engagement.id}/purge-report-{index:03d}.pdf",
                generated_at=_time(-index - 1),
                is_issued=index < 3,
            )
        )


# --- Specimen alignment -----------------------------------------------------------------
# The helpers below give the gated states the same real records the approved specimens show, so
# the pages render them from the database (never from template constants).


def _seed_review_stage(db: Session, assessment: Assessment, *, approved: int = 3, pending: int = 3) -> None:
    """Scope set, questionnaire fully answered, and approved + pending conclusions: the
    assessment_stage service then reports "Review · {approved} of {approved+pending} approved"."""
    from app.frameworks.registry import FrameworkRegistry
    from app.models.questionnaire import QuestionnaireResponse
    from app.services.question_engine import build_adaptive_questionnaire

    assessment.scope_answers = json.dumps({})
    db.flush()
    for _ in range(5):
        questionnaire = build_adaptive_questionnaire(assessment.id, db)
        question_ids = [
            question["id"]
            for section in questionnaire.get("sections", [])
            for question in section.get("questions", [])
            if question.get("status") != "skipped"
        ]
        answered = {
            row[0]
            for row in db.query(QuestionnaireResponse.question_id).filter(
                QuestionnaireResponse.assessment_id == assessment.id
            )
        }
        missing = [question_id for question_id in question_ids if question_id not in answered]
        if not missing:
            break
        for question_id in missing:
            db.add(
                QuestionnaireResponse(
                    assessment_id=assessment.id,
                    question_id=question_id,
                    answer="fully_implemented",
                )
            )
        db.flush()
    framework_id = assessment.frameworks[0]
    controls = FrameworkRegistry.get_all_controls(framework_id)[: approved + pending]
    for index, control in enumerate(controls):
        conclusion = Conclusion(
            id=f"conclusion-review-{assessment.id}-{index}",
            assessment_id=assessment.id,
            framework_id=framework_id,
            requirement_id=control.id,
            outcome="partially_compliant",
            rationale="Seeded conclusion awaiting review.",
            evidence_summary="Seeded evidence summary.",
            gaps_identified="Seeded gap.",
            risk_level="medium",
            recommended_action="Seeded recommendation.",
            ai_proposed=True,
            created_at=_time(-6),
            updated_at=_time(-5),
        )
        db.add(conclusion)
        db.flush()
        db.add(
            ConclusionRevision(
                id=f"revision-proposed-{conclusion.id}",
                conclusion_id=conclusion.id,
                actor="system:analysis",
                action="proposed",
                created_at=_time(-6),
            )
        )
        if index < approved:
            db.add(
                ConclusionRevision(
                    id=f"revision-approved-{conclusion.id}",
                    conclusion_id=conclusion.id,
                    actor=SEED_ACTOR,
                    action="approved",
                    created_at=_time(-5),
                )
            )
    db.flush()


def _seed_released(db: Session, assessment: Assessment, *, per_framework: int = 2) -> None:
    """A released assessment: a gap report, an approved conclusion for each in-scope control and
    the release record written by approved_report.record_release (the real release path)."""
    from app.frameworks.registry import FrameworkRegistry
    from app.models.report import GapReport
    from app.services import approved_report

    applicable = []
    for framework_id in assessment.frameworks:
        applicable.extend(control.id for control in FrameworkRegistry.get_all_controls(framework_id)[:per_framework])
    assessment.applicable_requirements = json.dumps(applicable)
    assessment.scope_answers = json.dumps({})
    db.add(
        GapReport(
            id=f"gap-report-{assessment.id}",
            assessment_id=assessment.id,
            overall_score=0.0,
            chapter_scores="{}",
            executive_summary="Seeded analysis report.",
            raw_ai_response="{}",
            framework_scores=None,
            generated_at=_time(-12),
        )
    )
    db.flush()
    for framework_id in assessment.frameworks:
        for index, control in enumerate(FrameworkRegistry.get_all_controls(framework_id)[:per_framework]):
            conclusion = Conclusion(
                id=f"conclusion-released-{assessment.id}-{framework_id}-{index}",
                assessment_id=assessment.id,
                framework_id=framework_id,
                requirement_id=control.id,
                outcome="compliant",
                rationale="Seeded approved conclusion.",
                evidence_summary="Seeded evidence summary.",
                gaps_identified="None.",
                risk_level="low",
                recommended_action="None.",
                ai_proposed=True,
                created_at=_time(-12),
                updated_at=_time(-11),
            )
            db.add(conclusion)
            db.flush()
            db.add(ConclusionRevision(id=f"revision-proposed-{conclusion.id}", conclusion_id=conclusion.id,
                                      actor="system:analysis", action="proposed", created_at=_time(-12)))
            db.add(ConclusionRevision(id=f"revision-approved-{conclusion.id}", conclusion_id=conclusion.id,
                                      actor=SEED_ACTOR, action="approved", created_at=_time(-11)))
    db.flush()
    approved_report.record_release(db, assessment, actor=SEED_ACTOR)
    db.flush()


def _seed_evidence(db: Session, engagement: Engagement, assessment: Assessment, count: int, prefix: str) -> None:
    for index in range(count):
        db.add(
            Evidence(
                id=f"{prefix}-{index:03d}",
                engagement_id=engagement.id,
                assessment_id=assessment.id,
                original_filename=f"evidence-{index:03d}.pdf",
                storage_path=f"evidence/{engagement.id}/{prefix}-{index:03d}.pdf",
                file_hash_sha256=(f"{index:064x}")[-64:],
                file_size_bytes=1024,
                mime_type="application/pdf",
                status="available",
                uploaded_by=SEED_ACTOR,
                created_at=_time(-30),
            )
        )


def _seed_action(
    db: Session,
    assessment: Assessment,
    key: str,
    *,
    framework_id: str,
    requirement_id: str,
    severity: str,
    status: str,
    owner: str | None,
    target: datetime,
    title: str,
    finding_title: str,
    updated_at: datetime | None = None,
) -> None:
    conclusion = Conclusion(
        id=f"conclusion-{key}",
        assessment_id=assessment.id,
        framework_id=framework_id,
        requirement_id=requirement_id,
        outcome="partially_compliant",
        rationale="Seeded remediation conclusion.",
        evidence_summary="Seeded evidence summary.",
        gaps_identified=finding_title,
        risk_level=severity,
        recommended_action=title,
        ai_proposed=False,
        created_at=_time(-40),
        updated_at=_time(-20),
    )
    finding = Finding(
        id=f"finding-{key}",
        assessment_id=assessment.id,
        conclusion_id=conclusion.id,
        title=finding_title,
        description=finding_title,
        business_impact="Seeded impact.",
        recommendation=title,
        severity=severity,
        priority=1,
        status="open",
        created_at=_time(-35),
        updated_at=_time(-20),
    )
    action = Action(
        id=f"action-{key}",
        finding_id=finding.id,
        title=title,
        owner=owner,
        responsibility="owner",
        target_date=target,
        status=status,
        history_json="[]",
        created_at=_time(-35),
        updated_at=updated_at or _time(-10),
    )
    db.add_all([conclusion, finding, action])
    db.flush()


def _seed_open_actions(db: Session, assessment: Assessment, count: int) -> None:
    """Open actions (the Overview's "Open actions" tile) on one assessment."""
    from app.frameworks.registry import FrameworkRegistry

    framework_id = assessment.frameworks[0]
    controls = FrameworkRegistry.get_all_controls(framework_id)
    for index in range(count):
        _seed_action(
            db,
            assessment,
            f"open-{assessment.id}-{index}",
            framework_id=framework_id,
            requirement_id=controls[index].id,
            severity="medium",
            status="open",
            owner="Meridian IT security",
            target=datetime(2026, 12, 15, tzinfo=timezone.utc),
            title=f"Seeded open action {index + 1}",
            finding_title=f"Seeded finding {index + 1}",
        )


SEP = lambda day: datetime(2026, 9, day, 12, tzinfo=timezone.utc)  # noqa: E731
OCT = lambda day: datetime(2026, 10, day, 12, tzinfo=timezone.utc)  # noqa: E731
LATER = datetime(2026, 12, 15, 12, tzinfo=timezone.utc)


def _seed_remediation_rollup(db: Session, head_office: Assessment, payments: Assessment) -> None:
    """Thirty-one actions across the two assessments, close to the Findings and actions specimen:
    three overdue and three awaiting verification with the specimen's titles, the rest spread over
    severities, statuses and owners."""
    from app.frameworks.registry import FrameworkRegistry

    controls = {
        framework_id: iter(control.id for control in FrameworkRegistry.get_all_controls(framework_id))
        for framework_id in ("dpdpa", "iso27001")
    }
    it, legal, platform = "Meridian IT security", "Meridian legal and privacy", "Meridian platform engineering"
    named = [
        # Overdue (active, target in the past).
        (head_office, "iso27001", "critical", "open", it, SEP(12), "Enforce MFA on service accounts", "Three service accounts exempt from MFA", None),
        (head_office, "dpdpa", "high", "in_progress", legal, SEP(20), "Add in-app consent withdrawal", "No in-app consent withdrawal", None),
        (head_office, "iso27001", "high", "open", it, SEP(28), "Test the DR failover against the 4-hour target", "DR failover exceeded the 4-hour RTO", None),
        # Awaiting verification (closed), in the order they were closed.
        (head_office, "dpdpa", "high", "closed", legal, OCT(15), "Publish a retention schedule for customer data", "No documented retention schedule", _time(-9)),
        (payments, "iso27001", "medium", "closed", platform, SEP(30), "Rotate shared admin credentials", "Shared admin credentials in the build system", _time(-8)),
        (head_office, "iso27001", "low", "closed", it, OCT(8), "Encrypt backups at rest", "Backups stored without encryption", _time(-7)),
    ]
    # (assessment, severity, status, owner) for the remaining actions, all due later.
    rest = (
        [(head_office, "critical", "in_progress", it), (head_office, "critical", "verified", it)]
        + [(head_office, "high", "open", it), (head_office, "high", "open", legal), (payments, "high", "open", None)]
        + [(head_office, "high", "in_progress", platform), (head_office, "high", "in_progress", legal)]
        + [(head_office, "high", "verified", it)] * 3 + [(payments, "high", "verified", platform)] * 2
        + [(head_office, "medium", "open", legal), (head_office, "medium", "open", it), (head_office, "medium", "open", platform)]
        + [(head_office, "medium", "in_progress", it), (payments, "medium", "in_progress", None)]
        + [(head_office, "medium", "verified", legal)] * 4
        + [(head_office, "low", "open", legal), (head_office, "low", "in_progress", platform)]
        + [(head_office, "low", "verified", it)] * 2
    )
    for index, (assessment, framework_id, severity, status, owner, target, title, finding_title, updated_at) in enumerate(named):
        if assessment is payments:
            framework_id = "iso27001"
        _seed_action(
            db, assessment, f"named-{index}", framework_id=framework_id,
            requirement_id=next(controls[framework_id]), severity=severity, status=status,
            owner=owner, target=target, title=title, finding_title=finding_title, updated_at=updated_at,
        )
    for index, (assessment, severity, status, owner) in enumerate(rest):
        framework_id = "iso27001" if assessment is payments or index % 2 else "dpdpa"
        _seed_action(
            db, assessment, f"rest-{index}", framework_id=framework_id,
            requirement_id=next(controls[framework_id]), severity=severity, status=status,
            owner=owner, target=LATER, title=f"Remediation action {index + 1}",
            finding_title=f"Remediation finding {index + 1}",
        )


def _align_overview(db: Session, data: dict) -> None:
    """Overview specimen: Head office in review (3 of 6 approved), Payments subsidiary at scope,
    148 evidence items and 9 open actions."""
    engagement = data["engagements"][0]
    head_office, payments = data["assessments"][0], data["assessments"][1]
    head_office.description = "Mumbai head office and cloud estate"
    payments.description = "Payments processing platform"
    db.flush()
    _seed_review_stage(db, head_office)
    _seed_evidence(db, engagement, payments, 148, f"overview-evidence-{engagement.id}")
    _seed_open_actions(db, payments, 9)


def _align_integrated(db: Session, data: dict, state: str) -> None:
    """Integrated report specimen: head office released and included, payments subsidiary not."""
    if not data.get("assessments"):
        return
    head_office, payments = data["assessments"][0], data["assessments"][1]
    head_office.description = "Meridian Ledger, head office"
    payments.description = "Meridian Ledger, payments subsidiary"
    db.flush()
    _seed_released(db, head_office)


def _align_engagement_list(db: Session, data: dict) -> None:
    """Engagement list specimen: row order, stages, progress and Updated dates."""
    assessments = {assessment.id: assessment for assessment in data["assessments"]}
    engagements = {engagement.id: engagement for engagement in data["engagements"]}
    # Row order is newest engagement activity first.
    order = ["eng-kestrel", "eng-meridian", "eng-loomwire", "eng-loomwire-gdpr", "eng-loomwire-vendor", "eng-meridian-fy2025"]
    for rank, engagement_id in enumerate(order):
        engagements[engagement_id].updated_at = _time(-rank)
    specs = {
        # assessment id: (Updated, workflow status, scope set, questionnaire answers)
        "assessment-head-office": (datetime(2026, 9, 28, 12, tzinfo=timezone.utc), "questionnaire_done", True, 1),
        "assessment-payments": (datetime(2026, 9, 20, 12, tzinfo=timezone.utc), "context_gathered", False, 0),
        "assessment-meridian-payments": (datetime(2026, 9, 24, 12, tzinfo=timezone.utc), "scoped", False, 0),
        "assessment-loomwire-nist": (datetime(2026, 9, 30, 12, tzinfo=timezone.utc), "context_gathered", True, 0),
        "assessment-loomwire-gdpr": (datetime(2026, 9, 21, 12, tzinfo=timezone.utc), "documents_uploaded", True, 0),
        "assessment-loomwire-vendor": (datetime(2026, 9, 29, 12, tzinfo=timezone.utc), "error", True, 1),
        "assessment-meridian-fy2025": (datetime(2026, 3, 12, 12, tzinfo=timezone.utc), "completed", True, 0),
    }
    # NIST CSF baseline is in review (conclusions awaiting decisions); the FY2025 assessment has
    # every conclusion approved, so its stage is Report.
    _seed_review_stage(db, assessments["assessment-loomwire-nist"], approved=2, pending=4)
    _seed_review_stage(db, assessments["assessment-meridian-fy2025"], approved=6, pending=0)
    from app.models.questionnaire import QuestionnaireResponse

    for assessment_id, (updated_at, status, scoped, answers) in specs.items():
        assessment = assessments[assessment_id]
        assessment.updated_at = updated_at
        assessment.status = status
        if scoped:
            assessment.scope_answers = json.dumps({})
        for index in range(answers):
            db.add(
                QuestionnaireResponse(
                    assessment_id=assessment.id,
                    question_id=f"CLUSTER_{index + 1:03d}",
                    answer="partially_implemented",
                )
            )
    db.flush()


def _report_basis_event(assessment: Assessment) -> AuditEvent:
    """Record the review period the specimens show (1 Apr 2025 to 31 Mar 2026, cut-off 15 Mar 2026)."""
    return _audit(
        f"audit-basis-{assessment.id}",
        action="assessment.report_basis_updated",
        entity_type="assessment",
        entity_id=assessment.id,
        created_at=_time(-27),
        metadata={
            "after": {
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "evidence_cutoff": "2026-03-15",
                "prepared_by": None,
                "reviewed_by": None,
            }
        },
    )


def _add_integrated_versions(db: Session, engagement: Engagement) -> None:
    """Four integrated report versions: v1 superseded draft, v2 and v3 issued, v4 a draft generated
    before the current source data (so it shows "Source data changed")."""
    from app.services import report_content

    current_source = report_content.integrated_report(db, engagement).source
    stale_source = {**current_source, "seed": "superseded inputs"}
    specs = [
        ("snapshot-meridian-v1", datetime(2026, 9, 2, 12, tzinfo=timezone.utc), None, 1468006, current_source),
        ("snapshot-meridian-v2", datetime(2026, 9, 11, 12, tzinfo=timezone.utc), datetime(2026, 9, 12, 10, tzinfo=timezone.utc), 1677722, current_source),
        ("snapshot-meridian-v3", datetime(2026, 9, 24, 12, tzinfo=timezone.utc), datetime(2026, 9, 25, 10, tzinfo=timezone.utc), 1782579, current_source),
        ("snapshot-meridian-v4", datetime(2026, 9, 30, 12, tzinfo=timezone.utc), None, 1887437, stale_source),
    ]
    for snapshot_id, generated_at, issued_at, size_bytes, source in specs:
        snapshot, events = _report_snapshot(
            snapshot_id,
            engagement_id=engagement.id,
            generated_at=generated_at,
            issued=issued_at is not None,
            issued_at=issued_at,
            size_bytes=size_bytes,
            source=source,
        )
        db.add(snapshot)
        db.flush()
        db.add_all(events)
        db.flush()


def seed_s4(output: str | Path, *, screen: str = "engagement_list", state: str = "default") -> dict:
    """Create one deterministic database for one S4 screen state."""
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.gdpr import GDPR_DEFINITION
    from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
    from app.frameworks.registry import FrameworkRegistry

    for framework in (
        DPDPA_DEFINITION,
        ISO27001_DEFINITION,
        GDPR_DEFINITION,
        HIPAA_DEFINITION,
        NIST_CSF_DEFINITION,
        PCI_DSS_DEFINITION,
    ):
        FrameworkRegistry.register(framework)
    if screen not in SCREEN_STATES:
        raise ValueError(f"unknown screen {screen!r}")
    if state not in SCREEN_STATES[screen]:
        raise ValueError(f"unknown state {state!r} for {screen}")
    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    engine = create_engine(f"sqlite:///{output_path}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(FirmSettings(id=1, archived_retention_years=7, accent_theme="midnight", updated_at=FROZEN_NOW))
        if screen == "engagement_purge":
            data = _seed_archived(
                db,
                # "error" is the failed-purge alert over an otherwise eligible engagement.
                eligible=state in {"default", "confirm", "error"},
                dependency=state == "blocked",
            )
            _seed_purge_inventory(db, data)
        elif screen == "engagement_detail" and state == "archived":
            data = _seed_archived(db, eligible=False, dependency=False, detail_date=True)
        elif screen == "engagement_detail" and state == "empty":
            empty_client = _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large")
            empty_engagement = _engagement("eng-empty", empty_client.id, "FY2026 privacy readiness")
            db.add(empty_client)
            db.add(empty_engagement)
            data = {"clients": [empty_client], "engagements": [empty_engagement], "assessments": []}
        elif screen == "integrated_reports" and state == "empty":
            # The harness opens the first engagement id; "none" sorts first. Two assessments, one
            # released, and no versions yet.
            empty_client = _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large")
            empty_engagement = _engagement("none", empty_client.id, "FY2026 privacy readiness")
            empty_assessments = [
                _assessment("assessment-head-office", empty_engagement.id, empty_client.name, "Head office", ("dpdpa", "iso27001")),
                _assessment("assessment-payments", empty_engagement.id, empty_client.name, "Payments subsidiary", ("iso27001",)),
            ]
            db.add_all([empty_client, empty_engagement, *empty_assessments])
            data = {"clients": [empty_client], "engagements": [empty_engagement], "assessments": empty_assessments}
        elif screen == "integrated_reports" and state == "none-approved":
            data = _seed_portfolio(db, state="default", screen="engagement_list")
        elif screen == "new_engagement" and state == "empty":
            data = _seed_portfolio(db, state="empty", screen="new_engagement")
        else:
            data = _seed_portfolio(db, state=state, screen=screen)

        for assessment in data.get("assessments", []):
            db.add(_report_basis_event(assessment))
        db.flush()
        if screen == "engagement_list" and state == "default":
            _align_engagement_list(db, data)
        if screen == "engagement_detail" and state in {"default", "archived", "archiving", "blocked"}:
            _align_overview(db, data)
        if screen == "remediation_tracker" and state == "default":
            _seed_remediation_rollup(db, data["assessments"][0], data["assessments"][1])
        if screen == "integrated_reports" and state not in {"none-approved"}:
            _align_integrated(db, data, state)
        if (screen == "integrated_reports" and state not in {"empty", "none-approved"}) or (
            screen == "engagement_detail" and state in {"default", "archived", "archiving", "blocked"}
        ):
            db.flush()
            _add_integrated_versions(db, data["engagements"][0])
        db.commit()
    engine.dispose()
    return {
        "output": str(output_path),
        "screen": screen,
        "state": state,
        "frozen_now": FROZEN_NOW.isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/yozora-s4.sqlite3")
    parser.add_argument("--screen", choices=tuple(SCREEN_STATES), default="engagement_list")
    parser.add_argument("--state", default="default")
    args = parser.parse_args()
    print(json.dumps(seed_s4(args.output, screen=args.screen, state=args.state), sort_keys=True))


if __name__ == "__main__":
    main()
