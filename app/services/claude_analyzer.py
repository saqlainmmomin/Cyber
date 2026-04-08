"""
Claude API integration for DPDPA gap analysis.

Supports:
- Prompt caching for system prompt (~90% cost reduction on repeated calls)
- Two-call architecture: evidence extraction → gap analysis
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
