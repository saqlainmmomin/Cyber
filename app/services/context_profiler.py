"""
Context Profiler — derives an organizational risk profile from Phase 1 context answers.

Uses a lightweight Claude call to compute risk tier, priority chapters, and contextual
framing that guides the adaptive Phase 2 questionnaire and gap analysis.
"""

import json
import logging

from app.dpdpa.context_questions import PRIVACY_FRAMEWORKS
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION
from app.services import llm_client

logger = logging.getLogger(__name__)

MAX_LIKELY_NOT_APPLICABLE = 20


def derive_risk_profile(
    context_answers: list[dict],
    industry: str,
    company_size: str,
    framework_ids: list[str] | None = None,
) -> dict:
    """
    Call Claude to derive a structured risk profile from context answers.

    `framework_ids=None` keeps the legacy DPDPA framing. Otherwise the DPDPA-only
    fields (privacy signals, chapters, likely_not_applicable) are used only when
    the matching framework is selected.

    Returns a dict matching ContextProfileOut schema fields.
    """
    frameworks = framework_ids if framework_ids is not None else ["dpdpa"]
    has_dpdpa = "dpdpa" in frameworks
    has_privacy = bool(set(frameworks) & PRIVACY_FRAMEWORKS)
    # First, compute deterministic signals from answers
    signals = _extract_signals(context_answers)

    # Build a focused prompt for risk profiling
    known_requirement_ids = _known_requirement_ids()
    prompt = _build_profile_prompt(
        context_answers,
        industry,
        company_size,
        signals,
        known_requirement_ids,
        has_dpdpa=has_dpdpa,
        has_privacy=has_privacy,
    )

    raw = _call_claude_context_profile(prompt)

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    profile = json.loads(raw)

    # Merge deterministic signals (these are ground truth, not inferred)
    profile["sdf_candidate"] = signals["sdf_candidate"]
    profile["processes_children_data"] = signals["processes_children_data"]
    profile["cross_border_transfers"] = signals["cross_border_transfers"]
    profile["has_breach_response"] = signals["has_breach_response"]
    profile["likely_not_applicable"] = (
        _filter_likely_not_applicable(
            profile.get("likely_not_applicable", []), known_requirement_ids
        )
        if has_dpdpa
        else []
    )

    return profile


def _known_requirement_ids() -> set[str]:
    """The profile's signals are DPDPA-specific (SDF, children's data), so
    likely_not_applicable is always a list of DPDPA requirement IDs."""
    return {control.id for control in DPDPA_DEFINITION.all_controls()}


def _filter_likely_not_applicable(
    proposed_ids: list[object], known_requirement_ids: set[str]
) -> list[str]:
    filtered: list[str] = []
    for requirement_id in proposed_ids if isinstance(proposed_ids, list) else []:
        if (
            not isinstance(requirement_id, str)
            or requirement_id not in known_requirement_ids
        ):
            logger.warning(
                "Dropping unknown likely_not_applicable ID %r", requirement_id
            )
            continue
        filtered.append(requirement_id)
    return filtered[:MAX_LIKELY_NOT_APPLICABLE]


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    """Seam for the OpenRouter-backed client — patched directly in tests."""
    return llm_client.call_llm(tier, stream=stream, **request)


def _call_claude_context_profile(prompt: str) -> str:
    """Call the LLM for a context profile and return the raw response text."""
    with llm_client.call_tag(stage="context_profile"):
        response = _call_llm(
            tier="extract",
            max_tokens=1024,
            temperature=0,
            system=(
                "You are an expert compliance advisor covering DPDPA, ISO 27001, GDPR, HIPAA, "
                "NIST CSF, and PCI-DSS. Given an organization's context, produce a risk profile "
                "that will guide an adaptive compliance assessment. "
                "Respond ONLY with valid JSON matching the requested schema. No markdown, no commentary."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
    return response["text"]


def _extract_signals(answers: list[dict]) -> dict:
    """Extract deterministic branching signals from context answers."""
    answer_map = {a["question_id"]: a["answer"] for a in answers}

    risk_factors = answer_map.get("CTX.RISK.1", [])
    if isinstance(risk_factors, str):
        risk_factors = [risk_factors]

    data_categories = answer_map.get("CTX.DATA.1", [])
    if isinstance(data_categories, str):
        data_categories = [data_categories]

    data_principals = answer_map.get("CTX.RISK.2", "under_10k")

    sensitive = (
        "handles_sensitive_personal_data" in risk_factors
        or "health" in data_categories
        or "biometric" in data_categories
        or "financial" in data_categories
    )
    large_scale = data_principals in ("1m_to_10m", "over_10m")

    return {
        "sdf_candidate": (
            "designated_or_likely_sdf" in risk_factors
            or (sensitive and large_scale)
        ),
        "processes_children_data": (
            "processes_childrens_data" in risk_factors
            or "childrens" in data_categories
        ),
        "cross_border_transfers": answer_map.get("CTX.DATA.4") == "yes",
        "has_breach_response": answer_map.get("CTX.RISK.3") != "no",
        "sensitive_data": sensitive,
        "large_scale": large_scale,
        "data_principals_band": data_principals,
    }


def _build_profile_prompt(
    answers: list[dict],
    industry: str,
    company_size: str,
    signals: dict,
    known_requirement_ids: set[str],
    *,
    has_dpdpa: bool = True,
    has_privacy: bool = True,
) -> str:
    """Build the prompt for risk profile generation."""
    answers_text = "\n".join(
        f"- {a['question_id']}: {json.dumps(a['answer'])}" for a in answers
    )

    privacy_lines = (
        f"""- SDF Candidate: {signals['sdf_candidate']}
- Processes Children's Data: {signals['processes_children_data']}
- Cross-Border Transfers: {signals['cross_border_transfers']}
- Sensitive Data: {signals['sensitive_data']}
- Data Principals Band: {signals['data_principals_band']}
"""
        if has_privacy
        else ""
    )

    if has_dpdpa:
        tier_rule = (
            "HIGH if SDF candidate, sensitive data with >1M principals, or critical infra. "
            "LOW if <10K principals, no sensitive data, internal policy only. MEDIUM otherwise."
        )
        chapters_rule = "Order the DPDPA chapters by relevance. Always include chapter_2 first."
        na_rule = (
            "List requirement IDs that are probably not applicable (e.g., SDF requirements "
            "for non-SDF orgs, children's data requirements if no children's data)."
        )
        na_ids_rule = (
            f"- likely_not_applicable must use only these IDs, at most {MAX_LIKELY_NOT_APPLICABLE}, "
            f"and must not be padded: {', '.join(sorted(known_requirement_ids))}"
        )
    else:
        tier_rule = (
            "HIGH if critical infrastructure, a recent incident, no formal security program, or "
            "no leadership owner for security risk. LOW if a mature, audited program with no "
            "recent incident. MEDIUM otherwise."
        )
        chapters_rule = "Return an empty list."
        na_rule = "Return an empty list."
        na_ids_rule = "- likely_not_applicable must be an empty list."

    return f"""## Organization Context
- Industry: {industry}
- Company Size: {company_size}
{privacy_lines}
## Context Questionnaire Answers
{answers_text}

## Task
Based on the above, produce a risk profile JSON with these fields:

{{
  "risk_tier": "HIGH" | "MEDIUM" | "LOW",
  "priority_chapters": ["chapter_2", ...],
  "likely_not_applicable": ["CH4.SDF.1", ...],
  "industry_context": "1-2 sentence industry-specific compliance framing",
  "timeline_pressure": "HIGH" | "MEDIUM" | "LOW",
  "framing_notes": "2-3 sentences on what the assessment should focus on given this org's profile"
}}

Rules:
- risk_tier: {tier_rule}
- priority_chapters: {chapters_rule}
- likely_not_applicable: {na_rule}
- timeline_pressure: Map from the assessment timeline answer (under_3_months=HIGH, 3_to_6=MEDIUM, else LOW).
- framing_notes: What should the assessor focus on? What's the biggest risk area?
{na_ids_rule}"""
