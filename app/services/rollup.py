"""One read-only stage and release status for assessment and portfolio screens."""

from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, object_session

from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.report_snapshot import ReportSnapshot
from app.services import approved_report, assessment_stage, vocabulary
from app.services.report_snapshots import AUDIT_ENTITY_TYPE, ISSUED_ACTION


@dataclass(frozen=True)
class AssessmentStatus:
    stage: str
    stage_label: str
    note: str
    release_state: str
    release_label: str
    next_label: str | None
    next_href: str | None

    @property
    def label(self) -> str:
        return self.stage_label


@dataclass(frozen=True)
class EngagementRollup:
    stage: str | None
    stage_label: str
    summary: str
    counts_by_stage: dict[str, int]
    counts_by_release: dict[str, int]
    earliest_note: str


def assessment_status(db: Session, assessment: Assessment) -> AssessmentStatus:
    current = assessment_stage.stage(db, assessment)
    event = approved_report.latest_release_event(db, assessment.id)
    release = approved_report.release_state(db, assessment) if event else None
    issued = db.execute(
        select(ReportSnapshot.id).where(
            ReportSnapshot.assessment_id == assessment.id,
            ReportSnapshot.is_issued.is_(True),
        ).limit(1)
    ).first() is not None
    state = "issued" if issued else "released" if event else "draft"
    label = (
        "Released version is out of date"
        if release and release.stale
        else vocabulary.release_label(state)
    )
    return AssessmentStatus(
        current.stage, current.label, current.note, state, label,
        current.next_label, current.next_href,
    )


def status_for_assessment(assessment: Assessment) -> AssessmentStatus | None:
    """Template adapter using the row's existing request session."""
    if not isinstance(assessment, Assessment):
        # Static design previews use a namespace rather than a stored row.
        return None
    return assessment_status(object_session(assessment), assessment)


def engagement_rollup(db: Session, engagement, assessments) -> EngagementRollup:
    statuses = [
        assessment_status(db, assessment)
        for assessment in assessments if assessment.status != "archived"
    ]
    stages = dict.fromkeys(assessment_stage.STAGES, 0)
    releases = dict.fromkeys(vocabulary.RELEASE_STATES, 0)
    for status in statuses:
        stages[status.stage] += 1
        releases[status.release_state] += 1
    if not statuses:
        return EngagementRollup(None, "No assessments", "No assessments", stages, releases, "")
    earliest = min(statuses, key=lambda status: assessment_stage.STAGES.index(status.stage))
    if len(statuses) == 1:
        only = statuses[0]
        summary = only.stage_label if only.release_state == "draft" else only.release_label
    else:
        counts = Counter(
            f"in {status.stage_label.lower()}"
            if status.release_state == "draft" else status.release_label.lower()
            for status in statuses
        )
        labels = [f"in {assessment_stage.STAGE_LABELS[stage].lower()}" for stage in assessment_stage.STAGES]
        labels += [vocabulary.release_label(state).lower() for state in ("released", "issued")]
        labels += ["released version is out of date"]
        summary = f"{len(statuses)} assessments: " + ", ".join(
            f"{counts[label]} {label}" for label in labels if counts[label]
        )
    return EngagementRollup(earliest.stage, earliest.stage_label, summary, stages, releases, earliest.note)


def assessment_label(assessment: Assessment, siblings=()) -> str:
    label = assessment.display_name
    if assessment.name or not siblings:
        return label
    matching = sorted(
        (row for row in siblings if not row.name and row.display_name == label),
        key=lambda row: (row.created_at, row.id),
    )
    for index, row in enumerate(matching, start=1):
        if row.id == assessment.id:
            return label if index == 1 else f"{label} ({index})"
    return label


def integrated_report_label(db: Session, engagement) -> str:
    snapshot = db.execute(
        select(ReportSnapshot).where(
            ReportSnapshot.engagement_id == engagement.id,
            ReportSnapshot.assessment_id.is_(None),
            ReportSnapshot.type == "integrated_report",
            ReportSnapshot.is_issued.is_(True),
        ).order_by(ReportSnapshot.generated_at.desc(), ReportSnapshot.id).limit(1)
    ).scalars().first()
    if snapshot is None:
        return "Integrated report: Not yet issued"
    issued_at = db.execute(
        select(AuditEvent.created_at).where(
            AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
            AuditEvent.entity_id == snapshot.id,
            AuditEvent.action == ISSUED_ACTION,
        ).order_by(AuditEvent.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    moment = issued_at or snapshot.generated_at
    return f"Integrated report: Issued {moment.day} {moment:%b %Y}"
