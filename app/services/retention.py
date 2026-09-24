"""Engagement retention (P4-4): reversible archive as an engagement status flip inferred by every child, per-client retention, and a manual two-phase permanent purge that commits the DB deletion first and removes the engagement's storage folders second, with audit events as the ledger. Never purges automatically."""

from __future__ import annotations

import json
import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from sqlalchemy import and_, delete, func, literal_column, or_, select, text, update
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.models.action import Action
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment, AssessmentDocument
from app.models.assessment_pack import AssessmentPack
from app.models.audit_event import AuditEvent
from app.models.client import Client
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.finding import Finding
from app.models.magic_link import MagicLink
from app.models.initiative import Initiative
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.models.report_snapshot import ReportSnapshot
from app.models.rfi import RFIDocument
from app.services import conclusion_review

logger = logging.getLogger(__name__)

ARCHIVED_STATUS = "archived"
ARCHIVABLE_STATUSES = ("active", "closed")
RETENTION_YEARS_RANGE = (1, 50)
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

PURGE_ORDER = (
    "evidence_uses",
    "actions",
    "findings",
    "conclusion_revisions",
    "conclusions",
    "analysis_runs",
    "initiatives",
    "gap_items",
    "gap_reports",
    "desk_review_findings",
    "desk_review_summaries",
    "questionnaire_responses",
    "rfi_documents",
    "assessment_packs",
    "report_snapshots",
    "evidence_versions",
    "evidence",
    "assessment_documents",
    "magic_links",
    "assessments",
    "engagements",
)
RETAINED_TABLES = ("clients", "audit_events")

REFUSAL_REASONS = (
    "not_archived",
    "archive_record_missing",
    "retention_invalid",
    "retention_not_elapsed",
    "active_dependencies",
    "storage_layout_invalid",
)
DEPENDENCY_CODES = (
    "evidence_used_elsewhere",
    "evidence_cited_elsewhere",
    "evidence_linked_elsewhere",
    "blob_shared_elsewhere",
)

ENGAGEMENT_ENTITY = "engagement"
CLIENT_ENTITY = "client"
ARCHIVED_EVENT = "engagement.archived"
UNARCHIVED_EVENT = "engagement.unarchived"
PURGE_REFUSED_EVENT = "engagement.purge_refused"
PURGED_EVENT = "engagement.purged"
PURGE_BLOBS_REMOVED_EVENT = "engagement.purge_blobs_removed"
RETENTION_CHANGED_EVENT = "client.retention_changed"
EVENT_SCHEMA_VERSION = 1
COMPLETION_SCRIPT_ACTOR = "system:purge-completion"

ENGAGEMENT_NOT_FOUND = "Engagement not found"
CLIENT_NOT_FOUND = "Client not found"
ARCHIVED_READ_ONLY = "This engagement is archived and read-only. Unarchive it to make changes."
ALREADY_ARCHIVED = "This engagement is already archived."
NOT_ARCHIVABLE = "Only an active or closed engagement can be archived."
ARCHIVE_IN_FLIGHT = "An analysis or desk review is still running in this engagement. Wait for it to finish, then archive."
ARCHIVE_CONFLICT = "This engagement changed while you were archiving it. Reload and try again."
NOT_ARCHIVED = "This engagement is not archived."
UNARCHIVE_CONFLICT = "This engagement changed while you were restoring it. Reload and try again."
RETENTION_YEARS_INVALID = "Retention must be a whole number of years from 1 to 50."
RETENTION_CONFLICT = "The retention of this client changed while you were editing it. Reload and try again."
CONFIRM_MISMATCH = "Type the engagement name exactly as shown to confirm permanent deletion."
ALREADY_PURGED = "This engagement has already been purged."
PURGE_FAILED = "The purge could not be completed. Nothing was deleted."
PURGE_BLOBS_PENDING = "The records of this engagement were permanently deleted, but some stored files could not be removed yet. Finish the purge from the client page or run scripts/complete_purges.py."
NO_PENDING_PURGE = "There is no unfinished purge for this engagement."
PURGE_LEDGER_INCONSISTENT = "The purge record for this engagement does not match the database. Nothing was removed."
PURGE_LEDGER_INVALID = "The purge record for this engagement is not valid. Nothing was removed."

REASON_MESSAGES = {
    "not_archived": "Only an archived engagement can be purged.",
    "archive_record_missing": "No archive record was found for this engagement. Unarchive it and archive it again to start its retention period.",
    "retention_invalid": "The retention setting of this client is not valid. Set a retention period from 1 to 50 years first.",
    "retention_not_elapsed": "The retention period has not elapsed. This engagement can be purged on or after {eligible_at:%d %b %Y}.",
    "active_dependencies": "Other records still depend on the evidence of this engagement: {dependencies}.",
    "storage_layout_invalid": "Some stored files of this engagement are outside its storage folders. Nothing can be purged until this is resolved.",
}
DEPENDENCY_LABELS = {
    "evidence_used_elsewhere": "evidence mapped into an assessment of another engagement",
    "evidence_cited_elsewhere": "evidence cited by records of another engagement",
    "evidence_linked_elsewhere": "evidence filed under another engagement",
    "blob_shared_elsewhere": "stored files shared with another engagement",
}


class RetentionError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RetentionNotFound(RetentionError):
    status_code = 404


class InvalidRetentionRequest(RetentionError):
    status_code = 400


class RetentionConflict(RetentionError):
    status_code = 409


class PurgeRefused(RetentionConflict):
    def __init__(self, eligibility: Eligibility):
        self.eligibility = eligibility
        super().__init__(refusal_message(eligibility))


class PurgeFailed(RetentionError):
    status_code = 500


class PurgeIntegrityError(Exception):
    pass


class BlobRootError(Exception):
    def __init__(self, root: str):
        self.root = root
        super().__init__(root)


class _BlobRemovalFailure(Exception):
    def __init__(self, root: str, cause: Exception):
        self.root = root
        self.cause = cause
        super().__init__(root)


@dataclass(frozen=True)
class ArchiveRecord:
    event_id: str
    archived_at: datetime
    actor: str
    previous_status: str | None
    retention_years_at_archive: int | None


@dataclass(frozen=True)
class RetentionState:
    engagement_id: str
    status: str
    archived: bool
    record: ArchiveRecord | None
    client_retention_years: int | None
    retention_years_applied: int | None
    eligible_at: datetime | None
    elapsed: bool
    archived_by_display: str


@dataclass(frozen=True)
class Dependency:
    code: str
    count: int


@dataclass(frozen=True)
class PurgePlan:
    engagement_id: str
    client_id: str
    assessment_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    version_ids: tuple[str, ...]
    row_counts: dict[str, int]
    blob_roots: tuple[str, ...]
    blob_file_count: int
    layout_violations: int


@dataclass(frozen=True)
class Eligibility:
    reasons: tuple[str, ...]
    dependencies: tuple[Dependency, ...]
    layout_violations: int
    state: RetentionState


@dataclass(frozen=True)
class PurgeResult:
    engagement_id: str
    client_id: str
    purge_event_id: str
    row_counts: dict[str, int]
    blob_roots: tuple[str, ...]
    blobs_removed: bool
    failed_root: str | None


@dataclass(frozen=True)
class PendingPurge:
    engagement_id: str
    purge_event_id: str
    purged_at: datetime
    blob_roots: tuple[str, ...]


@dataclass(frozen=True)
class CompletionOutcome:
    already_complete: bool
    removed_roots: tuple[str, ...]
    missing_roots: tuple[str, ...]


@dataclass(frozen=True)
class ArchivedEngagementRow:
    engagement_id: str
    name: str
    archived_at: datetime | None
    eligible_at: datetime | None
    elapsed: bool


@dataclass(frozen=True)
class PurgeRecordRow:
    engagement_id: str
    engagement_name: str
    purged_at: datetime
    purged_by_display: str
    blobs_removed: bool


@dataclass(frozen=True)
class ClientRetentionView:
    archived: list[ArchivedEngagementRow]
    purges: list[PurgeRecordRow]


def _as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _now(now: datetime | None = None) -> datetime:
    return _as_utc(now or datetime.now(timezone.utc))


def add_years(moment: datetime, years: int) -> datetime:
    moment = _as_utc(moment)
    try:
        return moment.replace(year=moment.year + years)
    except ValueError:
        return moment.replace(year=moment.year + years, day=28)


def _valid_retention(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and RETENTION_YEARS_RANGE[0] <= value <= RETENTION_YEARS_RANGE[1]
    )


def _parse_metadata(event: AuditEvent) -> dict | None:
    try:
        value = json.loads(event.metadata_json or "")
    except (TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict,
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata, sort_keys=True),
    )
    db.add(event)
    return event


def _engagement_events(
    db: Session,
    engagement_id: str,
    actions: tuple[str, ...],
) -> list[AuditEvent]:
    return list(
        db.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == ENGAGEMENT_ENTITY,
                AuditEvent.entity_id == engagement_id,
                AuditEvent.action.in_(actions),
            )
            .order_by(literal_column("audit_events.rowid").desc())
        ).all()
    )


def _has_purged_event(db: Session, engagement_id: str) -> bool:
    return (
        db.execute(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.entity_type == ENGAGEMENT_ENTITY,
                AuditEvent.entity_id == engagement_id,
                AuditEvent.action == PURGED_EVENT,
            )
        ).scalar_one()
        > 0
    )


def archive_record(db: Session, engagement_id: str) -> ArchiveRecord | None:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None or engagement.status != ARCHIVED_STATUS:
        return None
    for event in _engagement_events(db, engagement_id, (ARCHIVED_EVENT, UNARCHIVED_EVENT)):
        if event.action != ARCHIVED_EVENT:
            continue
        metadata = _parse_metadata(event)
        if metadata is None:
            continue
        retention_years = metadata.get("retention_years")
        return ArchiveRecord(
            event_id=event.id,
            archived_at=_as_utc(event.created_at),
            actor=event.actor,
            previous_status=(
                metadata.get("previous_status")
                if isinstance(metadata.get("previous_status"), str)
                else None
            ),
            retention_years_at_archive=(
                retention_years if _valid_retention(retention_years) else None
            ),
        )
    return None


def retention_state(
    db: Session,
    engagement: Engagement,
    *,
    now: datetime | None = None,
) -> RetentionState:
    client = db.get(Client, engagement.client_id)
    current_years = client.retention_years if client and _valid_retention(client.retention_years) else None
    archived = engagement.status == ARCHIVED_STATUS
    record = archive_record(db, engagement.id) if archived else None
    applied = None
    eligible_at = None
    if record is not None and current_years is not None:
        applied = max(
            current_years,
            record.retention_years_at_archive
            if record.retention_years_at_archive is not None
            else current_years,
        )
        eligible_at = add_years(record.archived_at, applied)
    current = _now(now)
    return RetentionState(
        engagement_id=engagement.id,
        status=engagement.status,
        archived=archived,
        record=record,
        client_retention_years=current_years,
        retention_years_applied=applied,
        eligible_at=eligible_at,
        elapsed=eligible_at is not None and current >= eligible_at,
        archived_by_display=(
            record.actor.removeprefix(conclusion_review.REVIEWER_ACTOR_PREFIX)
            if record is not None
            else ""
        ),
    )


def engagement_ids_for_path(
    db: Session,
    path_params: Mapping[str, str],
) -> set[str]:
    ids: set[str] = set()
    engagement_id = path_params.get("engagement_id")
    if engagement_id:
        ids.add(engagement_id)
    assessment_id = path_params.get("assessment_id")
    if assessment_id:
        assessment = db.get(Assessment, assessment_id)
        if assessment is not None and assessment.engagement_id is not None:
            ids.add(assessment.engagement_id)
    evidence_id = path_params.get("evidence_id")
    if evidence_id:
        evidence = db.get(Evidence, evidence_id)
        if evidence is not None:
            ids.add(evidence.engagement_id)
    return ids


def archived_engagement_ids(db: Session, engagement_ids: set[str]) -> set[str]:
    if not engagement_ids:
        return set()
    return set(
        db.scalars(
            select(Engagement.id).where(
                Engagement.id.in_(engagement_ids),
                Engagement.status == ARCHIVED_STATUS,
            )
        ).all()
    )


def _in_flight_count(db: Session, engagement_id: str) -> int:
    return db.execute(
        select(func.count())
        .select_from(Assessment)
        .where(
            Assessment.engagement_id == engagement_id,
            or_(
                Assessment.status == "analyzing",
                Assessment.desk_review_status == "analyzing",
            ),
        )
    ).scalar_one()


def archive_engagement(
    db: Session,
    *,
    engagement_id: str,
    actor: str,
    now: datetime | None = None,
) -> Engagement:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise RetentionNotFound(ENGAGEMENT_NOT_FOUND)
    if engagement.status == ARCHIVED_STATUS:
        raise RetentionConflict(ALREADY_ARCHIVED)
    if engagement.status not in ARCHIVABLE_STATUSES:
        raise RetentionConflict(NOT_ARCHIVABLE)
    if _in_flight_count(db, engagement_id):
        raise RetentionConflict(ARCHIVE_IN_FLIGHT)
    client = db.get(Client, engagement.client_id)
    if client is None:
        raise RetentionNotFound(CLIENT_NOT_FOUND)
    timestamp = _now(now)
    previous_status = engagement.status
    result = db.execute(
        update(Engagement)
        .where(Engagement.id == engagement_id, Engagement.status == previous_status)
        .values(status=ARCHIVED_STATUS, updated_at=timestamp)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise RetentionConflict(ARCHIVE_CONFLICT)
    db.expire(engagement)
    _audit(
        db,
        actor=actor,
        action=ARCHIVED_EVENT,
        entity_type=ENGAGEMENT_ENTITY,
        entity_id=engagement_id,
        metadata={
            "schema_version": EVENT_SCHEMA_VERSION,
            "client_id": client.id,
            "previous_status": previous_status,
            "retention_years": client.retention_years,
        },
    )
    db.flush()
    return engagement


def unarchive_engagement(
    db: Session,
    *,
    engagement_id: str,
    actor: str,
    now: datetime | None = None,
) -> Engagement:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise RetentionNotFound(ENGAGEMENT_NOT_FOUND)
    if engagement.status != ARCHIVED_STATUS:
        raise RetentionConflict(NOT_ARCHIVED)
    record = archive_record(db, engagement_id)
    restored_status = (
        record.previous_status if record and record.previous_status in ARCHIVABLE_STATUSES else "active"
    )
    timestamp = _now(now)
    result = db.execute(
        update(Engagement)
        .where(Engagement.id == engagement_id, Engagement.status == ARCHIVED_STATUS)
        .values(status=restored_status, updated_at=timestamp)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise RetentionConflict(UNARCHIVE_CONFLICT)
    db.expire(engagement)
    _audit(
        db,
        actor=actor,
        action=UNARCHIVED_EVENT,
        entity_type=ENGAGEMENT_ENTITY,
        entity_id=engagement_id,
        metadata={
            "schema_version": EVENT_SCHEMA_VERSION,
            "archive_event_id": record.event_id if record else None,
            "restored_status": restored_status,
        },
    )
    db.flush()
    return engagement


def set_client_retention(
    db: Session,
    *,
    client_id: str,
    retention_years: str | int | None,
    actor: str,
) -> tuple[Client, bool]:
    if isinstance(retention_years, bool):
        raise InvalidRetentionRequest(RETENTION_YEARS_INVALID)
    raw = str(retention_years).strip() if retention_years is not None else ""
    if not re.fullmatch(r"[0-9]{1,3}", raw):
        raise InvalidRetentionRequest(RETENTION_YEARS_INVALID)
    value = int(raw)
    if not _valid_retention(value):
        raise InvalidRetentionRequest(RETENTION_YEARS_INVALID)
    client = db.get(Client, client_id)
    if client is None:
        raise RetentionNotFound(CLIENT_NOT_FOUND)
    previous = client.retention_years
    if previous == value:
        return client, False
    timestamp = _now()
    result = db.execute(
        update(Client)
        .where(Client.id == client_id, Client.retention_years == previous)
        .values(retention_years=value, updated_at=timestamp)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise RetentionConflict(RETENTION_CONFLICT)
    db.expire(client)
    _audit(
        db,
        actor=actor,
        action=RETENTION_CHANGED_EVENT,
        entity_type=CLIENT_ENTITY,
        entity_id=client_id,
        metadata={
            "schema_version": EVENT_SCHEMA_VERSION,
            "from": previous,
            "to": value,
        },
    )
    db.flush()
    return client, True


def _blob_roots(engagement_id: str, assessment_ids: tuple[str, ...]) -> tuple[str, ...]:
    roots = [f"evidence/{engagement_id}", f"reports/engagements/{engagement_id}"]
    for assessment_id in assessment_ids:
        roots.extend((f"reports/assessments/{assessment_id}", assessment_id))
    return tuple(roots)


def _purge_scopes(
    plan: PurgePlan,
) -> list[tuple[str, type, object]]:
    assessment_ids = plan.assessment_ids
    evidence_ids = plan.evidence_ids
    engagement_id = plan.engagement_id
    finding_ids = select(Finding.id).where(Finding.assessment_id.in_(assessment_ids))
    conclusion_ids = select(Conclusion.id).where(Conclusion.assessment_id.in_(assessment_ids))
    report_ids = select(GapReport.id).where(GapReport.assessment_id.in_(assessment_ids))
    return [
        ("evidence_uses", EvidenceUse, or_(EvidenceUse.evidence_id.in_(evidence_ids), EvidenceUse.assessment_id.in_(assessment_ids))),
        ("actions", Action, Action.finding_id.in_(finding_ids)),
        ("findings", Finding, Finding.assessment_id.in_(assessment_ids)),
        ("conclusion_revisions", ConclusionRevision, ConclusionRevision.conclusion_id.in_(conclusion_ids)),
        ("conclusions", Conclusion, Conclusion.assessment_id.in_(assessment_ids)),
        ("analysis_runs", AnalysisRun, AnalysisRun.assessment_id.in_(assessment_ids)),
        ("initiatives", Initiative, Initiative.report_id.in_(report_ids)),
        ("gap_items", GapItem, GapItem.report_id.in_(report_ids)),
        ("gap_reports", GapReport, GapReport.assessment_id.in_(assessment_ids)),
        ("desk_review_findings", DeskReviewFinding, DeskReviewFinding.assessment_id.in_(assessment_ids)),
        ("desk_review_summaries", DeskReviewSummary, DeskReviewSummary.assessment_id.in_(assessment_ids)),
        ("questionnaire_responses", QuestionnaireResponse, QuestionnaireResponse.assessment_id.in_(assessment_ids)),
        ("rfi_documents", RFIDocument, RFIDocument.assessment_id.in_(assessment_ids)),
        ("assessment_packs", AssessmentPack, AssessmentPack.assessment_id.in_(assessment_ids)),
        ("report_snapshots", ReportSnapshot, or_(ReportSnapshot.assessment_id.in_(assessment_ids), ReportSnapshot.engagement_id == engagement_id)),
        ("evidence_versions", EvidenceVersion, EvidenceVersion.evidence_id.in_(evidence_ids)),
        ("evidence", Evidence, Evidence.engagement_id == engagement_id),
        ("assessment_documents", AssessmentDocument, AssessmentDocument.assessment_id.in_(assessment_ids)),
        ("magic_links", MagicLink, MagicLink.engagement_id == engagement_id),
        ("assessments", Assessment, Assessment.engagement_id == engagement_id),
        ("engagements", Engagement, (Engagement.id == engagement_id) & (Engagement.status == ARCHIVED_STATUS)),
    ]


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _root_paths(roots: tuple[str, ...]) -> tuple[Path, ...]:
    upload_root = Path(settings.upload_dir).resolve()
    return tuple(upload_root / root for root in roots)


def _safe_root_path(root: str) -> Path | None:
    upload_root = Path(settings.upload_dir).resolve()
    path = upload_root / root
    if path.is_symlink():
        return None
    try:
        resolved = path.resolve()
    except OSError:
        return None
    return resolved if _inside(resolved, upload_root) else None


def _valid_storage_path(value: str | None, roots: tuple[str, ...]) -> bool:
    if not value or "\\" in value:
        return False
    path = Path(value)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        return False
    return any(value.startswith(f"{root}/") for root in roots)


def _layout_violation_for_storage(
    value: str | None,
    roots: tuple[str, ...],
) -> bool:
    if not value:
        return False
    path = Path(settings.upload_dir) / value
    if not path.exists():
        return False
    try:
        resolved = path.resolve()
    except OSError:
        return True
    upload_root = Path(settings.upload_dir).resolve()
    return not _valid_storage_path(value, roots) or not _inside(resolved, upload_root)


def _count_blob_files(roots: tuple[str, ...]) -> int:
    count = 0
    for root in roots:
        safe_path = _safe_root_path(root)
        if safe_path is None or not safe_path.exists():
            continue
        count += sum(path.is_file() for path in safe_path.rglob("*"))
    return count


def build_purge_plan(db: Session, engagement: Engagement) -> PurgePlan:
    assessment_ids = tuple(
        sorted(
            db.scalars(
                select(Assessment.id).where(Assessment.engagement_id == engagement.id)
            ).all()
        )
    )
    evidence_ids = tuple(
        sorted(
            db.scalars(
                select(Evidence.id).where(Evidence.engagement_id == engagement.id)
            ).all()
        )
    )
    version_ids = tuple(
        sorted(
            db.scalars(
                select(EvidenceVersion.id).where(EvidenceVersion.evidence_id.in_(evidence_ids))
            ).all()
        )
    )
    db.scalars(select(Finding.id).where(Finding.assessment_id.in_(assessment_ids))).all()
    db.scalars(select(Conclusion.id).where(Conclusion.assessment_id.in_(assessment_ids))).all()
    db.scalars(select(GapReport.id).where(GapReport.assessment_id.in_(assessment_ids))).all()
    roots = _blob_roots(engagement.id, assessment_ids)
    layout_violations = sum(not SAFE_ID.fullmatch(value) for value in (engagement.id, *assessment_ids))
    layout_violations += sum(_safe_root_path(root) is None for root in roots)

    evidence_rows = db.scalars(
        select(Evidence).where(Evidence.engagement_id == engagement.id)
    ).all()
    version_rows = db.scalars(
        select(EvidenceVersion).where(EvidenceVersion.evidence_id.in_(evidence_ids))
    ).all()
    snapshot_rows = db.scalars(
        select(ReportSnapshot).where(
            or_(
                ReportSnapshot.assessment_id.in_(assessment_ids),
                ReportSnapshot.engagement_id == engagement.id,
            )
        )
    ).all()
    document_rows = db.scalars(
        select(AssessmentDocument).where(AssessmentDocument.assessment_id.in_(assessment_ids))
    ).all()
    for row in (*evidence_rows, *version_rows, *snapshot_rows):
        if _layout_violation_for_storage(row.storage_path, roots):
            layout_violations += 1
    resolved_roots = tuple(
        safe_path
        for root in roots
        if (safe_path := _safe_root_path(root)) is not None
    )
    for row in document_rows:
        path = Path(row.file_path)
        if not path.exists():
            continue
        try:
            resolved = path.resolve()
        except OSError:
            layout_violations += 1
            continue
        if not any(_inside(resolved, root) for root in resolved_roots):
            layout_violations += 1

    row_counts: dict[str, int] = {}
    plan_without_counts = PurgePlan(
        engagement_id=engagement.id,
        client_id=engagement.client_id,
        assessment_ids=assessment_ids,
        evidence_ids=evidence_ids,
        version_ids=version_ids,
        row_counts={},
        blob_roots=roots,
        blob_file_count=_count_blob_files(roots),
        layout_violations=layout_violations,
    )
    for table_name, model, clause in _purge_scopes(plan_without_counts):
        row_counts[table_name] = db.execute(
            select(func.count()).select_from(model).where(clause)
        ).scalar_one()
    return PurgePlan(
        engagement_id=plan_without_counts.engagement_id,
        client_id=plan_without_counts.client_id,
        assessment_ids=plan_without_counts.assessment_ids,
        evidence_ids=plan_without_counts.evidence_ids,
        version_ids=plan_without_counts.version_ids,
        row_counts=row_counts,
        blob_roots=plan_without_counts.blob_roots,
        blob_file_count=plan_without_counts.blob_file_count,
        layout_violations=plan_without_counts.layout_violations,
    )


def _dependency_count(db: Session, code: str, plan: PurgePlan) -> int:
    if code == "evidence_used_elsewhere":
        return db.execute(
            select(func.count()).select_from(EvidenceUse).where(
                EvidenceUse.evidence_id.in_(plan.evidence_ids),
                EvidenceUse.assessment_id.not_in(plan.assessment_ids),
            )
        ).scalar_one()
    if code == "evidence_cited_elsewhere":
        if not plan.version_ids:
            return 0
        patterns = [
            ConclusionRevision.citations_json.contains(version_id)
            for version_id in plan.version_ids
        ]
        conclusion_count = db.execute(
            select(func.count())
            .select_from(ConclusionRevision)
            .join(Conclusion, Conclusion.id == ConclusionRevision.conclusion_id)
            .where(
                Conclusion.assessment_id.not_in(plan.assessment_ids),
                ConclusionRevision.citations_json.is_not(None),
                or_(*patterns),
            )
        ).scalar_one()
        desk_count = db.execute(
            select(func.count()).select_from(DeskReviewFinding).where(
                DeskReviewFinding.assessment_id.not_in(plan.assessment_ids),
                DeskReviewFinding.citations_json.is_not(None),
                or_(*[
                    DeskReviewFinding.citations_json.contains(version_id)
                    for version_id in plan.version_ids
                ]),
            )
        ).scalar_one()
        action_count = db.execute(
            select(func.count())
            .select_from(Action)
            .join(Finding, Finding.id == Action.finding_id)
            .where(
                Finding.assessment_id.not_in(plan.assessment_ids),
                or_(*[
                    Action.history_json.contains(version_id)
                    for version_id in plan.version_ids
                ]),
            )
        ).scalar_one()
        return conclusion_count + desk_count + action_count
    if code == "evidence_linked_elsewhere":
        return db.execute(
            select(func.count()).select_from(Evidence).where(
                or_(
                    and_(
                        Evidence.assessment_id.in_(plan.assessment_ids),
                        Evidence.engagement_id != plan.engagement_id,
                    ),
                    and_(
                        Evidence.engagement_id == plan.engagement_id,
                        Evidence.assessment_id.is_not(None),
                        Evidence.assessment_id.not_in(plan.assessment_ids),
                    ),
                )
            )
        ).scalar_one()
    roots = plan.blob_roots
    prefixes = [f"{root}/" for root in roots]
    prefix_filter = lambda column: or_(*[
        func.substr(column, 1, len(prefix)) == prefix for prefix in prefixes
    ])
    if code == "blob_shared_elsewhere":
        evidence_count = db.execute(
            select(func.count()).select_from(Evidence).where(
                Evidence.id.not_in(plan.evidence_ids),
                prefix_filter(Evidence.storage_path),
            )
        ).scalar_one()
        version_count = db.execute(
            select(func.count()).select_from(EvidenceVersion).where(
                EvidenceVersion.evidence_id.not_in(plan.evidence_ids),
                prefix_filter(EvidenceVersion.storage_path),
            )
        ).scalar_one()
        snapshot_count = db.execute(
            select(func.count()).select_from(ReportSnapshot).where(
                ReportSnapshot.assessment_id.not_in(plan.assessment_ids),
                or_(
                    ReportSnapshot.engagement_id.is_(None),
                    ReportSnapshot.engagement_id != plan.engagement_id,
                ),
                prefix_filter(ReportSnapshot.storage_path),
            )
        ).scalar_one()
        document_rows = db.scalars(
            select(AssessmentDocument).where(
                AssessmentDocument.assessment_id.not_in(plan.assessment_ids)
            )
        ).all()
        root_paths = tuple(path.resolve() for path in _root_paths(roots))
        document_count = 0
        for row in document_rows:
            path = Path(row.file_path)
            if path.exists() and any(_inside(path.resolve(), root) for root in root_paths):
                document_count += 1
        return evidence_count + version_count + snapshot_count + document_count
    raise ValueError(code)


def _dependency_values(db: Session, plan: PurgePlan) -> tuple[Dependency, ...]:
    return tuple(
        Dependency(code, _dependency_count(db, code, plan)) for code in DEPENDENCY_CODES
    )


def evaluate_purge(
    db: Session,
    engagement: Engagement,
    plan: PurgePlan,
    *,
    now: datetime | None = None,
) -> Eligibility:
    state = retention_state(db, engagement, now=now)
    if not state.archived:
        return Eligibility(("not_archived",), (), 0, state)
    dependencies = _dependency_values(db, plan)
    reasons: list[str] = []
    if state.record is None:
        reasons.append("archive_record_missing")
    elif state.retention_years_applied is None:
        reasons.append("retention_invalid")
    elif not state.elapsed:
        reasons.append("retention_not_elapsed")
    if any(dependency.count for dependency in dependencies):
        reasons.append("active_dependencies")
    if plan.layout_violations:
        reasons.append("storage_layout_invalid")
    return Eligibility(tuple(reasons), dependencies, plan.layout_violations, state)


def refusal_message(eligibility: Eligibility) -> str:
    dependency_text = "; ".join(
        f"{DEPENDENCY_LABELS[dependency.code]} ({dependency.count})"
        for dependency in eligibility.dependencies
        if dependency.count
    )
    values = {
        "eligible_at": eligibility.state.eligible_at,
        "dependencies": dependency_text,
    }
    return " ".join(
        REASON_MESSAGES[reason].format(**values) for reason in eligibility.reasons
    )


def _write_purge_refused(
    db: Session,
    *,
    engagement_id: str,
    actor: str,
    eligibility: Eligibility,
) -> AuditEvent:
    state = eligibility.state
    dependencies = [
        {
            "code": code,
            "count": next(
                (dependency.count for dependency in eligibility.dependencies if dependency.code == code),
                0,
            ),
        }
        for code in DEPENDENCY_CODES
    ]
    return _audit(
        db,
        actor=actor,
        action=PURGE_REFUSED_EVENT,
        entity_type=ENGAGEMENT_ENTITY,
        entity_id=engagement_id,
        metadata={
            "schema_version": EVENT_SCHEMA_VERSION,
            "reasons": list(eligibility.reasons),
            "dependencies": dependencies,
            "layout_violations": eligibility.layout_violations,
            "archived_at": state.record.archived_at.isoformat() if state.record else None,
            "retention_years_applied": state.retention_years_applied,
            "eligible_at": state.eligible_at.isoformat() if state.eligible_at else None,
        },
    )


def _write_purged_event(
    db: Session,
    *,
    engagement_id: str,
    actor: str,
    engagement_name: str,
    plan: PurgePlan,
    state: RetentionState,
) -> AuditEvent:
    event = _audit(
        db,
        actor=actor,
        action=PURGED_EVENT,
        entity_type=ENGAGEMENT_ENTITY,
        entity_id=engagement_id,
        metadata={
            "schema_version": EVENT_SCHEMA_VERSION,
            "client_id": plan.client_id,
            "engagement_name": engagement_name,
            "archive_event_id": state.record.event_id if state.record else None,
            "archived_at": state.record.archived_at.isoformat() if state.record else None,
            "retention_years_applied": state.retention_years_applied,
            "eligible_at": state.eligible_at.isoformat() if state.eligible_at else None,
            "assessment_ids": list(plan.assessment_ids),
            "row_counts": dict(plan.row_counts),
            "blob_roots": list(plan.blob_roots),
            "blob_file_count": plan.blob_file_count,
        },
    )
    return event


def _remove_tree(path: Path) -> None:
    shutil.rmtree(path)


def _finish_blob_removal(
    db: Session,
    *,
    engagement_id: str,
    purge_event_id: str,
    roots: tuple[str, ...],
    actor: str,
) -> CompletionOutcome:
    removed_roots: list[str] = []
    missing_roots: list[str] = []
    upload_root = Path(settings.upload_dir).resolve()
    for root in roots:
        path = upload_root / root
        if path.is_symlink():
            raise BlobRootError(root)
        try:
            resolved = path.resolve()
        except OSError as exc:
            raise BlobRootError(root) from exc
        if not _inside(resolved, upload_root):
            raise BlobRootError(root)
        if not path.exists():
            missing_roots.append(root)
            continue
        try:
            _remove_tree(path)
        except Exception as exc:
            raise _BlobRemovalFailure(root, exc) from exc
        removed_roots.append(root)
    _audit(
        db,
        actor=actor,
        action=PURGE_BLOBS_REMOVED_EVENT,
        entity_type=ENGAGEMENT_ENTITY,
        entity_id=engagement_id,
        metadata={
            "schema_version": EVENT_SCHEMA_VERSION,
            "purge_event_id": purge_event_id,
            "removed_roots": removed_roots,
            "missing_roots": missing_roots,
        },
    )
    db.commit()
    return CompletionOutcome(False, tuple(removed_roots), tuple(missing_roots))


def purge_engagement(
    db: Session,
    *,
    engagement_id: str,
    confirm_name: str | None,
    actor: str,
    now: datetime | None = None,
) -> PurgeResult:
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        if _has_purged_event(db, engagement_id):
            raise RetentionNotFound(ALREADY_PURGED)
        raise RetentionNotFound(ENGAGEMENT_NOT_FOUND)
    if (confirm_name or "").strip() != engagement.name.strip():
        raise InvalidRetentionRequest(CONFIRM_MISMATCH)
    engagement_name = engagement.name
    client_id = engagement.client_id
    timestamp = _now(now)
    db.rollback()
    db.execute(text("PRAGMA secure_delete = ON"))
    locked = db.execute(
        update(Engagement)
        .where(Engagement.id == engagement_id, Engagement.status == ARCHIVED_STATUS)
        .values(updated_at=timestamp)
        .execution_options(synchronize_session=False)
    ).rowcount == 1
    db.expire_all()
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        db.rollback()
        raise RetentionNotFound(ALREADY_PURGED)
    if locked:
        plan = build_purge_plan(db, engagement)
        eligibility = evaluate_purge(db, engagement, plan, now=timestamp)
    else:
        state = retention_state(db, engagement, now=timestamp)
        plan = None
        eligibility = Eligibility(("not_archived",), (), 0, state)
    if eligibility.reasons:
        db.rollback()
        _write_purge_refused(
            db,
            engagement_id=engagement_id,
            actor=actor,
            eligibility=eligibility,
        )
        db.commit()
        raise PurgeRefused(eligibility)
    assert plan is not None
    try:
        for table_name, model, clause in _purge_scopes(plan):
            result = db.execute(
                delete(model)
                .where(clause)
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != plan.row_counts[table_name]:
                raise PurgeIntegrityError(table_name)
        purge_event = _write_purged_event(
            db,
            engagement_id=engagement_id,
            actor=actor,
            engagement_name=engagement_name,
            plan=plan,
            state=eligibility.state,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(
            "Purge of engagement %s failed before commit (%s); nothing was deleted",
            engagement_id,
            type(exc).__name__,
        )
        raise PurgeFailed(PURGE_FAILED) from exc
    try:
        outcome = _finish_blob_removal(
            db,
            engagement_id=engagement_id,
            purge_event_id=purge_event.id,
            roots=plan.blob_roots,
            actor=actor,
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            "Purge of engagement %s left stored files pending (%s)",
            engagement_id,
            type(exc).__name__,
        )
        return PurgeResult(
            engagement_id=engagement_id,
            client_id=client_id,
            purge_event_id=purge_event.id,
            row_counts=plan.row_counts,
            blob_roots=plan.blob_roots,
            blobs_removed=False,
            failed_root=getattr(exc, "root", None),
        )
    return PurgeResult(
        engagement_id=engagement_id,
        client_id=client_id,
        purge_event_id=purge_event.id,
        row_counts=plan.row_counts,
        blob_roots=plan.blob_roots,
        blobs_removed=True,
        failed_root=None,
    )


def _latest_purged_event(db: Session, engagement_id: str) -> AuditEvent | None:
    return next(iter(_engagement_events(db, engagement_id, (PURGED_EVENT,))), None)


def pending_purges(db: Session) -> list[PendingPurge]:
    events = list(
        db.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == ENGAGEMENT_ENTITY,
                AuditEvent.action == PURGED_EVENT,
            )
            .order_by(literal_column("audit_events.rowid"))
        ).all()
    )
    pending: list[PendingPurge] = []
    for event in events:
        complete = db.execute(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.entity_type == ENGAGEMENT_ENTITY,
                AuditEvent.entity_id == event.entity_id,
                AuditEvent.action == PURGE_BLOBS_REMOVED_EVENT,
            )
        ).scalar_one()
        if complete:
            continue
        metadata = _parse_metadata(event) or {}
        roots = metadata.get("blob_roots")
        roots = tuple(roots) if isinstance(roots, list) and all(isinstance(root, str) for root in roots) else ()
        pending.append(
            PendingPurge(
                engagement_id=event.entity_id,
                purge_event_id=event.id,
                purged_at=_as_utc(event.created_at),
                blob_roots=roots,
            )
        )
    return pending


def _ledger_roots(engagement_id: str, metadata: dict) -> tuple[str, ...] | None:
    assessment_ids = metadata.get("assessment_ids")
    roots = metadata.get("blob_roots")
    if not isinstance(assessment_ids, list) or not all(
        isinstance(value, str) and SAFE_ID.fullmatch(value) for value in assessment_ids
    ):
        return None
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        return None
    if len(set(roots)) != len(roots):
        return None
    if not SAFE_ID.fullmatch(engagement_id):
        return None
    expected = _blob_roots(engagement_id, tuple(sorted(assessment_ids)))
    if set(roots) != set(expected):
        return None
    return tuple(roots)


def complete_pending_purge(
    db: Session,
    *,
    engagement_id: str,
    actor: str,
) -> CompletionOutcome:
    event = _latest_purged_event(db, engagement_id)
    if event is None:
        raise RetentionNotFound(NO_PENDING_PURGE)
    if db.execute(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.entity_type == ENGAGEMENT_ENTITY,
            AuditEvent.entity_id == engagement_id,
            AuditEvent.action == PURGE_BLOBS_REMOVED_EVENT,
        )
    ).scalar_one():
        return CompletionOutcome(True, (), ())
    if db.get(Engagement, engagement_id) is not None:
        raise RetentionConflict(PURGE_LEDGER_INCONSISTENT)
    metadata = _parse_metadata(event)
    roots = _ledger_roots(engagement_id, metadata or {}) if metadata is not None else None
    if roots is None:
        raise RetentionConflict(PURGE_LEDGER_INVALID)
    try:
        return _finish_blob_removal(
            db,
            engagement_id=engagement_id,
            purge_event_id=event.id,
            roots=roots,
            actor=actor,
        )
    except Exception as exc:
        db.rollback()
        logger.error(
            "Completion of purge for engagement %s failed (%s)",
            engagement_id,
            type(exc).__name__,
        )
        raise PurgeFailed(PURGE_BLOBS_PENDING) from exc


def client_retention_view(db: Session, client: Client) -> ClientRetentionView:
    engagements = db.scalars(
        select(Engagement)
        .where(
            Engagement.client_id == client.id,
            Engagement.status == ARCHIVED_STATUS,
        )
        .order_by(Engagement.created_at, Engagement.id)
    ).all()
    archived = []
    for engagement in engagements:
        state = retention_state(db, engagement)
        archived.append(
            ArchivedEngagementRow(
                engagement_id=engagement.id,
                name=engagement.name,
                archived_at=state.record.archived_at if state.record else None,
                eligible_at=state.eligible_at,
                elapsed=state.elapsed,
            )
        )
    purges: list[PurgeRecordRow] = []
    events = db.scalars(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == ENGAGEMENT_ENTITY,
            AuditEvent.action == PURGED_EVENT,
        )
        .order_by(literal_column("audit_events.rowid").desc())
    ).all()
    for event in events:
        metadata = _parse_metadata(event)
        if metadata is None or metadata.get("client_id") != client.id:
            continue
        complete = db.execute(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.entity_type == ENGAGEMENT_ENTITY,
                AuditEvent.entity_id == event.entity_id,
                AuditEvent.action == PURGE_BLOBS_REMOVED_EVENT,
            )
        ).scalar_one()
        purges.append(
            PurgeRecordRow(
                engagement_id=event.entity_id,
                engagement_name=str(metadata.get("engagement_name", "")),
                purged_at=_as_utc(event.created_at),
                purged_by_display=event.actor.removeprefix(conclusion_review.REVIEWER_ACTOR_PREFIX),
                blobs_removed=bool(complete),
            )
        )
    return ClientRetentionView(archived=archived, purges=purges)
