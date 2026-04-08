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
   - "compliant": Clear, specific, verifiable evidence of full implementation with documented processes — not just a policy statement. Requires proof of OPERATIONAL implementation (procedures, system configs, training records, audit logs).
   - "partially_compliant": Substantial evidence of active implementation WITH specific bounded gaps. Requires BOTH: (a) concrete evidence of operational implementation beyond just a policy document, AND (b) gaps that are clearly bounded and remediable. If the only evidence is a policy document with no proof of operational follow-through, this is non_compliant.
   - "non_compliant": Any of: no evidence, only boilerplate/template policy language, GDPR/CCPA copy-paste without DPDPA adaptation, evidence of intent without implementation, or practices that contradict compliance (e.g., "retain everything" data practices, coerced consent).
   - "not_assessed": Insufficient information to determine — use ONLY when the requirement genuinely cannot be evaluated from available data. Do NOT use as a soft alternative to non_compliant.

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
- Assign exactly one root_cause_category per gap — this drives initiative clustering

## Skepticism Guidelines — READ BEFORE ASSESSING

1. **Policy != Implementation.** A written policy is necessary but NOT sufficient for "compliant" or "partially_compliant". Look for evidence of OPERATIONAL implementation: procedures actually followed, system configurations, training records, audit logs, or specific operational details that go beyond policy statements. A generic policy with no proof of follow-through is non_compliant.

2. **Template detection.** If a policy uses generic boilerplate language, references GDPR concepts (legitimate interest, right to be forgotten, data subject, DPO with EU scope), CCPA concepts (Do Not Sell, California-specific rights), or contains copy-paste from another framework without DPDPA-specific adaptation, this is a RED FLAG. Score as non_compliant unless there is ALSO strong DPDPA-specific operational evidence alongside the template language.

3. **Data minimization rigor.** "We collect only necessary data" without a documented data inventory, per-category retention schedules with specific timeframes, and active deletion procedures is non_compliant. "Retain everything" or indefinite retention defaults are explicitly non_compliant for all CH2.MINIMIZE requirements. A single blanket retention period for all data categories (suggesting no purpose-based analysis) is non_compliant.

4. **Burden of proof is on the organization.** Absence of evidence is evidence of absence. Do not infer compliance from silence or vague statements. If a requirement is not addressed in documents or questionnaire responses, it is non_compliant, not partially_compliant. "We plan to implement" or "this is in progress" without evidence of concrete steps taken is non_compliant.

5. **Cross-reference desk review signals.** If the desk review found a red flag (GDPR copy-paste, template artifacts, buried consent) for a requirement, that requirement starts with a presumption of non_compliant. This presumption can only be overcome by strong, specific countervailing evidence of DPDPA-compliant implementation.

6. **Questionnaire answer skepticism.** Self-reported "fully_implemented" answers with no supporting document evidence should be treated as partially_compliant at best. Look for corroboration between what the organization claims (questionnaire) and what their documents actually show.

## Data Minimization Assessment (CH2.MINIMIZE requirements)

When assessing data minimization requirements, explicitly check for:
- Does the organization have a documented data inventory/map listing what data is collected and for what purpose? If not, CH2.MINIMIZE.1 is non_compliant.
- Are retention periods specified PER DATA CATEGORY with legal justification for each? If a single blanket period or no periods documented, CH2.MINIMIZE.3 is non_compliant.
- Is there an active, documented deletion mechanism (automated or procedural) — not just a policy statement about deletion? If not, CH2.MINIMIZE.2 is non_compliant.
- "Retain data as long as necessary" or "as required by law" without specific timeframes per data category = non_compliant."""

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

### Level 4 — Signal Detection (CRITICAL — be aggressive, flag EVERY instance)

Flag every instance of the following. Do not give benefit of the doubt:

**GDPR copy-paste indicators** (flag_type: "gdpr_copy_paste"):
- "legitimate interest" or "legitimate interests" — DPDPA has NO legitimate interest basis for processing
- "right to be forgotten" — DPDPA uses "right to erasure" with different scope and conditions
- "data subject" instead of "data principal"
- "data controller" instead of "data fiduciary"
- "data processor" used in GDPR context rather than DPDPA "data processor" context
- "supervisory authority" instead of "Data Protection Board of India"
- Any references to EU GDPR, CCPA, LGPD, PIPEDA, or other non-Indian privacy laws as the governing framework
- "DPO" with references to EU establishment, EU data subject scope, or Article 37-39 GDPR

**Template/boilerplate artifacts** (flag_type: "template_artifact"):
- Placeholder text: "[Company Name]", "[Insert Date]", "[Your Company]", "XYZ Corp", "[Organization]"
- Generic industry references that don't match the actual organization's industry
- Identical language appearing in multiple unrelated sections (copy-paste within document)
- Policy effective dates that are suspiciously recent relative to organization age or in the future
- References to compliance frameworks the organization is unlikely to follow given their size/industry
- Boilerplate privacy policy language found verbatim on template websites

**CCPA-specific artifacts** (flag_type: "ccpa_copy_paste"):
- "Do Not Sell My Personal Information" or "Do Not Sell or Share"
- "California Consumer Privacy Act" or "CCPA" or "CPRA"
- "Shine the Light law"
- "Categories of personal information collected" in CCPA's specific format/categorization
- Opt-out language specific to sale of data (DPDPA uses consent-based model, not opt-out)

**Buried consent** (flag_type: "buried_consent"):
- Consent language hidden in lengthy Terms & Conditions instead of clear, specific, informed notice
- Bundled consent where data processing consent is mixed with service T&C acceptance
- Pre-checked consent boxes or consent-by-default patterns

**Missing DPDPA-specific timelines** (flag_type: "missing_timeline"):
- No 72-hour breach notification timeline per Section 8(6)
- No reasonable timeframe for data principal rights responses
- Vague language like "as soon as possible" or "without undue delay" without specific timeframes

**Scope gaps** (flag_type: "scope_gap"):
- Policy covers some data types but ignores others the organization likely processes given their industry
- Employee data processing not addressed despite organization having employees
- Children's data processing not addressed for organizations in relevant sectors (ed-tech, gaming, social media)

## Special Focus: Data Minimization (CH2.MINIMIZE.1, CH2.MINIMIZE.2, CH2.MINIMIZE.3)

These requirements are frequently under-detected. Apply heightened scrutiny:

**CH2.MINIMIZE.1 (Collection Limitation):**
- Look for: specific data elements listed per purpose, data mapping/inventory, explicit justification for each data category collected
- Red flag if: only general statements like "we collect only necessary data" without specifics, or no data inventory at all

**CH2.MINIMIZE.2 (Purpose-Based Erasure):**
- Look for: automatic deletion triggers, purpose expiry tracking, active erasure processes with documented procedures
- Red flag if: no deletion mechanism described, or "data may be retained for legal purposes" without specifying WHICH data or WHICH legal requirement, or no documented erasure procedure

**CH2.MINIMIZE.3 (Retention Schedules):**
- Look for: per-category retention periods with specific legal justification, systematic deletion procedures, retention review cadence
- Red flag if: single blanket retention period for all data categories (suggests no purpose-based analysis), indefinite retention, no documented deletion procedure, retention period > 7 years without specific legal mandate

**Data minimization red flags** (flag_type: "data_minimization_concern"):
- "Retain everything" or "retain all data" language
- Indefinite retention periods or no stated end date
- Absence of data inventory or data mapping
- No documented deletion procedures
- Retention schedules that retain ALL data categories for the SAME duration (no purpose-based differentiation)
- "As long as necessary" or "as required by applicable law" without specific timeframes per data category

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
    applicable_requirements: list[str] | None = None,
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

    # Scope filter — tell Claude which requirements are not applicable
    if applicable_requirements is not None:
        from app.dpdpa.framework import get_all_requirements
        all_ids = {r["id"] for r in get_all_requirements()}
        excluded_ids = sorted(all_ids - set(applicable_requirements))
        if excluded_ids:
            prompt += "## Scope — Requirements Excluded from This Assessment\n"
            prompt += "The following requirements are NOT applicable to this organisation based on their scope answers. "
            prompt += "Set compliance_status to 'not_applicable' for all of these — do not assess them:\n"
            for rid in excluded_ids:
                prompt += f"- {rid}\n"
            prompt += "\n"

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
