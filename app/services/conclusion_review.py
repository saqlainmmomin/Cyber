"""Individual consultant decisions for immutable Conclusions."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.report import GapItem, GapReport
from app.services import analysis_pipeline
from app.services.analysis_pipeline import ConclusionConflict
from app.services.citations import loads_citations, resolve_citations

REVIEWER_ACTOR_PREFIX = "consultant:"
DEFAULT_REVIEWER_NAME = "Manager Review"
CONCLUSION_OUTCOMES = (
    "compliant",
    "partially_compliant",
    "non_compliant",
    "not_applicable",
    "insufficient_evidence",
)
GAP_OUTCOMES = (
    "partially_compliant",
    "non_compliant",
    "insufficient_evidence",
)
RISK_LEVELS = ("critical", "high", "medium", "low")
EDITABLE_FIELDS = (
    "outcome",
    "rationale",
    "gaps_identified",
    "risk_level",
    "recommended_action",
)
ACTION_BY_ROUTE = {
    "approve": "approved",
    "edit": "edited",
    "reject": "rejected",
    "reopen": "reopened",
}
ALLOWED_ACTIONS = {
    "pending": ("approved", "edited", "rejected"),
    "rejected": ("approved", "edited"),
    "approved": ("reopened",),
    "edited": ("reopened",),
}

EVIDENCE_NOT_CAPTURED = (
    "Evidence support was not captured for this conclusion (migrated legacy data). "
    "Re-run analysis before approving."
)
INCOMPLETE_CONCLUSION = (
    "A conclusion needs an outcome, a rationale and a risk level before it can be "
    "approved."
)
INCOMPLETE_GAPS = (
    "A conclusion with gaps needs the identified gaps and a recommended action before "
    "it can be approved."
)


class ConclusionReviewError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ConclusionNotFound(ConclusionReviewError):
    status_code = 404


class InvalidDecision(ConclusionReviewError):
    status_code = 400


@dataclass(frozen=True)
class ConclusionCard:
    conclusion: Conclusion
    requirement_title: str
    state: str
    locked: bool
    allowed_actions: tuple[str, ...]
    approval_blocker: str | None
    citations_captured: bool
    citations: list[dict]
    unsupported_assertion: bool
    last_decision: dict | None
    legacy_bulk_approval: bool
    withheld_proposal: dict | None
    legacy_report_status: str | None
    previous_outcome: str | None = None


def reviewer_actor(reviewer_name: str | None) -> str:
    name = (reviewer_name or "").strip()[:200] or DEFAULT_REVIEWER_NAME
    return f"{REVIEWER_ACTOR_PREFIX}{name}"


def _revisions(db: Session, conclusion_ids: list[str]) -> list[ConclusionRevision]:
    if not conclusion_ids:
        return []
    return db.execute(
        select(ConclusionRevision)
        .where(ConclusionRevision.conclusion_id.in_(conclusion_ids))
        .order_by(
            ConclusionRevision.created_at,
            literal_column("conclusion_revisions.rowid"),
        )
    ).scalars().all()


def _decision_state(
    revisions: list[ConclusionRevision],
    *,
    locked: bool,
) -> tuple[str, ConclusionRevision | None]:
    latest_human = next(
        (
            revision
            for revision in reversed(revisions)
            if revision.action in analysis_pipeline.HUMAN_DECISION_ACTIONS
        ),
        None,
    )
    if locked and latest_human and latest_human.action in analysis_pipeline.LOCKING_ACTIONS:
        return latest_human.action, latest_human
    if latest_human and latest_human.action == "rejected":
        rejected_index = revisions.index(latest_human)
        newer_proposal = any(
            revision.action == "proposed"
            for revision in revisions[rejected_index + 1 :]
        )
        if not newer_proposal:
            return "rejected", latest_human
    return "pending", latest_human


def _latest_proposal(
    revisions: list[ConclusionRevision],
) -> ConclusionRevision | None:
    return next(
        (revision for revision in reversed(revisions) if revision.action == "proposed"),
        None,
    )


def _approval_blocker(
    content: dict[str, str],
    latest_proposal: ConclusionRevision | None,
) -> str | None:
    if latest_proposal is None or latest_proposal.citations_json is None:
        return EVIDENCE_NOT_CAPTURED
    if (
        content.get("outcome") not in CONCLUSION_OUTCOMES
        or not content.get("rationale", "").strip()
        or not content.get("risk_level", "").strip()
    ):
        return INCOMPLETE_CONCLUSION
    if content["outcome"] in GAP_OUTCOMES and (
        not content.get("gaps_identified", "").strip()
        or not content.get("recommended_action", "").strip()
    ):
        return INCOMPLETE_GAPS
    return None


def _content(conclusion: Conclusion) -> dict[str, str]:
    return {field: getattr(conclusion, field) for field in EDITABLE_FIELDS}


def _validated_edits(
    conclusion: Conclusion,
    edits: dict[str, str] | None,
    latest_proposal: ConclusionRevision | None,
) -> dict[str, str]:
    if edits is None or set(edits) != set(EDITABLE_FIELDS):
        raise InvalidDecision("Edit requires exactly the five editable conclusion fields.")
    if not all(isinstance(edits[field], str) for field in EDITABLE_FIELDS):
        raise InvalidDecision("Every editable conclusion field must be text.")
    normalized = {field: edits[field].strip() for field in EDITABLE_FIELDS}
    if normalized["outcome"] not in CONCLUSION_OUTCOMES:
        raise InvalidDecision("Unknown conclusion outcome.")
    if normalized["risk_level"] not in RISK_LEVELS:
        raise InvalidDecision("Unknown risk level.")
    blocker = _approval_blocker(normalized, latest_proposal)
    if blocker:
        raise InvalidDecision(blocker)
    if all(normalized[field] == getattr(conclusion, field) for field in EDITABLE_FIELDS):
        raise InvalidDecision(
            "No changes to save. Use Approve to approve the current content."
        )
    return normalized


def decide(
    db: Session,
    *,
    assessment_id: str,
    conclusion_id: str,
    action: str,
    expected_version: int,
    actor: str,
    edits: dict[str, str] | None = None,
) -> ConclusionRevision:
    conclusion = db.get(Conclusion, conclusion_id)
    if conclusion is None or conclusion.assessment_id != assessment_id:
        raise ConclusionNotFound("Conclusion not found")

    state = analysis_pipeline.load_conclusion_state(
        db,
        assessment_id=conclusion.assessment_id,
        framework_id=conclusion.framework_id,
    )[conclusion.requirement_id]
    if state.expected_version != expected_version:
        raise ConclusionConflict(conclusion.id)

    revisions = _revisions(db, [conclusion.id])
    decision_state, _ = _decision_state(revisions, locked=state.locked)
    if action not in ALLOWED_ACTIONS[decision_state]:
        raise InvalidDecision(
            f"The {action} action is not allowed while this conclusion is {decision_state}."
        )

    latest_proposal = _latest_proposal(revisions)
    values: dict[str, str | bool] = {}
    if action == "approved":
        blocker = _approval_blocker(_content(conclusion), latest_proposal)
        if blocker:
            raise InvalidDecision(blocker)
    elif action == "edited":
        values = {
            **_validated_edits(conclusion, edits, latest_proposal),
            "ai_proposed": False,
        }

    previous_outcome = conclusion.outcome
    previous_rationale = conclusion.rationale
    analysis_pipeline.swap_conclusion(
        db,
        conclusion,
        expected_version=expected_version,
        values=values,
    )
    revision = ConclusionRevision(
        conclusion_id=conclusion.id,
        actor=actor,
        action=action,
        previous_outcome=previous_outcome,
        previous_rationale=previous_rationale,
        citations_json=None,
        analysis_run_id=None,
    )
    db.add(revision)
    db.flush()
    return revision


def _requirement_titles(framework_ids: set[str]) -> dict[tuple[str, str], str]:
    titles: dict[tuple[str, str], str] = {}
    for framework_id in framework_ids:
        if not FrameworkRegistry.is_registered(framework_id):
            continue
        for control in FrameworkRegistry.get_all_controls(framework_id):
            titles[(framework_id, control.id)] = control.title
    return titles


def _ordered_conclusions(
    assessment: Assessment,
    conclusions: list[Conclusion],
) -> list[Conclusion]:
    selected = list(assessment.frameworks)
    remaining = sorted({row.framework_id for row in conclusions} - set(selected))
    framework_order = selected + remaining
    framework_rank = {framework_id: index for index, framework_id in enumerate(framework_order)}
    control_rank: dict[str, dict[str, int]] = {}
    for framework_id in framework_order:
        if FrameworkRegistry.is_registered(framework_id):
            control_rank[framework_id] = {
                control.id: index
                for index, control in enumerate(
                    FrameworkRegistry.get_all_controls(framework_id)
                )
            }
    return sorted(
        conclusions,
        key=lambda row: (
            framework_rank[row.framework_id],
            control_rank.get(row.framework_id, {}).get(row.requirement_id, 10**9),
            row.requirement_id,
        ),
    )


def _withheld_proposal(
    revisions: list[ConclusionRevision],
    runs: dict[str, AnalysisRun],
) -> dict | None:
    withheld = next(
        (
            revision
            for revision in reversed(revisions)
            if revision.action == "proposal_withheld"
        ),
        None,
    )
    if withheld is None:
        return None
    withheld_index = revisions.index(withheld)
    latest_lock_index = max(
        (
            index
            for index, revision in enumerate(revisions)
            if revision.action in analysis_pipeline.LOCKING_ACTIONS
        ),
        default=-1,
    )
    latest_proposed_index = max(
        (
            index
            for index, revision in enumerate(revisions)
            if revision.action == "proposed"
        ),
        default=-1,
    )
    if withheld_index <= latest_lock_index or withheld_index <= latest_proposed_index:
        return None

    result = {
        "outcome": None,
        "rationale": None,
        "revision_id": withheld.id,
        "run_id": withheld.analysis_run_id,
        "created_at": withheld.created_at,
        "citation_count": len(loads_citations(withheld.citations_json)),
    }
    run = runs.get(withheld.analysis_run_id or "")
    if run is None:
        return result
    try:
        claims = json.loads(run.claims_json).get("claims", [])
        claim = next(
            item for item in claims if item.get("revision_id") == withheld.id
        )
        result["outcome"] = claim.get("outcome")
        result["rationale"] = (claim.get("item") or {}).get("current_state")
    except (json.JSONDecodeError, AttributeError, StopIteration, TypeError):
        pass
    return result


def conclusion_cards(db: Session, assessment_id: str) -> list[ConclusionCard]:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        return []
    conclusions = db.execute(
        select(Conclusion).where(Conclusion.assessment_id == assessment_id)
    ).scalars().all()
    if not conclusions:
        return []

    ordered = _ordered_conclusions(assessment, conclusions)
    revisions = _revisions(db, [row.id for row in ordered])
    revisions_by_conclusion: dict[str, list[ConclusionRevision]] = {
        row.id: [] for row in ordered
    }
    for revision in revisions:
        revisions_by_conclusion[revision.conclusion_id].append(revision)

    states: dict[str, analysis_pipeline.ConclusionState] = {}
    for framework_id in dict.fromkeys(row.framework_id for row in ordered):
        framework_states = analysis_pipeline.load_conclusion_state(
            db,
            assessment_id=assessment_id,
            framework_id=framework_id,
        )
        states.update(
            {state.conclusion.id: state for state in framework_states.values()}
        )

    withheld_run_ids = {
        revision.analysis_run_id
        for revision in revisions
        if revision.action == "proposal_withheld" and revision.analysis_run_id
    }
    runs = {
        run.id: run
        for run in (
            db.execute(select(AnalysisRun).where(AnalysisRun.id.in_(withheld_run_ids)))
            .scalars()
            .all()
            if withheld_run_ids
            else []
        )
    }

    legacy_items = db.execute(
        select(GapItem)
        .join(GapReport, GapItem.report_id == GapReport.id)
        .where(GapReport.assessment_id == assessment_id)
    ).scalars().all()
    legacy_by_key = {
        (item.framework_id or "dpdpa", item.requirement_id): item
        for item in legacy_items
    }
    titles = _requirement_titles({row.framework_id for row in ordered})

    cards: list[ConclusionCard] = []
    for conclusion in ordered:
        row_revisions = revisions_by_conclusion[conclusion.id]
        state_row = states[conclusion.id]
        state, latest_human = _decision_state(
            row_revisions,
            locked=state_row.locked,
        )
        latest_proposal = _latest_proposal(row_revisions)
        citations_captured = (
            latest_proposal is not None and latest_proposal.citations_json is not None
        )
        citations = resolve_citations(
            db,
            latest_proposal.citations_json if latest_proposal else None,
        )
        blocker = _approval_blocker(_content(conclusion), latest_proposal)
        last_decision = None
        if latest_human is not None:
            actor_display = latest_human.actor
            if actor_display.startswith(REVIEWER_ACTOR_PREFIX):
                actor_display = actor_display[len(REVIEWER_ACTOR_PREFIX) :]
            last_decision = {
                "action": latest_human.action,
                "actor_display": actor_display,
                "created_at": latest_human.created_at,
            }
        legacy_bulk_approval = bool(
            latest_human
            and latest_human.action == "approved"
            and not latest_human.actor.startswith(REVIEWER_ACTOR_PREFIX)
        )
        legacy_item = legacy_by_key.get(
            (conclusion.framework_id, conclusion.requirement_id)
        )
        legacy_outcome = (
            analysis_pipeline.OUTCOME_BY_STATUS.get(
                legacy_item.compliance_status,
                analysis_pipeline.UNKNOWN_STATUS_OUTCOME,
            )
            if legacy_item is not None
            else None
        )
        edited_revision = next(
            (
                revision
                for revision in reversed(row_revisions)
                if revision.action == "edited"
            ),
            None,
        )
        cards.append(
            ConclusionCard(
                conclusion=conclusion,
                requirement_title=titles.get(
                    (conclusion.framework_id, conclusion.requirement_id),
                    conclusion.requirement_id,
                ),
                state=state,
                locked=state_row.locked,
                allowed_actions=ALLOWED_ACTIONS[state],
                approval_blocker=blocker,
                citations_captured=citations_captured,
                citations=citations,
                unsupported_assertion=(
                    conclusion.outcome in analysis_pipeline.SUPPORTING_OUTCOMES
                    and citations_captured
                    and not citations
                ),
                last_decision=last_decision,
                legacy_bulk_approval=legacy_bulk_approval,
                withheld_proposal=_withheld_proposal(row_revisions, runs),
                legacy_report_status=(
                    legacy_outcome
                    if legacy_outcome is not None
                    and legacy_outcome != conclusion.outcome
                    else None
                ),
                previous_outcome=(
                    edited_revision.previous_outcome if edited_revision else None
                ),
            )
        )
    return cards


def conclusion_card(
    db: Session,
    *,
    assessment_id: str,
    conclusion_id: str,
) -> ConclusionCard:
    for card in conclusion_cards(db, assessment_id):
        if card.conclusion.id == conclusion_id:
            return card
    raise ConclusionNotFound("Conclusion not found")
