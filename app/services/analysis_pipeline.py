"""Immutable analysis persistence for the dual-written assessment pipeline.

D-P2-3-A keeps the legacy report view and appends run, conclusion, and revision
records from the same analyzer result. D-P2-3-B makes the router own the
transaction boundaries and the running/completed/failed lifecycle, recording
only exception type names in durable errors. D-P2-3-C protects approved and
edited conclusions with the latest-human-decision lock rule and a versioned
compare-and-swap. D-P2-3-D snapshots evidence sources at run start and stores
only citations grounded in each claim's own quote, failing closed if a source
is no longer active. D-P2-3-E stores a versioned claims envelope with exact
inputs, claims, and error fields. D-P2-3-F relies on the pinned migration's
revision link and natural-key uniqueness guard. D-P2-3-G keeps legacy history
on replacement-based report rows while append-only rows carry their own
history. D-P2-3-H leaves pipeline-owned assessments out of legacy mapping.

This module never commits; the caller owns every transaction. It intentionally
contains no ORM row-removal operation.
The compare-and-swap is shared with the consultant decision service.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import literal_column, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.questionnaire import QuestionnaireResponse
from app.services.citations import (
    CitableSource,
    attach_citations,
    cite_quotes,
    citable_sources,
)
from app.services.auto_answer import confirmed_response_clause
from app.services.evidence import analysis_documents

logger = logging.getLogger(__name__)

CLAIMS_SCHEMA_VERSION = 1
PIPELINE_ACTOR = "system:analysis"
RUN_STATUSES = ("running", "completed", "failed")
OUTCOME_BY_STATUS = {
    "compliant": "compliant",
    "partially_compliant": "partially_compliant",
    "non_compliant": "non_compliant",
    "not_applicable": "not_applicable",
    "not_assessed": "insufficient_evidence",
}
UNKNOWN_STATUS_OUTCOME = "insufficient_evidence"
HUMAN_DECISION_ACTIONS = ("approved", "edited", "rejected", "reopened")
LOCKING_ACTIONS = ("approved", "edited")
SUPPORTING_OUTCOMES = ("compliant", "partially_compliant")


class AnalysisPipelineError(Exception):
    """Base error for immutable analysis persistence failures."""


class ConclusionConflict(AnalysisPipelineError):
    """Raised when a conclusion changed after its version was read."""

    def __init__(self, conclusion_id: str):
        super().__init__(f"Conclusion {conclusion_id} changed while analysis was running.")


@dataclass(frozen=True)
class RunContext:
    trigger_id: str
    run_ids: dict[str, str]
    sources: tuple[CitableSource, ...]


@dataclass(frozen=True)
class ConclusionState:
    conclusion: Conclusion
    locked: bool
    expected_version: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _envelope(
    *,
    trigger_id: str,
    framework_id: str,
    assessment_id: str,
    db: Session,
    sources: tuple[CitableSource, ...],
) -> dict[str, Any]:
    assessment = db.get(Assessment, assessment_id)
    applicable_requirements = None
    if assessment is not None and assessment.applicable_requirements:
        try:
            parsed = json.loads(assessment.applicable_requirements)
        except (TypeError, json.JSONDecodeError):
            parsed = None
        if isinstance(parsed, list):
            applicable_requirements = parsed

    documents = analysis_documents(db, assessment_id)
    questionnaire_response_count = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id,
        confirmed_response_clause(),
    ).count()
    return {
        "schema_version": CLAIMS_SCHEMA_VERSION,
        "trigger_id": trigger_id,
        "framework_id": framework_id,
        "model_tiers": {
            "extract": settings.llm_model_extract,
            "judge": settings.llm_model_judge,
            "synthesize": settings.llm_model_synthesize,
        },
        "inputs": {
            "evidence_versions": [
                {
                    "evidence_id": source.evidence_id,
                    "version_id": source.version_id,
                    "filename": source.filename,
                }
                for source in sources
            ],
            "legacy_document_ids": [
                document["legacy_document_id"]
                for document in documents
                if document.get("source") == "legacy"
            ],
            "questionnaire_response_count": questionnaire_response_count,
            "applicable_requirements": applicable_requirements,
        },
        "gap_report_id": None,
        "desk_review_used": None,
        "claims": [],
        "error": None,
    }


def start_runs(
    db: Session,
    *,
    assessment_id: str,
    framework_ids: list[str],
) -> RunContext:
    """Create one visible running row for each framework in trigger order."""
    sources = tuple(citable_sources(db, assessment_id))
    trigger_id = str(uuid4())
    run_ids: dict[str, str] = {}
    for framework_id in framework_ids:
        envelope = _envelope(
            trigger_id=trigger_id,
            framework_id=framework_id,
            assessment_id=assessment_id,
            db=db,
            sources=sources,
        )
        run = AnalysisRun(
            assessment_id=assessment_id,
            framework_id=framework_id,
            status="running",
            claims_json=json.dumps(envelope, sort_keys=True),
            model_id=settings.llm_model_judge,
            started_at=_utcnow(),
            completed_at=None,
        )
        db.add(run)
        db.flush()
        run_ids[framework_id] = run.id
    return RunContext(trigger_id=trigger_id, run_ids=run_ids, sources=sources)


def fail_runs(
    db: Session,
    context: RunContext,
    *,
    error_type: str,
    framework_ids: list[str] | None = None,
) -> None:
    """Close targeted running rows with a type-only durable error."""
    targets = framework_ids if framework_ids is not None else list(context.run_ids)
    for framework_id in targets:
        run_id = context.run_ids.get(framework_id)
        if run_id is None:
            continue
        run = db.get(AnalysisRun, run_id)
        if run is None or run.status != "running":
            continue
        envelope = json.loads(run.claims_json)
        envelope["claims"] = []
        envelope["error"] = {"type": error_type}
        run.status = "failed"
        run.completed_at = _utcnow()
        run.claims_json = json.dumps(envelope, sort_keys=True)
    db.flush()


def load_conclusion_state(
    db: Session,
    *,
    assessment_id: str,
    framework_id: str,
) -> dict[str, ConclusionState]:
    """Read conclusion rows and the latest human action for each row."""
    conclusions = db.execute(
        select(Conclusion).where(
            Conclusion.assessment_id == assessment_id,
            Conclusion.framework_id == framework_id,
        )
    ).scalars().all()
    if not conclusions:
        return {}

    conclusion_ids = [conclusion.id for conclusion in conclusions]
    revisions = db.execute(
        select(ConclusionRevision).where(
            ConclusionRevision.conclusion_id.in_(conclusion_ids),
            ConclusionRevision.action.in_(HUMAN_DECISION_ACTIONS),
        ).order_by(
            ConclusionRevision.created_at,
            literal_column("conclusion_revisions.rowid"),
        )
    ).scalars().all()
    latest_human_action: dict[str, str] = {}
    for revision in revisions:
        latest_human_action[revision.conclusion_id] = revision.action

    return {
        conclusion.requirement_id: ConclusionState(
            conclusion=conclusion,
            locked=latest_human_action.get(conclusion.id) in LOCKING_ACTIONS,
            expected_version=conclusion.version,
        )
        for conclusion in conclusions
    }


def swap_conclusion(
    db: Session,
    conclusion: Conclusion,
    *,
    expected_version: int,
    values: dict[str, Any],
) -> None:
    """Compare-and-swap one Conclusion on its version (D6).

    Writes ``values`` plus ``version = expected_version + 1`` iff the row still
    holds ``expected_version``; otherwise raises ConclusionConflict. Never commits.
    """
    result = db.execute(
        update(Conclusion)
        .where(Conclusion.id == conclusion.id, Conclusion.version == expected_version)
        .values(**values, version=expected_version + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise ConclusionConflict(conclusion.id)
    db.expire(conclusion)


def _cluster_id(framework_id: str, requirement_id: str) -> str | None:
    return {
        member["control"]: cluster["cluster_id"]
        for cluster in CONTROL_CLUSTERS
        for member in cluster["controls"]
        if member["framework"] == framework_id
    }.get(requirement_id)


def _desk_review_quality(desk_review_data: dict | None, requirement_id: str) -> tuple[int, bool]:
    findings = (desk_review_data or {}).get("findings", [])
    red_flags = sum(
        1
        for finding in findings
        if finding.get("type") == "signal"
        and finding.get("requirement_id") == requirement_id
    )
    absence = any(
        finding.get("type") == "absence"
        and finding.get("requirement_id") == requirement_id
        for finding in findings
    )
    return red_flags, absence


def record_framework_run(
    db: Session,
    context: RunContext,
    *,
    framework_id: str,
    assessments: list[dict],
    desk_review_data: dict | None,
    gap_report_id: str,
) -> AnalysisRun:
    """Persist claims, conclusions, revisions, and the completed run."""
    run = db.get(AnalysisRun, context.run_ids[framework_id])
    if run is None:
        raise AnalysisPipelineError(f"Analysis run for {framework_id} was not found.")
    envelope = json.loads(run.claims_json)
    applicable = envelope["inputs"]["applicable_requirements"]
    state = load_conclusion_state(
        db,
        assessment_id=run.assessment_id,
        framework_id=framework_id,
    )
    claims: list[dict[str, Any]] = []
    seen_requirements: set[str] = set()

    for item in assessments:
        requirement_id = item["requirement_id"]
        if requirement_id in seen_requirements:
            logger.warning("Duplicate analysis requirement %s ignored", requirement_id)
            continue
        seen_requirements.add(requirement_id)

        status = item.get("compliance_status")
        outcome = OUTCOME_BY_STATUS.get(status, UNKNOWN_STATUS_OUTCOME)
        if status not in OUTCOME_BY_STATUS:
            logger.warning(
                "Unknown compliance status for requirement %s; recording insufficient evidence",
                requirement_id,
            )
        quote = item.get("evidence_quote") or ""
        citations = cite_quotes(list(context.sources), [quote]) if quote.strip() else []
        grounded = None if not quote.strip() else bool(citations)
        cluster_id = _cluster_id(framework_id, requirement_id)
        content = {
            "outcome": outcome,
            "rationale": item.get("current_state") or "",
            "evidence_summary": quote if grounded else "",
            "gaps_identified": item.get("gap_description") or "",
            "risk_level": item.get("risk_level") or "medium",
            "recommended_action": item.get("remediation_action") or "",
            "cluster_id": cluster_id,
        }

        existing = state.get(requirement_id)
        previous_outcome = None
        previous_rationale = None
        if existing is None:
            conclusion = Conclusion(
                assessment_id=run.assessment_id,
                requirement_id=requirement_id,
                framework_id=framework_id,
                ai_proposed=True,
                version=1,
                **content,
            )
            db.add(conclusion)
            db.flush()
            disposition = "created"
        elif existing.locked:
            conclusion = existing.conclusion
            previous_outcome = conclusion.outcome
            previous_rationale = conclusion.rationale
            disposition = "withheld"
        else:
            conclusion = existing.conclusion
            previous_outcome = conclusion.outcome
            previous_rationale = conclusion.rationale
            swap_conclusion(
                db,
                conclusion,
                expected_version=existing.expected_version,
                values={**content, "ai_proposed": True},
            )
            disposition = "applied"

        revision = ConclusionRevision(
            conclusion_id=conclusion.id,
            actor=PIPELINE_ACTOR,
            action="proposal_withheld" if disposition == "withheld" else "proposed",
            previous_outcome=previous_outcome,
            previous_rationale=previous_rationale,
            analysis_run_id=run.id,
        )
        db.add(revision)
        db.flush()
        attach_citations(db, revision=revision, citations=citations)

        red_flags, absence = _desk_review_quality(desk_review_data, requirement_id)
        claims.append(
            {
                "requirement_id": requirement_id,
                "cluster_id": cluster_id,
                "outcome": outcome,
                "scope_enforced": bool(applicable) and requirement_id not in applicable,
                "item": item,
                "quality": {
                    "citation_count": len(citations),
                    "evidence_quote_grounded": grounded,
                    "unsupported_assertion": outcome in SUPPORTING_OUTCOMES and not citations,
                    "needs_review": bool(item.get("needs_review", False)),
                    "desk_review_red_flags": red_flags,
                    "desk_review_absence": absence,
                    "contradictions": None,
                },
                "conclusion_id": conclusion.id,
                "revision_id": revision.id,
                "disposition": disposition,
            }
        )

    envelope["claims"] = claims
    envelope["gap_report_id"] = gap_report_id
    envelope["desk_review_used"] = desk_review_data is not None
    envelope["error"] = None
    run.status = "completed"
    run.completed_at = _utcnow()
    run.claims_json = json.dumps(envelope, sort_keys=True)
    db.flush()
    return run
