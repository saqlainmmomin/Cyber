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


class IncompleteAssessmentError(ValueError):
    """Raised when a validated response doesn't cover every known requirement.

    The model (or the multi-framework wrapper) is expected to return exactly
    one item per known requirement ID — including out-of-scope ones, which it
    is separately instructed to mark `not_applicable` rather than omit (see
    `app/dpdpa/prompts.py::build_user_prompt`'s scope-filter section). Missing
    coverage is presented as a report over the *survivors only*: scoring
    (`app/services/scoring.py::compute_framework_scores`) treats a domain with
    no assessed items as not applicable and excludes it from the weighted
    average, so a response missing 40 of 41 controls can still produce a
    misleading 100% score built from the one item that survived. Persisting
    that is worse than failing the request outright.
    """


def validate_and_filter(parsed: dict, known_requirement_ids: set[str]) -> dict:
    """Validate a parsed gap-analysis response and drop unusable items.

    Two independent defenses, applied per item so one bad entry doesn't
    sink the other ~40:
    - Structurally invalid items (missing/wrong-typed required fields) are
      dropped and logged.
    - Items whose requirement_id isn't in known_requirement_ids are dropped
      and logged — today these silently become orphan GapItem rows that
      never map to a real control anywhere downstream.

    A duplicate requirement_id among the survivors keeps its first occurrence
    (logged) — the model returning the same control twice is itself a sign of
    a malformed response, and "first wins" is at least deterministic.

    After filtering and deduplication, every ID in known_requirement_ids must
    be covered by a surviving item, or this raises IncompleteAssessmentError.
    Rejecting the whole response is deliberate: scoring cannot distinguish
    "not assessed because out of scope" from "not assessed because the item
    got dropped," so a partial response must never reach persistence (see
    IncompleteAssessmentError's docstring). Callers already treat an
    exception from this call as a hard analysis failure
    (`app/routers/analysis.py`'s single- and multi-framework paths both wrap
    the analyzer call in try/except and surface it as a failed run).

    Returns a plain dict in the same shape callers already consume
    (`{"executive_summary": str, "assessments": [...]}`), so
    app/routers/analysis.py needs no further changes.
    """
    executive_summary = parsed.get("executive_summary")
    if not isinstance(executive_summary, str):
        executive_summary = ""

    valid_items: list[GapAssessmentItem] = []
    seen_ids: set[str] = set()
    dropped_malformed = 0
    dropped_unknown_id = 0
    dropped_duplicate = 0

    for index, raw_item in enumerate(parsed.get("assessments", [])):
        try:
            item = GapAssessmentItem.model_validate(raw_item)
        except ValidationError as exc:
            dropped_malformed += 1
            # exc.errors(include_input=False) omits the rejected field values —
            # str(exc) would include them verbatim, which can be quoted client
            # document text (e.g. evidence_quote), moving it into application
            # logs with broader access/retention than the assessment itself.
            sanitized_errors = [
                {"loc": err["loc"], "type": err["type"], "msg": err["msg"]}
                for err in exc.errors(include_input=False)
            ]
            logger.warning(
                "Dropping malformed assessment item at index %d: %s",
                index,
                sanitized_errors,
            )
            continue
        if item.requirement_id not in known_requirement_ids:
            dropped_unknown_id += 1
            logger.warning(
                "Dropping assessment item with unknown requirement_id %r",
                item.requirement_id,
            )
            continue
        if item.requirement_id in seen_ids:
            dropped_duplicate += 1
            logger.warning(
                "Dropping duplicate assessment item for requirement_id %r "
                "(first occurrence wins)",
                item.requirement_id,
            )
            continue
        seen_ids.add(item.requirement_id)
        valid_items.append(item)

    if dropped_malformed or dropped_unknown_id or dropped_duplicate:
        logger.warning(
            "Gap analysis response validation dropped %d malformed, %d "
            "unknown-requirement-id, and %d duplicate item(s) out of %d",
            dropped_malformed,
            dropped_unknown_id,
            dropped_duplicate,
            len(parsed.get("assessments", [])),
        )

    missing_ids = known_requirement_ids - seen_ids
    if missing_ids:
        raise IncompleteAssessmentError(
            f"Gap analysis response is missing {len(missing_ids)} of "
            f"{len(known_requirement_ids)} known requirement(s) after "
            f"validation: {sorted(missing_ids)[:10]}"
            + ("…" if len(missing_ids) > 10 else "")
        )

    return GapAnalysisResponse(
        executive_summary=executive_summary,
        assessments=valid_items,
    ).model_dump()
