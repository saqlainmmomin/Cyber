"""
Context Profiler — derives an organizational risk profile from Phase 1 context answers.

Uses a lightweight Claude call to compute risk tier, priority chapters, and contextual
framing that guides the adaptive Phase 2 questionnaire and gap analysis.
"""

import json

import anthropic

from app.config import settings


def derive_risk_profile(context_answers: list[dict], industry: str, company_size: str) -> dict:
    """
    Call Claude to derive a structured risk profile from context answers.

    Returns a dict matching ContextProfileOut schema fields.
    """
    # First, compute deterministic signals from answers
    signals = _extract_signals(context_answers)

    # Build a focused prompt for risk profiling
    prompt = _build_profile_prompt(context_answers, industry, company_size, signals)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        temperature=0,
        system=(
            "You are an expert DPDPA compliance advisor. Given an organization's context, "
            "produce a risk profile that will guide an adaptive compliance assessment. "
            "Respond ONLY with valid JSON matching the requested schema. No markdown, no commentary."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
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

    return profile


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
    answers: list[dict], industry: str, company_size: str, signals: dict
) -> str:
    """Build the prompt for risk profile generation."""
    answers_text = "\n".join(
        f"- {a['question_id']}: {json.dumps(a['answer'])}" for a in answers
    )

    return f"""## Organization Context
- Industry: {industry}
- Company Size: {company_size}
- SDF Candidate: {signals['sdf_candidate']}
- Processes Children's Data: {signals['processes_children_data']}
- Cross-Border Transfers: {signals['cross_border_transfers']}
- Sensitive Data: {signals['sensitive_data']}
- Data Principals Band: {signals['data_principals_band']}

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
- risk_tier: HIGH if SDF candidate, sensitive data with >1M principals, or critical infra. LOW if <10K principals, no sensitive data, internal policy only. MEDIUM otherwise.
- priority_chapters: Order the DPDPA chapters by relevance. Always include chapter_2 first.
- likely_not_applicable: List requirement IDs that are probably not applicable (e.g., SDF requirements for non-SDF orgs, children's data requirements if no children's data).
- timeline_pressure: Map from the assessment timeline answer (under_3_months=HIGH, 3_to_6=MEDIUM, else LOW).
- framing_notes: What should the assessor focus on? What's the biggest risk area?"""
