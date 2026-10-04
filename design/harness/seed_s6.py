"""Seed deterministic S6 evidence/workpaper data into throwaway SQLite.

The seed imports the S4 builders and frozen clock, never starts the app, and
does not make network or model calls. States that are interaction-only are
selected with ``?state=...`` by the preview harness.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.models  # noqa: F401 - register every model before create_all()
from app.database import Base
from app.frameworks.registry import FrameworkRegistry
from app.models.analysis_run import AnalysisRun
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.questionnaire import QuestionnaireResponse
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.firm_settings import FirmSettings
from app.models.magic_link import MagicLink
from app.models.audit_event import AuditEvent
from design.harness.seed_s4 import (
    FROZEN_NOW,
    SEED_ACTOR,
    _assessment,
    _audit,
    _client,
    _engagement,
    _seed_evidence,
    _seed_review_stage,
    _time,
)


SCREEN_STATES = {
    "evidence": ("default", "upload", "empty", "loading", "error", "prefill", "all"),
    "aws_evidence": ("ready", "pulling", "result", "error", "notconfigured"),
    "evidence_reuse": ("list", "error", "empty", "unlinked"),
    "evidence_detail": ("current", "quarantined", "unused"),
    "evidence_span": ("span", "whole", "superseded", "unavailable"),
    "workpaper": ("list", "empty"),
    "workpaper_entry": ("default", "legacy", "excluded"),
}


def _register_frameworks() -> None:
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.gdpr import GDPR_DEFINITION
    from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION

    for definition in (
        DPDPA_DEFINITION,
        ISO27001_DEFINITION,
        GDPR_DEFINITION,
        HIPAA_DEFINITION,
        NIST_CSF_DEFINITION,
        PCI_DSS_DEFINITION,
    ):
        FrameworkRegistry.register(definition)


def _version(
    evidence: Evidence,
    number: int,
    *,
    status: str = "active",
    created_at=None,
    filename: str | None = None,
    reason: str | None = None,
) -> EvidenceVersion:
    filename = filename or evidence.original_filename
    return EvidenceVersion(
        id=f"version-{evidence.id}-{number}",
        evidence_id=evidence.id,
        version_number=number,
        storage_path=f"evidence/{evidence.engagement_id}/{evidence.id}-v{number}",
        file_hash_sha256=(f"{evidence.id}-{number}" * 8)[:64].ljust(64, "0"),
        file_size_bytes=evidence.file_size_bytes + number * 128,
        change_reason=reason,
        status=status,
        original_filename=filename,
        mime_type=evidence.mime_type,
        extracted_text=(
            {
                "meridian-evidence-000": (
                    "The notice explains how Meridian collects and uses personal data.\n\n"
                    "It describes withdrawal and complaint channels for data principals.\n\n"
                    "The notice names the retention periods and responsible contact."
                ),
                "meridian-evidence-001": "The information security policy defines ownership, review and approval responsibilities.",
                "meridian-evidence-002": "IAM users and policies snapshot for the read-only review.",
                "meridian-evidence-003": "Access review export for the fourth quarter.",
                "meridian-evidence-004": "The procedure records how consent withdrawals are handled.",
                "meridian-evidence-005": "The retention policy defines deletion schedules and exceptions.",
                "meridian-evidence-006": "The cloud hosting agreement records supplier security obligations.",
                "meridian-evidence-007": "The vendor data processing agreement records processor duties.",
                "meridian-evidence-008": "S3 encryption and logging configuration snapshot.",
                "meridian-evidence-009": "The breach notification runbook records escalation and notice steps.",
                "meridian-evidence-010": "The payments data flow diagram shows systems and transfers.",
            }
            .get(evidence.id, "Seeded extracted text for evidence inventory and pre-fill.")
        ),
        created_at=created_at or _time(-20),
    )


def _magic_link(
    engagement_id: str,
    *,
    link_id: str = "magic-link-loomwire",
    assessment_ids: tuple[str, ...] = ("assessment-loomwire",),
    contact_name: str = "Anika Rao",
    contact_email: str = "anika@loomwire.example",
) -> MagicLink:
    return MagicLink(
        id=link_id,
        engagement_id=engagement_id,
        token_digest="a" * 64,
        scope_json=json.dumps({"assessment_ids": list(assessment_ids)}),
        max_uploads=20,
        max_size_bytes=20_000_000,
        expires_at=_time(30),
        contact_name=contact_name,
        contact_email=contact_email,
        created_at=_time(-8),
    )


def _seed_inventory(db: Session, screen: str = "evidence", state: str | None = None) -> dict[str, object]:
    clients = [
        _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large"),
        _client("client-loomwire", "Loomwire Labs", "IT services", "medium"),
        _client("client-kestrel", "Kestrel Advisory", "Professional services", "small"),
    ]
    engagements = [
        _engagement("eng-meridian", clients[0].id, "FY2026 privacy readiness"),
        _engagement("eng-loomwire", clients[1].id, "ISO 27001 surveillance review"),
        _engagement("eng-kestrel", clients[2].id, "Advisory controls review"),
    ]
    assessments = [
        _assessment("assessment-meridian-head", engagements[0].id, clients[0].name, "Head office", ("dpdpa", "iso27001"), status="questionnaire_done"),
        _assessment("assessment-meridian-payments", engagements[0].id, clients[0].name, "Payments subsidiary", ("iso27001",)),
        _assessment("assessment-loomwire", engagements[1].id, clients[1].name, "Platform review", ("iso27001",)),
        _assessment("assessment-kestrel", engagements[2].id, clients[2].name, "Advisory review", ("dpdpa",)),
    ]
    assessments.append(_assessment("assessment-unlinked", None, "Unlinked client", "Standalone review", ("dpdpa",)))
    db.add_all(clients + engagements + assessments)
    db.add(FirmSettings(id=1, contact_email="engagements@northgate.example", archived_retention_years=7, accent_theme="midnight", updated_at=FROZEN_NOW))
    db.add(_magic_link(engagements[0].id, link_id="magic-link-meridian", assessment_ids=(assessments[0].id, assessments[1].id), contact_name="Ananya Rao", contact_email="ananya@meridian.example"))
    db.add(_magic_link(engagements[0].id, link_id="magic-link-meridian-kiran", assessment_ids=(assessments[0].id, assessments[1].id), contact_name="Kiran Shah", contact_email="kiran@meridian.example"))
    db.add(_magic_link(engagements[1].id))
    db.flush()

    _seed_evidence(db, engagements[0], assessments[0], 11, "meridian-evidence")
    _seed_evidence(db, engagements[1], assessments[2], 2, "loomwire-evidence")
    _seed_evidence(db, engagements[2], assessments[3], 1, "kestrel-evidence")
    db.flush()
    rows = {row.id: row for row in db.query(Evidence).all()}
    for row in rows.values():
        if row.status == "available":
            row.status = "active"
    rows["meridian-evidence-002"].status = "active"
    rows["meridian-evidence-003"].status = "rejected"
    rows["meridian-evidence-004"].status = "quarantined"
    rows["meridian-evidence-005"].status = "invalidated"
    rows["meridian-evidence-010"].status = "quarantined"
    names = {
        "meridian-evidence-000": "Privacy notice.pdf",
        "meridian-evidence-001": "Information security policy.pdf",
        "meridian-evidence-002": "IAM users and policies",
        "meridian-evidence-003": "Access review export Q4.xlsx",
        "meridian-evidence-004": "Consent withdrawal procedure.docx",
        "meridian-evidence-005": "Data retention policy.pdf",
        "meridian-evidence-006": "Cloud hosting agreement.pdf",
        "meridian-evidence-007": "Vendor data processing agreement.pdf",
        "meridian-evidence-008": "S3 encryption and logging",
        "meridian-evidence-009": "Breach notification runbook.pdf",
        "meridian-evidence-010": "Data flow diagram, payments.png",
    }
    display_dates = {
        "meridian-evidence-000": datetime(2026, 3, 12, 12, tzinfo=timezone.utc),
        "meridian-evidence-001": datetime(2026, 3, 11, 12, tzinfo=timezone.utc),
        "meridian-evidence-002": datetime(2026, 3, 14, 12, tzinfo=timezone.utc),
        "meridian-evidence-003": datetime(2026, 3, 13, 12, tzinfo=timezone.utc),
        "meridian-evidence-004": datetime(2026, 3, 15, 12, tzinfo=timezone.utc),
        "meridian-evidence-005": datetime(2026, 3, 9, 12, tzinfo=timezone.utc),
        "meridian-evidence-006": datetime(2026, 3, 10, 12, tzinfo=timezone.utc),
        "meridian-evidence-007": datetime(2026, 3, 12, 12, tzinfo=timezone.utc),
        "meridian-evidence-008": datetime(2026, 3, 14, 12, tzinfo=timezone.utc),
        "meridian-evidence-009": datetime(2026, 3, 9, 12, tzinfo=timezone.utc),
        "meridian-evidence-010": datetime(2026, 3, 15, 12, tzinfo=timezone.utc),
    }
    current_order_dates = {
        evidence_id: datetime(2026, 4, 11 - index, 12, tzinfo=timezone.utc)
        for index, evidence_id in enumerate(names)
    }
    display_sizes = {
        "meridian-evidence-000": 2_400_000,
        "meridian-evidence-001": 1_100_000,
        "meridian-evidence-002": 340_000,
        "meridian-evidence-003": 860_000,
        "meridian-evidence-004": 96_000,
        "meridian-evidence-005": 780_000,
        "meridian-evidence-006": 3_200_000,
        "meridian-evidence-007": 1_400_000,
        "meridian-evidence-008": 212_000,
        "meridian-evidence-009": 520_000,
        "meridian-evidence-010": 1_100_000,
    }
    for evidence_id, filename in names.items():
        rows[evidence_id].original_filename = filename
        rows[evidence_id].created_at = display_dates[evidence_id]
        rows[evidence_id].file_size_bytes = display_sizes[evidence_id] - 128
    rows["meridian-evidence-001"].assessment_id = assessments[0].id
    rows["meridian-evidence-005"].assessment_id = assessments[0].id
    rows["meridian-evidence-009"].assessment_id = assessments[0].id
    rows["meridian-evidence-008"].assessment_id = assessments[1].id
    rows["meridian-evidence-006"].assessment_id = assessments[1].id
    rows["meridian-evidence-007"].assessment_id = assessments[1].id
    rows["meridian-evidence-010"].assessment_id = assessments[1].id
    rows["meridian-evidence-002"].uploaded_by = "aws_config:123456789012"
    rows["meridian-evidence-003"].uploaded_by = "client_link:magic-link-meridian"
    rows["meridian-evidence-004"].uploaded_by = "client_link:magic-link-meridian"
    rows["meridian-evidence-007"].uploaded_by = "client_link:magic-link-meridian-kiran"
    rows["meridian-evidence-008"].uploaded_by = "aws_config:123456789012"
    rows["meridian-evidence-003"].mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    rows["meridian-evidence-004"].mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    rows["meridian-evidence-010"].mime_type = "image/png"
    rows["loomwire-evidence-000"].uploaded_by = "aws_config:123456789012"
    rows["loomwire-evidence-000"].original_filename = "aws-config-snapshot.txt"
    rows["loomwire-evidence-001"].uploaded_by = "client_link:magic-link-loomwire"
    rows["loomwire-evidence-001"].original_filename = "vendor-register.xlsx"
    db.add_all(
        [
            _version(rows["meridian-evidence-000"], 1, status="superseded", created_at=datetime(2026, 4, 1, 12, tzinfo=timezone.utc), filename="Privacy notice v1.pdf", reason="Initial receipt"),
            _version(rows["meridian-evidence-000"], 2, status="superseded", created_at=datetime(2026, 4, 2, 12, tzinfo=timezone.utc), filename="Privacy notice v2.pdf", reason="Updated notice"),
            _version(rows["meridian-evidence-000"], 3, created_at=current_order_dates["meridian-evidence-000"], filename="Privacy notice.pdf", reason="Added reviewer advice"),
            _version(rows["meridian-evidence-001"], 1, created_at=current_order_dates["meridian-evidence-001"], filename="Information security policy.pdf"),
            _version(rows["meridian-evidence-002"], 1, created_at=current_order_dates["meridian-evidence-002"], filename="IAM users and policies"),
            _version(rows["meridian-evidence-003"], 1, status="rejected", created_at=current_order_dates["meridian-evidence-003"], filename="Access review export Q4.xlsx"),
            _version(rows["meridian-evidence-004"], 1, status="quarantined", created_at=current_order_dates["meridian-evidence-004"], filename="Consent withdrawal procedure.docx"),
            _version(rows["meridian-evidence-005"], 1, status="invalidated", created_at=current_order_dates["meridian-evidence-005"], filename="Data retention policy.pdf"),
            _version(rows["meridian-evidence-006"], 1, created_at=current_order_dates["meridian-evidence-006"], filename="Cloud hosting agreement.pdf"),
            _version(rows["meridian-evidence-007"], 1, created_at=current_order_dates["meridian-evidence-007"], filename="Vendor data processing agreement.pdf"),
            _version(rows["meridian-evidence-008"], 1, created_at=current_order_dates["meridian-evidence-008"], filename="S3 encryption and logging"),
            _version(rows["meridian-evidence-009"], 1, created_at=current_order_dates["meridian-evidence-009"], filename="Breach notification runbook.pdf"),
            _version(rows["meridian-evidence-010"], 1, status="quarantined", created_at=current_order_dates["meridian-evidence-010"], filename="Data flow diagram, payments.png"),
            _version(rows["loomwire-evidence-000"], 1, created_at=_time(-6), filename="aws-config-snapshot.txt"),
            _version(rows["loomwire-evidence-001"], 1, created_at=_time(-5), filename="vendor-register.xlsx"),
            _version(rows["kestrel-evidence-000"], 1, created_at=_time(-4)),
        ]
    )
    db.add_all(
        [
            EvidenceUse(id="use-meridian-privacy-5", evidence_id="meridian-evidence-000", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.5", relevance="supports"),
            EvidenceUse(id="use-meridian-privacy-6", evidence_id="meridian-evidence-000", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.6", relevance="supports"),
            EvidenceUse(id="use-meridian-privacy-7", evidence_id="meridian-evidence-000", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.7", relevance="supports"),
            EvidenceUse(id="use-meridian-privacy-8", evidence_id="meridian-evidence-000", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.8", relevance="supports"),
            EvidenceUse(id="use-meridian-privacy-9", evidence_id="meridian-evidence-000", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.9", relevance="supports"),
            EvidenceUse(id="use-meridian-access-1", evidence_id="meridian-evidence-001", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.1", relevance="supports"),
            EvidenceUse(id="use-meridian-access-2", evidence_id="meridian-evidence-001", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.2", relevance="supports"),
            EvidenceUse(id="use-meridian-access-3", evidence_id="meridian-evidence-001", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.3", relevance="supports"),
            EvidenceUse(id="use-meridian-access-4", evidence_id="meridian-evidence-001", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.4", relevance="supports"),
            EvidenceUse(id="use-meridian-access-5", evidence_id="meridian-evidence-001", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.5", relevance="supports"),
            EvidenceUse(id="use-reused-target", evidence_id="meridian-evidence-001", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.5.6", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-1", evidence_id="meridian-evidence-002", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.15", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-2", evidence_id="meridian-evidence-002", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.2", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-3", evidence_id="meridian-evidence-002", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.3", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-4", evidence_id="meridian-evidence-002", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.4", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-5", evidence_id="meridian-evidence-002", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.5", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-6", evidence_id="meridian-evidence-002", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.6", relevance="supports"),
            EvidenceUse(id="use-meridian-iam-head", evidence_id="meridian-evidence-002", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.8.2", relevance="supports"),
            EvidenceUse(id="use-meridian-access", evidence_id="meridian-evidence-003", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.5.18", relevance="supports"),
            EvidenceUse(id="use-meridian-access-iam", evidence_id="meridian-evidence-003", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.8.2", relevance="supports"),
            EvidenceUse(id="use-meridian-consent-6", evidence_id="meridian-evidence-004", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.6", relevance="supports"),
            EvidenceUse(id="use-meridian-consent-7", evidence_id="meridian-evidence-004", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.7", relevance="supports"),
            EvidenceUse(id="use-meridian-retention", evidence_id="meridian-evidence-005", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="s.8", relevance="supports"),
            EvidenceUse(id="use-meridian-retention-iso", evidence_id="meridian-evidence-005", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.5.33", relevance="supports"),
            EvidenceUse(id="use-meridian-hosting", evidence_id="meridian-evidence-006", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.19", relevance="supports"),
            EvidenceUse(id="use-meridian-hosting-iso", evidence_id="meridian-evidence-006", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.23", relevance="supports"),
            EvidenceUse(id="use-meridian-vendor", evidence_id="meridian-evidence-007", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.20", relevance="supports"),
            EvidenceUse(id="use-meridian-vendor-iso", evidence_id="meridian-evidence-007", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.19", relevance="supports"),
            EvidenceUse(id="use-meridian-s3-15", evidence_id="meridian-evidence-008", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.15", relevance="supports"),
            EvidenceUse(id="use-meridian-s3-20", evidence_id="meridian-evidence-008", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.20", relevance="supports"),
            EvidenceUse(id="use-meridian-s3-24", evidence_id="meridian-evidence-008", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.24", relevance="supports"),
            EvidenceUse(id="use-meridian-breach", evidence_id="meridian-evidence-009", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="s.8", relevance="supports"),
            EvidenceUse(id="use-meridian-breach-24", evidence_id="meridian-evidence-009", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.5.24", relevance="supports"),
            EvidenceUse(id="use-meridian-breach-25", evidence_id="meridian-evidence-009", assessment_id=assessments[0].id, framework_id="iso27001", requirement_id="A.5.25", relevance="supports"),
            EvidenceUse(id="use-meridian-flow-14", evidence_id="meridian-evidence-010", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.5.14", relevance="supports"),
            EvidenceUse(id="use-meridian-flow-20", evidence_id="meridian-evidence-010", assessment_id=assessments[1].id, framework_id="iso27001", requirement_id="A.8.20", relevance="supports"),
            EvidenceUse(id="use-loomwire-aws", evidence_id="loomwire-evidence-000", assessment_id=assessments[2].id, framework_id="iso27001", requirement_id="A.8.16", relevance="supports"),
            EvidenceUse(id="use-loomwire-client", evidence_id="loomwire-evidence-001", assessment_id=assessments[2].id, framework_id="iso27001", requirement_id="A.5.19", relevance="supports"),
            EvidenceUse(id="use-retention-target", evidence_id="meridian-evidence-005", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="s.8", relevance="supports"),
            EvidenceUse(id="use-breach-target", evidence_id="meridian-evidence-009", assessment_id=assessments[0].id, framework_id="dpdpa", requirement_id="DPDPA.9", relevance="supports"),
        ]
    )
    db.flush()
    for use in db.query(EvidenceUse).filter(
        EvidenceUse.assessment_id.in_((assessments[0].id, assessments[1].id))
    ).all():
        use.created_at = datetime(2026, 3, 1, 12, tzinfo=timezone.utc)
    db.add(_audit("audit-reuse-meridian-retention", action="evidence_reuse.confirmed", entity_type="evidence_use", entity_id="use-retention-target", created_at=_time(-3), metadata={"evidence_id": "meridian-evidence-005", "source_assessment_id": assessments[1].id, "target_assessment_id": assessments[0].id}))
    db.add(_audit("audit-reuse-meridian-breach", action="evidence_reuse.confirmed", entity_type="evidence_use", entity_id="use-breach-target", created_at=_time(-3), metadata={"evidence_id": "meridian-evidence-009", "source_assessment_id": assessments[1].id, "target_assessment_id": assessments[0].id}))
    for index, (framework_id, status, started_at, completed_at) in enumerate((
        ("dpdpa", "completed", datetime(2026, 3, 20, 9, tzinfo=timezone.utc), datetime(2026, 3, 20, 9, 15, tzinfo=timezone.utc)),
        ("iso27001", "completed", datetime(2026, 3, 20, 9, tzinfo=timezone.utc), datetime(2026, 3, 20, 9, 20, tzinfo=timezone.utc)),
        ("dpdpa", "failed", datetime(2026, 3, 21, 10, tzinfo=timezone.utc), datetime(2026, 3, 21, 10, 2, tzinfo=timezone.utc)),
        ("iso27001", "running", datetime(2026, 3, 21, 11, tzinfo=timezone.utc), None),
    )):
        if screen in ("workpaper", "workpaper_entry"):
            break  # the workpaper screens seed their own runs in _seed_workpaper
        db.add(AnalysisRun(id=f"analysis-run-meridian-{index + 1}", assessment_id=assessments[0].id, framework_id=framework_id, status=status, claims_json=json.dumps({"claims": [], "inputs": {"evidence_versions": ["version-meridian-evidence-000-2"]}}), model_id="anthropic/claude-sonnet-4.5", started_at=started_at, completed_at=completed_at))
    basis_metadata = {"before": {"period_start": None, "period_end": None, "evidence_cutoff": None}, "after": {"period_start": "2025-04-01", "period_end": "2026-03-31", "evidence_cutoff": "2026-03-15", "prepared_by": "Priya Sharma", "reviewed_by": None}}
    db.add(_audit("audit-report-basis-meridian", action="assessment.report_basis_updated", entity_type="assessment", entity_id=assessments[0].id, created_at=datetime(2026, 3, 21, 12, tzinfo=timezone.utc), metadata=basis_metadata))
    assessments[0].desk_review_status = "completed"
    db.add(DeskReviewSummary(assessment_id=assessments[0].id, document_catalog=json.dumps({"documents": 2}), coverage_summary=json.dumps({"covered": 1}), raw_ai_response="{}", status="completed", started_at=datetime(2026, 4, 4, 9, tzinfo=timezone.utc), completed_at=datetime(2026, 4, 5, 12, tzinfo=timezone.utc)))
    db.flush()

    if screen in ("workpaper", "workpaper_entry"):
        _seed_review_stage(db, assessments[0], approved=0, pending=0)
        _seed_workpaper(db, assessments[0], variant=state if screen == "workpaper_entry" else "list")
    else:
        _seed_review_stage(db, assessments[0], approved=3, pending=3)
    db.add(_audit("audit-upload-after-prefill", action="evidence.version.created", entity_type="evidence", entity_id="meridian-evidence-000", created_at=_time(-1), metadata={"version": 3}))
    db.commit()
    return {"clients": clients, "engagements": engagements, "assessments": assessments}


# --- s6-workpaper: Head office conclusions, runs and full traceability for the workpaper screens ---

WORKPAPER_PROPOSED_AT = datetime(2026, 3, 14, 10, 49, tzinfo=timezone.utc)
BREACH_SENTENCE = "We will notify affected customers within 72 hours of confirming a personal data breach."
# (requirement, outcome, decision, mapped evidence ids, risk) in registry order; decision is
# approved / edited / pending. Titles come from the framework registry, never from here.
WORKPAPER_ROWS = (
    ("CH2.CONSENT.2", "partially_compliant", "approved", ("meridian-evidence-000", "meridian-evidence-001", "meridian-evidence-006"), "medium"),
    ("CH2.CONSENT.3", "non_compliant", "edited", ("meridian-evidence-000", "meridian-evidence-007"), "high"),
    ("CH2.CONSENT.5", "partially_compliant", "approved", ("meridian-evidence-000", "meridian-evidence-001"), "medium"),
    ("CH2.NOTICE.1", "non_compliant", "pending", ("meridian-evidence-000",), "high"),
    ("CH2.MINIMIZE.3", "partially_compliant", "approved", ("meridian-evidence-001", "meridian-evidence-006"), "medium"),
    ("CH2.SECURITY.3", "compliant", "approved", ("meridian-evidence-006", "meridian-evidence-007", "meridian-evidence-001", "meridian-evidence-000"), "low"),
    ("CH3.GRIEVANCE.1", "insufficient_evidence", "pending", (), "medium"),
    ("BN.NOTIFY.1", None, None, None, None),  # the fully documented entry, built below
)
WORKPAPER_EXCLUDED = ("CH4.SDF.1", "CB.TRANSFER.1")
WORKPAPER_UNCONCLUDED = ("CH3.NOMINATE.1", "CH4.SDF.2", "CH4.SDF.3")


def _wp_claim(revision_id: str, requirement_id: str, outcome: str, *, rationale: str, gap: str, risk: str,
              action: str, citations: int, quote: str | None = None, red_flags: int = 0,
              scope_enforced: bool = False, disposition: str = "supported") -> dict:
    claim = {
        "revision_id": revision_id,
        "requirement_id": requirement_id,
        "outcome": outcome,
        "disposition": disposition,
        "item": {
            "current_state": rationale,
            "gap_description": gap,
            "risk_level": risk,
            "remediation_action": action,
            "evidence_quote": quote,
        },
        "quality": {
            "citation_count": citations,
            "evidence_quote_grounded": True if quote else None,
            "unsupported_assertion": False,
            "needs_review": False,
            "desk_review_red_flags": red_flags,
            "desk_review_absence": False,
            "contradictions": None,
        },
    }
    if scope_enforced:
        claim["scope_enforced"] = True
    return claim


def _wp_revision(conclusion_id: str, suffix: str, action: str, created_at: datetime, *, actor: str = SEED_ACTOR,
                 run_id: str | None = None, citations: list | None = None, previous_outcome: str | None = None,
                 previous_rationale: str | None = None) -> ConclusionRevision:
    return ConclusionRevision(
        id=f"revision-{suffix}-{conclusion_id}",
        conclusion_id=conclusion_id,
        actor=actor,
        action=action,
        previous_outcome=previous_outcome,
        previous_rationale=previous_rationale,
        citations_json=json.dumps(citations) if citations is not None else None,
        analysis_run_id=run_id,
        created_at=created_at,
    )


def _seed_workpaper(db: Session, assessment, *, variant: str | None = "default") -> None:
    """Conclusions, analysis runs and evidence for the Head office workpaper.

    variant: "list" (the breach conclusion is edited and locked), "default" (as list, plus a
    later re-run whose newer proposal the lock withheld), "legacy" (it was bulk-approved from the legacy report) or "excluded"
    (scope enforcement set it to not applicable at analysis time)."""
    variant = variant or "default"
    framework_id = "dpdpa"
    concluded = [row[0] for row in WORKPAPER_ROWS]
    excluded = list(WORKPAPER_EXCLUDED) + (["BN.NOTIFY.1"] if variant == "excluded" else [])
    applicable = [req for req in concluded if req not in excluded] + list(WORKPAPER_UNCONCLUDED)
    assessment.applicable_requirements = json.dumps(applicable)

    # Breach response procedure: the document the breach conclusion cites.
    breach_text = (
        "Incident response procedure, version 4.\n\n"
        "Section 3. Notifying customers. " + BREACH_SENTENCE + "\n\n"
        "Legal decides case by case whether any regulator is told."
    )
    breach = Evidence(
        id="meridian-evidence-breach", engagement_id=assessment.engagement_id, assessment_id=assessment.id,
        original_filename="Breach response procedure.docx", storage_path=f"evidence/{assessment.engagement_id}/meridian-evidence-breach",
        file_hash_sha256="b" * 64, file_size_bytes=184_000,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        status="active", uploaded_by="client_link:magic-link-meridian", created_at=datetime(2026, 3, 8, 12, tzinfo=timezone.utc),
    )
    db.add(breach)
    db.flush()
    breach_version = EvidenceVersion(
        id="version-meridian-evidence-breach-1", evidence_id=breach.id, version_number=1,
        storage_path=breach.storage_path + "-v1", file_hash_sha256="b" * 64, file_size_bytes=184_000,
        status="active", original_filename=breach.original_filename, mime_type=breach.mime_type,
        extracted_text=breach_text, created_at=breach.created_at,
    )
    db.add(breach_version)
    start = breach_text.index(BREACH_SENTENCE)
    breach_citation = [{
        "evidence_version_id": breach_version.id,
        "location_type": "text_span",
        "location_ref": f"chars:{start}-{start + len(BREACH_SENTENCE)}",
        "excerpt": BREACH_SENTENCE,
    }]

    version_ids = [
        row[0] for row in db.query(EvidenceVersion.id)
        .join(Evidence, Evidence.id == EvidenceVersion.evidence_id)
        .filter(Evidence.engagement_id == assessment.engagement_id, EvidenceVersion.status == "active")
        .order_by(EvidenceVersion.id)
    ]
    inputs = {"evidence_versions": version_ids}
    run_ids = {key: f"analysis-run-wp-{key}" for key in ("dpdpa", "iso", "iso-failed", "dpdpa-rerun", "dpdpa-stalled")}
    claims: dict[str, list[dict]] = {key: [] for key in run_ids}

    def add_conclusion(requirement_id: str, outcome: str, risk: str, *, rationale: str, gaps: str, action: str,
                       summary: str, ai_proposed: bool = True, version: int = 1, cluster_id: str | None = None) -> Conclusion:
        conclusion = Conclusion(
            id=f"conclusion-wp-{requirement_id}", assessment_id=assessment.id, framework_id=framework_id,
            requirement_id=requirement_id, cluster_id=cluster_id, outcome=outcome, rationale=rationale,
            evidence_summary=summary, gaps_identified=gaps, risk_level=risk, recommended_action=action,
            ai_proposed=ai_proposed, version=version, created_at=WORKPAPER_PROPOSED_AT, updated_at=WORKPAPER_PROPOSED_AT,
        )
        db.add(conclusion)
        db.flush()
        return conclusion

    edit_at = datetime(2026, 3, 17, 15, tzinfo=timezone.utc)
    approve_at = datetime(2026, 3, 18, 11, tzinfo=timezone.utc)
    for requirement_id, outcome, decision, evidence_ids, risk in WORKPAPER_ROWS:
        if requirement_id == "BN.NOTIFY.1":
            continue
        proposed_outcome = "partially_compliant" if decision == "edited" else outcome
        rationale = "Practice is documented for the main product; some channels are not covered." if outcome != "compliant" else "Practice is documented and was operating during the period."
        conclusion = add_conclusion(
            requirement_id, outcome, risk, rationale=rationale,
            gaps="Coverage gaps remain for secondary channels." if outcome != "compliant" else "None identified.",
            action="Extend the documented practice to every channel and keep evidence of operation.",
            summary="Supporting documents are mapped below.", ai_proposed=decision != "edited", version=2 if decision == "edited" else 1,
        )
        proposed = _wp_revision(conclusion.id, "proposed", "proposed", WORKPAPER_PROPOSED_AT, actor="system:analysis",
                                run_id=run_ids["dpdpa"], citations=[])
        db.add(proposed)
        claims["dpdpa"].append(_wp_claim(proposed.id, requirement_id, proposed_outcome, rationale=rationale,
                                         gap="Coverage gaps remain.", risk=risk, action="Extend the practice.", citations=0))
        if decision == "approved":
            db.add(_wp_revision(conclusion.id, "approved", "approved", approve_at))
        elif decision == "edited":
            db.add(_wp_revision(conclusion.id, "edited", "edited", edit_at, previous_outcome=proposed_outcome,
                                previous_rationale=rationale))
        for index, evidence_id in enumerate(evidence_ids):
            db.add(EvidenceUse(id=f"use-wp-{requirement_id}-{index}", evidence_id=evidence_id, assessment_id=assessment.id,
                               framework_id=framework_id, requirement_id=requirement_id, relevance="primary" if index == 0 else "supporting",
                               created_at=datetime(2026, 3, 10, 12, tzinfo=timezone.utc)))

    for requirement_id in WORKPAPER_EXCLUDED:
        conclusion = add_conclusion(
            requirement_id, "not_applicable", "low", rationale="Set to not applicable by the scope recorded for this assessment.",
            gaps="Not assessed.", action="None while out of scope.", summary="",
        )
        proposed = _wp_revision(conclusion.id, "proposed", "proposed", WORKPAPER_PROPOSED_AT, actor="system:analysis",
                                run_id=run_ids["dpdpa"], citations=[])
        db.add(proposed)
        claims["dpdpa"].append(_wp_claim(proposed.id, requirement_id, "not_applicable", rationale="Out of scope.",
                                         gap="", risk="low", action="", citations=0, scope_enforced=True, disposition="scope_enforced"))

    # The breach notification conclusion, shaped by the variant.
    ai_rationale = "Customers are told within 72 hours, but the procedure does not name the Board."
    ai_gap = "No step for notifying the Data Protection Board."
    ai_action = "Add Board notification to the procedure with an owner and a deadline."
    if variant == "excluded":
        conclusion = add_conclusion(
            "BN.NOTIFY.1", "not_applicable", "high", rationale="Set to not applicable by the scope recorded for this assessment.",
            gaps="Not assessed.", action="None while out of scope.", summary="", cluster_id="CLUSTER_017",
        )
        proposed = _wp_revision(conclusion.id, "proposed", "proposed", WORKPAPER_PROPOSED_AT, actor="system:analysis",
                                run_id=run_ids["dpdpa"], citations=breach_citation)
        db.add(proposed)
        claims["dpdpa"].append(_wp_claim(proposed.id, "BN.NOTIFY.1", "not_applicable", rationale=ai_rationale, gap=ai_gap,
                                         risk="high", action=ai_action, citations=1, quote=BREACH_SENTENCE, red_flags=1,
                                         scope_enforced=True, disposition="scope_enforced"))
    elif variant == "legacy":
        conclusion = add_conclusion(
            "BN.NOTIFY.1", "partially_compliant", "high", rationale=ai_rationale, gaps=ai_gap, action=ai_action,
            summary=BREACH_SENTENCE, cluster_id="CLUSTER_017",
        )
        legacy_at = datetime(2026, 1, 12, 10, tzinfo=timezone.utc)
        db.add(_wp_revision(conclusion.id, "proposed", "proposed", legacy_at, actor="system:legacy_migration"))
        db.add(_wp_revision(conclusion.id, "approved", "approved", legacy_at + timedelta(minutes=5), actor="system:legacy_migration"))
    else:
        conclusion = add_conclusion(
            "BN.NOTIFY.1", "non_compliant", "high",
            rationale="The procedure never tells the Data Protection Board about a breach. Customer notice alone does not meet the requirement.",
            gaps="No Board notification step, no owner, no deadline.",
            action="Add Board notification within the period the Rules set, and name the person responsible.",
            summary=BREACH_SENTENCE, ai_proposed=False, version=2, cluster_id="CLUSTER_017",
        )
        proposed = _wp_revision(conclusion.id, "proposed", "proposed", WORKPAPER_PROPOSED_AT, actor="system:analysis",
                                run_id=run_ids["dpdpa"], citations=breach_citation)
        db.add(proposed)
        claims["dpdpa"].append(_wp_claim(proposed.id, "BN.NOTIFY.1", "partially_compliant", rationale=ai_rationale, gap=ai_gap,
                                         risk="high", action=ai_action, citations=1, quote=BREACH_SENTENCE, red_flags=1))
        db.add(_wp_revision(conclusion.id, "edited", "edited", edit_at, previous_outcome="partially_compliant",
                            previous_rationale=ai_rationale))
        if variant == "default":  # a re-run after the edit produced a newer proposal the lock withheld
            withheld = _wp_revision(conclusion.id, "withheld", "proposal_withheld", datetime(2026, 3, 19, 9, 40, tzinfo=timezone.utc),
                                    actor="system:analysis", run_id=run_ids["dpdpa-rerun"], citations=breach_citation)
            db.add(withheld)
            claims["dpdpa-rerun"].append(_wp_claim(withheld.id, "BN.NOTIFY.1", "non_compliant", rationale="The procedure has no Board notification step.",
                                                   gap=ai_gap, risk="high", action=ai_action, citations=1, quote=BREACH_SENTENCE,
                                                   red_flags=1, disposition="withheld"))
    if variant != "excluded":
        db.add(EvidenceUse(id="use-wp-breach", evidence_id=breach.id, assessment_id=assessment.id, framework_id=framework_id,
                           requirement_id="BN.NOTIFY.1", relevance="primary", created_at=datetime(2026, 3, 10, 12, tzinfo=timezone.utc)))
        db.add(DeskReviewFinding(
            assessment_id=assessment.id, framework_id=framework_id, finding_type="absence", requirement_id="BN.NOTIFY.1",
            content="Breach notice promises customers 72 hours and never mentions the Board", severity="critical",
            source_quote=BREACH_SENTENCE, source_location="Section 3", citations_json=json.dumps(breach_citation),
            created_at=datetime(2026, 3, 12, 9, tzinfo=timezone.utc),
        ))

    # The shared cluster answer that informs the breach conclusion (and the ISO controls in CLUSTER_017).
    response = db.query(QuestionnaireResponse).filter_by(assessment_id=assessment.id, question_id="CLUSTER_017").first()
    if response is None:
        response = QuestionnaireResponse(assessment_id=assessment.id, question_id="CLUSTER_017")
        db.add(response)
    response.answer = "partially_implemented"
    response.answer_source = "human"
    response.confidence = "medium"
    response.cluster_id = "CLUSTER_017"
    response.notes = "We notify customers within 72 hours. Whether the Board is told is decided by legal, case by case."
    response.evidence_reference = "Breach response procedure.docx"
    response.submitted_at = datetime(2026, 3, 10, 12, tzinfo=timezone.utc)

    run_rows = (
        ("dpdpa", "dpdpa", "completed", datetime(2026, 3, 14, 10, 42), datetime(2026, 3, 14, 10, 49), True, None),
        ("iso", "iso27001", "completed", datetime(2026, 3, 16, 11, 5), datetime(2026, 3, 16, 11, 16), True, None),
        ("iso-failed", "iso27001", "failed", datetime(2026, 3, 16, 11, 18), datetime(2026, 3, 16, 11, 23), True, "LLMRequestTimeout"),
        ("dpdpa-rerun", "dpdpa", "completed", datetime(2026, 3, 19, 9, 30), datetime(2026, 3, 19, 9, 40), True, None),
        ("dpdpa-stalled", "dpdpa", "running", datetime(2026, 3, 20, 8, 10), None, False, None),
    )
    for key, run_framework, status, started_at, completed_at, desk_review_used, error_type in run_rows:
        if key == "dpdpa-rerun" and not claims[key]:
            continue  # only the default variant has a newer (withheld) proposal
        envelope = {"claims": claims[key], "desk_review_used": desk_review_used}
        if status != "running":
            envelope["inputs"] = inputs
        if error_type:
            envelope["error"] = {"type": error_type}
        db.add(AnalysisRun(
            id=run_ids[key], assessment_id=assessment.id, framework_id=run_framework, status=status,
            claims_json=json.dumps(envelope), model_id="anthropic/claude-sonnet-4.5",
            started_at=started_at.replace(tzinfo=timezone.utc),
            completed_at=completed_at.replace(tzinfo=timezone.utc) if completed_at else None,
        ))
    db.flush()


def _stamp_head(database_url: str) -> None:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.stamp(config, "head")


def seed(database_path: Path, screen: str = "evidence", state: str | None = None) -> dict[str, object]:
    if database_path.exists():
        database_path.unlink()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    _stamp_head(database_url)
    _register_frameworks()
    with Session(engine, expire_on_commit=False) as db:
        data = _seed_inventory(db, screen, state)
    engine.dispose()
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", "--output", dest="database", type=Path, default=Path("/tmp/yozora-s6.sqlite3"))
    parser.add_argument("--screen", choices=tuple(SCREEN_STATES), default="evidence")
    parser.add_argument("--state", default=None)
    args = parser.parse_args()
    if args.state and args.state not in SCREEN_STATES[args.screen]:
        parser.error(f"state {args.state!r} is not valid for {args.screen}")
    data = seed(args.database, args.screen, args.state)
    manifest = {
        "database": str(args.database),
        "frozen_now": FROZEN_NOW.isoformat(),
        "screen": args.screen,
        "state": args.state or SCREEN_STATES[args.screen][0],
        "produced_by": {
            screen: {state: "seeded records for reachable data; use ?state for interaction-only preview state" for state in states}
            for screen, states in SCREEN_STATES.items()
        },
        "clients": [client.name for client in data["clients"]],
    }
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
