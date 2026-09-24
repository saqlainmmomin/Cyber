"""Read-only remediation rollup (P3-4): Action counts and lists across an engagement's assessments, each row keeping its assessment, framework and requirement. Counts only; never a score. Never writes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.services import findings
from app.services.conclusion_review import RISK_LEVELS

ROLLUP_KEYS = (
    "open",
    "in_progress",
    "awaiting_verification",
    "verified",
    "overdue",
    "unassigned",
    "total",
)
ACTIVE_STATUSES = ("open", "in_progress")
UNASSIGNED_LABEL = "Unassigned"


@dataclass(frozen=True)
class TrackedAction:
    action_id: str
    title: str
    owner_display: str
    target_date: date | None
    status: str
    status_label: str
    overdue: bool
    finding_id: str
    finding_title: str
    severity: str
    assessment_id: str
    assessment_label: str
    framework_id: str | None
    requirement_id: str | None
    href: str


@dataclass(frozen=True)
class AssessmentRollup:
    assessment_id: str
    label: str
    findings_href: str
    counts: dict[str, int]


@dataclass(frozen=True)
class EngagementRollup:
    counts: dict[str, int]
    by_severity: list[dict]
    by_owner: list[dict]
    assessments: list[AssessmentRollup]
    overdue: list[TrackedAction]
    awaiting_verification: list[TrackedAction]


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in ROLLUP_KEYS}


def _date_today(today: date | None) -> date:
    return today or datetime.now(timezone.utc).date()


def _owner_display(owner: str | None) -> str:
    return owner.strip() if owner is not None else UNASSIGNED_LABEL


def _counts(actions: list[Action], *, today: date) -> dict[str, int]:
    counts = _empty_counts()
    for action in actions:
        if action.status in counts:
            counts[action.status] += 1
        elif action.status == "closed":
            counts["awaiting_verification"] += 1
        if (
            action.target_date is not None
            and action.target_date.date() < today
            and action.status in ACTIVE_STATUSES
        ):
            counts["overdue"] += 1
        if action.owner is None and action.status in ACTIVE_STATUSES:
            counts["unassigned"] += 1
        counts["total"] += 1
    return counts


def assessment_action_counts(
    db: Session, assessment_id: str, *, today: date | None = None
) -> dict[str, int]:
    finding_ids = db.execute(
        select(Finding.id).where(Finding.assessment_id == assessment_id)
    ).scalars().all()
    actions = (
        db.execute(select(Action).where(Action.finding_id.in_(finding_ids))).scalars().all()
        if finding_ids
        else []
    )
    return _counts(actions, today=_date_today(today))


def _tracked_action(
    action: Action,
    finding: Finding,
    assessment: Assessment,
    conclusion: Conclusion | None,
    *,
    today: date,
) -> TrackedAction:
    target_date = action.target_date.date() if action.target_date else None
    overdue = (
        target_date is not None
        and target_date < today
        and action.status in ACTIVE_STATUSES
    )
    return TrackedAction(
        action_id=action.id,
        title=action.title,
        owner_display=_owner_display(action.owner),
        target_date=target_date,
        status=action.status,
        status_label=findings.ACTION_STATUS_LABELS.get(action.status, action.status),
        overdue=overdue,
        finding_id=finding.id,
        finding_title=finding.title,
        severity=finding.severity,
        assessment_id=assessment.id,
        assessment_label=f"{assessment.description or assessment.company_name} ({assessment.created_at:%d %b %Y})",
        framework_id=conclusion.framework_id if conclusion else None,
        requirement_id=conclusion.requirement_id if conclusion else None,
        href=f"/assessments/{assessment.id}/findings#finding-{finding.id}",
    )


def engagement_rollup(
    db: Session, engagement: Engagement, *, today: date | None = None
) -> EngagementRollup:
    as_of = _date_today(today)
    assessments = db.execute(
        select(Assessment)
        .where(
            Assessment.engagement_id == engagement.id,
            Assessment.status != "archived",
        )
        .order_by(Assessment.created_at, Assessment.id)
    ).scalars().all()
    assessment_ids = [assessment.id for assessment in assessments]
    finding_rows = (
        db.execute(
            select(Finding).where(Finding.assessment_id.in_(assessment_ids))
        ).scalars().all()
        if assessment_ids
        else []
    )
    finding_ids = [finding.id for finding in finding_rows]
    action_rows = (
        db.execute(select(Action).where(Action.finding_id.in_(finding_ids))).scalars().all()
        if finding_ids
        else []
    )
    conclusion_ids = [finding.conclusion_id for finding in finding_rows]
    conclusion_rows = (
        db.execute(
            select(Conclusion).where(Conclusion.id.in_(conclusion_ids))
        ).scalars().all()
        if conclusion_ids
        else []
    )
    findings_by_id = {finding.id: finding for finding in finding_rows}
    assessments_by_id = {assessment.id: assessment for assessment in assessments}
    conclusions_by_id = {conclusion.id: conclusion for conclusion in conclusion_rows}
    actions_by_assessment: dict[str, list[Action]] = defaultdict(list)
    for action in action_rows:
        actions_by_assessment[findings_by_id[action.finding_id].assessment_id].append(action)
    tracked = [
        _tracked_action(
            action,
            findings_by_id[action.finding_id],
            assessments_by_id[findings_by_id[action.finding_id].assessment_id],
            conclusions_by_id.get(findings_by_id[action.finding_id].conclusion_id),
            today=as_of,
        )
        for action in action_rows
    ]
    counts = _empty_counts()
    for action in tracked:
        if action.status in counts:
            counts[action.status] += 1
        elif action.status == "closed":
            counts["awaiting_verification"] += 1
        if action.overdue:
            counts["overdue"] += 1
        if action.owner_display == UNASSIGNED_LABEL and action.status in ACTIVE_STATUSES:
            counts["unassigned"] += 1
        counts["total"] += 1

    severity_values = list(RISK_LEVELS)
    severity_values.extend(
        sorted(
            {
                action.severity
                for action in tracked
                if action.severity not in severity_values
            }
        )
    )
    by_severity = []
    for severity in severity_values:
        row = {
            "severity": severity,
            "open": 0,
            "in_progress": 0,
            "awaiting_verification": 0,
            "verified": 0,
            "total": 0,
        }
        for action in tracked:
            if action.severity != severity:
                continue
            if action.status in ("open", "in_progress", "verified"):
                row[action.status] += 1
            elif action.status == "closed":
                row["awaiting_verification"] += 1
            row["total"] += 1
        by_severity.append(row)

    owner_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"active": 0, "overdue": 0})
    for action in tracked:
        if action.status not in ACTIVE_STATUSES:
            continue
        owner_stats[action.owner_display]["active"] += 1
        if action.overdue:
            owner_stats[action.owner_display]["overdue"] += 1
    by_owner = [
        {"owner": owner, **values}
        for owner, values in sorted(
            owner_stats.items(),
            key=lambda item: (-item[1]["overdue"], -item[1]["active"], item[0]),
        )
    ]

    assessments_rollup = []
    for assessment in assessments:
        assessments_rollup.append(
            AssessmentRollup(
                assessment_id=assessment.id,
                label=f"{assessment.description or assessment.company_name} ({assessment.created_at:%d %b %Y})",
                findings_href=f"/assessments/{assessment.id}/findings",
                counts=_counts(actions_by_assessment[assessment.id], today=as_of),
            )
        )
    overdue = sorted(
        [action for action in tracked if action.overdue],
        key=lambda action: (action.target_date, action.action_id),
    )
    updated_by_id = {action.id: action.updated_at for action in action_rows}
    awaiting_verification = sorted(
        [action for action in tracked if action.status == "closed"],
        key=lambda action: (
            updated_by_id[action.action_id],
            action.action_id,
        ),
    )
    return EngagementRollup(
        counts=counts,
        by_severity=by_severity,
        by_owner=by_owner,
        assessments=assessments_rollup,
        overdue=overdue,
        awaiting_verification=awaiting_verification,
    )
