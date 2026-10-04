"""Seed deterministic Yozora S3 preview data into a throwaway SQLite database.

The script deliberately uses only the local ORM and framework definitions. It does not
start the app, call a model, use boto3, or require network access. The seeded database
uses the same frozen instant as the screenshot harness so dates stay stable.
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
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.engagement import Engagement
from app.models.firm_settings import FirmSettings
from app.models.questionnaire import QuestionnaireResponse
from app.services.question_engine import build_adaptive_questionnaire

FROZEN_NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
DEFAULT_DB = Path("/private/tmp/yozora-s3.sqlite3")


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
    framework_id: str,
    completed: bool = False,
    scoped: bool = False,
) -> Assessment:
    assessment = Assessment(
        id=assessment_id,
        company_name=client.name,
        name=engagement.name,
        industry=client.industry,
        company_size=client.size,
        selected_frameworks=json.dumps([framework_id]),
        engagement_id=engagement.id,
        status="completed" if completed else "created",
        scope_answers=json.dumps({}) if completed or scoped else None,
        created_at=FROZEN_NOW,
        updated_at=FROZEN_NOW,
    )
    db.add(assessment)
    db.flush()
    if not completed:
        return assessment

    questionnaire = build_adaptive_questionnaire(assessment.id, db)
    questions = [
        question
        for section in questionnaire.get("sections", [])
        for question in section.get("questions", [])
        if question.get("status") != "skipped"
    ]
    for question in questions:
        db.add(
            QuestionnaireResponse(
                assessment_id=assessment.id,
                question_id=question["id"],
                answer="partially_implemented",
                submitted_at=FROZEN_NOW,
            )
        )
    for index, question in enumerate(questions[:3], start=1):
        conclusion_id = f"conclusion-meridian-{index}"
        db.add(
            Conclusion(
                id=conclusion_id,
                assessment_id=assessment.id,
                requirement_id=question["id"],
                framework_id=framework_id,
                outcome="partially_compliant",
                rationale="The control is documented but operating evidence is incomplete.",
                evidence_summary="Policy and operating notes were provided for desk review.",
                gaps_identified="Evidence of periodic review is not yet complete.",
                risk_level="high" if index == 1 else "medium",
                recommended_action="Complete the evidence pack and record the review owner.",
                ai_proposed=True,
                created_at=FROZEN_NOW,
                updated_at=FROZEN_NOW,
            )
        )
        db.add(
            ConclusionRevision(
                id=f"revision-meridian-{index}",
                conclusion_id=conclusion_id,
                actor="system:seed-s3",
                action="proposed",
                created_at=FROZEN_NOW,
            )
        )
    return assessment


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
                contact_email="hello@yozora.example",
                updated_at=FROZEN_NOW,
            )
        )
        if empty:
            db.commit()
            return {}

        meridian = Client(
            id="client-meridian",
            name="Meridian Ledger Technologies",
            industry="fintech",
            size="sme",
            created_at=FROZEN_NOW,
            updated_at=FROZEN_NOW,
        )
        loomwire = Client(
            id="client-loomwire",
            name="Loomwire Labs",
            industry="it_services",
            size="startup",
            created_at=FROZEN_NOW,
            updated_at=FROZEN_NOW,
        )
        kestrel = Client(
            id="client-kestrel",
            name="Kestrel Advisory",
            industry="professional_services",
            size="sme",
            created_at=FROZEN_NOW,
            updated_at=FROZEN_NOW,
        )
        db.add_all([meridian, loomwire, kestrel])
        db.flush()

        meridian_engagement = Engagement(
            id="engagement-meridian-fy2026",
            client_id=meridian.id,
            name="FY2026 DPDPA and ISO 27001 programme",
            type="gap_assessment",
            status="active",
            created_at=FROZEN_NOW,
            updated_at=FROZEN_NOW,
        )
        loomwire_engagement = Engagement(
            id="engagement-loomwire-nist",
            client_id=loomwire.id,
            name="NIST gap assessment",
            type="gap_assessment",
            status="active",
            created_at=FROZEN_NOW,
            updated_at=FROZEN_NOW,
        )
        db.add_all([meridian_engagement, loomwire_engagement])
        db.flush()
        meridian_assessment = _seed_assessment(
            db,
            assessment_id="assessment-meridian-dpdpa",
            client=meridian,
            engagement=meridian_engagement,
            framework_id="dpdpa",
            completed=True,
        )
        _seed_assessment(
            db,
            assessment_id="assessment-meridian-iso27001",
            client=meridian,
            engagement=meridian_engagement,
            framework_id="iso27001",
        )
        _seed_assessment(
            db,
            assessment_id="assessment-loomwire-nist",
            client=loomwire,
            engagement=loomwire_engagement,
            framework_id="nist_csf",
            scoped=True,
        )
        db.commit()
    engine.dispose()
    return {
        "meridian_client": meridian.id,
        "meridian_assessment": meridian_assessment.id,
        "meridian_engagement": meridian_engagement.id,
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
