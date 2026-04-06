"""
Conversational Follow-up Engine — generates targeted follow-up questions when
questionnaire answers are weak or contradict desk review findings.

The engine uses a lightweight Claude call to generate 1-3 follow-up questions
based on:
  - The original question and answer
  - Desk review evidence/findings for mapped requirements
  - The answer's weakness level (not_implemented, partially_implemented, planned)
  - Inconsistency between answer and desk review findings

Follow-up count is DYNAMIC based on answer content:
  - Strong contradiction with desk review: 2-3 follow-ups
  - Weak answer (not_implemented/planned) on critical question: 1-2 follow-ups
  - Partial implementation claim without specifics: 1 follow-up
"""

import json

import anthropic

from app.config import settings


def generate_followups(
    question_text: str,
    question_id: str,
    answer: str,
    criticality: str,
    maps_to: list[str],
    desk_review_evidence: list[dict] | None = None,
    desk_review_note: str | None = None,
    guidance: str = "",
) -> list[dict]:
    """
    Generate follow-up questions based on the answer and context.

    Returns a list of follow-up question dicts:
    [{"id": "FU.{question_id}.1", "text": "...", "reason": "..."}]

    Returns empty list if no follow-up is needed.
    """
    # Determine if follow-up is warranted
    trigger = _assess_trigger(answer, criticality, desk_review_evidence, desk_review_note)
    if trigger["level"] == "none":
        return []

    # Build prompt for Claude
    prompt = _build_followup_prompt(
        question_text=question_text,
        answer=answer,
        criticality=criticality,
        trigger=trigger,
        desk_review_evidence=desk_review_evidence,
        desk_review_note=desk_review_note,
        guidance=guidance,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=512,
        temperature=0.3,
        system=(
            "You are an expert DPDPA compliance auditor conducting a gap assessment. "
            "Generate targeted follow-up questions that probe deeper into the respondent's answer. "
            "Be specific, not generic. Reference concrete evidence gaps or contradictions when present. "
            "Respond ONLY with valid JSON. No markdown fences, no commentary."
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
        followups = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(followups, list):
        followups = followups.get("followups", []) if isinstance(followups, dict) else []

    # Tag with IDs and cap at trigger's max count
    result = []
    for i, fu in enumerate(followups[: trigger["max_count"]]):
        result.append({
            "id": f"FU.{question_id}.{i + 1}",
            "text": fu.get("text", fu.get("question", "")),
            "reason": fu.get("reason", ""),
            "parent_question_id": question_id,
        })

    return result


def _assess_trigger(
    answer: str,
    criticality: str,
    desk_review_evidence: list[dict] | None,
    desk_review_note: str | None,
) -> dict:
    """
    Determine follow-up trigger level and max question count.

    Dynamic scaling based on answer content + context:
      - Contradiction with desk review → high trigger, 2-3 questions
      - Weak answer on critical question → medium trigger, 1-2 questions
      - Weak answer on non-critical → low trigger, 1 question
      - Strong answer → no trigger
    """
    has_evidence = bool(desk_review_evidence)
    has_signals = bool(desk_review_note)

    # Strong answers don't need follow-up (unless contradicting evidence)
    if answer == "fully_implemented":
        if has_evidence and has_signals:
            # Claim of full implementation but desk review flagged issues
            return {"level": "contradiction", "max_count": 2, "reason": "Claims full implementation but document review flagged concerns"}
        return {"level": "none", "max_count": 0, "reason": ""}

    if answer == "not_applicable":
        return {"level": "none", "max_count": 0, "reason": ""}

    # Contradiction: answer says weak but evidence says something different, or vice versa
    if has_evidence and answer in ("not_implemented", "planned"):
        return {
            "level": "contradiction",
            "max_count": 3,
            "reason": "Document evidence exists but answer indicates no implementation",
        }

    # Weak answers on critical/high questions
    if answer in ("not_implemented", "planned"):
        if criticality in ("critical", "high"):
            return {"level": "high", "max_count": 2, "reason": f"Not implemented on {criticality} requirement"}
        return {"level": "low", "max_count": 1, "reason": "Not implemented"}

    # Partial implementation — probe for specifics
    if answer == "partially_implemented":
        if criticality == "critical":
            return {"level": "medium", "max_count": 2, "reason": "Partial implementation on critical requirement"}
        if has_signals:
            return {"level": "medium", "max_count": 2, "reason": "Partial implementation with document signals"}
        return {"level": "low", "max_count": 1, "reason": "Partial implementation — need specifics"}

    return {"level": "none", "max_count": 0, "reason": ""}


def _build_followup_prompt(
    question_text: str,
    answer: str,
    criticality: str,
    trigger: dict,
    desk_review_evidence: list[dict] | None,
    desk_review_note: str | None,
    guidance: str,
) -> str:
    """Build the follow-up generation prompt for Claude."""
    answer_labels = {
        "fully_implemented": "Fully Implemented",
        "partially_implemented": "Partially Implemented",
        "planned": "Planned (not yet implemented)",
        "not_implemented": "Not Implemented",
        "not_applicable": "Not Applicable",
    }

    parts = [
        f"## Context\n",
        f"**Original Question:** {question_text}\n",
        f"**Respondent's Answer:** {answer_labels.get(answer, answer)}\n",
        f"**Criticality:** {criticality}\n",
        f"**Trigger:** {trigger['reason']}\n",
    ]

    if guidance:
        parts.append(f"**DPDPA Guidance:** {guidance}\n")

    if desk_review_evidence:
        parts.append("\n## Document Review Evidence\n")
        for ev in desk_review_evidence[:3]:
            parts.append(f"- {ev['content']}")
            if ev.get("source_quote"):
                parts.append(f'  Quote: "{ev["source_quote"][:300]}"')

    if desk_review_note:
        parts.append(f"\n## Desk Review Note\n{desk_review_note}\n")

    parts.append(f"""
## Task
Generate {trigger['max_count']} targeted follow-up question(s) that:
1. Probe the specific gap between the answer and what we'd expect
2. Are concrete and answerable (not vague "tell us more")
3. Reference document findings if there's a contradiction
4. Help us understand the TRUE compliance state

Return JSON array:
[{{"text": "The follow-up question", "reason": "Why we're asking this"}}]
""")

    return "\n".join(parts)
