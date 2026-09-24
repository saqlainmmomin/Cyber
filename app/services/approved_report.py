"""Read-only client report view built from consultant-approved Conclusions.

The legacy analysis rows remain history.  This
module is the single reader that turns Conclusions into release-facing rows,
scores, coverage and release state.  It is read-only and performs no persistence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.report import GapReport
from app.services import analysis_pipeline, conclusion_review
from app.services.scoring import (
    approved_framework_scores,
    failed_framework_scores,
    is_failed_framework_score,
    namespaced_domain_scores,
    report_framework_scores,
)

RELEASE_EVENT = "assessment.released"
RELEASE_SCHEMA_VERSION = 1
FRAMEWORK_VIEW_STATUSES = (
    "scored",
    "not_scored",
    "pending_review",
    "unavailable",
    "failed",
)
PRIORITY_BY_RISK = {"critical": 1, "high": 2, "medium": 3, "low": 4}

NO_ANALYSIS_MESSAGE = "Run analysis before releasing this report."
ANALYSIS_RUNNING_MESSAGE = (
    "Analysis is running. Wait for it to finish before releasing this report."
)
RELEASE_BLOCKED_MESSAGE = (
    "Analysis failed for {names}. Run analysis again before releasing this report."
)
MISSING_CONCLUSIONS_MESSAGE = (
    "{name}: no conclusion was proposed for {count} in-scope requirement(s). "
    "Run analysis again."
)
AWAITING_DECISION_MESSAGE = (
    "{name}: {count} of {total} in-scope conclusions still need an individual "
    "consultant decision."
)
NOTHING_IN_SCOPE_MESSAGE = (
    "No requirement is in scope for this assessment. Record the scope before releasing."
)
ALREADY_RELEASED_MESSAGE = (
    "This report is already released for the current approved conclusions."
)
NOT_RELEASED_MESSAGE = (
    "Report not yet approved for release. Complete the review process first."
)
LEGACY_REVIEW_RETIRED = (
    "Assessment-level review has been retired. Approve each conclusion individually "
    "on the Conclusions page, then release the report."
)


def in_scope_requirement_ids(raw: str | None) -> frozenset[str] | None:
    """Apply the same scope semantics as ``workpaper._scope``."""
    try:
        values = json.loads(raw) if raw else None
    except (json.JSONDecodeError, TypeError):
        return None
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(value, str) for value in values)
    ):
        return None
    return frozenset(values)


@dataclass(frozen=True)
class ApprovedRow:
    id: str
    conclusion_id: str
    conclusion_version: int
    framework_id: str
    requirement_id: str
    requirement_title: str
    chapter: str
    chapter_title: str
    control_reference: str | None
    compliance_status: str
    current_state: str
    gap_description: str
    risk_level: str
    remediation_action: str
    remediation_priority: int
    evidence_quote: str | None
    decision: str
    decided_by: str
    decided_at: datetime
    remediation_effort: str | None
    timeline_weeks: int | None
    maturity_level: int | None
    root_cause_category: str | None
    evidence_confidence: str | None


@dataclass(frozen=True)
class FrameworkReview:
    framework_id: str
    name: str
    in_scope_ids: tuple[str, ...]
    out_of_scope_ids: tuple[str, ...]
    missing_ids: tuple[str, ...]
    awaiting_ids: tuple[str, ...]
    rows: tuple[ApprovedRow, ...]
    coverage: dict[str, int]
    status: str
    score: dict


@dataclass(frozen=True)
class ReleaseState:
    blockers: tuple[str, ...]
    releasable: bool
    released: bool
    stale: bool
    release_event_id: str | None
    released_by: str | None
    released_at: datetime | None


@dataclass(frozen=True)
class RenderReport:
    id: str
    assessment_id: str
    chapter_scores: str
    framework_scores: str
    executive_summary: str
    generated_at: datetime


@dataclass(frozen=True)
class ApprovedReport:
    assessment_id: str
    report_id: str | None
    generated_at: datetime | None
    rows: tuple[ApprovedRow, ...]
    framework_reviews: dict[str, FrameworkReview]
    framework_scores: dict[str, dict]
    chapter_scores: dict[str, dict]
    summary_text: str
    release: ReleaseState

    def render_report(self) -> RenderReport:
        if self.report_id is None or self.generated_at is None:
            raise ValueError("An approved report requires a generated GapReport")
        return RenderReport(
            id=self.report_id,
            assessment_id=self.assessment_id,
            chapter_scores=json.dumps(self.chapter_scores, sort_keys=True),
            framework_scores=json.dumps(self.framework_scores, sort_keys=True),
            executive_summary=self.summary_text,
            generated_at=self.generated_at,
        )


class ReleaseRefused(Exception):
    status_code = 409

    def __init__(self, message: str, blockers: tuple[str, ...] = ()):
        self.message = message
        self.blockers = blockers
        super().__init__(message)


def _framework_name(framework_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    return framework.name if framework else framework_id.upper()


def _latest_release_event_query(db: Session, assessment_id: str) -> AuditEvent | None:
    return db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.action == RELEASE_EVENT,
            AuditEvent.entity_type == "assessment",
            AuditEvent.entity_id == assessment_id,
        )
        .order_by(
            AuditEvent.created_at.desc(),
            literal_column("audit_events.rowid").desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def latest_release_event(db: Session, assessment_id: str) -> AuditEvent | None:
    return _latest_release_event_query(db, assessment_id)


def _event_metadata(event: AuditEvent | None) -> dict:
    if event is None or not event.metadata_json:
        return {}
    try:
        value = json.loads(event.metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_decisions(
    db: Session,
    conclusions: list[Conclusion],
) -> dict[str, ConclusionRevision | None]:
    if not conclusions:
        return {}
    revisions = db.execute(
        select(ConclusionRevision)
        .where(
            ConclusionRevision.conclusion_id.in_(
                [conclusion.id for conclusion in conclusions]
            ),
            ConclusionRevision.action.in_(analysis_pipeline.HUMAN_DECISION_ACTIONS),
        )
        .order_by(
            ConclusionRevision.created_at,
            literal_column("conclusion_revisions.rowid"),
        )
    ).scalars().all()
    decisions: dict[str, ConclusionRevision | None] = {
        conclusion.id: None for conclusion in conclusions
    }
    for revision in revisions:
        decisions[revision.conclusion_id] = revision
    return decisions


def _ordered_controls(framework_id: str):
    framework = FrameworkRegistry.get(framework_id)
    controls = []
    for domain_key, domain in framework.domains.items():
        for section in domain.sections.values():
            for control in section.controls:
                controls.append((control, domain_key, domain.title))
    return controls


def _eligible(decision: ConclusionRevision | None) -> bool:
    return bool(
        decision
        and decision.action in analysis_pipeline.LOCKING_ACTIONS
        and decision.actor.startswith(conclusion_review.REVIEWER_ACTOR_PREFIX)
    )


def _row(
    conclusion: Conclusion,
    decision: ConclusionRevision,
    *,
    domain_key: str,
    domain_title: str,
    control,
    framework_name: str,
) -> ApprovedRow:
    risk_level = conclusion.risk_level or "medium"
    return ApprovedRow(
        id=conclusion.id,
        conclusion_id=conclusion.id,
        conclusion_version=conclusion.version,
        framework_id=conclusion.framework_id,
        requirement_id=conclusion.requirement_id,
        requirement_title=control.title if control else conclusion.requirement_id,
        chapter=f"{conclusion.framework_id}:{domain_key}",
        chapter_title=f"{framework_name} — {domain_title}",
        control_reference=getattr(control, "reference", None),
        compliance_status=conclusion.outcome,
        current_state=conclusion.rationale or "",
        gap_description=conclusion.gaps_identified or "",
        risk_level=risk_level,
        remediation_action=conclusion.recommended_action or "",
        remediation_priority=PRIORITY_BY_RISK.get(risk_level, 3),
        evidence_quote=conclusion.evidence_summary or None,
        decision=decision.action,
        decided_by=decision.actor.removeprefix(conclusion_review.REVIEWER_ACTOR_PREFIX),
        decided_at=decision.created_at,
        remediation_effort=None,
        timeline_weeks=None,
        maturity_level=None,
        root_cause_category=None,
        evidence_confidence=None,
    )


def _coverage(
    in_scope_ids: tuple[str, ...],
    out_of_scope_ids: list[str],
    rows: list[ApprovedRow],
    missing_ids: list[str],
    awaiting_ids: list[str],
) -> dict[str, int]:
    counts = {
        "in_scope": len(in_scope_ids),
        "out_of_scope": len(out_of_scope_ids),
        "eligible": len(rows),
        "missing": len(missing_ids),
        "awaiting": len(awaiting_ids),
        "scored": 0,
        "compliant": 0,
        "partially_compliant": 0,
        "non_compliant": 0,
        "not_applicable": 0,
        "insufficient_evidence": 0,
    }
    for row in rows:
        counts[row.compliance_status] = counts.get(row.compliance_status, 0) + 1
    counts["scored"] = sum(
        counts[outcome]
        for outcome in ("compliant", "partially_compliant", "non_compliant")
    )
    return counts


def _summary_text(
    assessment: Assessment,
    framework_reviews: dict[str, FrameworkReview],
) -> str:
    lines = ["This summary is generated from consultant-approved conclusions only."]
    for framework_id in assessment.frameworks:
        review = framework_reviews[framework_id]
        name = review.name
        coverage = review.coverage
        if review.status == "scored":
            lines.append(
                f"{name}: {review.score['overall_score']:.0f}% "
                f"({review.score['overall_rating']}), {coverage['scored']} of "
                f"{coverage['in_scope']} in-scope requirements scored; "
                f"{coverage['compliant']} compliant, "
                f"{coverage['partially_compliant']} partially compliant, "
                f"{coverage['non_compliant']} non-compliant, "
                f"{coverage['insufficient_evidence']} insufficient evidence, "
                f"{coverage['not_applicable']} not applicable."
            )
        elif review.status == "not_scored":
            lines.append(
                f"{name}: not scored; no in-scope requirement has a scoring "
                f"outcome ({coverage['insufficient_evidence']} insufficient evidence, "
                f"{coverage['not_applicable']} not applicable)."
            )
        elif review.status == "pending_review":
            lines.append(
                f"{name}: review in progress; {coverage['eligible']} of "
                f"{coverage['in_scope']} in-scope conclusions approved."
            )
        elif review.status == "unavailable":
            lines.append(f"{name}: no conclusions recorded. Run analysis.")
        else:
            lines.append(f"{name}: analysis failed. Not scored.")
    return "\n".join(lines)


def _manifest(
    assessment: Assessment,
    in_scope_by_framework: dict[str, tuple[str, ...]],
    rows: tuple[ApprovedRow, ...],
) -> dict:
    return {
        "framework_ids": list(assessment.frameworks),
        "in_scope": {
            framework_id: list(in_scope_by_framework[framework_id])
            for framework_id in assessment.frameworks
        },
        "conclusion_versions": [
            [row.conclusion_id, row.conclusion_version]
            for row in sorted(rows, key=lambda item: item.conclusion_id)
        ],
    }


def _release_state(
    db: Session,
    assessment: Assessment,
    *,
    blockers: tuple[str, ...],
    report_id: str | None,
    in_scope_by_framework: dict[str, tuple[str, ...]],
    rows: tuple[ApprovedRow, ...],
    framework_scores: dict[str, dict],
) -> ReleaseState:
    event = _latest_release_event_query(db, assessment.id)
    metadata = _event_metadata(event)
    current_manifest = _manifest(assessment, in_scope_by_framework, rows)
    released = bool(
        not blockers
        and event is not None
        and metadata.get("manifest") == current_manifest
    )
    released_by = (
        event.actor.removeprefix(conclusion_review.REVIEWER_ACTOR_PREFIX)
        if event
        else None
    )
    return ReleaseState(
        blockers=blockers,
        releasable=not blockers,
        released=released,
        stale=bool(event and not released),
        release_event_id=event.id if event else None,
        released_by=released_by,
        released_at=event.created_at if event else None,
    )


def build_approved_report(db: Session, assessment: Assessment) -> ApprovedReport:
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment.id)
        .first()
    )
    conclusions = db.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment.id)
    ).scalars().all()
    decisions = _load_decisions(db, conclusions)
    by_key = {(row.framework_id, row.requirement_id): row for row in conclusions}
    scope = in_scope_requirement_ids(assessment.applicable_requirements)

    rows: list[ApprovedRow] = []
    reviews: dict[str, FrameworkReview] = {}
    in_scope_by_framework: dict[str, tuple[str, ...]] = {}
    failed_frameworks: list[str] = []
    for framework_id in assessment.frameworks:
        framework = FrameworkRegistry.get(framework_id)
        framework_name = framework.name
        controls = _ordered_controls(framework_id)
        in_scope_controls = [
            (control, domain_key, domain_title)
            for control, domain_key, domain_title in controls
            if scope is None or control.id in scope
        ]
        in_scope_ids = tuple(control.id for control, _, _ in in_scope_controls)
        in_scope_by_framework[framework_id] = in_scope_ids

        framework_conclusions = [
            conclusion
            for conclusion in conclusions
            if conclusion.framework_id == framework_id
        ]
        in_scope_set = set(in_scope_ids)
        out_of_scope_ids = [
            conclusion.requirement_id
            for conclusion in framework_conclusions
            if conclusion.requirement_id not in in_scope_set
        ]
        missing_ids = [
            requirement_id
            for requirement_id in in_scope_ids
            if (framework_id, requirement_id) not in by_key
        ]
        awaiting_ids = [
            requirement_id
            for requirement_id in in_scope_ids
            if (framework_id, requirement_id) in by_key
            and not _eligible(decisions[(by_key[(framework_id, requirement_id)]).id])
        ]

        framework_rows: list[ApprovedRow] = []
        outcomes: dict[str, str] = {}
        for control, domain_key, domain_title in in_scope_controls:
            conclusion = by_key.get((framework_id, control.id))
            if conclusion is None:
                continue
            decision = decisions[conclusion.id]
            if not _eligible(decision):
                continue
            approved_row = _row(
                conclusion,
                decision,
                domain_key=domain_key,
                domain_title=domain_title,
                control=control,
                framework_name=framework_name,
            )
            framework_rows.append(approved_row)
            outcomes[control.id] = conclusion.outcome

        coverage = _coverage(
            in_scope_ids,
            out_of_scope_ids,
            framework_rows,
            missing_ids,
            awaiting_ids,
        )
        stored_scores = report_framework_scores(report, assessment) if report else {}
        stored_entry = stored_scores.get(framework_id)
        if is_failed_framework_score(stored_entry):
            status = "failed"
            score = failed_framework_scores()
            failed_frameworks.append(framework_id)
        elif not framework_conclusions and in_scope_ids:
            status = "unavailable"
            score = {
                "status": status,
                "overall_score": None,
                "overall_rating": None,
                "domain_scores": {},
            }
        elif missing_ids or awaiting_ids:
            status = "pending_review"
            score = {
                "status": status,
                "overall_score": None,
                "overall_rating": None,
                "domain_scores": {},
            }
        else:
            score = approved_framework_scores(outcomes, framework_id)
            status = score["status"]
        if status in ("scored", "not_scored", "pending_review", "unavailable"):
            score = {**score, "coverage": coverage}
        review = FrameworkReview(
            framework_id=framework_id,
            name=framework_name,
            in_scope_ids=in_scope_ids,
            out_of_scope_ids=tuple(out_of_scope_ids),
            missing_ids=tuple(missing_ids),
            awaiting_ids=tuple(awaiting_ids),
            rows=tuple(framework_rows),
            coverage=coverage,
            status=status,
            score=score,
        )
        reviews[framework_id] = review
        rows.extend(framework_rows)

    framework_scores = {
        framework_id: reviews[framework_id].score
        for framework_id in assessment.frameworks
    }
    chapter_scores = namespaced_domain_scores(
        {
            framework_id: score
            for framework_id, score in framework_scores.items()
            if score.get("status") == "scored"
        }
    )
    blockers: list[str] = []
    if report is None:
        blockers.append(NO_ANALYSIS_MESSAGE)
    else:
        if assessment.status == "analyzing":
            blockers.append(ANALYSIS_RUNNING_MESSAGE)
        if failed_frameworks:
            names = ", ".join(reviews[framework_id].name for framework_id in failed_frameworks)
            blockers.append(RELEASE_BLOCKED_MESSAGE.format(names=names))
        for framework_id in assessment.frameworks:
            review = reviews[framework_id]
            if review.status == "failed":
                continue
            if review.missing_ids:
                blockers.append(
                    MISSING_CONCLUSIONS_MESSAGE.format(
                        name=review.name,
                        count=len(review.missing_ids),
                    )
                )
            if review.awaiting_ids:
                blockers.append(
                    AWAITING_DECISION_MESSAGE.format(
                        name=review.name,
                        count=len(review.awaiting_ids),
                        total=len(review.in_scope_ids),
                    )
                )
        if sum(len(review.in_scope_ids) for review in reviews.values()) == 0:
            blockers.append(NOTHING_IN_SCOPE_MESSAGE)

    release = _release_state(
        db,
        assessment,
        blockers=tuple(blockers),
        report_id=report.id if report else None,
        in_scope_by_framework=in_scope_by_framework,
        rows=tuple(rows),
        framework_scores=framework_scores,
    )
    return ApprovedReport(
        assessment_id=assessment.id,
        report_id=report.id if report else None,
        generated_at=report.generated_at if report else None,
        rows=tuple(rows),
        framework_reviews=reviews,
        framework_scores=framework_scores,
        chapter_scores=chapter_scores,
        summary_text=_summary_text(assessment, reviews),
        release=release,
    )


def release_state(db: Session, assessment: Assessment) -> ReleaseState:
    return build_approved_report(db, assessment).release


def is_released(db: Session, assessment: Assessment) -> bool:
    return release_state(db, assessment).released


def record_release(db: Session, assessment: Assessment, *, actor: str) -> AuditEvent:
    approved = build_approved_report(db, assessment)
    if approved.release.blockers:
        raise ReleaseRefused(
            " ".join(approved.release.blockers),
            approved.release.blockers,
        )
    if approved.release.released:
        raise ReleaseRefused(ALREADY_RELEASED_MESSAGE)

    in_scope_by_framework = {
        framework_id: approved.framework_reviews[framework_id].in_scope_ids
        for framework_id in assessment.frameworks
    }
    manifest = _manifest(assessment, in_scope_by_framework, approved.rows)
    coverage = {
        framework_id: approved.framework_scores[framework_id]["coverage"]
        for framework_id in assessment.frameworks
        if approved.framework_scores[framework_id]["status"] in ("scored", "not_scored")
    }
    metadata = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "manifest": manifest,
        "gap_report_id": approved.report_id,
        "coverage": coverage,
    }
    event = AuditEvent(
        actor=actor,
        action=RELEASE_EVENT,
        entity_type="assessment",
        entity_id=assessment.id,
        metadata_json=json.dumps(metadata, sort_keys=True),
    )
    db.add(event)
    assessment.review_status = "approved"
    db.flush()
    return event
