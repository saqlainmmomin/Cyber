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
SEED_ACTOR = "consultant:S4 harness"
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
        "size_bytes": 184320,
    }
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
                created_at=generated_at + timedelta(hours=2),
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

    meridian = _engagement("eng-meridian", clients[0].id, "FY2026 privacy readiness")
    loomwire = _engagement("eng-loomwire", clients[1].id, "Security controls baseline")
    kestrel = _engagement("eng-kestrel", clients[2].id, "Advisory operations review")
    engagements = [meridian, loomwire, kestrel]
    db.add_all(engagements)
    assessments = [
        _assessment("assessment-meridian-core", meridian.id, clients[0].name, "Core privacy assessment"),
        _assessment("assessment-meridian-ops", meridian.id, clients[0].name, "Operations assessment", ("iso27001",)),
        _assessment("assessment-loomwire", loomwire.id, clients[1].name, "Platform controls", ("iso27001",)),
        _assessment("assessment-kestrel", kestrel.id, clients[2].name, "Client advisory workflow", ("dpdpa",)),
    ]
    db.add_all(assessments)
    if screen == "remediation_tracker":
        _add_actions(db, assessments[2])
    return {"clients": clients, "engagements": engagements, "assessments": assessments}


def _seed_archived(db: Session, *, eligible: bool, dependency: bool, invalid: bool = False) -> dict:
    client = _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large")
    engagement = _engagement(
        "eng-meridian-archive",
        client.id,
        "FY2025 privacy readiness",
        status="archived",
        days=-400,
    )
    assessment = _assessment(
        "assessment-meridian-archive",
        engagement.id,
        client.name,
        "Archived privacy assessment",
        ("dpdpa",),
        days=-390,
    )
    db.add_all([client, engagement, assessment])
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
    archive_at = _time(-365 * 8 if eligible else -30)
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
        other = _engagement("eng-loomwire-dependency", client.id, "Loomwire dependency")
        db.add(other)
        db.add(
            Evidence(
                id="evidence-external-dependency",
                engagement_id=other.id,
                assessment_id=assessment.id,
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
    return {"clients": [client], "engagements": [engagement], "assessments": [assessment]}


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
                eligible=state in {"default", "confirm"},
                dependency=state == "blocked",
                invalid=state == "error",
            )
        elif screen == "engagement_detail" and state == "archived":
            data = _seed_archived(db, eligible=True, dependency=False)
        elif screen == "engagement_detail" and state == "empty":
            empty_client = _client("client-meridian", "Meridian Ledger Technologies", "Fintech", "large")
            empty_engagement = _engagement("eng-empty", empty_client.id, "New privacy readiness")
            db.add(empty_client)
            db.add(empty_engagement)
            data = {"clients": [empty_client], "engagements": [empty_engagement], "assessments": []}
        elif screen == "integrated_reports" and state in {"empty", "none-approved"}:
            data = _seed_portfolio(db, state="empty" if state == "empty" else "default", screen="engagement_list")
        elif screen == "new_engagement" and state == "empty":
            data = _seed_portfolio(db, state="empty", screen="new_engagement")
        else:
            data = _seed_portfolio(db, state=state, screen=screen)

        if screen == "integrated_reports" and state not in {"empty", "none-approved"}:
            engagement = data["engagements"][0]
            snapshots = [
                _report_snapshot("snapshot-meridian-v1", engagement_id=engagement.id, generated_at=_time(-10))[0],
                _report_snapshot("snapshot-meridian-v2", engagement_id=engagement.id, generated_at=_time(-2), issued=state != "issue")[0],
            ]
            db.add_all(snapshots)
            for snapshot in snapshots:
                _, events = _report_snapshot(
                    f"event-source-{snapshot.id}",
                    engagement_id=engagement.id,
                    generated_at=snapshot.generated_at,
                    issued=False,
                )
                # Keep the event rows deterministic without adding the helper snapshot.
                for event in events:
                    event.entity_id = snapshot.id
                    event.id = f"audit-generated-{snapshot.id}"
                    db.add(event)
                    break
                if snapshot.is_issued:
                    db.add(
                        _audit(
                            f"audit-issued-{snapshot.id}",
                            action="report_snapshot.issued",
                            entity_type="report_snapshot",
                            entity_id=snapshot.id,
                            created_at=snapshot.generated_at + timedelta(hours=2),
                        )
                    )
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
