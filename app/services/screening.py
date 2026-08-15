"""
Domain-Level Screening Pass (Phase 3).

Orchestrates a single Claude call using 9 broad domain answers to infer
preliminary compliance status for all 41 DPDPA requirements.

Results are stored in Assessment.screening_results as JSON:
  {req_id: {"compliance_status": str, "confidence": str, "reasoning": str}}
"""

import json
import logging
import re

import anthropic

from app.config import settings
from app.dpdpa.prompts import (
    SCREENING_DOMAINS,
    build_screening_system_prompt,
    build_screening_user_prompt,
)
from app.dpdpa.framework import get_all_requirements
from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def run_screening_pass(
    assessment_id: str,
    domain_answers: dict[str, str],
    db: Session,
) -> dict:
    """
    Run the domain-level screening pass for an assessment.

    1. Calls Claude with the 9 domain answers.
    2. Parses inferences (compliance_status + confidence per requirement).
    3. Persists screening_results to the Assessment row.
    4. Creates QuestionnaireResponse records with answer_source="inferred"
       for high-confidence non-non_compliant inferences (never overwrites human answers).

    Returns the parsed inferences dict.
    """
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    system_blocks = build_screening_system_prompt()
    user_prompt = build_screening_user_prompt(
        company_name=assessment.company_name,
        industry=assessment.industry or "other",
        company_size=assessment.company_size or "sme",
        domain_answers=domain_answers,
    )

    logger.info("Screening: calling Claude for assessment %s", assessment_id)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_blocks,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text
    inferences = _parse_inferences(raw_text)

    logger.info(
        "Screening: received %d inferences for assessment %s",
        len(inferences),
        assessment_id,
    )

    # Persist screening results
    assessment.screening_results = json.dumps(inferences)
    assessment.screening_status = "completed"

    # Create inferred QuestionnaireResponse records for high-confidence inferences
    _persist_inferred_answers(assessment_id, inferences, db)

    db.commit()
    return inferences


def _parse_inferences(raw_text: str) -> dict:
    """Parse Claude's JSON output. Returns {req_id: {compliance_status, confidence, reasoning}}."""
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object from the response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            logger.error("Screening: failed to parse Claude response as JSON")
            return {}

    raw_inferences = parsed.get("inferences", {})

    # Validate and normalize
    valid_statuses = {"compliant", "partially_compliant", "non_compliant", "not_assessed"}
    valid_confidences = {"high", "medium", "low"}
    all_req_ids = {r["id"] for r in get_all_requirements()}

    result = {}
    for req_id, inf in raw_inferences.items():
        if req_id not in all_req_ids:
            continue
        status = inf.get("compliance_status", "not_assessed")
        confidence = inf.get("confidence", "low")
        if status not in valid_statuses:
            status = "not_assessed"
        if confidence not in valid_confidences:
            confidence = "low"
        result[req_id] = {
            "compliance_status": status,
            "confidence": confidence,
            "reasoning": inf.get("reasoning", ""),
        }

    # Fill in any missing requirements as not_assessed/low
    for req_id in all_req_ids:
        if req_id not in result:
            result[req_id] = {
                "compliance_status": "not_assessed",
                "confidence": "low",
                "reasoning": "Not covered by screening answers.",
            }

    return result


# Maps screening compliance_status to questionnaire answer values
_STATUS_TO_ANSWER = {
    "compliant": "fully_implemented",
    "partially_compliant": "partially_implemented",
    "non_compliant": "not_implemented",
}


def _persist_inferred_answers(
    assessment_id: str,
    inferences: dict,
    db: Session,
) -> None:
    """
    Create QuestionnaireResponse records for high-confidence inferences.

    Rules:
    - Only high-confidence inferences that are NOT non_compliant get pre-filled.
    - non_compliant stays at medium/low confidence so human still reviews.
    - Never overwrites existing human or document answers.
    """
    # Load existing responses to avoid overwrites
    existing = {
        r.question_id
        for r in db.query(QuestionnaireResponse)
        .filter(QuestionnaireResponse.assessment_id == assessment_id)
        .all()
    }

    created = 0
    for req_id, inf in inferences.items():
        if req_id in existing:
            continue

        confidence = inf["confidence"]
        status = inf["compliance_status"]

        # Only pre-fill high-confidence non-non_compliant inferences
        if confidence != "high" or status == "not_assessed":
            continue
        if status == "non_compliant":
            # Don't pre-fill gaps — human must confirm these
            continue

        answer = _STATUS_TO_ANSWER.get(status)
        if not answer:
            continue

        db.add(QuestionnaireResponse(
            assessment_id=assessment_id,
            question_id=req_id,
            answer=answer,
            notes=f"Inferred from domain screening: {inf.get('reasoning', '')[:200]}",
            answer_source="inferred",
            confidence="high",
        ))
        created += 1

    logger.info(
        "Screening: created %d inferred pre-fills for assessment %s",
        created,
        assessment_id,
    )


def get_domain_coverage() -> list[dict]:
    """Return the screening domain definitions for use in templates."""
    return SCREENING_DOMAINS
