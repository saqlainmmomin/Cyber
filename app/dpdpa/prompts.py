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

def build_evidence_extraction_prompt(
    documents: list[dict],
    desk_review_findings: list[dict] | None = None,
) -> str:
    """Build prompt for Call 1: extracting evidence quotes from documents.

    If desk_review_findings are provided, includes them as context to focus
    the evidence extraction on areas where the desk review found gaps or signals.
    """
    requirements_text = _build_requirements_text()

    docs_text = ""
    if documents:
        for doc in documents:
            docs_text += f"\n### Document: {doc['filename']} (Category: {doc['category']})\n\n"
            docs_text += doc["text"] + "\n\n"
    else:
        docs_text = "\n_No supporting documents provided._\n"

    desk_review_context = ""
    if desk_review_findings:
        desk_review_context = "\n## Desk Review Context (from prior document analysis)\n\n"
        desk_review_context += "The following findings were identified during desk review. Pay special attention to these areas:\n\n"
        for f in desk_review_findings:
            prefix = {"evidence": "Evidence", "absence": "Gap", "signal": "Red Flag"}.get(f["type"], "Finding")
            desk_review_context += f"- **{prefix}** ({f.get('requirement_id', 'general')}): {f['content']}\n"
        desk_review_context += "\n"

    return f"""## Task: Evidence Extraction

For each DPDPA requirement below, find and quote the EXACT language from the organization's documents that is relevant to that requirement. If no relevant language exists, state "No relevant language found."
{desk_review_context}
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

# ─── Desk Review Prompt (Call 0) ──────────────────────────────────────────

def build_desk_review_system_prompt() -> list[dict]:
    """
    Build the system prompt for Call 0: desk review analysis.

    Shares the same requirements framework text (and prompt cache) as Calls 1+2.
    """
    requirements_text = _build_requirements_text()
    req_count = len(get_all_requirements())

    instructions = f"""You are a compliance document analyst specializing in India's Digital Personal Data Protection Act (DPDPA), 2023.

## Your Task

Analyze the uploaded documents BEFORE the questionnaire begins. You are performing a desk review — the first step of a professional compliance audit. Your goal is to catalog what exists, map evidence to requirements, identify what's missing, and flag red flags.

## DPDPA Requirements Framework

{requirements_text}

## Analysis Levels

Perform ALL four analysis levels for each document:

### Level 1 — Document Catalog
For each document, identify:
- Document type (privacy policy, consent form, breach procedure, etc.)
- Which DPDPA chapters/requirements it covers
- A 1-2 sentence summary of what it contains

### Level 2 — Evidence Mapping
For each DPDPA requirement ({req_count} total), extract EXACT quotes from the documents that address that requirement. Include the document filename and approximate location (section heading, page, paragraph).

### Level 3 — Absence Detection
For each DPDPA requirement, identify what is MISSING from the documents. Be specific:
- NOT "lacks consent mechanism" but "no mention of consent withdrawal process per Section 6(6)"
- NOT "missing breach notification" but "no 72-hour notification timeline specified per Section 8(6)"

### Level 4 — Signal Detection
Catch red flags that reveal deeper compliance issues:
- **GDPR copy-paste**: References to "legitimate interest", "right to be forgotten", "DPO" (DPDPA uses "Data Protection Officer" but different scope), EU-specific terminology
- **Buried consent**: Consent language hidden in lengthy T&C instead of being "clear, specific, and informed"
- **Missing DPDPA-specific timelines**: No 72-hour breach notification, no reasonable timeframe for data principal rights
- **Template artifacts**: Generic/boilerplate language not customized to the organization
- **Inconsistent terminology**: Mixing "data subject" (GDPR) with "data principal" (DPDPA), or "data controller" with "data fiduciary"
- **Scope gaps**: Policy covers some data types but ignores others the organization likely processes

## Output Format

Respond ONLY with valid JSON. No markdown fences, no commentary.

{{{{
  "document_catalog": [
    {{{{
      "filename": "privacy_policy.pdf",
      "document_type": "Privacy Policy",
      "coverage_areas": ["CH2.CONSENT", "CH3.ACCESS"],
      "summary": "Corporate privacy policy covering..."
    }}}}
  ],
  "evidence_map": {{{{
    "CH2.CONSENT.1": [
      {{{{
        "quote": "Exact quoted text from document...",
        "document": "privacy_policy.pdf",
        "location": "Section 3, paragraph 2"
      }}}}
    ]
  }}}},
  "absence_findings": [
    {{{{
      "requirement_id": "CH2.CONSENT.3",
      "description": "No consent withdrawal mechanism described. Section 6(6) requires...",
      "severity": "high",
      "affected_documents": ["privacy_policy.pdf"]
    }}}}
  ],
  "signal_flags": [
    {{{{
      "flag_type": "gdpr_copy_paste",
      "description": "Privacy policy references 'legitimate interest' — a GDPR concept not present in DPDPA",
      "severity": "high",
      "source_quote": "We process data based on legitimate interest...",
      "document": "privacy_policy.pdf",
      "location": "Section 2",
      "requirement_ids": ["CH2.CONSENT.1"]
    }}}}
  ],
  "coverage_summary": {{{{
    "CH2.CONSENT.1": "adequate",
    "CH2.CONSENT.2": "partial",
    "CH2.CONSENT.3": "absent",
    "CH3.ACCESS.1": "not_covered"
  }}}}
}}}}

Coverage levels: "adequate" (requirement well-addressed), "partial" (some mention but gaps), "absent" (explicitly missing despite relevant document), "not_covered" (no relevant document uploaded).

Include ALL {req_count} requirement IDs in coverage_summary. Be thorough and precise."""

    return [
        {"type": "text", "text": "You are a compliance document analyst specializing in India's DPDPA 2023."},
        {
            "type": "text",
            "text": instructions,
            "cache_control": {"type": "ephemeral"},
        },
    ]


def build_desk_review_user_prompt(documents: list[dict], company_name: str, industry: str) -> str:
    """Build the user prompt for Call 0 with document content."""
    prompt = f"""## Organization
- **Company:** {company_name}
- **Industry:** {industry}

## Documents for Review

"""
    for doc in documents:
        prompt += f"### {doc['filename']} (Category: {doc['category']})\n\n"
        prompt += doc["text"] + "\n\n---\n\n"

    prompt += "Analyze these documents and provide the structured desk review output."
    return prompt


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
    desk_review_summary: dict | None = None,
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

    # Desk review findings (from Call 0)
    if desk_review_summary:
        prompt += "## Desk Review Findings (pre-questionnaire document analysis)\n\n"
        if desk_review_summary.get("coverage_summary"):
            prompt += "### Coverage Summary\n"
            for req_id, level in desk_review_summary["coverage_summary"].items():
                prompt += f"- **{req_id}**: {level}\n"
            prompt += "\n"
        if desk_review_summary.get("signal_flags"):
            prompt += "### Red Flags Detected\n"
            for flag in desk_review_summary["signal_flags"]:
                prompt += f"- **{flag.get('severity', 'medium').upper()}**: {flag['content']}"
                if flag.get("requirement_id"):
                    prompt += f" (affects {flag['requirement_id']})"
                prompt += "\n"
            prompt += "\n"
        if desk_review_summary.get("absence_findings"):
            prompt += "### Missing Provisions\n"
            for absence in desk_review_summary["absence_findings"]:
                prompt += f"- **{absence.get('requirement_id', 'general')}**: {absence['content']}\n"
            prompt += "\n"

    # Questionnaire responses — separated into base, industry, and follow-up
    base_responses = []
    industry_responses = []
    followup_responses = []
    for r in responses:
        qid = r["question_id"]
        if qid.startswith("FU."):
            followup_responses.append(r)
        elif qid.startswith("IND."):
            industry_responses.append(r)
        else:
            base_responses.append(r)

    prompt += "## Questionnaire Responses\n\n"
    if base_responses:
        for r in base_responses:
            notes_str = f" — Notes: {r['notes']}" if r.get("notes") else ""
            confidence_str = f" [Confidence: {r['confidence']}]" if r.get("confidence") else ""
            prompt += f"- **{r['question_id']}**: {r['answer']}{notes_str}{confidence_str}\n"
    else:
        prompt += "_No base questionnaire responses submitted._\n"

    if industry_responses:
        prompt += "\n### Industry-Specific Responses\n"
        for r in industry_responses:
            notes_str = f" — Notes: {r['notes']}" if r.get("notes") else ""
            prompt += f"- **{r['question_id']}**: {r['answer']}{notes_str}\n"

    if followup_responses:
        prompt += "\n### Follow-up Clarifications\n"
        prompt += "_These are auditor follow-up responses probing deeper into specific answers:_\n"
        for r in followup_responses:
            parent_note = f" (follow-up to {r['notes'].replace('Follow-up to ', '')})" if r.get("notes", "").startswith("Follow-up to") else ""
            prompt += f"- **{r['question_id']}**{parent_note}: {r['answer']}\n"

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
