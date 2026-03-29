"""
Claude prompt templates for DPDPA gap analysis.

Supports two-call architecture:
  Call 1 — Evidence extraction (quote-first grounding)
  Call 2 — Gap analysis using extracted evidence
"""

from app.dpdpa.framework import DPDPA_FRAMEWORK, get_all_requirements


def _build_requirements_text() -> str:
    """Build the DPDPA requirements reference text used in system prompts."""
    req_lines = []
    for req in get_all_requirements():
        req_lines.append(
            f"- **{req['id']}** | {req['title']} | {req['section_ref']} | Criticality: {req['criticality']}\n"
            f"  {req['description']}"
        )
    return "\n".join(req_lines)


# ─── System Prompts (cacheable) ─────────────────────────────────────────────

ANALYST_PERSONA = """You are an expert DPDPA (Digital Personal Data Protection Act, 2023, India) compliance assessor with deep knowledge of Indian data protection law, ISO 27001, ISO 27701, and global privacy frameworks."""


def build_system_prompt() -> list[dict]:
    """
    Build the system prompt as a list of content blocks for prompt caching.

    Returns a list of dicts suitable for the `system` parameter of messages.create().
    The last stable block (requirements framework) gets cache_control.
    """
    requirements_text = _build_requirements_text()
    req_count = len(get_all_requirements())

    assessment_instructions = f"""Your task is to assess an organization's compliance with the DPDPA based on their questionnaire responses, supporting documents, and organizational context.

## DPDPA Requirements Framework

{requirements_text}

## Assessment Instructions

For EACH requirement above, you must assess the organization and provide:

1. **compliance_status**: One of "compliant", "partially_compliant", "non_compliant", or "not_assessed"
   - "compliant": Clear evidence of full implementation
   - "partially_compliant": Some evidence but gaps remain
   - "non_compliant": No evidence or explicitly not implemented
   - "not_assessed": Insufficient information to determine (use sparingly)

2. **current_state**: What the organization currently does regarding this requirement (1-2 sentences). Base this on their questionnaire answers and document evidence.

3. **gap_description**: What is missing or insufficient. If compliant, state "No gap identified." (1-2 sentences)

4. **risk_level**: "critical", "high", "medium", or "low" — based on the requirement's criticality and the severity of the gap

5. **remediation_action**: Specific, actionable step to close the gap. Tailor to the organization's industry and size. (1-3 sentences)

6. **remediation_priority**: 1 (immediate, 0-4 weeks), 2 (short-term, 1-3 months), 3 (medium-term, 3-6 months), 4 (long-term, 6-12 months)

7. **remediation_effort**: "low", "medium", or "high"

8. **timeline_weeks**: Estimated weeks to remediate

9. **maturity_level**: 0-5 CMMI-aligned maturity score:
   - 0: Non-existent — control entirely absent
   - 1: Initial — ad-hoc, depends on individuals
   - 2: Managed — documented but inconsistently applied
   - 3: Defined — standardized, consistent, auditable
   - 4: Quantitative — KPIs tracked, deviations alerted
   - 5: Optimizing — continuous improvement embedded

10. **root_cause_category**: Exactly one of: "policy", "people", "process", "technology", "governance"

11. **evidence_quote**: The exact text from the organization's documents that supports your assessment, or "No relevant language found" if no evidence exists.

## Output Format

Respond ONLY with valid JSON matching this exact schema. No markdown, no commentary, no code fences.

{{{{
  "executive_summary": "A 3-5 sentence executive summary of the organization's overall DPDPA compliance posture, key strengths, and critical gaps.",
  "assessments": [
    {{{{
      "requirement_id": "CH2.CONSENT.1",
      "compliance_status": "partially_compliant",
      "current_state": "...",
      "gap_description": "...",
      "risk_level": "high",
      "remediation_action": "...",
      "remediation_priority": 1,
      "remediation_effort": "medium",
      "timeline_weeks": 6,
      "maturity_level": 2,
      "root_cause_category": "process",
      "evidence_quote": "..."
    }}}}
  ]
}}}}

The "assessments" array must contain exactly one entry for every requirement ID listed above ({req_count} total). Do not skip any.

## Important Guidelines

- Before assessing each requirement, quote the exact policy language from documents or state "No relevant language found"
- Be specific and practical in remediation advice — tailor to the organization's industry and size
- For "not_applicable" questionnaire answers, assess whether not_applicable is genuinely appropriate given the organization's profile
- Cross-reference document evidence with questionnaire answers — flag inconsistencies
- Consider the organization's industry context when assessing risk levels
- Remediation actions should be implementable, not generic compliance advice
- Assign maturity_level based on observed practices, not aspirational state
- Assign exactly one root_cause_category per gap — this drives initiative clustering"""

    return [
        {"type": "text", "text": ANALYST_PERSONA},
        {
            "type": "text",
            "text": assessment_instructions,
            "cache_control": {"type": "ephemeral"},
        },
    ]


def build_system_prompt_text() -> str:
    """Build system prompt as plain text (backward-compatible for single-call mode)."""
    blocks = build_system_prompt()
    return "\n\n".join(b["text"] for b in blocks)


# ─── Evidence Extraction Prompt (Call 1) ────────────────────────────────────

def build_evidence_extraction_prompt(documents: list[dict]) -> str:
    """Build prompt for Call 1: extracting evidence quotes from documents."""
    requirements_text = _build_requirements_text()

    docs_text = ""
    if documents:
        for doc in documents:
            docs_text += f"\n### Document: {doc['filename']} (Category: {doc['category']})\n\n"
            docs_text += doc["text"] + "\n\n"
    else:
        docs_text = "\n_No supporting documents provided._\n"

    return f"""## Task: Evidence Extraction

For each DPDPA requirement below, find and quote the EXACT language from the organization's documents that is relevant to that requirement. If no relevant language exists, state "No relevant language found."

## Requirements
{requirements_text}

## Organization Documents
{docs_text}

## Output Format

Respond ONLY with valid JSON. For each requirement, provide the evidence quotes:

{{{{
  "evidence": {{{{
    "CH2.CONSENT.1": ["Exact quoted text from document...", "Another relevant quote..."],
    "CH2.CONSENT.2": ["No relevant language found"]
  }}}}
}}}}

Include ALL requirement IDs. Quote verbatim — do not paraphrase."""


# ─── Risk Profile Prompt (for context_profiler.py) ─────────────────────────

def build_risk_profile_system_prompt() -> str:
    """System prompt for the lightweight risk profiling call."""
    return (
        "You are an expert DPDPA compliance advisor. Given an organization's context, "
        "produce a risk profile that will guide an adaptive compliance assessment. "
        "Respond ONLY with valid JSON matching the requested schema. No markdown, no commentary."
    )


# ─── User Prompt ────────────────────────────────────────────────────────────

def build_user_prompt(
    company_name: str,
    industry: str,
    company_size: str,
    description: str | None,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None = None,
    evidence: dict | None = None,
) -> str:
    """
    Build the user prompt with organization context, responses, and documents.

    If context_profile is provided, includes structured risk context header.
    If evidence is provided (from Call 1), includes extracted evidence quotes.
    """
    size_labels = {
        "startup": "Startup (<50 employees)",
        "sme": "SME (50-500 employees)",
        "large": "Large (500-5000 employees)",
        "enterprise": "Enterprise (5000+ employees)",
    }

    # Organization profile
    prompt = f"""## Organization Profile
- **Company:** {company_name}
- **Industry:** {industry}
- **Size:** {size_labels.get(company_size, company_size)}
- **Description:** {description or 'Not provided'}

"""

    # Context profile header (from Phase 1)
    if context_profile:
        prompt += f"""## Risk Profile (from organizational context assessment)
- **Risk Tier:** {context_profile.get('risk_tier', 'MEDIUM')}
- **Priority Chapters:** {', '.join(context_profile.get('priority_chapters', []))}
- **SDF Candidate:** {context_profile.get('sdf_candidate', False)}
- **Cross-Border Transfers:** {context_profile.get('cross_border_transfers', False)}
- **Children's Data:** {context_profile.get('processes_children_data', False)}
- **Industry Context:** {context_profile.get('industry_context', '')}
- **Timeline Pressure:** {context_profile.get('timeline_pressure', 'MEDIUM')}
- **Focus Areas:** {context_profile.get('framing_notes', '')}

"""

    # Questionnaire responses (grouped by chapter if context available)
    prompt += "## Questionnaire Responses\n\n"
    if responses:
        for r in responses:
            notes_str = f" — Notes: {r['notes']}" if r.get("notes") else ""
            confidence_str = f" [Confidence: {r['confidence']}]" if r.get("confidence") else ""
            prompt += f"- **{r['question_id']}**: {r['answer']}{notes_str}{confidence_str}\n"
    else:
        prompt += "_No questionnaire responses submitted._\n"

    prompt += "\n"

    # Evidence from Call 1 (if available)
    if evidence:
        prompt += "## Extracted Document Evidence\n\n"
        for req_id, quotes in evidence.items():
            prompt += f"### {req_id}\n"
            for quote in quotes:
                prompt += f"> {quote}\n"
            prompt += "\n"
    else:
        # Include raw documents
        prompt += "## Supporting Documents\n\n"
        if documents:
            for doc in documents:
                prompt += f"### Document: {doc['filename']} (Category: {doc['category']})\n\n"
                prompt += doc["text"] + "\n\n"
        else:
            prompt += "_No supporting documents uploaded._\n"

    prompt += "\n---\n\nPlease assess this organization against all DPDPA requirements and provide the structured JSON output."

    return prompt
