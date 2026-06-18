"""
Claude API integration for gap analysis.

Supports:
- Single-framework (DPDPA legacy path) and multi-framework analysis
- Prompt caching for system prompts (~90% cost reduction per framework)
- Two/three-call architecture: evidence extraction → per-framework analysis → synthesis
- Structured context assembly with risk profile
"""

import json
import logging
import re

import anthropic

from app.config import settings
from app.dpdpa.prompts import (
    build_evidence_extraction_prompt,
    build_system_prompt,
    build_user_prompt,
)

logger = logging.getLogger(__name__)


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
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
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
            evidence = _run_evidence_extraction(client, truncated_docs, desk_review_findings)

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

    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=16384,
        temperature=0,
        system=system_blocks,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text
    parsed = _parse_json_response(raw_text)

    # Log cache stats
    usage = message.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_create = getattr(usage, "cache_creation_input_tokens", 0)
    logger.info(
        f"Gap analysis tokens — input: {usage.input_tokens}, "
        f"output: {usage.output_tokens}, "
        f"cache_read: {cache_read}, cache_create: {cache_create}"
    )

    return {
        "parsed": parsed,
        "raw": raw_text,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
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


def _run_evidence_extraction(
    client: anthropic.Anthropic,
    documents: list[dict],
    desk_review_findings: list[dict] | None = None,
) -> dict | None:
    """
    Call 1: Extract evidence quotes from documents for each requirement.

    Returns a dict mapping requirement_id → list of quoted text.
    """
    prompt = build_evidence_extraction_prompt(documents, desk_review_findings)

    try:
        message = client.messages.create(
            model=settings.claude_model,
            max_tokens=8192,
            temperature=0,
            system="You are a document analyst. Extract exact quotes from documents that are relevant to each compliance requirement. Be precise and quote verbatim.",
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text
        parsed = _parse_json_response(raw)
        evidence = parsed.get("evidence", {})

        logger.info(f"Evidence extraction: found quotes for {len(evidence)} requirements")
        return evidence

    except Exception as e:
        logger.warning(f"Evidence extraction failed, falling back to single-call: {e}")
        return None


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
    from app.frameworks.prompts import (
        build_framework_system_prompt,
        build_framework_user_prompt,
        build_synthesis_prompt,
        build_synthesis_system_prompt,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    truncated_docs = _truncate_documents(documents)

    # Step 1: Evidence extraction (reuse desk review if available)
    evidence = None
    if truncated_docs:
        dr_evidence = _evidence_from_desk_review(desk_review_data)
        if dr_evidence:
            evidence = dr_evidence
            logger.info(f"Reusing desk review evidence ({len(dr_evidence)} requirements)")
        else:
            desk_review_findings = desk_review_data.get("findings") if desk_review_data else None
            evidence = _run_evidence_extraction(client, truncated_docs, desk_review_findings)

    # Step 2: Per-framework gap analysis
    framework_results: dict[str, dict] = {}
    total_usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}

    for fw_id in framework_ids:
        logger.info(f"Running gap analysis for framework: {fw_id}")
        try:
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
            with client.messages.stream(
                model=settings.claude_model,
                max_tokens=16384,
                temperature=0,
                system=system_blocks,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                raw_text = stream.get_final_text()
                message = stream.get_final_message()

            parsed = _parse_json_response(raw_text)

            usage = message.usage
            cache_read = getattr(usage, "cache_read_input_tokens", 0)
            cache_create = getattr(usage, "cache_creation_input_tokens", 0)

            framework_results[fw_id] = {
                "parsed": parsed,
                "raw": raw_text,
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cache_read_input_tokens": cache_read,
                    "cache_creation_input_tokens": cache_create,
                },
            }

            total_usage["input_tokens"] += usage.input_tokens
            total_usage["output_tokens"] += usage.output_tokens
            total_usage["cache_read_input_tokens"] += cache_read
            total_usage["cache_creation_input_tokens"] += cache_create

            logger.info(
                f"{fw_id} analysis complete — input: {usage.input_tokens}, "
                f"output: {usage.output_tokens}, cache_read: {cache_read}"
            )

        except Exception as e:
            logger.error(f"Gap analysis failed for {fw_id}: {e}")
            framework_results[fw_id] = {
                "parsed": {"executive_summary": f"Analysis failed: {e}", "assessments": []},
                "raw": str(e),
                "usage": {},
                "error": str(e),
            }

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

            with client.messages.stream(
                model=settings.claude_model,
                max_tokens=4096,
                temperature=0,
                system=synthesis_system,
                messages=[{"role": "user", "content": synthesis_prompt}],
            ) as stream:
                raw_text = stream.get_final_text()
                message = stream.get_final_message()

            synthesis = {
                "parsed": _parse_json_response(raw_text),
                "raw": raw_text,
            }

            total_usage["input_tokens"] += message.usage.input_tokens
            total_usage["output_tokens"] += message.usage.output_tokens
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
