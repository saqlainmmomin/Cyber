"""
RFI (Request for Information) Generator — produces a formal evidence request
document from gap analysis results and desk review findings.

The RFI is structured as a professional document that can be sent directly to
the assessed organization requesting specific evidence for compliance gaps.

Structure:
  - Header (client name, date, assessment reference)
  - Introduction (purpose, DPDPA context)
  - Evidence Items (grouped by DPDPA chapter):
      Item ID, Description, DPDPA Requirement Reference,
      Priority, Current Status, Suggested Deadline
  - Response Instructions
  - Appendix: DPDPA requirement summary
"""

import json
import logging
from datetime import datetime, timezone, timedelta

import anthropic

from app.config import settings
from app.dpdpa.framework import get_all_requirements

logger = logging.getLogger(__name__)

# Requirement lookup
_REQ_TITLES = {r["id"]: r["title"] for r in get_all_requirements()}
_REQ_SECTIONS = {r["id"]: r["section_ref"] for r in get_all_requirements()}
_REQ_CHAPTERS = {r["id"]: r["chapter_title"] for r in get_all_requirements()}


def generate_rfi(
    assessment_id: str,
    company_name: str,
    industry: str,
    gap_items: list[dict],
    desk_review_absences: list[dict] | None = None,
    desk_review_signals: list[dict] | None = None,
) -> dict:
    """
    Generate an RFI document from gap analysis results.

    Returns a dict with:
      title, introduction, evidence_items (list), response_instructions, appendix,
      total_items, critical_items, raw_ai_response
    """
    # Build evidence request items from gaps (non-compliant and partially compliant)
    evidence_items = _build_evidence_items(gap_items, desk_review_absences, desk_review_signals)

    if not evidence_items:
        return {
            "title": f"DPDPA Compliance — Request for Information: {company_name}",
            "introduction": "No evidence gaps identified. The assessed organization appears to have adequate documentation.",
            "evidence_items": [],
            "response_instructions": "",
            "appendix": "",
            "total_items": 0,
            "critical_items": 0,
            "raw_ai_response": None,
        }

    # Use Claude to generate professional prose for introduction and item descriptions
    raw_response = _call_claude_rfi(company_name, industry, evidence_items)

    # Merge Claude-enhanced descriptions back into items
    enhanced = _merge_claude_enhancements(evidence_items, raw_response)

    critical_count = sum(1 for item in enhanced["items"] if item["priority"] == "Critical")
    today = datetime.now(timezone.utc).strftime("%d %B %Y")

    return {
        "title": f"DPDPA Compliance — Request for Information: {company_name}",
        "introduction": enhanced.get("introduction", _default_introduction(company_name, today)),
        "evidence_items": enhanced["items"],
        "response_instructions": enhanced.get("response_instructions", _default_response_instructions(today)),
        "appendix": enhanced.get("appendix", ""),
        "total_items": len(enhanced["items"]),
        "critical_items": critical_count,
        "raw_ai_response": raw_response.get("_raw", ""),
    }


def _build_evidence_items(
    gap_items: list[dict],
    absences: list[dict] | None,
    signals: list[dict] | None,
) -> list[dict]:
    """Build structured evidence request items from gaps and desk review findings."""
    items = []
    seen_reqs = set()

    # From gap items — non-compliant and partially compliant
    for gap in gap_items:
        status = gap.get("compliance_status", "")
        if status in ("compliant", "not_assessed"):
            continue

        req_id = gap["requirement_id"]
        seen_reqs.add(req_id)

        priority = _compute_priority(gap)
        deadline_weeks = _compute_deadline(priority)

        items.append({
            "item_id": f"RFI-{len(items) + 1:03d}",
            "requirement_id": req_id,
            "requirement_title": gap.get("requirement_title", _REQ_TITLES.get(req_id, req_id)),
            "dpdpa_section": _REQ_SECTIONS.get(req_id, ""),
            "chapter": gap.get("chapter", _REQ_CHAPTERS.get(req_id, "")),
            "priority": priority,
            "current_status": _describe_current_status(gap),
            "gap_description": gap.get("gap_description", ""),
            "remediation_action": gap.get("remediation_action", ""),
            "evidence_requested": "",  # Claude will fill this
            "deadline_weeks": deadline_weeks,
            "evidence_quote": gap.get("evidence_quote"),
        })

    # From desk review absences — requirements with no document evidence
    if absences:
        for absence in absences:
            req_id = absence.get("requirement_id")
            if not req_id or req_id in seen_reqs:
                continue
            seen_reqs.add(req_id)

            items.append({
                "item_id": f"RFI-{len(items) + 1:03d}",
                "requirement_id": req_id,
                "requirement_title": _REQ_TITLES.get(req_id, req_id),
                "dpdpa_section": _REQ_SECTIONS.get(req_id, ""),
                "chapter": _REQ_CHAPTERS.get(req_id, ""),
                "priority": "Medium",
                "current_status": "No evidence found in submitted documents",
                "gap_description": absence.get("content", ""),
                "remediation_action": "",
                "evidence_requested": "",
                "deadline_weeks": 4,
                "evidence_quote": None,
            })

    return items


def _compute_priority(gap: dict) -> str:
    """Determine RFI item priority from gap data."""
    risk = gap.get("risk_level", "medium")
    status = gap.get("compliance_status", "")

    if risk == "critical" or (status == "non_compliant" and gap.get("remediation_priority", 5) <= 1):
        return "Critical"
    if risk == "high" or status == "non_compliant":
        return "High"
    if status == "partially_compliant":
        return "Medium"
    return "Low"


def _compute_deadline(priority: str) -> int:
    """Suggested response deadline in weeks based on priority."""
    return {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}.get(priority, 3)


def _describe_current_status(gap: dict) -> str:
    """Build a human-readable current status description."""
    status = gap.get("compliance_status", "unknown")
    current = gap.get("current_state", "")

    if status == "non_compliant":
        prefix = "Not implemented"
    elif status == "partially_compliant":
        prefix = "Partially addressed"
    else:
        prefix = status.replace("_", " ").title()

    if current:
        return f"{prefix} — {current[:200]}"
    return prefix


def _call_claude_rfi(company_name: str, industry: str, items: list[dict]) -> dict:
    """Call Claude to generate professional RFI prose."""
    items_summary = []
    for item in items:
        items_summary.append({
            "item_id": item["item_id"],
            "requirement_id": item["requirement_id"],
            "requirement_title": item["requirement_title"],
            "dpdpa_section": item["dpdpa_section"],
            "priority": item["priority"],
            "current_status": item["current_status"],
            "gap_description": item["gap_description"],
        })

    prompt = f"""Generate a professional Request for Information (RFI) document for DPDPA compliance.

## Context
- **Organization:** {company_name}
- **Industry:** {industry}
- **Total evidence items:** {len(items)}
- **Critical items:** {sum(1 for i in items if i['priority'] == 'Critical')}

## Evidence Items Requiring Documentation
{json.dumps(items_summary, indent=2)}

## Task
Generate JSON with these fields:

1. **introduction**: A professional 2-3 paragraph introduction explaining:
   - This RFI is part of a DPDPA compliance gap assessment
   - The organization needs to provide evidence for the listed items
   - Urgency based on critical/high items found
   - Do NOT include dates or deadlines in the introduction

2. **items**: For each item_id, provide an "evidence_requested" field — a specific, actionable description of what evidence the organization should provide. Be concrete: name specific document types, screenshots, policy excerpts, system configurations, etc.

3. **response_instructions**: Professional instructions for how to respond (format, submission, contact info placeholder, timelines)

Return ONLY valid JSON:
{{"introduction": "...", "items": [{{"item_id": "RFI-001", "evidence_requested": "..."}}], "response_instructions": "..."}}
"""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        temperature=0.2,
        system=(
            "You are a senior DPDPA compliance consultant drafting a formal Request for Information. "
            "Write in a professional, authoritative tone suitable for sending directly to a client organization. "
            "Be specific about what evidence is needed — vague requests waste everyone's time. "
            "Respond ONLY with valid JSON. No markdown fences."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        parsed["_raw"] = raw
        return parsed
    except json.JSONDecodeError:
        logger.warning("Failed to parse Claude RFI response")
        return {"_raw": raw, "items": [], "introduction": "", "response_instructions": ""}


def _merge_claude_enhancements(base_items: list[dict], claude_response: dict) -> dict:
    """Merge Claude-generated evidence descriptions into base items."""
    # Build lookup by item_id
    claude_items = {ci["item_id"]: ci for ci in claude_response.get("items", []) if isinstance(ci, dict)}

    for item in base_items:
        claude_item = claude_items.get(item["item_id"], {})
        if claude_item.get("evidence_requested"):
            item["evidence_requested"] = claude_item["evidence_requested"]
        elif not item["evidence_requested"]:
            item["evidence_requested"] = f"Please provide documentation demonstrating compliance with {item['requirement_title']} ({item['dpdpa_section']})."

    return {
        "items": base_items,
        "introduction": claude_response.get("introduction", ""),
        "response_instructions": claude_response.get("response_instructions", ""),
        "appendix": claude_response.get("appendix", ""),
    }


def _default_introduction(company_name: str, date: str) -> str:
    return (
        f"This Request for Information (RFI) has been prepared as part of the Digital Personal Data Protection Act, 2023 (DPDPA) "
        f"compliance gap assessment for {company_name}. The assessment has identified areas where additional evidence "
        f"is required to confirm compliance status. Please provide the requested documentation at your earliest convenience."
    )


def _default_response_instructions(date: str) -> str:
    return (
        "Please respond to each evidence item by providing the requested documentation. "
        "For each item, clearly reference the RFI Item ID (e.g., RFI-001) in your response. "
        "Documents may be submitted in PDF, DOCX, or image format. "
        "If an item is not applicable to your organization, please provide a written justification."
    )
