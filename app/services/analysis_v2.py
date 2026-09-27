"""Persistence adapter for the v2 grounded analysis and judge."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.initiative import Initiative
from app.models.report import GapItem, GapReport
from app.services import analysis_pipeline
from app.services.analysis_pipeline import (
    PIPELINE_ACTOR,
    _attach_llm_calls,
    _cluster_id,
    load_conclusion_state,
    swap_conclusion,
)
from app.services.citations import attach_citations
from app.services.desk_review_v2 import load_claim_set
from app.services.grounding import judge
from app.services.grounding.claims import ClaimSet, claim_set_is_current
from app.services.grounding.sources import load_source_documents
from app.services.scoring import compute_framework_scores, failed_framework_scores, namespaced_domain_scores

PIPELINE_VERSION = "v2"
V2_STALE_CLAIM_SET_MESSAGE = (
    "The v2 desk-review evidence for this assessment is missing or out of date. "
    "Run desk review again, then run analysis."
)
V2_ANALYSIS_FAILED_MESSAGE = "Analysis failed: {error}"
V2_ALL_FAILED_MESSAGE = "Analysis failed for every selected framework. Run analysis again."
V2_SAVE_FAILED_MESSAGE = "Analysis results could not be saved ({error}). Run analysis again."
LEGACY_STATUS_BY_OUTCOME = {
    "compliant": "compliant",
    "partially_compliant": "partially_compliant",
    "non_compliant": "non_compliant",
    "insufficient_evidence": "not_assessed",
    "not_applicable": "not_applicable",
}
LEGACY_PLACEHOLDER_EFFORT = ""
LEGACY_PLACEHOLDER_TIMELINE_WEEKS = 0
SUMMARY_LINE = (
    "**{name}:** {total} requirements: {compliant} compliant, {partial} partially compliant, "
    "{non} non-compliant, {insufficient} insufficient evidence, {na} not applicable."
)


class AnalysisV2Error(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _applicable(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, list) and value else None


def build_rationale(record: dict) -> str:
    if record.get("scope_excluded"):
        return "Outside the recorded assessment scope."
    criteria = "; ".join(
        f"{criterion['criterion_id']}: {criterion['result']}"
        + (f" ({', '.join(criterion['claim_ids'])})" if criterion["claim_ids"] else "")
        for criterion in record["criteria"]
    )
    return f"Criteria ({record['criteria_source']}): {criteria}"


def _claim_dict(claim) -> dict:
    return {
        "claim_id": claim.claim_id,
        "source_id": claim.source_id,
        "evidence_version_id": claim.evidence_version_id,
        "filename": claim.filename,
        "chunk_id": claim.chunk_id,
        "start": claim.start,
        "end": claim.end,
        "quote": claim.quote,
        "statement": claim.statement,
        "kind": claim.kind,
        "requirement_ids": list(claim.requirement_ids),
        "needs_review": claim.needs_review,
        "derived_from_image": claim.derived_from_image,
        "citation": claim.citation,
    }


def _record_claims(record: dict, claim_set: ClaimSet | None) -> list:
    if claim_set is None:
        return []
    by_id = {claim.claim_id: claim for claim in claim_set.claims}
    return [
        by_id[claim_id]
        for claim_id in record["cited_claim_ids"]
        if claim_id in by_id
    ]


def _citations_for(record: dict, claim_set: ClaimSet | None) -> tuple[list[dict], list]:
    cited_claims = _record_claims(record, claim_set)
    citations: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for claim in cited_claims:
        citation = claim.citation
        if not isinstance(citation, dict):
            continue
        identity = (
            citation["evidence_version_id"],
            citation["location_type"],
            citation["location_ref"],
        )
        if identity in seen:
            continue
        seen.add(identity)
        citations.append(citation)
    return citations, cited_claims


def _framework_divergences(framework_id: str, divergences: tuple[dict, ...]) -> list[dict]:
    return [
        divergence
        for divergence in divergences
        if any(
            framework_id == member[0]
            for member in divergence["compliant"] + divergence["non_compliant"]
        )
    ]


def record_framework_run_v2(
    db: Session,
    context,
    *,
    framework_id: str,
    judgment_set: judge.JudgmentSet,
    claim_set: ClaimSet | None,
    gap_report_id: str,
    llm_calls: list[dict] | None,
) -> AnalysisRun:
    run = db.get(AnalysisRun, context.run_ids[framework_id])
    if run is None:
        raise RuntimeError(f"Analysis run for {framework_id} was not found.")
    envelope = json.loads(run.claims_json)
    state = load_conclusion_state(
        db,
        assessment_id=run.assessment_id,
        framework_id=framework_id,
    )
    framework = FrameworkRegistry.get(framework_id)
    records = judgment_set.judgments[framework_id]
    claims: list[dict] = []
    cited_claim_ids: set[str] = set()

    for record in records:
        requirement_id = record["requirement_id"]
        citations, cited_claims = _citations_for(record, claim_set)
        cited_claim_ids.update(record["cited_claim_ids"])
        cited_with_citation = [claim for claim in cited_claims if claim.citation is not None]
        evidence_summary = cited_with_citation[0].quote if cited_with_citation else ""
        rationale = build_rationale(record)
        cluster_id = _cluster_id(framework_id, requirement_id)
        content = {
            "outcome": record["conclusion_outcome"],
            "rationale": rationale,
            "evidence_summary": evidence_summary,
            "gaps_identified": record["gap_statement"],
            "risk_level": record["risk_level"],
            "recommended_action": "",
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

        item = {**record, "current_state": rationale}
        claims.append({
            "requirement_id": requirement_id,
            "cluster_id": cluster_id,
            "outcome": record["conclusion_outcome"],
            "scope_enforced": record["scope_excluded"],
            "item": item,
            "quality": {
                "citation_count": len(citations),
                "evidence_quote_grounded": bool(citations) if cited_claims else None,
                "unsupported_assertion": record["unsupported_assertion"],
                "needs_review": any(claim.needs_review for claim in cited_claims),
                "desk_review_red_flags": len(record["red_flags"]),
                "desk_review_absence": bool(record["absences"]),
                "contradictions": len(record["contradictions"]),
                "criteria_source": record["criteria_source"],
                "analysis_incomplete": record["analysis_incomplete"],
                "framework_divergence": record["framework_divergence"],
            },
            "conclusion_id": conclusion.id,
            "revision_id": revision.id,
            "disposition": disposition,
        })

    verified_claims = [
        _claim_dict(claim)
        for claim in (claim_set.claims if claim_set is not None else ())
        if claim.claim_id in cited_claim_ids
    ]
    envelope.update({
        "analysis_pipeline_version": PIPELINE_VERSION,
        "judge_prompt_version": judgment_set.prompt_version,
        "judge_prompt_fingerprint": judgment_set.prompt_fingerprint,
        "claim_set_id": judgment_set.claim_set_id,
        "verified_claims": verified_claims,
        "divergences": _framework_divergences(framework_id, judgment_set.divergences),
        "judgment_metrics": judgment_set.metrics[framework_id],
        "claims": claims,
        "gap_report_id": gap_report_id,
        "desk_review_used": claim_set is not None,
        "error": None,
    })
    _attach_llm_calls(
        envelope,
        context,
        framework_id=framework_id,
        llm_calls=llm_calls,
    )
    run.status = "completed"
    run.completed_at = datetime.now().astimezone()
    run.claims_json = json.dumps(envelope, sort_keys=True)
    db.flush()
    return run


def _replace_legacy_report(db: Session, assessment_id: str) -> str | None:
    existing = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    if existing is None:
        return None
    old_items = db.query(GapItem).filter(GapItem.report_id == existing.id).all()
    snapshot = {
        "preserved_at": datetime.now().isoformat(),
        "label": "gap_analysis_rerun",
        "report": {
            column.name: getattr(existing, column.name)
            for column in existing.__table__.columns
            if column.name != "legacy_history"
        },
        "items": [
            {column.name: getattr(item, column.name) for column in item.__table__.columns}
            for item in old_items
        ],
    }
    history = []
    if existing.legacy_history:
        try:
            history = json.loads(existing.legacy_history)
            if not isinstance(history, list):
                history = [history]
        except json.JSONDecodeError:
            history = []
    history.append(snapshot)
    carried = json.dumps(history, default=str)
    db.query(GapItem).filter(GapItem.report_id == existing.id).delete()
    db.query(Initiative).filter(Initiative.report_id == existing.id).delete()
    db.delete(existing)
    db.flush()
    return carried


def _summary_line(framework_id: str, records: Sequence[dict]) -> str:
    counts = {outcome: 0 for outcome in LEGACY_STATUS_BY_OUTCOME}
    for record in records:
        counts[record["conclusion_outcome"]] += 1
    return SUMMARY_LINE.format(
        name=FrameworkRegistry.get(framework_id).name,
        total=len(records),
        compliant=counts["compliant"],
        partial=counts["partially_compliant"],
        non=counts["non_compliant"],
        insufficient=counts["insufficient_evidence"],
        na=counts["not_applicable"],
    )


def _legacy_item(
    report_id: str,
    framework_id: str,
    record: dict,
    claim_set: ClaimSet | None,
) -> GapItem:
    control = FrameworkRegistry.get(framework_id).get_control(record["requirement_id"])
    cited_claims = _record_claims(record, claim_set)
    cited_with_citation = [claim for claim in cited_claims if claim.citation is not None]
    evidence_quote = cited_with_citation[0].quote if cited_with_citation else None
    response = record["response"]
    if cited_claims and response is not None:
        evidence_confidence = "strong"
    elif cited_claims:
        evidence_confidence = "moderate"
    else:
        evidence_confidence = "weak"
    needs_review = (
        record["unsupported_assertion"]
        or record["applicability_proposed"]
        or record["analysis_incomplete"]
        or any(claim.needs_review for claim in cited_claims)
    )
    status = LEGACY_STATUS_BY_OUTCOME[record["conclusion_outcome"]]
    rationale = build_rationale(record)
    return GapItem(
        report_id=report_id,
        requirement_id=record["requirement_id"],
        framework_id=framework_id,
        cluster_id=_cluster_id(framework_id, record["requirement_id"]),
        chapter=control.reference,
        control_reference=control.reference,
        requirement_title=control.title,
        compliance_status=status,
        current_state=rationale,
        gap_description=record["gap_statement"],
        risk_level=record["risk_level"],
        remediation_action="",
        remediation_priority=record["priority"],
        remediation_effort=LEGACY_PLACEHOLDER_EFFORT,
        timeline_weeks=LEGACY_PLACEHOLDER_TIMELINE_WEEKS,
        maturity_level=None,
        root_cause_category=None,
        evidence_quote=evidence_quote,
        evidence_confidence=evidence_confidence,
        review_status="draft",
        needs_review=needs_review,
        ai_compliance_status=status,
        ai_gap_description=record["gap_statement"],
        ai_risk_level=record["risk_level"],
    )


def _persist_v2(
    db: Session,
    assessment: Assessment,
    responses: list[dict],
    claim_set: ClaimSet | None,
    judgment_set: judge.JudgmentSet,
    run_context,
) -> dict:
    selected_frameworks = list(judgment_set.framework_ids)
    failed = list(judgment_set.failed_frameworks)
    per_fw_scores: dict[str, dict] = {}
    for framework_id in selected_frameworks:
        if framework_id in judgment_set.failed_frameworks:
            per_fw_scores[framework_id] = failed_framework_scores()
            continue
        legacy = [
            {
                "requirement_id": record["requirement_id"],
                "compliance_status": LEGACY_STATUS_BY_OUTCOME[record["conclusion_outcome"]],
            }
            for record in judgment_set.judgments[framework_id]
        ]
        per_fw_scores[framework_id] = compute_framework_scores(legacy, framework_id)

    carried_history = _replace_legacy_report(db, assessment.id)
    summary = "\n\n".join(
        _summary_line(framework_id, judgment_set.judgments[framework_id])
        for framework_id in selected_frameworks
        if framework_id in judgment_set.judgments
    )
    report = GapReport(
        assessment_id=assessment.id,
        overall_score=0.0,
        chapter_scores=json.dumps(namespaced_domain_scores(per_fw_scores)),
        framework_scores=json.dumps(per_fw_scores),
        executive_summary=summary,
        raw_ai_response=json.dumps({
            "analysis_pipeline_version": PIPELINE_VERSION,
            "judge_prompt_version": judgment_set.prompt_version,
            "claim_set_id": judgment_set.claim_set_id,
            "divergences": list(judgment_set.divergences),
            "failed_frameworks": judgment_set.failed_frameworks,
        }, sort_keys=True),
        legacy_history=carried_history,
    )
    db.add(report)
    db.flush()

    for framework_id in selected_frameworks:
        if framework_id in judgment_set.judgments:
            record_framework_run_v2(
                db,
                run_context,
                framework_id=framework_id,
                judgment_set=judgment_set,
                claim_set=claim_set,
                gap_report_id=report.id,
                llm_calls=list(judgment_set.llm_calls),
            )
            for record in judgment_set.judgments[framework_id]:
                db.add(_legacy_item(report.id, framework_id, record, claim_set))

    assessment.status = "error" if failed else "completed"
    db.commit()
    db.refresh(report)
    return {
        "report_id": report.id,
        "status": "incomplete" if failed else "completed",
        "analysis_pipeline_version": PIPELINE_VERSION,
        "frameworks_analyzed": list(per_fw_scores),
        "per_framework_scores": {fw_id: s["overall_score"] for fw_id, s in per_fw_scores.items()},
        "initiatives_generated": 0,
        "failed_frameworks": failed,
        "message": (
            "Results for the other frameworks were saved. Run analysis again to complete the assessment."
            if failed
            else f"Analysis completed ({len(judgment_set.judgments)} frameworks)"
        ),
        "analysis_run_ids": dict(run_context.run_ids),
    }


def run_analysis_v2(db: Session, assessment: Assessment, *, responses: list[dict]) -> dict:
    framework_ids = list(assessment.frameworks)
    sources = load_source_documents(db, assessment.id)
    claim_set = load_claim_set(db, assessment.id) if sources else None
    if sources and (
        claim_set is None
        or not claim_set_is_current(claim_set, sources, framework_ids)
    ):
        db.rollback()
        raise AnalysisV2Error(400, V2_STALE_CLAIM_SET_MESSAGE)
    applicable_requirements = _applicable(assessment.applicable_requirements)

    assessment.status = "analyzing"
    db.commit()
    run_context = analysis_pipeline.start_runs(
        db,
        assessment_id=assessment.id,
        framework_ids=framework_ids,
    )
    db.commit()
    try:
        judgment_set = judge.run_stage_2(
            claim_set,
            framework_ids,
            responses,
            applicable_requirements=applicable_requirements,
        )
    except Exception as exc:
        analysis_pipeline.fail_runs(
            db,
            run_context,
            error_type=type(exc).__name__,
        )
        assessment.status = "error"
        db.commit()
        raise AnalysisV2Error(
            500,
            V2_ANALYSIS_FAILED_MESSAGE.format(error=f"{type(exc).__name__}: {exc}"),
        ) from exc

    failed = list(judgment_set.failed_frameworks)
    if failed:
        analysis_pipeline.fail_runs(
            db,
            run_context,
            error_type="FrameworkAnalysisError",
            framework_ids=failed,
            llm_calls=list(judgment_set.llm_calls),
        )
    db.commit()
    if len(failed) == len(framework_ids):
        assessment.status = "error"
        db.commit()
        raise AnalysisV2Error(500, V2_ALL_FAILED_MESSAGE)

    try:
        return _persist_v2(
            db,
            assessment,
            responses,
            claim_set,
            judgment_set,
            run_context,
        )
    except Exception as exc:
        db.rollback()
        analysis_pipeline.fail_runs(
            db,
            run_context,
            error_type=type(exc).__name__,
            llm_calls=list(judgment_set.llm_calls),
        )
        assessment.status = "error"
        db.commit()
        raise AnalysisV2Error(
            500,
            V2_SAVE_FAILED_MESSAGE.format(error=type(exc).__name__),
        ) from exc
