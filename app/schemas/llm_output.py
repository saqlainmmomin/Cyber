"""Validation schema for the gap-analysis LLM response.

Nothing validated Claude's raw JSON against a schema before this — callers
read `a["requirement_id"]` / `a["compliance_status"]` straight off the
parsed dict. Since scoring.py is deterministic and these two fields are the
only signal it acts on, an unvalidated hallucination here becomes a wrong
score with nothing catching it first.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from pydantic import BaseModel, Field, ValidationError, model_validator

from app.services.scoring import KNOWN_STATUSES

logger = logging.getLogger(__name__)


class GapAssessmentItem(BaseModel):
    requirement_id: str
    compliance_status: str
    current_state: str = ""
    gap_description: str = ""
    risk_level: str = "medium"
    remediation_action: str = ""
    remediation_priority: int = 3
    remediation_effort: str = "medium"
    timeline_weeks: int = 8
    maturity_level: int = 0
    root_cause_category: str = "process"
    evidence_quote: str = ""
    # Not part of the model's own output — set after validation by the
    # deterministic sanity rule in claude_analyzer.py.
    needs_review: bool = False

    _OPTIONAL_FIELDS_WITH_DEFAULTS: ClassVar[tuple[str, ...]] = (
        "current_state",
        "gap_description",
        "risk_level",
        "remediation_action",
        "remediation_priority",
        "remediation_effort",
        "timeline_weeks",
        "maturity_level",
        "root_cause_category",
        "evidence_quote",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_permissive_fields(cls, data):
        if not isinstance(data, dict):
            return data
        # A field explicitly present as null (Claude sometimes emits this for
        # an optional field it has nothing to say) should fall back to the
        # field's own default, not fail validation — only requirement_id and
        # compliance_status are load-bearing enough to reject the item over.
        data = {
            key: value
            for key, value in data.items()
            if not (value is None and key in cls._OPTIONAL_FIELDS_WITH_DEFAULTS)
        }
        if data.get("compliance_status") not in KNOWN_STATUSES:
            logger.warning(
                "Unexpected compliance_status %r for %s — treating as not_assessed",
                data.get("compliance_status"),
                data.get("requirement_id", "<unknown>"),
            )
            data["compliance_status"] = "not_assessed"
        return data


class GapAnalysisResponse(BaseModel):
    executive_summary: str = ""
    assessments: list[GapAssessmentItem] = Field(default_factory=list)


def validate_and_filter(parsed: dict, known_requirement_ids: set[str]) -> dict:
    """Validate a parsed gap-analysis response and drop unusable items.

    Two independent defenses, applied per item so one bad entry doesn't
    sink the other ~40:
    - Structurally invalid items (missing/wrong-typed required fields) are
      dropped and logged.
    - Items whose requirement_id isn't in known_requirement_ids are dropped
      and logged — today these silently become orphan GapItem rows that
      never map to a real control anywhere downstream.

    Returns a plain dict in the same shape callers already consume
    (`{"executive_summary": str, "assessments": [...]}`), so
    app/routers/analysis.py needs no changes.
    """
    executive_summary = parsed.get("executive_summary")
    if not isinstance(executive_summary, str):
        executive_summary = ""

    valid_items: list[GapAssessmentItem] = []
    dropped_malformed = 0
    dropped_unknown_id = 0

    for raw_item in parsed.get("assessments", []):
        try:
            item = GapAssessmentItem.model_validate(raw_item)
        except ValidationError as exc:
            dropped_malformed += 1
            logger.warning("Dropping malformed assessment item: %s", exc)
            continue
        if item.requirement_id not in known_requirement_ids:
            dropped_unknown_id += 1
            logger.warning(
                "Dropping assessment item with unknown requirement_id %r",
                item.requirement_id,
            )
            continue
        valid_items.append(item)

    if dropped_malformed or dropped_unknown_id:
        logger.warning(
            "Gap analysis response validation dropped %d malformed and %d "
            "unknown-requirement-id item(s) out of %d",
            dropped_malformed,
            dropped_unknown_id,
            len(parsed.get("assessments", [])),
        )

    return GapAnalysisResponse(
        executive_summary=executive_summary,
        assessments=valid_items,
    ).model_dump()
