"""Read-only workpaper read model (P2-6): per-requirement traceability from client response and evidence to AI proposal, consultant decision and every revision. Never writes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.conclusion import ConclusionRevision
from app.models.desk_review import DeskReviewFinding
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.models.questionnaire import QuestionnaireResponse
from app.services import analysis_pipeline, conclusion_review
from app.services.citations import resolve_citations
from app.services.conclusion_review import REVIEWER_ACTOR_PREFIX, ConclusionCard

STALE_RUNNING_AFTER = timedelta(hours=1)
CONTENT_CHANGING_ACTIONS = ("proposed", "edited")
ACTION_LABELS = {
    "proposed": "AI proposal",
    "proposal_withheld": "AI proposal withheld (conclusion locked)",
    "approved": "Approved",
    "edited": "Edited and approved",
    "rejected": "Rejected",
    "reopened": "Reopened",
}
LEGACY_BULK_LABEL = "Legacy bulk approval, not individually reviewed"


def anchor_for(framework_id: str, requirement_id: str) -> str:
    """Return the fragment id of a requirement's entry."""
    return f"wp-{framework_id}-{requirement_id}"


@dataclass(frozen=True)
class RunSummary:
    id: str
    framework_id: str
    status: str
    stale: bool
    model_id: str
    started_at: datetime
    completed_at: datetime | None
    trigger_id: str | None
    claim_count: int
    error_type: str | None
    evidence_version_count: int | None
    desk_review_used: bool | None


@dataclass(frozen=True)
class ClientResponse:
    question_id: str
    matched_on: str
    answer: str
    notes: str | None
    evidence_reference: str | None
    na_reason: str | None
    confidence: str | None
    answer_source: str | None
    submitted_at: datetime


@dataclass(frozen=True)
class RevisionEntry:
    sequence: int
    revision: ConclusionRevision
    action_label: str
    actor_display: str
    is_human: bool
    legacy_bulk_approval: bool
    outcome_after: str | None
    rationale_after: str | None
    run: RunSummary | None
    claim: dict | None
    citations_captured: bool
    citations: list[dict]


@dataclass(frozen=True)
class WorkpaperEntry:
    card: ConclusionCard
    anchor: str
    in_scope: bool
    client_response: ClientResponse | None
    mapped_evidence: list[dict]
    desk_review_findings: list[dict]
    ai_proposal: RevisionEntry | None
    revisions: list[RevisionEntry]


@dataclass(frozen=True)
class FrameworkSection:
    framework_id: str
    entries: list[WorkpaperEntry]
    excluded_entries: list[WorkpaperEntry]
    unconcluded: list[dict]


@dataclass(frozen=True)
class Workpaper:
    sections: list[FrameworkSection]
    runs: list[RunSummary]
    counts: dict[str, int]
    applicable: frozenset[str] | None


def _scope(raw: str | None) -> frozenset[str] | None:
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


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _run_data(raw: str) -> tuple[dict, list[dict]]:
    try:
        envelope = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}, []
    if not isinstance(envelope, dict):
        return {}, []
    claims = envelope.get("claims")
    return envelope, claims if isinstance(claims, list) else []


def _run_summaries(
    rows: list[AnalysisRun],
    *,
    now: datetime,
) -> tuple[list[RunSummary], dict[str, dict]]:
    summaries: list[RunSummary] = []
    claims_by_revision: dict[str, dict] = {}
    cutoff = _utc(now) - STALE_RUNNING_AFTER
    for row in rows:
        envelope, claims = _run_data(row.claims_json)
        inputs = envelope.get("inputs")
        evidence_versions = inputs.get("evidence_versions") if isinstance(inputs, dict) else None
        error = envelope.get("error")
        desk_review_used = envelope.get("desk_review_used")
        summary = RunSummary(
            id=row.id,
            framework_id=row.framework_id,
            status=row.status,
            stale=row.status == "running" and _utc(row.started_at) < cutoff,
            model_id=row.model_id,
            started_at=row.started_at,
            completed_at=row.completed_at,
            trigger_id=envelope.get("trigger_id"),
            claim_count=len(claims),
            error_type=error.get("type") if isinstance(error, dict) else None,
            evidence_version_count=(
                len(evidence_versions) if isinstance(evidence_versions, list) else None
            ),
            desk_review_used=(
                desk_review_used if isinstance(desk_review_used, bool) else None
            ),
        )
        summaries.append(summary)
        for claim in claims:
            if not isinstance(claim, dict) or not claim.get("revision_id"):
                continue
            claims_by_revision[claim["revision_id"]] = claim
    return summaries, claims_by_revision


def _responses(db: Session, assessment_id: str) -> dict[str, QuestionnaireResponse]:
    rows = db.execute(
        select(QuestionnaireResponse)
        .where(QuestionnaireResponse.assessment_id == assessment_id)
        .order_by(QuestionnaireResponse.submitted_at, QuestionnaireResponse.id)
    ).scalars().all()
    return {row.question_id: row for row in rows}


def _client_response(card: ConclusionCard, rows: dict[str, QuestionnaireResponse]) -> ClientResponse | None:
    conclusion = card.conclusion
    candidates = [(conclusion.requirement_id, "requirement")]
    if conclusion.cluster_id is not None:
        candidates.append((conclusion.cluster_id, "cluster"))
    candidates.append((f"SINGLE.{conclusion.requirement_id}", "singleton"))
    match = next(
        ((rows[key], matched_on) for key, matched_on in candidates if key in rows),
        None,
    )
    if match is None:
        return None
    row, matched_on = match
    return ClientResponse(
        question_id=row.question_id,
        matched_on=matched_on,
        answer=row.answer,
        notes=row.notes,
        evidence_reference=row.evidence_reference,
        na_reason=row.na_reason,
        confidence=row.confidence,
        answer_source=row.answer_source,
        submitted_at=row.submitted_at,
    )


def _mapped_evidence(db: Session, assessment_id: str) -> dict[tuple[str, str], list[dict]]:
    rows = db.execute(
        select(EvidenceUse, Evidence)
        .join(Evidence, EvidenceUse.evidence_id == Evidence.id)
        .where(EvidenceUse.assessment_id == assessment_id)
        .order_by(EvidenceUse.created_at, EvidenceUse.id)
    ).all()
    evidence_ids = {use.evidence_id for use, _evidence in rows}
    active_versions = (
        db.execute(
            select(EvidenceVersion).where(
                EvidenceVersion.evidence_id.in_(evidence_ids),
                EvidenceVersion.status == "active",
            )
        ).scalars().all()
        if evidence_ids
        else []
    )
    active_by_evidence = {version.evidence_id: version for version in active_versions}
    by_key: dict[tuple[str, str], list[dict]] = {}
    for use, evidence in rows:
        version = active_by_evidence.get(evidence.id)
        by_key.setdefault((use.framework_id, use.requirement_id), []).append(
            {
                "use_id": use.id,
                "evidence_id": evidence.id,
                "filename": (
                    version.original_filename if version else evidence.original_filename
                ),
                "evidence_status": evidence.status,
                "relevance": use.relevance,
                "created_at": use.created_at,
            }
        )
    return by_key


def _desk_findings(db: Session, assessment_id: str) -> dict[str, list[dict]]:
    rows = db.execute(
        select(DeskReviewFinding)
        .where(
            DeskReviewFinding.assessment_id == assessment_id,
            DeskReviewFinding.requirement_id.isnot(None),
        )
        .order_by(DeskReviewFinding.id)
    ).scalars().all()
    by_requirement: dict[str, list[dict]] = {}
    for row in rows:
        by_requirement.setdefault(row.requirement_id, []).append(
            {
                "finding_type": row.finding_type,
                "severity": row.severity,
                "content": row.content,
                "source_quote": row.source_quote,
                "source_location": row.source_location,
                "citations_captured": row.citations_json is not None,
                "citations": resolve_citations(db, row.citations_json),
            }
        )
    return by_requirement


def _revision_entries(
    db: Session,
    revisions: list[ConclusionRevision],
    card: ConclusionCard,
    runs: dict[str, RunSummary],
    claims: dict[str, dict],
) -> list[RevisionEntry]:
    entries: list[RevisionEntry] = []
    next_content_after: list[ConclusionRevision | None] = [None] * len(revisions)
    next_content = None
    for index in range(len(revisions) - 1, -1, -1):
        next_content_after[index] = next_content
        if revisions[index].action in CONTENT_CHANGING_ACTIONS:
            next_content = revisions[index]
    for index, revision in enumerate(revisions):
        legacy_bulk = (
            revision.action == "approved"
            and not revision.actor.startswith(REVIEWER_ACTOR_PREFIX)
        )
        actor_display = revision.actor
        if actor_display.startswith(REVIEWER_ACTOR_PREFIX):
            actor_display = actor_display[len(REVIEWER_ACTOR_PREFIX) :]
        outcome_after = None
        rationale_after = None
        if revision.action in CONTENT_CHANGING_ACTIONS:
            following_content = next_content_after[index]
            if following_content is None:
                outcome_after = card.conclusion.outcome
                rationale_after = card.conclusion.rationale
            else:
                outcome_after = following_content.previous_outcome
                rationale_after = following_content.previous_rationale
        entries.append(
            RevisionEntry(
                sequence=index + 1,
                revision=revision,
                action_label=(
                    LEGACY_BULK_LABEL
                    if legacy_bulk
                    else ACTION_LABELS.get(revision.action, revision.action)
                ),
                actor_display=actor_display,
                is_human=revision.action in analysis_pipeline.HUMAN_DECISION_ACTIONS,
                legacy_bulk_approval=legacy_bulk,
                outcome_after=outcome_after,
                rationale_after=rationale_after,
                run=runs.get(revision.analysis_run_id or ""),
                claim=claims.get(revision.id),
                citations_captured=revision.citations_json is not None,
                citations=resolve_citations(db, revision.citations_json),
            )
        )
    return entries


def build_workpaper(
    db: Session,
    assessment: Assessment,
    *,
    now: datetime | None = None,
) -> Workpaper:
    cards = conclusion_review.conclusion_cards(db, assessment.id)
    conclusion_ids = [card.conclusion.id for card in cards]
    revision_rows = (
        db.execute(
            select(ConclusionRevision)
            .where(ConclusionRevision.conclusion_id.in_(conclusion_ids))
            .order_by(
                ConclusionRevision.created_at,
                literal_column("conclusion_revisions.rowid"),
            )
        ).scalars().all()
        if conclusion_ids
        else []
    )
    run_rows = db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.assessment_id == assessment.id)
        .order_by(AnalysisRun.started_at, literal_column("analysis_runs.rowid"))
    ).scalars().all()
    run_summaries, claims = _run_summaries(
        run_rows,
        now=now or datetime.now(timezone.utc),
    )
    runs_by_id = {run.id: run for run in run_summaries}
    responses = _responses(db, assessment.id)
    mapped_evidence = _mapped_evidence(db, assessment.id)
    desk_findings = _desk_findings(db, assessment.id)
    revisions_by_conclusion: dict[str, list[ConclusionRevision]] = {
        conclusion_id: [] for conclusion_id in conclusion_ids
    }
    for revision in revision_rows:
        revisions_by_conclusion[revision.conclusion_id].append(revision)

    applicable = _scope(assessment.applicable_requirements)
    entries: list[WorkpaperEntry] = []
    for card in cards:
        conclusion = card.conclusion
        revision_entries = _revision_entries(
            db,
            revisions_by_conclusion[conclusion.id],
            card,
            runs_by_id,
            claims,
        )
        entries.append(
            WorkpaperEntry(
                card=card,
                anchor=anchor_for(conclusion.framework_id, conclusion.requirement_id),
                in_scope=(
                    applicable is None or conclusion.requirement_id in applicable
                ),
                client_response=_client_response(card, responses),
                mapped_evidence=mapped_evidence.get(
                    (conclusion.framework_id, conclusion.requirement_id), []
                ),
                desk_review_findings=desk_findings.get(conclusion.requirement_id, []),
                ai_proposal=next(
                    (
                        revision
                        for revision in reversed(revision_entries)
                        if revision.revision.action == "proposed"
                    ),
                    None,
                ),
                revisions=revision_entries,
            )
        )

    sections: list[FrameworkSection] = []
    if cards:
        selected = list(assessment.frameworks)
        remaining = sorted(
            {entry.card.conclusion.framework_id for entry in entries} - set(selected)
        )
        concluded_keys = {
            (entry.card.conclusion.framework_id, entry.card.conclusion.requirement_id)
            for entry in entries
        }
        for framework_id in selected + remaining:
            framework_entries = [
                entry
                for entry in entries
                if entry.card.conclusion.framework_id == framework_id
            ]
            unconcluded = []
            if FrameworkRegistry.is_registered(framework_id):
                for control in FrameworkRegistry.get_all_controls(framework_id):
                    if (
                        applicable is not None
                        and control.id not in applicable
                    ) or (framework_id, control.id) in concluded_keys:
                        continue
                    unconcluded.append(
                        {
                            "requirement_id": control.id,
                            "title": control.title,
                            "anchor": anchor_for(framework_id, control.id),
                        }
                    )
            sections.append(
                FrameworkSection(
                    framework_id=framework_id,
                    entries=[entry for entry in framework_entries if entry.in_scope],
                    excluded_entries=[
                        entry for entry in framework_entries if not entry.in_scope
                    ],
                    unconcluded=unconcluded,
                )
            )

    counts = {
        "conclusions": len(entries),
        "in_scope": sum(entry.in_scope for entry in entries),
        "excluded": sum(not entry.in_scope for entry in entries),
        "unconcluded": sum(len(section.unconcluded) for section in sections),
        "pending": sum(entry.card.state == "pending" for entry in entries),
        "rejected": sum(entry.card.state == "rejected" for entry in entries),
        "approved": sum(
            entry.card.state == "approved" and not entry.card.legacy_bulk_approval
            for entry in entries
        ),
        "edited": sum(entry.card.state == "edited" for entry in entries),
        "legacy_bulk": sum(entry.card.legacy_bulk_approval for entry in entries),
        "runs": len(run_summaries),
    }
    return Workpaper(
        sections=sections,
        runs=run_summaries,
        counts=counts,
        applicable=applicable,
    )
