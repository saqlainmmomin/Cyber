"""v2 desk-review adapter and persistence boundary."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.services.desk_review import (
    DESK_REVIEW_ALL_FAILED_MESSAGE,
    DESK_REVIEW_PARTIAL_MESSAGE,
    _merge_document_catalogs,
    _persist_findings,
    _raw_response,
)
from app.services.grounding import (
    ClaimBudgetExceeded,
    ClaimSet,
    load_source_documents,
    run_stages_0_1,
)
from app.services.grounding.metadata_fallback import fill_metadata_gaps


logger = logging.getLogger(__name__)

COVERAGE_WITH_CLAIMS = "partial"
COVERAGE_WITHOUT_CLAIMS = "not_covered"
CLAIM_SET_KEY = "claim_set"
PIPELINE_VERSION = "v2"

V2_BUDGET_MESSAGE = (
    "Desk review was not run: the documents need {planned} claim-extraction calls, "
    "above the limit of {cap}. Remove or split documents, or raise v2_max_extraction_calls."
)
V2_FAILED_MESSAGE = "Desk review failed before any framework was reviewed: {error}"
V2_INCOMPLETE_MESSAGE = (
    "Desk review for {name} is incomplete: {count} grounding unit(s) failed "
    "(first error: {error}). Run desk review again."
)


def claims_to_desk_review_result(claim_set: ClaimSet, framework_id: str) -> dict:
    """Adapt verified claims to the five-key desk-review result contract."""
    control_ids = [
        control.id for control in FrameworkRegistry.get(framework_id).all_controls()
    ]
    chunk_by_id = {chunk.chunk_id: chunk for chunk in claim_set.chunks}
    claims_by_requirement = {
        requirement_id: [
            claim
            for claim in claim_set.claims
            if requirement_id in claim.requirement_ids
        ]
        for requirement_id in control_ids
    }

    def evidence_item(claim) -> dict:
        chunk = chunk_by_id[claim.chunk_id]
        return {
            "quote": claim.quote,
            "document": claim.filename,
            "location": chunk.heading or f"Part {chunk.ordinal}",
            "citation": claim.citation,
            "claim_id": claim.claim_id,
            "statement": claim.statement,
            "kind": claim.kind,
            "support": claim.support,
            "tag_status": claim.tag_status,
            "needs_review": claim.needs_review,
            "derived_from_image": claim.derived_from_image,
        }

    evidence_map = {
        requirement_id: [
            evidence_item(claim)
            for claim in claims_by_requirement[requirement_id]
        ]
        for requirement_id in control_ids
        if claims_by_requirement[requirement_id]
    }
    coverage_summary = {
        requirement_id: (
            COVERAGE_WITH_CLAIMS
            if requirement_id in evidence_map
            else COVERAGE_WITHOUT_CLAIMS
        )
        for requirement_id in control_ids
    }

    document_catalog = []
    for source in claim_set.sources:
        source_claims = [
            claim for claim in claim_set.claims if claim.source_id == source["source_id"]
        ]
        tagged = {
            requirement_id
            for claim in source_claims
            for requirement_id in claim.requirement_ids
        }
        document_catalog.append(
            {
                "filename": source["filename"],
                "document_type": source["category"],
                "coverage_areas": [
                    requirement_id
                    for requirement_id in control_ids
                    if requirement_id in tagged
                ],
                "summary": f"{len(source_claims)} verified claim(s) extracted.",
                "derived_from_image": source["derived_from_image"],
                "metadata": source["metadata"],
            }
        )

    return {
        "document_catalog": document_catalog,
        "evidence_map": evidence_map,
        "absence_findings": [],
        "signal_flags": [],
        "coverage_summary": coverage_summary,
    }


def _raw_response_v2(
    framework_ids,
    results,
    errors,
    claim_set: ClaimSet | None,
) -> str:
    payload = json.loads(
        _raw_response(
            framework_ids,
            results,
            errors,
            llm_calls=list(claim_set.llm_calls) if claim_set is not None else [],
        )
    )
    payload["analysis_pipeline_version"] = PIPELINE_VERSION
    payload[CLAIM_SET_KEY] = (
        json.loads(claim_set.to_json()) if claim_set is not None else None
    )
    return json.dumps(payload)


def load_claim_set(db: Session, assessment_id: str) -> ClaimSet | None:
    """Return the stored claim set, or ``None`` for v1 or malformed rows."""
    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )
    if not summary or not summary.raw_ai_response:
        return None
    try:
        payload = json.loads(summary.raw_ai_response)
        claim_set_payload = payload.get(CLAIM_SET_KEY)
        if not isinstance(claim_set_payload, dict):
            return None
        return ClaimSet.from_json(json.dumps(claim_set_payload))
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _incomplete_errors(claim_set: ClaimSet) -> dict[str, str]:
    errors: dict[str, str] = {}
    for framework_id in claim_set.affected_framework_ids():
        control_ids = {
            control.id
            for control in FrameworkRegistry.get(framework_id).all_controls()
        }
        units = [
            unit
            for unit in claim_set.failed_units
            if control_ids.intersection(unit.requirement_ids)
        ]
        errors[framework_id] = V2_INCOMPLETE_MESSAGE.format(
            name=FrameworkRegistry.get(framework_id).name,
            count=len(units),
            error=units[0].error,
        )
    return errors


def run_desk_review_v2(
    db: Session,
    assessment: Assessment,
    summary: DeskReviewSummary,
    doc_id_by_filename: dict[str, str],
) -> DeskReviewSummary:
    """Run v2 grounding, adapt claims, and persist ordinary desk-review rows."""
    framework_ids = assessment.frameworks
    claim_set: ClaimSet | None = None
    errors: dict[str, str] = {}

    try:
        sources = load_source_documents(db, assessment.id)
        claim_set = run_stages_0_1(
            sources,
            framework_ids,
            max_workers=settings.v2_max_concurrency,
        )
    except ClaimBudgetExceeded as exc:
        message = V2_BUDGET_MESSAGE.format(planned=exc.planned, cap=exc.cap)
        errors = {framework_id: message for framework_id in framework_ids}
    except Exception as exc:
        logger.exception("v2 desk review failed before adaptation")
        message = V2_FAILED_MESSAGE.format(error=f"{type(exc).__name__}: {exc}")
        errors = {framework_id: message for framework_id in framework_ids}

    if claim_set is not None and settings.v2_metadata_fallback:
        try:
            claim_set = fill_metadata_gaps(claim_set, sources)
        except Exception:
            logger.exception(
                "v2 metadata fallback failed; continuing with Stage 1 claim set"
            )

    if claim_set is not None:
        errors.update(_incomplete_errors(claim_set))
        results = {
            framework_id: claims_to_desk_review_result(claim_set, framework_id)
            for framework_id in framework_ids
            if framework_id not in errors
        }
    else:
        results = {}

    if not results:
        summary.status = "error"
        if len(framework_ids) == 1:
            summary.error_message = errors[framework_ids[0]]
        else:
            names = ", ".join(
                FrameworkRegistry.get(framework_id).name
                for framework_id in framework_ids
            )
            summary.error_message = DESK_REVIEW_ALL_FAILED_MESSAGE.format(names=names)
        summary.raw_ai_response = _raw_response_v2(
            framework_ids, results, errors, claim_set
        )
        assessment.desk_review_status = "error"
        db.commit()
        return summary

    try:
        for framework_id in framework_ids:
            if framework_id in results:
                _persist_findings(
                    db=db,
                    assessment_id=assessment.id,
                    framework_id=framework_id,
                    result=results[framework_id],
                    doc_id_by_filename=doc_id_by_filename,
                )

        merged_coverage: dict[str, str] = {}
        for framework_id in framework_ids:
            if framework_id in results:
                merged_coverage.update(results[framework_id]["coverage_summary"])

        successful_ids = [
            framework_id for framework_id in framework_ids if framework_id in results
        ]
        if len(successful_ids) == 1:
            catalog = results[successful_ids[0]]["document_catalog"]
        else:
            catalog = _merge_document_catalogs(successful_ids, results)

        summary.document_catalog = json.dumps(catalog)
        summary.coverage_summary = json.dumps(merged_coverage)
        summary.raw_ai_response = _raw_response_v2(
            framework_ids, results, errors, claim_set
        )
        summary.status = "completed"
        summary.error_message = None
        if errors:
            names = ", ".join(
                FrameworkRegistry.get(framework_id).name
                for framework_id in framework_ids
                if framework_id in errors
            )
            summary.error_message = DESK_REVIEW_PARTIAL_MESSAGE.format(names=names)
        summary.completed_at = datetime.now(timezone.utc)
        assessment.desk_review_status = "completed"
        db.commit()

        try:
            from app.services.auto_answer import persist_document_answers

            pre_fill_count = persist_document_answers(assessment.id, db)
            db.commit()
            if pre_fill_count:
                logger.info(
                    "Desk review: pre-filled %s responses from evidence", pre_fill_count
                )
        except Exception as exc:
            logger.warning("Auto-answer pre-fill failed (non-blocking): %s", exc)
    except Exception as exc:
        logger.error("Desk review persist failed: %s", exc)
        summary.status = "error"
        summary.error_message = f"Failed to persist findings: {exc}"
        assessment.desk_review_status = "error"
        db.commit()

    return summary
