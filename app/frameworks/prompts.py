"""
Multi-framework prompt factory.

Builds per-framework system and user prompts for Claude gap analysis.
Each framework gets its own cached system prompt (persona + controls + instructions).
"""

from __future__ import annotations

import re

from app.frameworks.registry import FrameworkRegistry
from app.frameworks.schema import FrameworkDefinition, RedFlagPattern
from app.services.desk_review_findings import LEGACY_FINDING_FRAMEWORK_ID


CURATED_PROMPT_FRAMEWORK_ID = "dpdpa"  # keeps its hand-curated desk-review and evidence-extraction prompts (P5-3 D-P5-3-A)
UNCLASSIFIED_FLAG_TYPE = "unclassified"


# ── Per-framework persona templates ───────────────────────────────────────

_FRAMEWORK_PERSONAS: dict[str, str] = {
    "dpdpa": (
        "You are an expert DPDPA (Digital Personal Data Protection Act, 2023, India) "
        "compliance assessor with deep knowledge of Indian data protection law, "
        "ISO 27001, ISO 27701, and global privacy frameworks."
    ),
    "iso27001": (
        "You are an expert ISO/IEC 27001:2022 auditor with deep knowledge of "
        "information security management systems, Annex A controls, risk assessment "
        "methodologies, and certification audit practices."
    ),
    "gdpr": (
        "You are an expert EU General Data Protection Regulation (GDPR) assessor "
        "with deep knowledge of EU data protection law, supervisory authority guidance, "
        "DPIAs, international transfer mechanisms, and the EDPB's interpretation of key provisions."
    ),
    "hipaa": (
        "You are an expert HIPAA compliance assessor with deep knowledge of the "
        "HIPAA Privacy Rule, Security Rule, Breach Notification Rule, and the HITECH Act. "
        "You understand covered entity and business associate obligations."
    ),
    "nist_csf": (
        "You are an expert cybersecurity framework assessor specializing in "
        "NIST Cybersecurity Framework 2.0. You understand the six functions "
        "(Govern, Identify, Protect, Detect, Respond, Recover), organizational profiling, "
        "and implementation tiers."
    ),
    "pci_dss": (
        "You are an expert PCI-DSS v4.0 Qualified Security Assessor (QSA) with deep "
        "knowledge of cardholder data environment scoping, network segmentation, "
        "cryptographic controls, and the 12 PCI requirements."
    ),
}

_DEFAULT_PERSONA = (
    "You are an expert compliance assessor with deep knowledge of regulatory "
    "frameworks, information security standards, and privacy law."
)


def _expand_cluster_responses(
    responses: list[dict],
    framework_id: str,
    fw_control_ids: set[str],
) -> list[dict]:
    """
    Expand cluster-ID-keyed responses to control-ID-keyed responses for a framework.

    Singleton clusters ("SINGLE.<control_id>"): strip prefix, include if control belongs
    to this framework. Real clusters ("CLUSTER_<N>"): look up in cluster mappings and
    include controls belonging to this framework. Legacy DPDPA IDs (no prefix): pass
    through unchanged if in fw_control_ids.
    """
    expanded = []
    cluster_defs: dict[str, dict] | None = None  # lazy-loaded

    for resp in responses:
        qid = resp.get("question_id", "")

        if qid.startswith("SINGLE."):
            control_id = qid[len("SINGLE."):]
            if control_id in fw_control_ids:
                expanded.append({**resp, "question_id": control_id})

        elif qid.startswith("CLUSTER_"):
            if cluster_defs is None:
                try:
                    from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
                    cluster_defs = {c["cluster_id"]: c for c in CONTROL_CLUSTERS}
                except (ImportError, KeyError):
                    cluster_defs = {}
            cdef = cluster_defs.get(qid)
            if cdef:
                for mc in cdef.get("controls", []):
                    if mc.get("framework") == framework_id and mc.get("control") in fw_control_ids:
                        expanded.append({**resp, "question_id": mc["control"]})

        else:
            # Legacy DPDPA control ID or direct control reference
            if qid in fw_control_ids:
                expanded.append(resp)

    return expanded


def _build_controls_text(fw: FrameworkDefinition) -> str:
    """Build the controls reference text for system prompts."""
    lines = []
    for ctrl_dict in fw.all_controls_enriched():
        lines.append(
            f"- **{ctrl_dict['id']}** | {ctrl_dict['title']} | "
            f"{ctrl_dict['section_ref']} | Criticality: {ctrl_dict['criticality']}\n"
            f"  {ctrl_dict['description']}"
        )
    return "\n".join(lines)


def _build_red_flag_section(fw: FrameworkDefinition) -> str:
    """Build skepticism guidelines from red flag patterns."""
    if not fw.red_flag_patterns:
        return ""

    lines = ["\n## Skepticism Guidelines\n"]
    for i, rf in enumerate(fw.red_flag_patterns, 1):
        lines.append(f"{i}. **{rf.pattern}** ({rf.severity} severity): {rf.description}")
    return "\n".join(lines)


def red_flag_key(pattern: RedFlagPattern) -> str:
    """Return the stable flag_type derived from a registry red-flag pattern."""
    return re.sub(r"[^a-z0-9]+", "_", pattern.pattern.lower()).strip("_")


def desk_review_flag_types(framework_id: str) -> tuple[str, ...]:
    """Return the flag_type values a desk review for this framework may store."""
    if framework_id == CURATED_PROMPT_FRAMEWORK_ID:
        from app.dpdpa.prompts import DESK_REVIEW_FLAG_TYPES

        return DESK_REVIEW_FLAG_TYPES
    return tuple(
        red_flag_key(pattern)
        for pattern in FrameworkRegistry.get(framework_id).red_flag_patterns
    )


def build_framework_desk_review_system_prompt(framework_id: str) -> list[dict]:
    """Build the registry-driven desk-review prompt for a non-curated framework."""
    fw = FrameworkRegistry.get(framework_id)
    persona = _FRAMEWORK_PERSONAS.get(framework_id, _DEFAULT_PERSONA)
    controls_text = _build_controls_text(fw)
    controls = fw.all_controls()
    n = fw.control_count()
    id0 = controls[0].id
    id1 = controls[1].id

    if fw.red_flag_patterns:
        signal_lines = [
            "Flag every instance of the following patterns. Use exactly the flag_type shown:",
            "",
        ]
        signal_lines.extend(
            f'- **{pattern.pattern}** (flag_type: "{red_flag_key(pattern)}", severity: {pattern.severity}): {pattern.description}'
            for pattern in fw.red_flag_patterns
        )
        signal_lines.extend(
            [
                "",
                "Use only the flag_type values listed above. Do not flag anything that fits none of them.",
            ]
        )
        signal_block = "\n".join(signal_lines)
        first_key = red_flag_key(fw.red_flag_patterns[0])
        signal_example = (
            f'[{{"flag_type": "{first_key}", "description": "...", "severity": "high", '
            f'"source_quote": "...", "document": "policy.pdf", "location": "Section 2", '
            f'"requirement_ids": ["{id0}", "{id1}"]}}]'
        )
    else:
        signal_block = (
            "This framework defines no red-flag patterns. Return an empty signal_flags list."
        )
        signal_example = "[]"

    instructions = f"""You are performing a desk review of an organization's documents against {fw.name} ({fw.version}). This is the first step of a professional assessment: catalog what exists, map evidence to controls, identify what is missing, and flag red flags. Assess against {fw.name} only.

## {fw.name} Controls Reference

{controls_text}

## Analysis Levels

Perform ALL four analysis levels for each document:

### Level 1 - Document Catalog
For each document, identify:
- Document type (policy, procedure, standard, register, report, contract, or other)
- Which {fw.name} controls it covers
- A 1-2 sentence summary of what it contains

### Level 2 - Evidence Mapping
For each control ({n} total), extract EXACT quotes from the documents that address that control. Include the document filename and approximate location (section heading, page, paragraph). Quote verbatim; do not paraphrase.

### Level 3 - Absence Detection
For each control, identify what is MISSING from the documents. Be specific: name the missing element, not a generic gap.

### Level 4 - Signal Detection
{signal_block}

## Control IDs

Use only the control IDs listed in the Controls Reference above, exactly as written, in evidence_map, absence_findings, signal_flags requirement_ids and coverage_summary. List every control a red flag affects in its requirement_ids.

## Output Format

Respond ONLY with valid JSON. No markdown fences, no commentary.

{{
  "document_catalog": [
    {{"filename": "policy.pdf", "document_type": "Information Security Policy", "coverage_areas": ["{id0}"], "summary": "..."}}
  ],
  "evidence_map": {{
    "{id0}": [{{"quote": "Exact quoted text from document...", "document": "policy.pdf", "location": "Section 3"}}]
  }},
  "absence_findings": [
    {{"requirement_id": "{id1}", "description": "...", "severity": "high", "affected_documents": ["policy.pdf"]}}
  ],
  "signal_flags": {signal_example},
  "coverage_summary": {{"{id0}": "adequate", "{id1}": "absent"}}
}}

Coverage levels: "adequate" (control well-addressed), "partial" (some mention but gaps), "absent" (explicitly missing despite a relevant document), "not_covered" (no relevant document uploaded).

Include ALL {n} control IDs in coverage_summary. Be thorough and precise."""

    return [
        {"type": "text", "text": persona},
        {
            "type": "text",
            "text": instructions,
            "cache_control": {"type": "ephemeral"},
        },
    ]


def build_framework_evidence_extraction_prompt(
    framework_id: str,
    documents: list[dict],
    desk_review_findings: list[dict] | None = None,
) -> str:
    """Build a framework-specific prompt for grounded evidence extraction."""
    fw = FrameworkRegistry.get(framework_id)
    controls = fw.all_controls()
    controls_text = _build_controls_text(fw)

    docs_text = ""
    if documents:
        for document in documents:
            docs_text += (
                f"\n### Document: {document['filename']} "
                f"(Category: {document['category']})\n\n"
            )
            docs_text += document["text"] + "\n\n"
    else:
        docs_text = "\n_No supporting documents provided._\n"

    desk_review_context = ""
    if desk_review_findings:
        desk_review_context = "\n## Desk Review Context (from prior document analysis)\n\n"
        desk_review_context += (
            "The following findings were identified during desk review. "
            "Pay special attention to these areas:\n\n"
        )
        for finding in desk_review_findings:
            prefix = {
                "evidence": "Evidence",
                "absence": "Gap",
                "signal": "Red Flag",
            }.get(finding["type"], "Finding")
            desk_review_context += (
                f"- **{prefix}** ({finding.get('requirement_id', 'general')}): "
                f"{finding['content']}\n"
            )
        desk_review_context += "\n"

    return f"""## Task: Evidence Extraction

For each {fw.name} ({fw.version}) control below, find and quote the EXACT language from the organization's documents that is relevant to that control. Omit controls for which no relevant language exists.
{desk_review_context}
## Controls
{controls_text}

## Organization Documents
{docs_text}

## Output Format

Respond ONLY with valid JSON:

{{
  "evidence": {{
    "{controls[0].id}": ["Exact quoted text from document...", "Another relevant quote..."]
  }}
}}

Use only the control IDs listed above. Quote verbatim - do not paraphrase."""


def build_framework_system_prompt(framework_id: str) -> list[dict]:
    """
    Build a cacheable system prompt for a specific framework's gap analysis.

    Returns content blocks with cache_control on the stable controls block.
    Each framework's prompt caches independently.
    """
    fw = FrameworkRegistry.get(framework_id)
    controls_text = _build_controls_text(fw)
    persona = _FRAMEWORK_PERSONAS.get(framework_id, _DEFAULT_PERSONA)
    red_flags = _build_red_flag_section(fw)
    ctrl_count = fw.control_count()

    instructions = f"""Your task is to assess an organization's compliance with {fw.name} ({fw.version}) based on their questionnaire responses, supporting documents, and organizational context.

## {fw.name} Controls Reference

{controls_text}

## Assessment Instructions

For EACH control above, you must assess the organization and provide:

1. **compliance_status**: One of "compliant", "partially_compliant", "non_compliant", or "not_assessed"
   - "compliant": Clear, specific, verifiable evidence of full implementation with documented processes.
   - "partially_compliant": Substantial evidence of active implementation WITH specific bounded gaps.
   - "non_compliant": No evidence, only boilerplate, or practices that contradict compliance.
   - "not_assessed": Insufficient information to determine.

2. **current_state**: What the organization currently does (1-2 sentences).
3. **gap_description**: What is missing. If compliant, "No gap identified."
4. **risk_level**: "critical", "high", "medium", or "low"
5. **remediation_action**: Specific, actionable step to close the gap (1-3 sentences).
6. **remediation_priority**: 1 (immediate), 2 (short-term), 3 (medium-term), 4 (long-term)
7. **remediation_effort**: "low", "medium", or "high"
8. **timeline_weeks**: Estimated weeks to remediate
9. **maturity_level**: 0-5 CMMI-aligned maturity score
10. **root_cause_category**: One of "policy", "people", "process", "technology", "governance"
11. **evidence_quote**: Exact text from documents, or "No relevant language found"

## Output Format

Respond ONLY with valid JSON:

{{{{
  "executive_summary": "3-5 sentence summary of compliance posture, strengths, and critical gaps.",
  "assessments": [
    {{{{
      "requirement_id": "{fw.all_controls()[0].id if fw.all_controls() else 'CTRL.1'}",
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

The "assessments" array must contain exactly one entry for every control ID listed above ({ctrl_count} total).

## Important Guidelines

- Quote exact policy language from documents before assessing each control
- Be specific and practical in remediation advice
- Cross-reference document evidence with questionnaire answers
- Assign maturity_level based on observed practices, not aspirational state
- Policy != Implementation: a written policy is not sufficient for "compliant"
- Burden of proof is on the organization
{red_flags}"""

    return [
        {"type": "text", "text": persona},
        {
            "type": "text",
            "text": instructions,
            "cache_control": {"type": "ephemeral"},
        },
    ]


def build_framework_user_prompt(
    framework_id: str,
    company_name: str,
    industry: str,
    company_size: str,
    description: str | None,
    responses: list[dict],
    documents: list[dict],
    context_profile: dict | None = None,
    evidence: dict | None = None,
    desk_review_summary: dict | None = None,
    applicable_controls: list[str] | None = None,
) -> str:
    """
    Build the user prompt scoped to one framework's controls.

    Filters responses and evidence to only include items relevant to this framework.
    """
    fw = FrameworkRegistry.get(framework_id)
    fw_control_ids = {c.id for c in fw.all_controls()}

    # Expand cluster-ID-keyed responses to control-ID-keyed responses for this framework.
    # Singleton clusters: "SINGLE.ISO.A5.24" → control_id "ISO.A5.24"
    # Real clusters: "CLUSTER_001" → look up in cluster mappings
    responses = _expand_cluster_responses(responses, framework_id, fw_control_ids)

    size_labels = {
        "startup": "Startup (<50 employees)",
        "sme": "SME (50-500 employees)",
        "large": "Large (500-5000 employees)",
        "enterprise": "Enterprise (5000+ employees)",
    }

    prompt = f"""## Organization Profile
- **Company:** {company_name}
- **Industry:** {industry}
- **Size:** {size_labels.get(company_size, company_size)}
- **Description:** {description or 'Not provided'}
- **Framework:** {fw.name} ({fw.version})

"""

    # Scope exclusions
    if applicable_controls is not None:
        excluded = sorted(fw_control_ids - set(applicable_controls))
        if excluded:
            prompt += "## Scope — Controls Excluded\n"
            prompt += "Set compliance_status to 'not_applicable' for these:\n"
            for cid in excluded:
                prompt += f"- {cid}\n"
            prompt += "\n"

    # Context profile
    if context_profile:
        prompt += f"""## Risk Profile
- **Risk Tier:** {context_profile.get('risk_tier', 'MEDIUM')}
- **Industry Context:** {context_profile.get('industry_context', '')}

"""

    # Desk review findings (filtered to this framework's controls)
    if desk_review_summary:
        prompt += "## Desk Review Findings\n\n"
        if desk_review_summary.get("coverage_summary"):
            prompt += "### Coverage\n"
            for req_id, level in desk_review_summary["coverage_summary"].items():
                if req_id in fw_control_ids:
                    prompt += f"- **{req_id}**: {level}\n"
            prompt += "\n"
        if desk_review_summary.get("signal_flags"):
            relevant_flags = [
                f for f in desk_review_summary["signal_flags"]
                if (
                    set(
                        f.get("requirement_ids")
                        or ([f["requirement_id"]] if f.get("requirement_id") else [])
                    )
                    & fw_control_ids
                )
                or (
                    not f.get("requirement_ids")
                    and not f.get("requirement_id")
                    and (f.get("framework_id") or LEGACY_FINDING_FRAMEWORK_ID)
                    == framework_id
                )
            ]
            if relevant_flags:
                prompt += "### Red Flags\n"
                for flag in relevant_flags:
                    prompt += f"- **{flag.get('severity', 'medium').upper()}**: {flag['content']}\n"
                prompt += "\n"

    # Questionnaire responses (filtered to this framework)
    fw_responses = [r for r in responses if r["question_id"] in fw_control_ids]
    prompt += "## Questionnaire Responses\n\n"
    if fw_responses:
        for r in fw_responses:
            notes_str = f" — Notes: {r['notes']}" if r.get("notes") else ""
            confidence_str = f" [Confidence: {r['confidence']}]" if r.get("confidence") else ""
            prompt += f"- **{r['question_id']}**: {r['answer']}{notes_str}{confidence_str}\n"
    else:
        prompt += "_No questionnaire responses for this framework._\n"
    prompt += "\n"

    # Evidence (filtered to this framework)
    if evidence:
        fw_evidence = {k: v for k, v in evidence.items() if k in fw_control_ids}
        if fw_evidence:
            prompt += "## Extracted Document Evidence\n\n"
            for req_id, quotes in fw_evidence.items():
                prompt += f"### {req_id}\n"
                for quote in quotes:
                    prompt += f"> {quote}\n"
                prompt += "\n"
        else:
            prompt += _documents_section(documents)
    else:
        prompt += _documents_section(documents)

    prompt += f"\n---\n\nAssess this organization against all {fw.name} controls and provide the structured JSON output."
    return prompt


def build_synthesis_prompt(
    per_framework_results: dict[str, dict],
    company_name: str,
    industry: str,
) -> str:
    """
    Build prompt for cross-framework synthesis call.

    Input: per-framework gap analysis results.
    Output: unified executive summary + cross-framework recommendations.
    """
    framework_names = []
    for fw_id in per_framework_results:
        fw = FrameworkRegistry.get_or_none(fw_id)
        if fw:
            framework_names.append(f"{fw.name} ({fw.version})")

    prompt = f"""## Cross-Framework Synthesis

You are producing a unified executive summary for {company_name} ({industry}).
They were assessed against: {', '.join(framework_names)}.

## Per-Framework Results

"""
    for fw_id, result in per_framework_results.items():
        fw = FrameworkRegistry.get(fw_id)
        prompt += f"### {fw.name}\n"
        prompt += f"**Executive Summary:** {result.get('executive_summary', 'N/A')}\n\n"

        # Summary stats
        assessments = result.get("assessments", [])
        compliant = sum(1 for a in assessments if a.get("compliance_status") == "compliant")
        partial = sum(1 for a in assessments if a.get("compliance_status") == "partially_compliant")
        non_comp = sum(1 for a in assessments if a.get("compliance_status") == "non_compliant")
        prompt += f"- Compliant: {compliant}, Partially: {partial}, Non-compliant: {non_comp}\n"

        # Top critical gaps
        critical_gaps = [
            a for a in assessments
            if a.get("risk_level") == "critical" and a.get("compliance_status") != "compliant"
        ]
        if critical_gaps:
            prompt += "- Critical gaps: " + ", ".join(a["requirement_id"] for a in critical_gaps[:5]) + "\n"
        prompt += "\n"

    prompt += """## Task

Produce a unified cross-framework analysis:

1. **unified_executive_summary**: 5-8 sentences covering overall compliance posture across all frameworks, common strengths, common weaknesses, and most urgent priorities.

2. **cross_framework_themes**: List of 3-5 themes that appear across multiple frameworks (e.g., "Access control gaps appear in both ISO 27001 and HIPAA").

3. **prioritized_recommendations**: Top 5-10 remediation actions that address gaps across multiple frameworks simultaneously, ordered by impact.

4. **framework_comparison**: For each framework, a 1-2 sentence posture summary. Do not estimate or state any numeric score; scores are computed deterministically elsewhere.

Respond ONLY with valid JSON:

{
  "unified_executive_summary": "...",
  "cross_framework_themes": ["...", "..."],
  "prioritized_recommendations": [
    {"action": "...", "frameworks_addressed": ["iso27001", "hipaa"], "priority": 1}
  ],
  "framework_comparison": {
    "iso27001": {"summary": "..."}
  }
}"""

    return prompt


def build_synthesis_system_prompt() -> list[dict]:
    """System prompt for cross-framework synthesis call."""
    return [
        {
            "type": "text",
            "text": (
                "You are a senior compliance strategist synthesizing gap analysis results "
                "across multiple regulatory and industry frameworks. Produce actionable, "
                "cross-referenced insights. Respond ONLY with valid JSON."
            ),
        },
    ]


def _documents_section(documents: list[dict]) -> str:
    """Build raw documents section for user prompt."""
    prompt = "## Supporting Documents\n\n"
    if documents:
        for doc in documents:
            prompt += f"### Document: {doc['filename']} (Category: {doc['category']})\n\n"
            prompt += doc["text"] + "\n\n"
    else:
        prompt += "_No supporting documents uploaded._\n"
    return prompt
