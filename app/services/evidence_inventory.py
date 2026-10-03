"""Evidence inventory read model (Yozora b4-evidence): one row per evidence item of an engagement, or
across engagements, with its source, the assessments that use it, the controls it supports, a status
label and counts. Read-only; never calls a model.

Status labels (users never see the raw states): quarantined -> Scanning, active -> Available,
rejected -> Rejected, invalidated -> Out of date. Archived evidence is not listed.

Source, worked out from what the app already stores:
- "aws": Evidence.uploaded_by starts with aws_config: or aws_securityhub: (app.services.aws_evidence).
- "client_link": Evidence.uploaded_by is client_link:<magic link id> (app.services.magic_links); the
  row carries that link's contact name when one was recorded.
- "upload": anything else (consultant uploads and migrated legacy documents).
- "reused": a reuse confirmation (audit event evidence_reuse.confirmed, app.services.evidence_reuse)
  mapped the item into an assessment. Reuse is recorded per assessment, not on the item, so: with an
  assessment filter the row is "reused" when it was reused into that assessment; without one it is
  "reused" when it was reused into any assessment of the engagement. reused_from names the source
  assessment. The item's own channel stays available as `origin`.
Evidence that reached an assessment only through a manual mapping (no reuse confirmation) keeps its
origin; nothing distinguishes it in the stored data, so no column was added for it.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePath

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.magic_link import MagicLink
from app.services.aws_evidence import CONFIG_PROVENANCE_PREFIX, SECURITYHUB_PROVENANCE_PREFIX
from app.services.evidence_reuse import REUSE_CONFIRMED_ACTION

SOURCES = ("upload", "aws", "client_link", "reused")
SOURCE_LABELS = {"upload": "Upload", "aws": "AWS", "client_link": "Client link", "reused": "Reused"}
STATUS_LABELS = {
    "quarantined": "Scanning",
    "active": "Available",
    "rejected": "Rejected",
    "invalidated": "Out of date",
}
LISTED_STATUSES = tuple(STATUS_LABELS)
CLIENT_LINK_PREFIX = "client_link:"
TYPE_LABELS = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/msword": "DOC",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
    "application/vnd.ms-excel": "XLS",
    "text/csv": "CSV",
    "text/plain": "Text",
    "application/json": "JSON",
    "image/png": "PNG",
    "image/jpeg": "JPG",
    "image/webp": "WEBP",
}


@dataclass(frozen=True)
class AssessmentRef:
    assessment_id: str
    name: str


@dataclass(frozen=True)
class InventoryRow:
    evidence_id: str
    filename: str
    mime_type: str
    type_label: str
    size_bytes: int
    source: str
    source_label: str
    origin: str
    contact_name: str | None
    reused_from: str | None
    used_by: tuple[AssessmentRef, ...]
    supports: tuple[str, ...]
    status: str
    status_label: str
    updated_at: datetime
    engagement_id: str
    engagement_name: str
    client_name: str


def _as_utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def type_label(mime_type: str, filename: str, origin: str = "upload") -> str:
    if origin == "aws":
        return "Snapshot"  # an AWS Config or Security Hub capture
    if mime_type in TYPE_LABELS:
        return TYPE_LABELS[mime_type]
    suffix = PurePath(filename).suffix.lstrip(".").upper()
    return suffix or "File"


def origin_of(uploaded_by: str) -> str:
    if uploaded_by.startswith((CONFIG_PROVENANCE_PREFIX, SECURITYHUB_PROVENANCE_PREFIX)):
        return "aws"
    if uploaded_by.startswith(CLIENT_LINK_PREFIX):
        return "client_link"
    return "upload"


def _current_versions(db: Session, evidence_ids: list[str]) -> dict[str, EvidenceVersion]:
    """The newest version of each item (the frozen Evidence columns record only v1)."""
    if not evidence_ids:
        return {}
    versions = db.execute(
        select(EvidenceVersion)
        .where(EvidenceVersion.evidence_id.in_(evidence_ids))
        .order_by(EvidenceVersion.evidence_id, EvidenceVersion.version_number.desc())
    ).scalars().all()
    current: dict[str, EvidenceVersion] = {}
    for version in versions:
        current.setdefault(version.evidence_id, version)
    return current


def _reuse_sources(db: Session, evidence_ids: set[str]) -> dict[tuple[str, str], str]:
    """{(evidence id, target assessment id): source assessment id} from reuse confirmations."""
    if not evidence_ids:
        return {}
    events = db.execute(
        select(AuditEvent).where(AuditEvent.action == REUSE_CONFIRMED_ACTION)
    ).scalars().all()
    use_ids = {event.entity_id for event in events}
    targets = (
        dict(db.execute(select(EvidenceUse.id, EvidenceUse.assessment_id).where(EvidenceUse.id.in_(use_ids))).all())
        if use_ids
        else {}
    )
    result: dict[tuple[str, str], str] = {}
    for event in events:
        try:
            metadata = json.loads(event.metadata_json or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        evidence_id = metadata.get("evidence_id")
        target = targets.get(event.entity_id)
        source = metadata.get("source_assessment_id")
        if evidence_id in evidence_ids and target and isinstance(source, str):
            result.setdefault((evidence_id, target), source)
    return result


def _build_rows(
    db: Session,
    evidence_rows: list[Evidence],
    *,
    assessment_id: str | None,
) -> list[InventoryRow]:
    evidence_ids = [row.id for row in evidence_rows]
    if not evidence_ids:
        return []
    versions = _current_versions(db, evidence_ids)
    uses = db.execute(select(EvidenceUse).where(EvidenceUse.evidence_id.in_(evidence_ids))).scalars().all()
    uses_by_evidence: dict[str, list[EvidenceUse]] = defaultdict(list)
    for use in uses:
        uses_by_evidence[use.evidence_id].append(use)
    assessment_ids = {use.assessment_id for use in uses} | {
        row.assessment_id for row in evidence_rows if row.assessment_id
    }
    reuse = _reuse_sources(db, set(evidence_ids))
    assessment_ids |= set(reuse.values())
    assessments = (
        {row.id: row for row in db.execute(select(Assessment).where(Assessment.id.in_(assessment_ids))).scalars()}
        if assessment_ids
        else {}
    )
    engagement_ids = {row.engagement_id for row in evidence_rows}
    engagements = {
        row.id: row for row in db.execute(select(Engagement).where(Engagement.id.in_(engagement_ids))).scalars()
    }
    client_ids = {row.client_id for row in engagements.values()}
    clients = {row.id: row for row in db.execute(select(Client).where(Client.id.in_(client_ids))).scalars()}
    link_ids = {
        row.uploaded_by.removeprefix(CLIENT_LINK_PREFIX)
        for row in evidence_rows
        if row.uploaded_by.startswith(CLIENT_LINK_PREFIX)
    }
    contacts = (
        dict(db.execute(select(MagicLink.id, MagicLink.contact_name).where(MagicLink.id.in_(link_ids))).all())
        if link_ids
        else {}
    )

    rows = []
    for evidence in evidence_rows:
        version = versions.get(evidence.id)
        used_ids = list(
            dict.fromkeys(
                ([evidence.assessment_id] if evidence.assessment_id else [])
                + sorted(
                    {use.assessment_id for use in uses_by_evidence[evidence.id]},
                    key=lambda aid: (assessments[aid].display_name if aid in assessments else "", aid),
                )
            )
        )
        if assessment_id is not None:
            sources = [reuse[(evidence.id, assessment_id)]] if (evidence.id, assessment_id) in reuse else []
        else:
            sources = [source for (eid, _target), source in reuse.items() if eid == evidence.id]
        origin = origin_of(evidence.uploaded_by)
        source = "reused" if sources else origin
        reused_from = assessments[sources[0]].display_name if sources and sources[0] in assessments else None
        filename = version.original_filename if version else evidence.original_filename
        mime_type = version.mime_type if version else evidence.mime_type
        updated = max(
            [_as_utc(evidence.created_at)] + ([_as_utc(version.created_at)] if version else [])
        )
        engagement = engagements.get(evidence.engagement_id)
        client = clients.get(engagement.client_id) if engagement else None
        supports_uses = [
            use for use in uses_by_evidence[evidence.id]
            if assessment_id is None or use.assessment_id == assessment_id
        ]
        rows.append(
            InventoryRow(
                evidence_id=evidence.id,
                filename=filename,
                mime_type=mime_type,
                type_label=type_label(mime_type, filename, origin),
                size_bytes=version.file_size_bytes if version else evidence.file_size_bytes,
                source=source,
                source_label=SOURCE_LABELS[source],
                origin=origin,
                contact_name=(
                    contacts.get(evidence.uploaded_by.removeprefix(CLIENT_LINK_PREFIX))
                    if origin == "client_link"
                    else None
                ),
                reused_from=reused_from,
                used_by=tuple(
                    AssessmentRef(aid, assessments[aid].display_name) for aid in used_ids if aid in assessments
                ),
                supports=tuple(sorted({use.requirement_id for use in supports_uses})),
                status=evidence.status,
                status_label=STATUS_LABELS[evidence.status],
                updated_at=updated,
                engagement_id=evidence.engagement_id,
                engagement_name=engagement.name if engagement else "",
                client_name=client.name if client else "",
            )
        )
    return sorted(rows, key=lambda row: (row.updated_at, row.evidence_id), reverse=True)


def _filter(
    rows: list[InventoryRow],
    *,
    source: str | None,
    status: str | None,
    search: str | None,
) -> list[InventoryRow]:
    needle = (search or "").strip().casefold()
    return [
        row
        for row in rows
        if (source is None or row.source == source)
        and (status is None or row.status == status)
        and (
            not needle
            or needle in row.filename.casefold()
            or any(needle in code.casefold() for code in row.supports)
            or (row.contact_name is not None and needle in row.contact_name.casefold())
        )
    ]


def _listed(query):
    return query.where(Evidence.status.in_(LISTED_STATUSES))


def inventory_rows(
    db: Session,
    engagement_id: str,
    *,
    assessment_id: str | None = None,
    source: str | None = None,
    status: str | None = None,
    search: str | None = None,
) -> list[InventoryRow]:
    """The engagement's evidence, newest first. assessment_id keeps the items uploaded to or mapped
    into that assessment; source is one of SOURCES; status is a raw state (see STATUS_LABELS)."""
    query = _listed(select(Evidence).where(Evidence.engagement_id == engagement_id))
    if assessment_id is not None:
        used = select(EvidenceUse.evidence_id).where(EvidenceUse.assessment_id == assessment_id)
        query = query.where(or_(Evidence.assessment_id == assessment_id, Evidence.id.in_(used)))
    rows = _build_rows(db, db.execute(query).scalars().all(), assessment_id=assessment_id)
    return _filter(rows, source=source, status=status, search=search)


def cross_engagement_rows(
    db: Session,
    *,
    client_id: str | None = None,
    engagement_id: str | None = None,
    source: str | None = None,
    status: str | None = None,
    search: str | None = None,
) -> list[InventoryRow]:
    """Evidence across every engagement that is not archived (the side-menu Evidence view), newest
    first; each row carries its engagement and client."""
    engagements = select(Engagement.id).where(Engagement.status != "archived")
    if client_id is not None:
        engagements = engagements.where(Engagement.client_id == client_id)
    if engagement_id is not None:
        engagements = engagements.where(Engagement.id == engagement_id)
    query = _listed(select(Evidence).where(Evidence.engagement_id.in_(engagements)))
    rows = _build_rows(db, db.execute(query).scalars().all(), assessment_id=None)
    return _filter(rows, source=source, status=status, search=search)


def status_counts(rows: list[InventoryRow]) -> dict[str, int]:
    """{"total": n, "Scanning": n, "Available": n, "Rejected": n, "Out of date": n} for the given rows."""
    counted = Counter(row.status_label for row in rows)
    return {"total": len(rows), **{label: counted.get(label, 0) for label in STATUS_LABELS.values()}}
