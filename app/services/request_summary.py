"""Request summary (Yozora engagement Evidence > Requests): per assessment of an engagement, its RFI
version, how many items it asks for, and how many of them the client has answered through magic
links. Read-only; never calls a model.

Client links are created only from the current issued RFI version (rfi_requests.create_client_link),
so the counts are for that version: version is its number in the assessment's RFI history, items is
its item count, received is the number of its items with at least one upload received through a
client link scoped to that version. latest_version is the newest RFI version, issued or not, so a
draft that has not gone to the client yet is visible (latest_version > version).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.evidence import Evidence
from app.models.magic_link import MagicLink
from app.services import report_snapshots, rfi_requests

UPLOAD_RECEIVED_EVENT = "magic_link.upload_received"


@dataclass(frozen=True)
class RequestSummary:
    assessment_id: str
    assessment_name: str
    version: int | None
    items: int | None
    received: int
    active_links: int
    latest_version: int | None
    expires_at: object | None = None


def _received_item_ids(db: Session, assessment: Assessment, snapshot_id: str) -> tuple[set[str], int]:
    links, link_items = rfi_requests._link_rows(db, assessment)
    scoped = {row.link_id for row in links if row.snapshot_id == snapshot_id}
    active = sum(1 for row in links if row.link_id in scoped and row.status == "active")
    if not scoped:
        return set(), active
    events = db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "magic_link",
            AuditEvent.action == UPLOAD_RECEIVED_EVENT,
            AuditEvent.entity_id.in_(scoped),
        )
        .order_by(literal_column("audit_events.rowid"))
    ).scalars().all()
    received: set[str] = set()
    for event in events:
        try:
            metadata = json.loads(event.metadata_json or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        item_id = link_items.get(event.entity_id, {}).get(metadata.get("item_key"))
        evidence_id = metadata.get("evidence_id")
        if item_id and evidence_id and db.get(Evidence, evidence_id) is not None:
            received.add(item_id)
    return received, active


def assessment_summary(db: Session, assessment: Assessment) -> RequestSummary:
    rows = report_snapshots.rfi_snapshot_rows(db, assessment, current_source=None)
    latest = max((row.sequence for row in rows), default=None)
    issue = report_snapshots.current_rfi_issue(db, assessment)
    if issue is None:
        # Older links predate versioned RFIs. They still represent outstanding
        # client requests on the portfolio home page until migrated.
        legacy = (
            db.query(MagicLink)
            .filter(MagicLink.engagement_id == assessment.engagement_id)
            .order_by(MagicLink.created_at.desc(), MagicLink.id.desc())
            .first()
            if assessment.engagement_id
            else None
        )
        if legacy is not None:
            try:
                scope = json.loads(legacy.scope_json)
            except (json.JSONDecodeError, TypeError):
                scope = {}
            if (
                scope.get("version") == 1
                and isinstance(scope.get("items"), list)
                and scope.get("assessment_id", assessment.id) == assessment.id
            ):
                active = 1 if legacy.revoked_at is None else 0
                return RequestSummary(
                    assessment.id,
                    assessment.display_name,
                    None,
                    len(scope["items"]),
                    0,
                    active,
                    latest,
                    legacy.expires_at,
                )
        return RequestSummary(assessment.id, assessment.display_name, None, None, 0, 0, latest)
    sequence = next((row.sequence for row in rows if row.snapshot.id == issue.id), None)
    try:
        item_ids = [item["item_id"] for item in report_snapshots.read_rfi_document(db, issue)["items"]]
    except report_snapshots.SnapshotError:
        item_ids = None
    received, active = _received_item_ids(db, assessment, issue.id)
    if item_ids is not None:
        received &= set(item_ids)
    return RequestSummary(
        assessment_id=assessment.id,
        assessment_name=assessment.display_name,
        version=sequence,
        items=len(item_ids) if item_ids is not None else None,
        received=len(received),
        active_links=active,
        latest_version=latest,
    )


def engagement_summaries(db: Session, engagement_id: str) -> list[RequestSummary]:
    assessments = db.execute(
        select(Assessment)
        .where(Assessment.engagement_id == engagement_id, Assessment.status != "archived")
        .order_by(Assessment.created_at, Assessment.id)
    ).scalars().all()
    return [assessment_summary(db, assessment) for assessment in assessments]
