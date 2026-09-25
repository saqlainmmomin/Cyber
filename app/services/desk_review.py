"""
Desk Review Pipeline — Call 0 (pre-questionnaire document analysis).

Analyzes uploaded documents to produce:
- Document catalog (type, coverage, summary per doc)
- Evidence map (requirement_id -> evidence items with source quotes)
- Absence findings (missing provisions per requirement)
- Signal flags (red flags: GDPR copy-paste, buried consent, etc.)
- Coverage summary (requirement_id -> coverage level)
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.dpdpa.prompts import build_desk_review_system_prompt, build_desk_review_user_prompt
from app.frameworks.prompts import (
    CURATED_PROMPT_FRAMEWORK_ID,
    UNCLASSIFIED_FLAG_TYPE,
    build_framework_desk_review_system_prompt,
    desk_review_flag_types,
)
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
from app.services import llm_client
from app.services.parallel import run_bounded
from app.services.citations import (
    CitableSource,
    cite_quotes,
    citable_sources,
    dumps_citations,
    whole_item_citation,
)
from app.services.evidence import analysis_documents

logger = logging.getLogger(__name__)

DESK_REVIEW_PARTIAL_MESSAGE = (
    "Desk review failed for {names}. Findings for the other frameworks were saved. "
    "Run desk review again to complete it."
)
DESK_REVIEW_ALL_FAILED_MESSAGE = (
    "Desk review failed for every selected framework ({names}). Run desk review again."
)
RAW_RESPONSE_SCHEMA_VERSION = 2


def run_desk_review(assessment_id: str, db: Session) -> DeskReviewSummary:
    """
    Run desk review analysis on all uploaded documents for an assessment.

    Creates/updates DeskReviewSummary and DeskReviewFinding records.
    Returns the summary record.
    """
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    # Load documents
    docs_db = analysis_documents(db, assessment_id)
    if not docs_db:
        raise ValueError("No documents uploaded for this assessment")

    documents = [
        {
            "id": d["id"],
            "filename": d["filename"],
            "category": d["category"],
            "text": d["text"],
        }
        for d in docs_db
    ]

    # Build document ID lookup for linking findings to documents
    doc_id_by_filename = {d["filename"]: d["legacy_document_id"] for d in docs_db}

    # Create or reset summary
    summary = (
        db.query(DeskReviewSummary)
        .filter(DeskReviewSummary.assessment_id == assessment_id)
        .first()
    )
    if summary:
        # Clear previous findings
        db.query(DeskReviewFinding).filter(
            DeskReviewFinding.assessment_id == assessment_id
        ).delete()
        summary.status = "analyzing"
        summary.error_message = None
        summary.started_at = datetime.now(timezone.utc)
        summary.completed_at = None
    else:
        summary = DeskReviewSummary(
            assessment_id=assessment_id,
            status="analyzing",
            started_at=datetime.now(timezone.utc),
        )
        db.add(summary)

    assessment.desk_review_status = "analyzing"
    db.commit()
    db.refresh(summary)

    # Truncate documents for prompt
    truncated = _truncate_documents(documents)

    framework_ids = assessment.frameworks
    results: dict[str, dict] = {}
    errors: dict[str, str] = {}
    with llm_client.collect_calls() as llm_calls:
        def review_framework(framework_id: str) -> dict:
            with llm_client.call_tag(stage="desk_review", framework_id=framework_id):
                return _normalize_result(
                    framework_id,
                    _desk_review_call(
                        framework_id,
                        documents=truncated,
                        company_name=assessment.company_name,
                        industry=assessment.industry,
                    ),
                )

        review_results = run_bounded(
            review_framework,
            framework_ids,
            max_workers=settings.llm_max_concurrency,
        )
        for framework_id, (result, error) in zip(framework_ids, review_results):
            if error is not None:
                errors[framework_id] = str(error)
                logger.error("Desk review failed for %s: %s", framework_id, error)
            else:
                results[framework_id] = result

    if not results:
        summary.status = "error"
        if len(framework_ids) == 1:
            summary.error_message = str(errors[framework_ids[0]])
        else:
            names = ", ".join(
                FrameworkRegistry.get(framework_id).name
                for framework_id in framework_ids
            )
            summary.error_message = DESK_REVIEW_ALL_FAILED_MESSAGE.format(names=names)
        summary.raw_ai_response = _raw_response(
            framework_ids, results, errors, llm_calls=llm_calls
        )
        assessment.desk_review_status = "error"
        db.commit()
        return summary

    # Parse and persist results
    try:
        sources = citable_sources(db, assessment_id)
        for framework_id in framework_ids:
            if framework_id in results:
                _persist_findings(
                    db=db,
                    assessment_id=assessment_id,
                    framework_id=framework_id,
                    result=results[framework_id],
                    doc_id_by_filename=doc_id_by_filename,
                    sources=sources,
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
        summary.raw_ai_response = _raw_response(
            framework_ids, results, errors, llm_calls=llm_calls
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

        # Auto-create pre-filled questionnaire responses from document evidence
        try:
            from app.services.auto_answer import persist_document_answers
            pre_fill_count = persist_document_answers(assessment_id, db)
            db.commit()
            if pre_fill_count:
                logger.info(f"Desk review: pre-filled {pre_fill_count} responses from evidence")
        except Exception as e:
            # Pre-fill failure should not block the desk review result
            logger.warning(f"Auto-answer pre-fill failed (non-blocking): {e}")

    except Exception as e:
        logger.error(f"Desk review persist failed: {e}")
        summary.status = "error"
        summary.error_message = f"Failed to persist findings: {e}"
        assessment.desk_review_status = "error"
        db.commit()

    return summary


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    """Seam for the OpenRouter-backed client — patched directly in tests."""
    return llm_client.call_llm(tier, stream=stream, **request)


def _call_claude_desk_review(
    documents: list[dict],
    company_name: str,
    industry: str,
) -> dict:
    """Call the LLM for desk review analysis (Call 0)."""
    system_blocks = build_desk_review_system_prompt()
    user_prompt = build_desk_review_user_prompt(documents, company_name, industry)

    response = _call_llm(
        tier="judge",
        max_tokens=16000,
        temperature=0,
        system=system_blocks,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response["text"]

    # Log cache stats
    usage = response["usage"]
    logger.info(
        f"Desk review tokens — input: {usage['input_tokens']}, "
        f"output: {usage['output_tokens']}, "
        f"cache_read: {usage['cache_read_input_tokens']}, "
        f"cache_create: {usage['cache_creation_input_tokens']}"
    )

    return _parse_json_response(raw_text)


def _call_framework_desk_review(
    framework_id: str,
    documents: list[dict],
    company_name: str,
    industry: str,
) -> dict:
    """Run a registry-driven desk review for a non-curated framework."""
    system_blocks = build_framework_desk_review_system_prompt(framework_id)
    user_prompt = build_desk_review_user_prompt(documents, company_name, industry)
    response = _call_llm(
        tier="judge",
        stream=True,
        max_tokens=settings.llm_max_output_tokens_framework,
        temperature=0,
        system=system_blocks,
        messages=[{"role": "user", "content": user_prompt}],
    )
    usage = response["usage"]
    logger.info(
        "Desk review (%s) tokens — input: %s, output: %s, cache_read: %s, cache_create: %s",
        framework_id,
        usage["input_tokens"],
        usage["output_tokens"],
        usage["cache_read_input_tokens"],
        usage["cache_creation_input_tokens"],
    )
    return _parse_json_response(response["text"])


def _desk_review_call(
    framework_id: str,
    *,
    documents,
    company_name,
    industry,
) -> dict:
    """Dispatch desk review to the curated or registry-driven prompt seam."""
    if framework_id == CURATED_PROMPT_FRAMEWORK_ID:
        return _call_claude_desk_review(
            documents=documents,
            company_name=company_name,
            industry=industry,
        )
    return _call_framework_desk_review(
        framework_id, documents, company_name, industry
    )


def _normalize_result(framework_id: str, result: dict) -> dict:
    """Normalize one framework's desk-review result before persistence."""
    control_ids = {
        control.id for control in FrameworkRegistry.get(framework_id).all_controls()
    }
    flag_vocab = set(desk_review_flag_types(framework_id))
    dropped = 0

    catalog = result.get("document_catalog") or []
    if not isinstance(catalog, list):
        catalog = []

    evidence_map: dict[str, list[dict]] = {}
    raw_evidence = result.get("evidence_map") or {}
    if isinstance(raw_evidence, dict):
        for requirement_id, items in raw_evidence.items():
            if requirement_id not in control_ids:
                dropped += 1
                continue
            if not isinstance(items, list):
                continue
            evidence_map[requirement_id] = [
                item for item in items if isinstance(item, dict)
            ]

    absences: list[dict] = []
    raw_absences = result.get("absence_findings") or []
    if isinstance(raw_absences, list):
        for item in raw_absences:
            if not isinstance(item, dict):
                continue
            requirement_id = item.get("requirement_id")
            if (
                isinstance(requirement_id, str)
                and requirement_id
                and requirement_id not in control_ids
            ):
                dropped += 1
                continue
            absences.append(item)

    signals: list[dict] = []
    raw_signals = result.get("signal_flags") or []
    if isinstance(raw_signals, list):
        for item in raw_signals:
            if not isinstance(item, dict):
                continue
            valid_requirement_ids = []
            for requirement_id in item.get("requirement_ids") or []:
                if isinstance(requirement_id, str) and requirement_id in control_ids:
                    if requirement_id not in valid_requirement_ids:
                        valid_requirement_ids.append(requirement_id)
                elif isinstance(requirement_id, str):
                    dropped += 1
            signal = dict(item)
            signal["requirement_ids"] = valid_requirement_ids
            signal["flag_type"] = (
                item.get("flag_type")
                if item.get("flag_type") in flag_vocab
                else UNCLASSIFIED_FLAG_TYPE
            )
            signals.append(signal)

    coverage: dict[str, object] = {}
    raw_coverage = result.get("coverage_summary") or {}
    if isinstance(raw_coverage, dict):
        for requirement_id, value in raw_coverage.items():
            if requirement_id in control_ids:
                coverage[requirement_id] = value
            else:
                dropped += 1

    if dropped:
        logger.warning(
            "Desk review (%s) dropped %d unknown control id(s)",
            framework_id,
            dropped,
        )

    return {
        "document_catalog": catalog,
        "evidence_map": evidence_map,
        "absence_findings": absences,
        "signal_flags": signals,
        "coverage_summary": coverage,
    }


def _raw_response(
    framework_ids: list[str],
    results: dict[str, dict],
    errors: dict[str, str],
    *,
    llm_calls: list[dict] | None = None,
) -> str:
    """Serialize the versioned per-framework raw desk-review response."""
    response = {
        "schema_version": RAW_RESPONSE_SCHEMA_VERSION,
        "frameworks": {
            framework_id: (
                {"status": "completed", "result": results[framework_id]}
                if framework_id in results
                else {"status": "error", "error": errors[framework_id]}
            )
            for framework_id in framework_ids
        },
    }
    if llm_calls is not None:
        response["llm_calls"] = llm_calls
    return json.dumps(response)


def _merge_document_catalogs(
    framework_ids: list[str],
    results: dict[str, dict],
) -> list[dict]:
    """Merge successful framework catalogs by filename in framework order."""
    catalog: list[dict] = []
    by_filename: dict[str, dict] = {}
    for framework_id in framework_ids:
        for entry in results[framework_id]["document_catalog"]:
            if not isinstance(entry, dict) or not entry.get("filename"):
                catalog.append(entry)
                continue
            filename = entry["filename"]
            if filename not in by_filename:
                merged = dict(entry)
                merged["coverage_areas"] = list(
                    dict.fromkeys(entry.get("coverage_areas") or [])
                )
                catalog.append(merged)
                by_filename[filename] = merged
                continue
            coverage_areas = by_filename[filename].setdefault("coverage_areas", [])
            for control_id in entry.get("coverage_areas") or []:
                if control_id not in coverage_areas:
                    coverage_areas.append(control_id)
    return catalog


def _persist_findings(
    db: Session,
    assessment_id: str,
    framework_id: str,
    result: dict,
    doc_id_by_filename: dict[str, str],
    sources: list[CitableSource] = (),
) -> None:
    """Persist desk review findings to the database."""

    # Evidence map -> findings
    for req_id, evidence_items in result.get("evidence_map", {}).items():
        for item in evidence_items:
            doc_filename = item.get("document", "")
            quote = item.get("quote", "")
            citations = (
                cite_quotes(sources, [quote], preferred_filename=doc_filename)
                if quote.strip()
                else [
                    whole_item_citation(source)
                    for source in sources
                    if source.filename == doc_filename
                ][:1]
            )
            db.add(DeskReviewFinding(
                assessment_id=assessment_id,
                framework_id=framework_id,
                finding_type="evidence",
                requirement_id=req_id,
                document_id=doc_id_by_filename.get(doc_filename),
                content=item.get("quote", ""),
                severity="info",
                source_quote=item.get("quote", ""),
                source_location=item.get("location", ""),
                citations_json=dumps_citations(citations),
            ))

    # Absence findings
    for finding in result.get("absence_findings", []):
        db.add(DeskReviewFinding(
            assessment_id=assessment_id,
            framework_id=framework_id,
            finding_type="absence",
            requirement_id=finding.get("requirement_id"),
            content=finding.get("description", ""),
            severity=finding.get("severity", "medium"),
            citations_json="[]",
        ))

    # Signal flags
    for flag in result.get("signal_flags", []):
        doc_filename = flag.get("document", "")
        req_ids = flag.get("requirement_ids", [])
        quote = flag.get("source_quote", "")
        citations = (
            cite_quotes(sources, [quote], preferred_filename=doc_filename)
            if quote.strip()
            else [
                whole_item_citation(source)
                for source in sources
                if source.filename == doc_filename
            ][:1]
        )
        serialized = dumps_citations(citations)
        group_id = str(uuid.uuid4())
        for requirement_id in (req_ids or [None]):
            db.add(DeskReviewFinding(
                assessment_id=assessment_id,
                framework_id=framework_id,
                finding_type="signal",
                requirement_id=requirement_id,
                flag_type=flag["flag_type"],
                signal_group_id=group_id,
                document_id=doc_id_by_filename.get(doc_filename),
                content=flag.get("description", ""),
                severity=flag.get("severity", "medium"),
                source_quote=flag.get("source_quote", ""),
                source_location=flag.get("location", ""),
                citations_json=serialized,
            ))

    db.flush()


def _truncate_documents(documents: list[dict]) -> list[dict]:
    """Enforce word limits for desk review prompt."""
    max_total = settings.max_total_document_words
    total_words = 0
    result = []

    for doc in documents:
        words = doc["text"].split()
        remaining = max_total - total_words
        if remaining <= 0:
            break
        if len(words) > remaining:
            doc = {**doc, "text": " ".join(words[:remaining]) + "\n\n[... truncated ...]"}
            words = words[:remaining]
        total_words += len(words)
        result.append(doc)

    return result


def _parse_json_response(text: str) -> dict:
    """Parse Claude's JSON response, handling potential markdown fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse desk review response as JSON: {e}\nResponse: {text[:500]}")
