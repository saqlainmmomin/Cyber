"""
Gap analysis pipeline. Talks to whichever model each tier is configured for
via the shared OpenRouter-backed client in app/services/llm_client.py.

Supports:
- Single-framework (DPDPA legacy path) and multi-framework analysis
- System prompt caching via cache_control blocks (see app/dpdpa/prompts.py) —
  effective cost reduction depends on whether the tier's provider honors it;
  not yet verified for the OpenRouter transport, see llm_client.py.
- Two/three-call architecture: evidence extraction → per-framework analysis → synthesis
- Structured context assembly with risk profile
"""

import json
import logging
import re

from app.config import settings
from app.services import llm_client
from app.services.parallel import run_bounded
from app.dpdpa.framework import get_all_requirements
from app.dpdpa.prompts import (
    build_evidence_extraction_prompt,
    build_system_prompt,
    build_user_prompt,
)
from app.schemas.llm_output import validate_and_filter

logger = logging.getLogger(__name__)


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    """Make one LLM request for the given tier and return a plain dict.

    Golden tests patch this boundary. Keeping the provider client behind the
    boundary makes recordings deterministic and guarantees an uncached
    replay cannot accidentally reach the network.
    """
    return llm_client.call_llm(tier, stream=stream, **request)


def run_gap_analysis(
    company_name: str,
    industry: str,
    company_size: str,
    description: str | None,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None = None,
    desk_review_data: dict | None = None,
    applicable_requirements: list[str] | None = None,
) -> dict:
    """
    Run full DPDPA gap analysis using Claude.

    Uses two-call architecture when documents are present:
      Call 1: Extract evidence quotes from documents (grounding)
      Call 2: Gap analysis using evidence + responses + context

    Returns:
        Dict with "parsed" (structured assessment) and "raw" (Claude's text),
        plus "usage" with token stats including cache info.
    """
    return _run_gap_analysis(
        company_name=company_name,
        industry=industry,
        company_size=company_size,
        description=description,
        responses=responses,
        documents=documents,
        context_profile=context_profile,
        desk_review_data=desk_review_data,
        applicable_requirements=applicable_requirements,
    )


def _run_gap_analysis(
    company_name: str,
    industry: str,
    company_size: str,
    description: str | None,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None = None,
    desk_review_data: dict | None = None,
    applicable_requirements: list[str] | None = None,
) -> dict:
    truncated_docs = _truncate_documents(documents)

    # Call 1: Evidence extraction — skip if desk review already extracted evidence.
    # Desk review (Call 0) maps document quotes to requirements. When it has run
    # successfully, re-extracting evidence is redundant and wastes ~45-60s.
    evidence = None
    if truncated_docs:
        dr_evidence = _evidence_from_desk_review(desk_review_data)
        if dr_evidence:
            evidence = dr_evidence
            logger.info(
                "Skipping evidence extraction Call 1 — reusing desk review evidence "
                f"({len(dr_evidence)} requirements covered)"
            )
        else:
            desk_review_findings = desk_review_data.get("findings") if desk_review_data else None
            with llm_client.call_tag(stage="evidence_extraction", framework_id="dpdpa"):
                evidence = _run_evidence_extraction(truncated_docs, desk_review_findings)

    # Call 2: Gap analysis with cached system prompt
    system_blocks = build_system_prompt()
    user_prompt = build_user_prompt(
        company_name=company_name,
        industry=industry,
        company_size=company_size,
        description=description,
        responses=responses,
        documents=truncated_docs,
        context_profile=context_profile,
        evidence=evidence,
        desk_review_summary=desk_review_data,
        applicable_requirements=applicable_requirements,
    )

    with llm_client.call_tag(stage="judge", framework_id="dpdpa"):
        response = _call_llm(
            tier="judge",
            max_tokens=16384,
            temperature=0,
            system=system_blocks,
            messages=[{"role": "user", "content": user_prompt}],
        )

    raw_text = response["text"]
    parsed = _parse_json_response(raw_text)
    known_ids = {r["id"] for r in get_all_requirements()}
    parsed = validate_and_filter(parsed, known_ids)
    parsed["assessments"] = _flag_unsupported_compliant_items(parsed["assessments"])

    # Log cache stats
    usage = response["usage"]
    cache_read = usage["cache_read_input_tokens"]
    cache_create = usage["cache_creation_input_tokens"]
    logger.info(
        f"Gap analysis tokens — input: {usage['input_tokens']}, "
        f"output: {usage['output_tokens']}, "
        f"cache_read: {cache_read}, cache_create: {cache_create}"
    )

    return {
        "parsed": parsed,
        "raw": raw_text,
        "usage": {
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_create,
        },
    }


def _evidence_from_desk_review(desk_review_data: dict | None) -> dict | None:
    """
    Build a Call-1-compatible evidence dict from desk review findings.

    Returns {requirement_id: [quote, ...]} if desk review has evidence findings,
    otherwise None (caller should fall back to running Call 1).
    """
    if not desk_review_data:
        return None
    findings = desk_review_data.get("findings", [])
    evidence: dict[str, list[str]] = {}
    for f in findings:
        if f.get("type") == "evidence" and f.get("requirement_id"):
            rid = f["requirement_id"]
            # Prefer source_quote if present, otherwise content
            quote = f.get("source_quote") or f.get("content", "")
            if quote:
                evidence.setdefault(rid, []).append(quote)
    return evidence if evidence else None


# Smart quotes/apostrophes a PDF extractor or the model itself can introduce
# in text that's otherwise a verbatim match — normalized to their straight
# equivalents so grounding doesn't reject a genuine quote over punctuation
# style alone. This stays a substring check, not fuzzy matching: only
# whitespace, hyphenation-across-line-breaks, quote style, and case are
# normalized, nothing about matching approximate wording.
_QUOTE_NORMALIZE_TABLE = str.maketrans(
    {"‘": "'", "’": "'", "“": '"', "”": '"'}
)


def _ground_evidence_quotes(evidence: dict, documents: list[dict]) -> dict:
    """Drop extracted quotes that don't actually appear in the source documents.

    Verbatim substring check (case-insensitive, whitespace/hyphenation/quote-
    style normalized), run before evidence is threaded into Call 2's prompt —
    catches a fabricated citation deterministically and for free, regardless
    of which model produced it.
    """

    def normalize(text: str) -> str:
        # De-hyphenate a word wrapped across a line break (e.g.
        # "authoriza-\ntion") before whitespace collapsing erases the break.
        text = re.sub(r"-\s*\n\s*", "", text)
        text = text.translate(_QUOTE_NORMALIZE_TABLE)
        return " ".join(text.split()).lower()

    source_text = normalize(" ".join(doc.get("text", "") for doc in documents))
    grounded: dict[str, list[str]] = {}
    dropped = 0
    for req_id, quotes in evidence.items():
        kept = [q for q in quotes if normalize(q) in source_text]
        dropped += len(quotes) - len(kept)
        if kept:
            grounded[req_id] = kept
    if dropped:
        logger.warning("Evidence grounding check dropped %d ungrounded quote(s)", dropped)
    return grounded


def _run_evidence_extraction(
    documents: list[dict],
    desk_review_findings: list[dict] | None = None,
) -> dict | None:
    """
    Call 1: Extract evidence quotes from documents for each requirement.

    Returns a dict mapping requirement_id → list of quoted text.
    """
    prompt = build_evidence_extraction_prompt(documents, desk_review_findings)

    try:
        with llm_client.call_tag(stage="evidence_extraction"):
            response = _call_llm(
                tier="extract",
                max_tokens=8192,
                temperature=0,
                system="You are a document analyst. Extract exact quotes from documents that are relevant to each compliance requirement. Be precise and quote verbatim.",
                messages=[{"role": "user", "content": prompt}],
            )

        raw = response["text"]
        parsed = _parse_json_response(raw)
        evidence = _ground_evidence_quotes(parsed.get("evidence", {}), documents)

        logger.info(f"Evidence extraction: found quotes for {len(evidence)} requirements")
        return evidence

    except Exception as e:
        logger.warning(f"Evidence extraction failed, falling back to single-call: {e}")
        return None


def _run_framework_evidence_extraction(
    framework_id: str,
    documents: list[dict],
    desk_review_findings: list[dict] | None = None,
) -> dict | None:
    """Extract grounded evidence using the selected framework's prompt."""
    from app.frameworks.prompts import (
        CURATED_PROMPT_FRAMEWORK_ID,
        build_framework_evidence_extraction_prompt,
    )
    from app.frameworks.registry import FrameworkRegistry

    if framework_id == CURATED_PROMPT_FRAMEWORK_ID:
        return _run_evidence_extraction(documents, desk_review_findings)

    framework = FrameworkRegistry.get(framework_id)
    try:
        with llm_client.call_tag(stage="evidence_extraction"):
            response = _call_llm(
                tier="extract",
                max_tokens=settings.llm_max_output_tokens_framework,
                temperature=0,
                system=(
                    "You are a document analyst. Extract exact quotes from documents "
                    f"that are relevant to each {framework.name} control. Be precise and quote verbatim."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": build_framework_evidence_extraction_prompt(
                            framework_id, documents, desk_review_findings
                        ),
                    }
                ],
            )
        parsed = _parse_json_response(response["text"])
        grounded = _ground_evidence_quotes(parsed.get("evidence", {}), documents)
        control_ids = {control.id for control in framework.all_controls()}
        evidence = {
            requirement_id: quotes
            for requirement_id, quotes in grounded.items()
            if requirement_id in control_ids
        }
        logger.info(
            "Evidence extraction (%s): found quotes for %d controls",
            framework_id,
            len(evidence),
        )
        return evidence
    except Exception as exc:
        logger.warning(
            "Evidence extraction failed for %s, falling back to documents: %s",
            framework_id,
            exc,
        )
        return None


def _collect_framework_evidence(
    framework_ids: list[str],
    documents: list[dict],
    desk_review_data: dict | None,
) -> dict | None:
    """Collect desk-review or extracted evidence independently per framework."""
    from app.frameworks.registry import FrameworkRegistry

    if not documents:
        return None

    evidence: dict[str, list[str]] = {}
    evidence_by_framework: dict[str, dict[str, list[str]]] = {}
    desk_review_evidence = _evidence_from_desk_review(desk_review_data) or {}
    extraction_items: list[tuple[str, list[dict] | None]] = []
    for framework_id in framework_ids:
        control_ids = {
            control.id
            for control in FrameworkRegistry.get(framework_id).all_controls()
        }
        reused = {
            requirement_id: quotes
            for requirement_id, quotes in desk_review_evidence.items()
            if requirement_id in control_ids
        }
        if reused:
            evidence_by_framework[framework_id] = reused
            logger.info(
                "Reusing desk review evidence for %s (%d controls)",
                framework_id,
                len(reused),
            )
            continue

        framework_findings = [
            finding
            for finding in (desk_review_data or {}).get("findings", [])
            if finding.get("requirement_id") in control_ids
        ]
        extraction_items.append((framework_id, framework_findings or None))

    def extract_framework(item: tuple[str, list[dict] | None]):
        framework_id, framework_findings = item
        with llm_client.call_tag(framework_id=framework_id):
            return _run_framework_evidence_extraction(
                framework_id,
                documents,
                framework_findings,
            )

    extraction_results = run_bounded(
        extract_framework,
        extraction_items,
        max_workers=settings.llm_max_concurrency,
    )
    for (framework_id, _), (extracted, error) in zip(extraction_items, extraction_results):
        if error is not None:
            logger.warning("Evidence extraction failed for %s: %s", framework_id, error)
            continue
        if extracted:
            evidence_by_framework[framework_id] = extracted

    for framework_id in framework_ids:
        if framework_id in evidence_by_framework:
            evidence.update(evidence_by_framework[framework_id])

    return evidence or None


def _truncate_documents(documents: list[dict]) -> list[dict]:
    """Enforce total document word limit across all documents."""
    max_total = settings.max_total_document_words
    total_words = 0
    result = []

    # Prioritize by category importance
    priority_order = [
        "privacy_policy",
        "consent_form",
        "breach_procedure",
        "dpia",
        "retention_policy",
        "processing_records",
        "data_flow_diagram",
        "vendor_agreement",
        "other",
    ]
    sorted_docs = sorted(
        documents,
        key=lambda d: (
            priority_order.index(d["category"])
            if d["category"] in priority_order
            else 99
        ),
    )

    for doc in sorted_docs:
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


def run_multi_framework_analysis(
    framework_ids: list[str],
    company_name: str,
    industry: str,
    company_size: str,
    description: str | None,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None = None,
    desk_review_data: dict | None = None,
    applicable_controls: list[str] | None = None,
) -> dict:
    """
    Run multi-framework gap analysis.

    Pipeline:
      1. Evidence extraction (one call, all documents)
      2. Per-framework gap analysis (one call each, cached system prompts)
      3. Cross-framework synthesis (one lightweight call)

    Returns:
        {
            "frameworks": {fw_id: {"parsed": ..., "raw": ..., "usage": ...}},
            "synthesis": {"parsed": ..., "raw": ...},
            "total_usage": {...},
        }
    """
    return _run_multi_framework_analysis(
        framework_ids=framework_ids,
        company_name=company_name,
        industry=industry,
        company_size=company_size,
        description=description,
        responses=responses,
        documents=documents,
        context_profile=context_profile,
        desk_review_data=desk_review_data,
        applicable_controls=applicable_controls,
    )


def _run_multi_framework_analysis(
    framework_ids: list[str],
    company_name: str,
    industry: str,
    company_size: str,
    description: str | None,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None = None,
    desk_review_data: dict | None = None,
    applicable_controls: list[str] | None = None,
) -> dict:
    from app.frameworks.prompts import (
        build_framework_system_prompt,
        build_framework_user_prompt,
        build_synthesis_prompt,
        build_synthesis_system_prompt,
    )
    from app.frameworks.registry import FrameworkRegistry

    truncated_docs = _truncate_documents(documents)

    # Step 1: Evidence extraction (reuse desk review independently per framework)
    evidence = _collect_framework_evidence(
        framework_ids, truncated_docs, desk_review_data
    )

    # Step 2: Per-framework gap analysis
    framework_results: dict[str, dict] = {}
    total_usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}

    def run_framework(fw_id: str) -> dict:
        with llm_client.call_tag(stage="judge", framework_id=fw_id):
            logger.info(f"Running gap analysis for framework: {fw_id}")
            system_blocks = build_framework_system_prompt(fw_id)
            user_prompt = build_framework_user_prompt(
                framework_id=fw_id,
                company_name=company_name,
                industry=industry,
                company_size=company_size,
                description=description,
                responses=responses,
                documents=truncated_docs,
                context_profile=context_profile,
                evidence=evidence,
                desk_review_summary=desk_review_data,
                applicable_controls=applicable_controls,
            )

            # Use streaming to avoid server disconnects on large responses
            # (per-framework prompts with 90+ controls can produce ~50KB responses)
            response = _call_llm(
                tier="judge",
                stream=True,
                max_tokens=settings.llm_max_output_tokens_framework,
                temperature=0,
                system=system_blocks,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = response["text"]

            parsed = _parse_json_response(raw_text)
            known_ids = {c.id for c in FrameworkRegistry.get(fw_id).all_controls()}
            parsed = validate_and_filter(parsed, known_ids)
            parsed["assessments"] = _flag_unsupported_compliant_items(parsed["assessments"])

            usage = response["usage"]
            cache_read = usage["cache_read_input_tokens"]
            cache_create = usage["cache_creation_input_tokens"]

            result = {
                "parsed": parsed,
                "raw": raw_text,
                "usage": {
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "cache_read_input_tokens": cache_read,
                    "cache_creation_input_tokens": cache_create,
                },
            }
            logger.info(
                f"{fw_id} analysis complete — input: {usage['input_tokens']}, "
                f"output: {usage['output_tokens']}, cache_read: {cache_read}"
            )
            return result

    framework_runs = run_bounded(
        run_framework,
        framework_ids,
        max_workers=settings.llm_max_concurrency,
    )
    for fw_id, (framework_result, error) in zip(framework_ids, framework_runs):
        if error is not None:
            logger.error(f"Gap analysis failed for {fw_id}: {error}")
            framework_results[fw_id] = {
                "parsed": {"executive_summary": f"Analysis failed: {error}", "assessments": []},
                "raw": str(error),
                "usage": {},
                "error": str(error),
            }
            continue

        framework_results[fw_id] = framework_result
        usage = framework_result["usage"]
        total_usage["input_tokens"] += usage["input_tokens"]
        total_usage["output_tokens"] += usage["output_tokens"]
        total_usage["cache_read_input_tokens"] += usage["cache_read_input_tokens"]
        total_usage["cache_creation_input_tokens"] += usage["cache_creation_input_tokens"]

    # Step 3: Cross-framework synthesis (only for 2+ frameworks)
    synthesis = None
    if len(framework_ids) > 1 and any("error" not in r for r in framework_results.values()):
        try:
            per_fw_parsed = {
                fw_id: r["parsed"]
                for fw_id, r in framework_results.items()
                if "error" not in r
            }
            synthesis_prompt = build_synthesis_prompt(per_fw_parsed, company_name, industry)
            synthesis_system = build_synthesis_system_prompt()

            with llm_client.call_tag(stage="synthesis"):
                response = _call_llm(
                    tier="synthesize",
                    stream=True,
                    max_tokens=4096,
                    temperature=0,
                    system=synthesis_system,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                )
            raw_text = response["text"]

            synthesis = {
                "parsed": _parse_json_response(raw_text),
                "raw": raw_text,
            }

            total_usage["input_tokens"] += response["usage"]["input_tokens"]
            total_usage["output_tokens"] += response["usage"]["output_tokens"]
            logger.info("Cross-framework synthesis complete")

        except Exception as e:
            logger.warning(f"Synthesis call failed: {e}")
            synthesis = {"parsed": {}, "raw": str(e)}

    return {
        "frameworks": framework_results,
        "synthesis": synthesis,
        "total_usage": total_usage,
    }


def _parse_json_response(text: str) -> dict:
    """Parse Claude's JSON response, handling potential markdown fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude response as JSON: {e}\nResponse: {text[:500]}")


_NO_EVIDENCE_PHRASES = {"", "no relevant language found"}


def _flag_unsupported_compliant_items(assessments: list[dict]) -> list[dict]:
    """Flag a "compliant" verdict backed by no evidence quote instead of trusting it outright.

    Doesn't change compliance_status — scoring.py owns that mapping — just
    marks needs_review so the item surfaces for a human look.
    """
    for item in assessments:
        quote = (item.get("evidence_quote") or "").strip().lower()
        if item.get("compliance_status") == "compliant" and quote in _NO_EVIDENCE_PHRASES:
            item["needs_review"] = True
    return assessments
