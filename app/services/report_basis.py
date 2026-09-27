"""Assessment period and report sign-off basis stored in the audit trail."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session, object_session
from sqlalchemy.orm.exc import UnmappedInstanceError

from app.models.audit_event import AuditEvent
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion

PERIOD_REQUIRED_MESSAGE = "Record the assessment period and evidence cut-off before approving conclusions."
PERIOD_LOCKED_MESSAGE = (
    "The assessment period and evidence cut-off are locked while any conclusion is "
    "approved. Reopen the approved conclusions to change them."
)
PERIOD_INCOMPLETE_MESSAGE = (
    "Enter the period start, period end and evidence cut-off together, or leave all three blank."
)
PERIOD_ORDER_MESSAGE = "The assessment period must end on or after its start date."
CUTOFF_ORDER_MESSAGE = "The evidence cut-off must be on or after the start of the assessment period."
DATE_FORMAT_MESSAGE = "Dates must be in YYYY-MM-DD format."
NOT_RECORDED = "not recorded"
SIGN_OFF_MAX_CHARS = 200
DISPLAY_DATE_FORMAT = "%d %b %Y"
AUDIT_ENTITY_TYPE = "assessment"
AUDIT_ACTION = "assessment.report_basis_updated"


class ReportBasisError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ReportBasis:
    period_start: date | None
    period_end: date | None
    evidence_cutoff: date | None
    prepared_by: str | None
    reviewed_by: str | None

    @property
    def period_recorded(self) -> bool:
        return all((self.period_start, self.period_end, self.evidence_cutoff))

    @property
    def period_label(self) -> str:
        if not self.period_recorded:
            return NOT_RECORDED
        return f"{self.period_start:{DISPLAY_DATE_FORMAT}} to {self.period_end:{DISPLAY_DATE_FORMAT}}"

    @property
    def cutoff_label(self) -> str:
        return (
            f"{self.evidence_cutoff:{DISPLAY_DATE_FORMAT}}"
            if self.evidence_cutoff is not None
            else NOT_RECORDED
        )

    def to_metadata(self) -> dict:
        return {
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "evidence_cutoff": self.evidence_cutoff.isoformat() if self.evidence_cutoff else None,
            "prepared_by": self.prepared_by,
            "reviewed_by": self.reviewed_by,
        }


EMPTY_BASIS = ReportBasis(None, None, None, None, None)


def parse_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except (TypeError, ValueError) as exc:
        raise ReportBasisError(DATE_FORMAT_MESSAGE) from exc


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip()[:SIGN_OFF_MAX_CHARS]
    return cleaned or None


def _basis_from_after(after: dict) -> ReportBasis:
    try:
        period_start = parse_date(after.get("period_start"))
        period_end = parse_date(after.get("period_end"))
        evidence_cutoff = parse_date(after.get("evidence_cutoff"))
    except ReportBasisError:
        return EMPTY_BASIS
    return ReportBasis(
        period_start=period_start,
        period_end=period_end,
        evidence_cutoff=evidence_cutoff,
        prepared_by=after.get("prepared_by") if isinstance(after.get("prepared_by"), str) else None,
        reviewed_by=after.get("reviewed_by") if isinstance(after.get("reviewed_by"), str) else None,
    )


def current_basis(db: Session | None, assessment) -> ReportBasis:
    if db is None or assessment is None or not getattr(assessment, "id", None):
        return EMPTY_BASIS
    event = db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.action == AUDIT_ACTION,
            AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
            AuditEvent.entity_id == assessment.id,
        )
        .order_by(
            AuditEvent.created_at.desc(),
            literal_column("audit_events.rowid").desc(),
        )
        .limit(1)
    ).scalar_one_or_none()
    if event is None or not event.metadata_json:
        return EMPTY_BASIS
    try:
        metadata = json.loads(event.metadata_json)
    except (TypeError, json.JSONDecodeError):
        return EMPTY_BASIS
    after = metadata.get("after") if isinstance(metadata, dict) else None
    return _basis_from_after(after) if isinstance(after, dict) else EMPTY_BASIS


def basis_for(assessment) -> ReportBasis:
    if assessment is None:
        return EMPTY_BASIS
    try:
        return current_basis(object_session(assessment), assessment)
    except UnmappedInstanceError:
        return EMPTY_BASIS


def period_locked(db: Session, assessment) -> bool:
    if db is None or assessment is None or not getattr(assessment, "id", None):
        return False
    from app.services import analysis_pipeline

    framework_ids = db.execute(
        select(Conclusion.framework_id)
        .where(Conclusion.assessment_id == assessment.id)
        .distinct()
    ).scalars()
    for framework_id in framework_ids:
        states = analysis_pipeline.load_conclusion_state(
            db,
            assessment_id=assessment.id,
            framework_id=framework_id,
        )
        if any(state.locked for state in states.values()):
            return True
    return False


def approval_blocker(db: Session, assessment) -> str | None:
    return None if current_basis(db, assessment).period_recorded else PERIOD_REQUIRED_MESSAGE


def update_report_basis(
    db: Session,
    assessment: Assessment,
    *,
    period_start: str | date | None,
    period_end: str | date | None,
    evidence_cutoff: str | date | None,
    prepared_by: str | None,
    reviewed_by: str | None,
    actor: str,
) -> ReportBasis:
    start = parse_date(period_start)
    end = parse_date(period_end)
    cutoff = parse_date(evidence_cutoff)
    dates = (start, end, cutoff)
    if any(dates) and not all(dates):
        raise ReportBasisError(PERIOD_INCOMPLETE_MESSAGE)
    if start is not None and end < start:
        raise ReportBasisError(PERIOD_ORDER_MESSAGE)
    if start is not None and cutoff < start:
        raise ReportBasisError(CUTOFF_ORDER_MESSAGE)

    after = ReportBasis(
        period_start=start,
        period_end=end,
        evidence_cutoff=cutoff,
        prepared_by=_clean_name(prepared_by),
        reviewed_by=_clean_name(reviewed_by),
    )
    before = current_basis(db, assessment)
    if after == before:
        return after
    if (
        (after.period_start, after.period_end, after.evidence_cutoff)
        != (before.period_start, before.period_end, before.evidence_cutoff)
        and period_locked(db, assessment)
    ):
        raise ReportBasisError(PERIOD_LOCKED_MESSAGE)

    db.add(
        AuditEvent(
            actor=actor,
            action=AUDIT_ACTION,
            entity_type=AUDIT_ENTITY_TYPE,
            entity_id=assessment.id,
            metadata_json=json.dumps(
                {"before": before.to_metadata(), "after": after.to_metadata()},
                sort_keys=True,
            ),
        )
    )
    db.flush()
    return after
