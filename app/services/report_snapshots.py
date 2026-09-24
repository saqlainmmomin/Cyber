"""Report snapshots (P3-2): write-once rendered report versions with a one-way draft-to-issued lifecycle. Never re-renders, never overwrites, never un-issues."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import literal_column, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.assessment import Assessment, _new_id
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion
from app.models.report import GapReport
from app.models.report_snapshot import ReportSnapshot
from app.services.conclusion_review import REVIEWER_ACTOR_PREFIX

SNAPSHOT_TYPES = ("gap_report", "workpaper", "integrated_report")
ASSESSMENT_SNAPSHOT_TYPES = ("gap_report", "workpaper")
FORMAT_BY_TYPE = {
    "gap_report": "pdf",
    "workpaper": "html",
    "integrated_report": "pdf",
}
MEDIA_TYPES = {"pdf": "application/pdf", "html": "text/html; charset=utf-8"}
TYPE_LABELS = {
    "gap_report": "Gap report (PDF)",
    "workpaper": "Workpaper (HTML)",
    "integrated_report": "Integrated engagement report (PDF)",
}

AUDIT_ENTITY_TYPE = "report_snapshot"
GENERATED_ACTION = "report_snapshot.generated"
ISSUED_ACTION = "report_snapshot.issued"
MANIFEST_SCHEMA_VERSION = 1
ISSUE_SQL = """UPDATE report_snapshots SET is_issued = 1
WHERE id = :id AND is_issued = 0
  AND NOT EXISTS (
    SELECT 1 FROM report_snapshots AS newer
    WHERE newer.type = report_snapshots.type
      AND newer.rowid > report_snapshots.rowid
      AND (
        (report_snapshots.assessment_id IS NOT NULL AND newer.assessment_id = report_snapshots.assessment_id)
        OR (report_snapshots.assessment_id IS NULL AND newer.assessment_id IS NULL
            AND newer.engagement_id = report_snapshots.engagement_id)
      )
  )"""

INTEGRITY_MESSAGE = (
    "The stored file for this version is missing or does not match its recorded "
    "hash. Nothing was issued."
)
SNAPSHOT_STALE_MESSAGE = (
    "This version was generated before the current release. Generate a new version, "
    "then issue it."
)


class SnapshotError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidSnapshot(SnapshotError):
    status_code = 400


class SnapshotNotFound(SnapshotError):
    status_code = 404


class SnapshotNotIssuable(SnapshotError):
    status_code = 409


class SnapshotIntegrityError(SnapshotError):
    status_code = 500


def storage_path_for(
    *,
    snapshot_id: str,
    fmt: str,
    assessment_id: str | None = None,
    engagement_id: str | None = None,
) -> str:
    if assessment_id is not None:
        return f"reports/assessments/{assessment_id}/{snapshot_id}.{fmt}"
    if engagement_id is not None:
        return f"reports/engagements/{engagement_id}/{snapshot_id}.{fmt}"
    raise ValueError("A report snapshot requires an assessment or engagement scope.")


def snapshot_path(snapshot: ReportSnapshot) -> Path:
    return Path(settings.upload_dir) / snapshot.storage_path


def source_manifest(db: Session, assessment: Assessment) -> dict:
    report_row = (
        db.query(GapReport.id)
        .filter(GapReport.assessment_id == assessment.id)
        .first()
    )
    conclusion_versions = db.execute(
        select(Conclusion.id, Conclusion.version)
        .where(Conclusion.assessment_id == assessment.id)
        .order_by(Conclusion.id)
    ).all()
    return {
        "gap_report_id": report_row[0] if report_row else None,
        "conclusion_versions": [[row.id, row.version] for row in conclusion_versions],
    }


def _write_file(storage_path: str, content: bytes) -> Path:
    path = Path(settings.upload_dir) / storage_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)
    return path


def _record_event(
    db: Session,
    *,
    actor: str,
    action: str,
    snapshot_id: str,
    metadata: dict,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type=AUDIT_ENTITY_TYPE,
            entity_id=snapshot_id,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    )


def _store(
    db: Session,
    *,
    snapshot_id: str,
    snapshot_type: str,
    fmt: str,
    storage_path: str,
    content: bytes,
    actor: str,
    assessment_id: str | None,
    engagement_id: str | None,
    review_status: str | None,
    source: dict,
) -> ReportSnapshot:
    digest = hashlib.sha256(content).hexdigest()
    path = _write_file(storage_path, content)
    try:
        snapshot = ReportSnapshot(
            id=snapshot_id,
            assessment_id=assessment_id,
            engagement_id=engagement_id,
            type=snapshot_type,
            format=fmt,
            storage_path=storage_path,
            is_issued=False,
        )
        db.add(snapshot)
        _record_event(
            db,
            actor=actor,
            action=GENERATED_ACTION,
            snapshot_id=snapshot_id,
            metadata={
                "schema_version": MANIFEST_SCHEMA_VERSION,
                "type": snapshot_type,
                "format": fmt,
                "storage_path": storage_path,
                "sha256": digest,
                "size_bytes": len(content),
                "assessment_id": assessment_id,
                "engagement_id": engagement_id,
                "review_status": review_status,
                "source": source,
            },
        )
        db.flush()
        return snapshot
    except Exception:
        path.unlink(missing_ok=True)
        raise


def create_snapshot(
    db: Session,
    *,
    assessment: Assessment,
    snapshot_type: str,
    content: bytes,
    actor: str,
) -> ReportSnapshot:
    if snapshot_type not in ASSESSMENT_SNAPSHOT_TYPES:
        raise InvalidSnapshot("Unknown report type.")
    if not content:
        raise InvalidSnapshot("Rendered report was empty; nothing was saved.")

    snapshot_id = _new_id()
    fmt = FORMAT_BY_TYPE[snapshot_type]
    storage_path = storage_path_for(
        snapshot_id=snapshot_id,
        fmt=fmt,
        assessment_id=assessment.id,
    )
    manifest = source_manifest(db, assessment)
    return _store(
        db,
        snapshot_id=snapshot_id,
        snapshot_type=snapshot_type,
        fmt=fmt,
        storage_path=storage_path,
        content=content,
        actor=actor,
        assessment_id=assessment.id,
        engagement_id=assessment.engagement_id,
        review_status=assessment.review_status,
        source=manifest,
    )


def create_engagement_snapshot(
    db: Session,
    *,
    engagement,
    content: bytes,
    actor: str,
    source: dict,
) -> ReportSnapshot:
    if not content:
        raise InvalidSnapshot("Rendered report was empty; nothing was saved.")
    snapshot_id = _new_id()
    fmt = FORMAT_BY_TYPE["integrated_report"]
    storage_path = storage_path_for(
        snapshot_id=snapshot_id,
        fmt=fmt,
        engagement_id=engagement.id,
    )
    return _store(
        db,
        snapshot_id=snapshot_id,
        snapshot_type="integrated_report",
        fmt=fmt,
        storage_path=storage_path,
        content=content,
        actor=actor,
        assessment_id=None,
        engagement_id=engagement.id,
        review_status=None,
        source=source,
    )


def load_engagement_snapshot(
    db: Session,
    *,
    engagement_id: str,
    snapshot_id: str,
) -> ReportSnapshot:
    snapshot = (
        db.query(ReportSnapshot)
        .filter(
            ReportSnapshot.id == snapshot_id,
            ReportSnapshot.engagement_id == engagement_id,
            ReportSnapshot.assessment_id.is_(None),
            ReportSnapshot.type == "integrated_report",
        )
        .first()
    )
    if snapshot is None:
        raise SnapshotNotFound("Report version not found.")
    return snapshot


def load_snapshot(
    db: Session,
    *,
    assessment_id: str,
    snapshot_id: str,
) -> ReportSnapshot:
    snapshot = (
        db.query(ReportSnapshot)
        .filter(
            ReportSnapshot.id == snapshot_id,
            ReportSnapshot.assessment_id == assessment_id,
        )
        .first()
    )
    if snapshot is None:
        raise SnapshotNotFound("Report version not found.")
    return snapshot


def generated_event(db: Session, snapshot_id: str) -> dict:
    event = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
            AuditEvent.entity_id == snapshot_id,
            AuditEvent.action == GENERATED_ACTION,
        )
        .first()
    )
    if event is None or event.metadata_json is None:
        raise SnapshotIntegrityError(INTEGRITY_MESSAGE)
    try:
        metadata = json.loads(event.metadata_json)
    except (json.JSONDecodeError, TypeError):
        raise SnapshotIntegrityError(INTEGRITY_MESSAGE) from None
    if not isinstance(metadata, dict):
        raise SnapshotIntegrityError(INTEGRITY_MESSAGE)
    return metadata


def generated_after(db: Session, snapshot_id: str, event_id: str) -> bool:
    """Return whether a snapshot was generated after the supplied audit event."""
    generated_rowid = db.execute(
        select(literal_column("audit_events.rowid"))
        .where(
            AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
            AuditEvent.entity_id == snapshot_id,
            AuditEvent.action == GENERATED_ACTION,
        )
        .order_by(literal_column("audit_events.rowid").desc())
        .limit(1)
    ).scalar_one_or_none()
    release_rowid = db.execute(
        select(literal_column("audit_events.rowid")).where(
            AuditEvent.id == event_id,
        )
    ).scalar_one_or_none()
    return (
        generated_rowid is not None
        and release_rowid is not None
        and generated_rowid > release_rowid
    )


def read_snapshot_bytes(db: Session, snapshot: ReportSnapshot) -> bytes:
    metadata = generated_event(db, snapshot.id)
    expected = metadata.get("sha256")
    try:
        content = snapshot_path(snapshot).read_bytes()
    except OSError:
        raise SnapshotIntegrityError(INTEGRITY_MESSAGE) from None
    if not isinstance(expected, str) or hashlib.sha256(content).hexdigest() != expected:
        raise SnapshotIntegrityError(INTEGRITY_MESSAGE)
    return content


def verify_snapshot_file(db: Session, snapshot: ReportSnapshot) -> None:
    read_snapshot_bytes(db, snapshot)


def issue_snapshot(
    db: Session,
    snapshot: ReportSnapshot,
    *,
    actor: str,
) -> ReportSnapshot:
    verify_snapshot_file(db, snapshot)
    result = db.execute(text(ISSUE_SQL), {"id": snapshot.id})
    if result.rowcount != 1:
        db.expire(snapshot)
        if snapshot.is_issued:
            raise SnapshotNotIssuable("This version is already issued.")
        raise SnapshotNotIssuable(
            "A newer version of this report exists. Issue the newest version, or generate a new one."
        )

    db.expire(snapshot)
    metadata = generated_event(db, snapshot.id)
    _record_event(
        db,
        actor=actor,
        action=ISSUED_ACTION,
        snapshot_id=snapshot.id,
        metadata={
            "assessment_id": snapshot.assessment_id,
            "engagement_id": snapshot.engagement_id,
            "sha256": metadata["sha256"],
            "type": snapshot.type,
        },
    )
    db.flush()
    return snapshot


def _actor_display(actor: str | None) -> str | None:
    if actor is None:
        return None
    if actor.startswith(REVIEWER_ACTOR_PREFIX):
        return actor.removeprefix(REVIEWER_ACTOR_PREFIX)
    return actor


@dataclass(frozen=True)
class SnapshotRow:
    snapshot: ReportSnapshot
    sequence: int
    state: str
    is_current_issue: bool
    issuable: bool
    sha256: str | None
    size_bytes: int | None
    generated_by: str | None
    issued_by: str | None
    issued_at: datetime | None
    source_changed: bool


def _build_rows(
    snapshots: list[ReportSnapshot],
    generated_by_id: dict[str, AuditEvent],
    issued_by_id: dict[str, AuditEvent],
    current_source: dict | None,
) -> list[SnapshotRow]:
    newest_id = snapshots[-1].id if snapshots else None
    issued_rows = [row for row in snapshots if row.is_issued]
    current_issue_id = issued_rows[-1].id if issued_rows else None
    rendered_rows = []
    for sequence, snapshot in enumerate(snapshots, start=1):
        generated = generated_by_id.get(snapshot.id)
        issued = issued_by_id.get(snapshot.id)
        try:
            metadata = (
                json.loads(generated.metadata_json)
                if generated is not None and generated.metadata_json is not None
                else {}
            )
        except (json.JSONDecodeError, TypeError):
            metadata = {}
        state = (
            "issued"
            if snapshot.is_issued
            else "draft"
            if snapshot.id == newest_id
            else "superseded_draft"
        )
        rendered_rows.append(
            SnapshotRow(
                snapshot=snapshot,
                sequence=sequence,
                state=state,
                is_current_issue=snapshot.id == current_issue_id,
                issuable=state == "draft",
                sha256=metadata.get("sha256"),
                size_bytes=metadata.get("size_bytes"),
                generated_by=_actor_display(generated.actor if generated else None),
                issued_by=_actor_display(issued.actor if issued else None),
                issued_at=issued.created_at if issued else None,
                source_changed=(
                    current_source is not None
                    and metadata.get("source") != current_source
                ),
            )
        )
    return list(reversed(rendered_rows))


def _event_maps(db: Session, snapshot_ids: list[str]):
    events = (
        db.execute(
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
                AuditEvent.entity_id.in_(snapshot_ids),
                AuditEvent.action.in_((GENERATED_ACTION, ISSUED_ACTION)),
            )
            .order_by(literal_column("audit_events.rowid"))
        ).scalars().all()
        if snapshot_ids
        else []
    )
    generated_by_id: dict[str, AuditEvent] = {}
    issued_by_id: dict[str, AuditEvent] = {}
    for event in events:
        if event.action == GENERATED_ACTION:
            generated_by_id[event.entity_id] = event
        elif event.action == ISSUED_ACTION:
            issued_by_id[event.entity_id] = event
    return generated_by_id, issued_by_id


def snapshot_rows(
    db: Session,
    assessment: Assessment,
) -> dict[str, list[SnapshotRow]]:
    snapshots = db.execute(
        select(ReportSnapshot)
        .where(ReportSnapshot.assessment_id == assessment.id)
        .order_by(literal_column("report_snapshots.rowid"))
    ).scalars().all()
    snapshot_ids = [snapshot.id for snapshot in snapshots]
    generated_by_id, issued_by_id = _event_maps(db, snapshot_ids)
    current_manifest = source_manifest(db, assessment)

    grouped: dict[str, list[ReportSnapshot]] = {
        snapshot_type: [] for snapshot_type in ASSESSMENT_SNAPSHOT_TYPES
    }
    for snapshot in snapshots:
        if snapshot.type in grouped:
            grouped[snapshot.type].append(snapshot)

    result: dict[str, list[SnapshotRow]] = {
        snapshot_type: [] for snapshot_type in ASSESSMENT_SNAPSHOT_TYPES
    }
    for snapshot_type, rows in grouped.items():
        result[snapshot_type] = _build_rows(
            rows,
            generated_by_id,
            issued_by_id,
            current_manifest,
        )
    return result


def engagement_snapshot_rows(
    db: Session,
    engagement,
    *,
    current_source: dict | None,
) -> list[SnapshotRow]:
    snapshots = db.execute(
        select(ReportSnapshot)
        .where(
            ReportSnapshot.engagement_id == engagement.id,
            ReportSnapshot.assessment_id.is_(None),
            ReportSnapshot.type == "integrated_report",
        )
        .order_by(literal_column("report_snapshots.rowid"))
    ).scalars().all()
    generated_by_id, issued_by_id = _event_maps(
        db, [snapshot.id for snapshot in snapshots]
    )
    return _build_rows(
        snapshots,
        generated_by_id,
        issued_by_id,
        current_source,
    )
