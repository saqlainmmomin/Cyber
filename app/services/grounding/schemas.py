"""Pydantic parsing models for v2 structured responses."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class LooseExtractionResponse(BaseModel):
    claims: list[dict]


class ExtractionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quote: str
    statement: str
    kind: Literal["design", "operating", "context"]
    stated_period: str | None
    stated_owner: str | None
    requirement_ids: list[str]


class LooseSupportResponse(BaseModel):
    verdicts: list[dict]


class SupportItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str
    verdict: Literal["yes", "no", "partial"]
    supported_statement: str | None


def _parse_json(raw: str) -> Any:
    cleaned = raw.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.I | re.S)
    if fence:
        cleaned = fence.group(1)
    return json.loads(cleaned)


def parse_extraction_response(raw: str) -> list[dict]:
    try:
        return LooseExtractionResponse.model_validate(_parse_json(raw)).claims
    except (ValueError, TypeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("parse_failure") from exc


def parse_support_response(raw: str) -> list[dict]:
    try:
        return LooseSupportResponse.model_validate(_parse_json(raw)).verdicts
    except (ValueError, TypeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("parse_failure") from exc
