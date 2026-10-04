"""Seed deterministic Yozora S3 preview data into a throwaway SQLite database.

The fixture deliberately uses the same stored values and dates that appear in
the approved mockups. It does not start the app, call a model, use boto3, or
require network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import Base
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.firm_settings import FirmSettings
from app.models.report import GapReport
from app.models.magic_link import MagicLink
from app.services import approved_report, magic_links
from app.services.question_engine import build_adaptive_questionnaire

FROZEN_NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
DEFAULT_DB = Path("/private/tmp/yozora-s3.sqlite3")


def _at(month: int, day: int) -> datetime:
    return datetime(2026, month, day, 12, 0, tzinfo=timezone.utc)


def _register_frameworks() -> None:
    """Register framework definitions without importing the app/router graph."""
    from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
    from app.frameworks.definitions.gdpr import GDPR_DEFINITION
    from app.frameworks.definitions.hipaa import HIPAA_DEFINITION
    from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION
    from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION
    from app.frameworks.definitions.pci_dss import PCI_DSS_DEFINITION
    from app.frameworks.registry import FrameworkRegistry

    for definition in (
        DPDPA_DEFINITION,
        ISO27001_DEFINITION,
        GDPR_DEFINITION,
        HIPAA_DEFINITION,
        NIST_CSF_DEFINITION,
        PCI_DSS_DEFINITION,
    ):
        FrameworkRegistry.register(definition)


def _seed_assessment(
    db: Session,
    *,
    assessment_id: str,
    client: Client,
    engagement: Engagement,
    framework_ids: tuple[str, ...],
    status: str,
    created_at: datetime,
    updated_at: datetime,
    conclusion_count: int = 0,
    conclusion_prefix: str = "conclusion-s3",
    decision: str = "proposed",
    risk_level: str = "medium",
    releaseable: bool = False,
) -> Assessment:
    assessment = Assessment(
        id=assessment_id,
        company_name=client.name,
        name=engagement.name,
        industry=client.industry,
        company_size=client.size,
        selected_frameworks=json.dumps(list(framework_ids)),
        engagement_id=engagement.id,
        status=status,
        scope_answers=json.dumps({}),
        applicable_requirements=None,
        created_at=created_at,
        updated_at=updated_at,
    )
    db.add(assessment)
    db.flush()

    if status in {"completed", "questionnaire_done"}:
        questionnaire = build_adaptive_questionnaire(assessment.id, db)
        questions = [
            question
            for section in questionnaire.get("sections", [])
            for question in section.get("questions", [])
            if question.get("status") != "skipped"
        ]
        for question in questions:
            from app.models.questionnaire import QuestionnaireResponse

            db.add(
                QuestionnaireResponse(
                    assessment_id=assessment.id,
                    question_id=question["id"],
                    answer="partially_implemented",
                    submitted_at=updated_at,
                )
            )
        if releaseable:
            assessment.applicable_requirements = json.dumps(
                [questions[0].get("maps_to", [questions[0]["id"]])[0]] if questions else []
            )

        for index, question in enumerate(questions[:conclusion_count], start=1):
            framework_id = framework_ids[(index - 1) % len(framework_ids)]
            conclusion_id = f"{conclusion_prefix}-{index}"
            requirement_id = question.get("maps_to", [question["id"]])[0]
            db.add(
                Conclusion(
                    id=conclusion_id,
                    assessment_id=assessment.id,
                    requirement_id=requirement_id,
                    framework_id=framework_id,
                    outcome="partially_compliant",
                    rationale="The control is documented but operating evidence is incomplete.",
                    evidence_summary="Policy and operating notes were provided for desk review.",
                    gaps_identified="Evidence of periodic review is not yet complete.",
                    risk_level=risk_level,
                    recommended_action="Complete the evidence pack and record the review owner.",
                    ai_proposed=True,
                    created_at=updated_at,
                    updated_at=updated_at,
                )
            )
            db.add(
                ConclusionRevision(
                    id=f"revision-{conclusion_prefix}-{index}",
                    conclusion_id=conclusion_id,
                    actor="system:seed-s3" if decision == "proposed" else "consultant:Priya Sharma",
                    action=decision,
                    created_at=updated_at,
                )
            )
    return assessment


def _seed_purge_event(
    db: Session,
    *,
    engagement_id: str,
    client_id: str,
    name: str,
    purged_at: datetime,
    actor: str,
    blobs_removed: bool,
) -> None:
    db.add(
        AuditEvent(
            id=f"audit-purge-{engagement_id}",
            actor=actor,
            action="engagement.purged",
            entity_type="engagement",
            entity_id=engagement_id,
            metadata_json=json.dumps(
                {"client_id": client_id, "engagement_name": name},
                sort_keys=True,
            ),
            created_at=purged_at,
        )
    )
    if blobs_removed:
        db.add(
            AuditEvent(
                id=f"audit-purge-complete-{engagement_id}",
                actor="system:purge-completion",
                action="engagement.purge_blobs_removed",
                entity_type="engagement",
                entity_id=engagement_id,
                metadata_json="{}",
                created_at=purged_at,
            )
        )


def seed_database(path: Path, *, empty: bool = False) -> dict[str, str]:
    """Create a fresh S3 database and return stable route ids for the harness."""
    if path.exists():
        raise SystemExit(f"Refusing to overwrite {path}; choose a new throwaway path.")
    path.parent.mkdir(parents=True, exist_ok=True)
    _register_frameworks()
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        db.add(
            FirmSettings(
                id=1,
                archived_retention_years=7,
                accent_theme="midnight",
                accent_custom_hex=None,
                contact_email="engagements@northgate.example",
                updated_at=FROZEN_NOW,
            )
        )
        if empty:
            db.commit()
            return {}

        meridian = Client(id="client-meridian", name="Meridian Ledger Technologies", industry="fintech", size="sme", created_at=_at(9, 1), updated_at=_at(9, 24))
        loomwire = Client(id="client-loomwire", name="Loomwire Labs Inc.", industry="it_services", size="startup", created_at=_at(9, 2), updated_at=_at(9, 29))
        orchard = Client(id="client-orchard", name="Orchard Lane Retail", industry="e_commerce", size="large", created_at=_at(9, 3), updated_at=_at(9, 18))
        kestrel = Client(id="client-kestrel", name="Kestrel Health Partners", industry="healthcare", size="large", created_at=_at(9, 4), updated_at=_at(9, 2))
        brightfold = Client(id="client-brightfold", name="Brightfold Learning", industry="education", size="sme", created_at=_at(9, 5), updated_at=_at(8, 11))
        db.add_all([meridian, loomwire, orchard, kestrel, brightfold])
        db.flush()

        meridian_main = Engagement(id="engagement-meridian-fy2026", client_id=meridian.id, name="FY2026 DPDPA and ISO 27001 programme", type="gap_assessment", status="active", created_at=_at(9, 30), updated_at=_at(9, 24))
        meridian_surveillance = Engagement(id="engagement-meridian-fy2025", client_id=meridian.id, name="FY2025 ISO 27001 surveillance audit", type="gap_assessment", status="active", created_at=_at(9, 29), updated_at=_at(3, 14))
        meridian_vendor = Engagement(id="engagement-meridian-vendor", client_id=meridian.id, name="Vendor risk review", type="gap_assessment", status="active", created_at=_at(9, 28), updated_at=_at(9, 2))
        loomwire_engagement = Engagement(id="engagement-loomwire-nist", client_id=loomwire.id, name="NIST CSF 2.0 gap assessment", type="gap_assessment", status="active", created_at=_at(9, 27), updated_at=_at(9, 29))
        orchard_engagement = Engagement(id="engagement-orchard-pci", client_id=orchard.id, name="PCI DSS readiness review", type="gap_assessment", status="active", created_at=_at(9, 26), updated_at=_at(9, 18))
        orchard_closed = Engagement(id="engagement-orchard-closed", client_id=orchard.id, name="PCI DSS discovery workshop", type="gap_assessment", status="closed", created_at=_at(6, 1), updated_at=_at(6, 1))
        kestrel_closed = Engagement(id="engagement-kestrel-closed", client_id=kestrel.id, name="Kestrel Health intake", type="gap_assessment", status="closed", created_at=_at(8, 2), updated_at=_at(9, 2))
        brightfold_closed = Engagement(id="engagement-brightfold-closed", client_id=brightfold.id, name="Brightfold Learning pilot", type="gap_assessment", status="closed", created_at=_at(8, 11), updated_at=_at(8, 11))
        db.add_all([meridian_main, meridian_surveillance, meridian_vendor, loomwire_engagement, orchard_engagement, orchard_closed, kestrel_closed, brightfold_closed])
        db.flush()

        main_assessment = _seed_assessment(db, assessment_id="assessment-meridian-dpdpa", client=meridian, engagement=meridian_main, framework_ids=("dpdpa", "iso27001"), status="completed", created_at=_at(9, 20), updated_at=_at(9, 24), conclusion_count=3, conclusion_prefix="conclusion-meridian", risk_level="high")
        _seed_assessment(db, assessment_id="assessment-meridian-iso", client=meridian, engagement=meridian_main, framework_ids=("iso27001",), status="questionnaire_done", created_at=_at(9, 19), updated_at=_at(9, 20))
        _seed_assessment(db, assessment_id="assessment-meridian-controls", client=meridian, engagement=meridian_main, framework_ids=("dpdpa",), status="questionnaire_done", created_at=_at(9, 18), updated_at=_at(9, 19))
        _seed_assessment(db, assessment_id="assessment-meridian-scope", client=meridian, engagement=meridian_main, framework_ids=("dpdpa",), status="scoped", created_at=_at(9, 17), updated_at=_at(9, 18))

        surveillance = _seed_assessment(db, assessment_id="assessment-meridian-surveillance", client=meridian, engagement=meridian_surveillance, framework_ids=("iso27001",), status="completed", created_at=_at(3, 10), updated_at=_at(3, 14), conclusion_count=1, conclusion_prefix="conclusion-surveillance", decision="approved", releaseable=True)
        db.add(GapReport(id="report-surveillance", assessment_id=surveillance.id, overall_score=0.0, chapter_scores="{}", framework_scores="{}", executive_summary="Seeded released report", raw_ai_response="{}", generated_at=_at(3, 14)))

        _seed_assessment(db, assessment_id="assessment-meridian-vendor-1", client=meridian, engagement=meridian_vendor, framework_ids=("dpdpa",), status="created", created_at=_at(9, 1), updated_at=_at(9, 2))
        _seed_assessment(db, assessment_id="assessment-meridian-vendor-2", client=meridian, engagement=meridian_vendor, framework_ids=("dpdpa",), status="scoped", created_at=_at(9, 1), updated_at=_at(9, 2))
        loom_assessment = _seed_assessment(db, assessment_id="assessment-loomwire-nist", client=loomwire, engagement=loomwire_engagement, framework_ids=("nist_csf",), status="completed", created_at=_at(9, 25), updated_at=_at(9, 29), conclusion_count=1, conclusion_prefix="conclusion-loomwire", decision="approved")
        _seed_assessment(db, assessment_id="assessment-orchard-pci", client=orchard, engagement=orchard_engagement, framework_ids=("pci_dss",), status="created", created_at=_at(9, 18), updated_at=_at(9, 18))
        _seed_assessment(db, assessment_id="assessment-kestrel-closed", client=kestrel, engagement=kestrel_closed, framework_ids=("hipaa",), status="completed", created_at=_at(9, 2), updated_at=_at(9, 2))
        _seed_assessment(db, assessment_id="assessment-brightfold-closed", client=brightfold, engagement=brightfold_closed, framework_ids=("dpdpa",), status="completed", created_at=_at(8, 11), updated_at=_at(8, 11))

        for assessment_id, name, company_name, created_at in (
            ("assessment-legacy-harbour", "Harbour and Finch Logistics", "Harbour and Finch Logistics", datetime(2026, 2, 4, 12, 0, tzinfo=timezone.utc)),
            ("assessment-legacy-brightfold", "Brightfold Learning pilot", "Brightfold Learning", datetime(2026, 1, 19, 12, 0, tzinfo=timezone.utc)),
            ("assessment-legacy-kestrel", "Kestrel Health intake", "Kestrel Health Partners", datetime(2025, 12, 8, 12, 0, tzinfo=timezone.utc)),
        ):
            db.add(Assessment(id=assessment_id, company_name=company_name, name=name, industry="other", company_size="sme", selected_frameworks=json.dumps(["dpdpa"]), status="created", created_at=created_at, updated_at=created_at))

        # A legacy link is enough for the home request summary and keeps the
        # fixture independent of filesystem-backed RFI snapshot files.
        db.add(MagicLink(id="magic-s3-waiting", engagement_id=meridian_main.id, token_digest=magic_links.token_digest("s3-waiting-token"), scope_json=json.dumps({"version": 1, "assessment_id": main_assessment.id, "items": [{"key": "item-1"}, {"key": "item-2"}, {"key": "item-3"}]}), max_uploads=20, max_size_bytes=50 * 1024 * 1024, expires_at=datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc), created_at=FROZEN_NOW))

        for engagement, archived_at, years in (
            (Engagement(id="engagement-meridian-archived-2023", client_id=meridian.id, name="FY2023 DPDPA readiness review", type="gap_assessment", status="archived", created_at=_at(3, 1), updated_at=_at(3, 12)), _at(3, 12), 7),
            (Engagement(id="engagement-meridian-archived-2022", client_id=meridian.id, name="FY2022 ISO 27001 gap assessment", type="gap_assessment", status="archived", created_at=datetime(2021, 3, 1, tzinfo=timezone.utc), updated_at=datetime(2021, 4, 3, tzinfo=timezone.utc)), datetime(2021, 4, 3, tzinfo=timezone.utc), 1),
        ):
            db.add(engagement)
            db.flush()
            db.add(AuditEvent(id=f"audit-archive-{engagement.id}", actor="consultant:Priya Sharma", action="engagement.archived", entity_type="engagement", entity_id=engagement.id, metadata_json=json.dumps({"previous_status": "active", "retention_years": years, "retention_source": "firm"}), created_at=archived_at))

        _seed_purge_event(db, engagement_id="engagement-meridian-purged-pending", client_id=meridian.id, name="FY2021 DPDPA programme", purged_at=_at(6, 2), actor="consultant:Priya Sharma", blobs_removed=False)
        _seed_purge_event(db, engagement_id="engagement-meridian-purged-complete", client_id=meridian.id, name="FY2020 ISO 27001 audit", purged_at=_at(1, 9), actor="consultant:Arjun Mehta", blobs_removed=True)

        db.flush()
        db.add(approved_report.record_release(db, surveillance, actor="consultant:Priya Sharma"))
        surveillance.updated_at = _at(3, 14)
        db.commit()
    engine.dispose()
    return {
        "meridian_client": meridian.id,
        "meridian_assessment": main_assessment.id,
        "meridian_engagement": meridian_main.id,
        "loomwire_client": loomwire.id,
        "kestrel_client": kestrel.id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="new SQLite path")
    parser.add_argument("--empty", action="store_true", help="seed only firm settings")
    args = parser.parse_args()
    ids = seed_database(args.db, empty=args.empty)
    print(json.dumps({"db": str(args.db), "frozen_now": FROZEN_NOW.isoformat(), "ids": ids}, indent=2))


if __name__ == "__main__":
    main()
