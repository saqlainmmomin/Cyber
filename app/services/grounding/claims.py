"""Claim records, deterministic identity, and serialisable claim sets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Sequence

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.services.grounding.batches import RequirementBatch
from app.services.grounding.chunking import Chunk
from app.services.grounding import prompts
from app.services.grounding.sources import SourceDocument


REJECTION_REASONS = (
    "over_call_cap",
    "malformed_item",
    "no_valid_requirement",
    "quote_too_long",
    "quote_too_short",
    "quote_outside_chunk",
    "quote_in_other_document",
    "quote_unicode_mismatch",
    "quote_not_found",
    "quote_in_truncation_marker",
    "support_no",
    "support_partial_unusable",
    "support_missing",
    "support_unit_failed",
)


@dataclass(frozen=True)
class VerifiedClaim:
    claim_id: str
    source_id: str
    evidence_id: str | None
    evidence_version_id: str | None
    filename: str
    chunk_id: str
    start: int
    end: int
    quote: str
    model_quote: str
    statement: str
    original_statement: str | None
    kind: str
    stated_period: str | None
    stated_owner: str | None
    requirement_ids: tuple[str, ...]
    framework_ids: tuple[str, ...]
    tag_status: str
    support: str
    needs_review: bool
    kind_conflict: bool
    derived_from_image: bool
    origins: tuple[dict, ...]
    citation: dict | None


@dataclass(frozen=True)
class RejectedClaim:
    reason: str
    source_id: str
    chunk_id: str
    batch: str | None
    model_quote: str
    statement: str
    requirement_ids: tuple[str, ...]


@dataclass(frozen=True)
class FailedUnit:
    stage: str
    label: str
    chunk_id: str
    requirement_ids: tuple[str, ...]
    error: str


def _statement_norm(statement: str) -> str:
    result = " ".join(statement.casefold().split())
    return result[:-1] if result.endswith(".") else result


def claim_id(source_id: str, start: int, end: int, statement: str) -> str:
    payload = f"{source_id}|{start}|{end}|{_statement_norm(statement)}"
    return "CLM-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _setting_snapshot() -> dict[str, object]:
    names = (
        "v2_chunk_min_words",
        "v2_chunk_max_words",
        "v2_extraction_batch_max_requirements",
        "v2_max_claims_per_call",
        "v2_support_batch_max_claims",
        "v2_min_quote_chars",
        "v2_max_quote_chars",
        "v2_max_extraction_calls",
        "v2_extraction_max_tokens",
        "v2_support_max_tokens",
        "v2_structured_output",
        "llm_model_extract",
    )
    return {name: getattr(settings, name) for name in names}


@dataclass(frozen=True)
class ClaimSet:
    schema_version: int
    claim_set_id: str
    created_at: str
    framework_ids: tuple[str, ...]
    pack_versions: dict[str, str]
    prompt_version: str
    prompt_fingerprints: dict[str, str]
    settings: dict[str, object]
    sources: tuple[dict, ...]
    chunks: tuple[Chunk, ...]
    batches: tuple[RequirementBatch, ...]
    claims: tuple[VerifiedClaim, ...]
    rejected: tuple[RejectedClaim, ...]
    failed_units: tuple[FailedUnit, ...]
    status: str
    metrics: dict[str, object]
    llm_calls: tuple[dict, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "ClaimSet":
        value = json.loads(raw)
        value["framework_ids"] = tuple(value["framework_ids"])
        value["sources"] = tuple(value["sources"])
        value["chunks"] = tuple(Chunk(**chunk) for chunk in value["chunks"])
        value["batches"] = tuple(
            RequirementBatch(
                index=batch["index"],
                count=batch["count"],
                group_keys=tuple(batch["group_keys"]),
                requirement_ids=tuple(batch["requirement_ids"]),
                framework_ids=tuple(batch["framework_ids"]),
            )
            for batch in value["batches"]
        )
        value["claims"] = tuple(
            VerifiedClaim(
                **{
                    **claim,
                    "requirement_ids": tuple(claim["requirement_ids"]),
                    "framework_ids": tuple(claim["framework_ids"]),
                    "origins": tuple(claim["origins"]),
                }
            )
            for claim in value["claims"]
        )
        value["rejected"] = tuple(
            RejectedClaim(**{**item, "requirement_ids": tuple(item["requirement_ids"])})
            for item in value["rejected"]
        )
        value["failed_units"] = tuple(
            FailedUnit(**{**item, "requirement_ids": tuple(item["requirement_ids"])})
            for item in value["failed_units"]
        )
        value["llm_calls"] = tuple(value["llm_calls"])
        return cls(**value)

    def claims_for_requirement(self, requirement_id: str) -> tuple[VerifiedClaim, ...]:
        return tuple(claim for claim in self.claims if requirement_id in claim.requirement_ids)

    def affected_framework_ids(self) -> tuple[str, ...]:
        framework_by_requirement: dict[str, str] = {}
        for framework_id in self.framework_ids:
            for control in FrameworkRegistry.get(framework_id).all_controls():
                framework_by_requirement.setdefault(control.id, framework_id)
        affected = {
            framework_by_requirement[requirement_id]
            for unit in self.failed_units
            for requirement_id in unit.requirement_ids
            if requirement_id in framework_by_requirement
        }
        return tuple(framework_id for framework_id in self.framework_ids if framework_id in affected)

    def comparable(self) -> dict:
        value = json.loads(self.to_json())
        value.pop("claim_set_id", None)
        value.pop("created_at", None)
        for record in value["llm_calls"]:
            record.pop("latency_ms", None)
        return value


def claim_set_is_current(
    claim_set: ClaimSet,
    sources: Sequence[SourceDocument],
    framework_ids: Sequence[str],
) -> bool:
    if claim_set.schema_version != 1:
        return False
    if tuple(framework_ids) != claim_set.framework_ids:
        return False
    if claim_set.prompt_version != prompts.PROMPT_VERSION:
        return False
    if claim_set.prompt_fingerprints != prompts.prompt_fingerprints():
        return False
    try:
        versions = {
            framework_id: FrameworkRegistry.get(framework_id).version
            for framework_id in framework_ids
        }
    except KeyError:
        return False
    if claim_set.pack_versions != versions:
        return False
    if claim_set.settings != _setting_snapshot():
        return False
    expected_sources = [(source.source_id, source.text_sha256) for source in sources]
    actual_sources = [(source["source_id"], source["text_sha256"]) for source in claim_set.sources]
    return expected_sources == actual_sources
