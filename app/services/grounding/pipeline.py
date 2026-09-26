"""Stages 0-1: deterministic grounding and bounded claim verification."""

from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.services import llm_client
from app.services.citations import MAX_EXCERPT_CHARS, locate_excerpt, normalize_with_offsets
from app.services.grounding import prompts
from app.services.grounding.batches import RequirementBatch, extraction_batches, requirement_order
from app.services.grounding.claims import (
    ClaimSet,
    FailedUnit,
    RejectedClaim,
    REJECTION_REASONS,
    VerifiedClaim,
    _setting_snapshot,
    _statement_norm,
    claim_id,
)
from app.services.grounding.chunking import Chunk, chunk_sources
from app.services.grounding.metadata import extract_metadata
from app.services.grounding.schemas import (
    ExtractionItem,
    SupportItem,
    parse_extraction_response,
    parse_support_response,
)
from app.services.grounding.sources import SourceDocument
from app.services.parallel import run_bounded


_TRUNCATION_MARKER = re.compile(r"\[\.\.\. truncated[^\]]*\]", re.I)


def _call_llm(*, tier: str, stream: bool = False, **request) -> dict:
    return llm_client.call_llm(tier, stream=stream, **request)


class ClaimBudgetExceeded(Exception):
    def __init__(self, planned: int, cap: int):
        self.planned = planned
        self.cap = cap
        super().__init__(f"planned extraction calls {planned} exceeds cap {cap}")


@dataclass(frozen=True)
class _ExtractionUnit:
    batch: RequirementBatch
    chunk: Chunk
    source: SourceDocument
    total_chunks: int
    total_chunks_all: int

    @property
    def label(self) -> str:
        return f"{self.batch.label}|c{self.chunk.global_index}/{self.total_chunks_all}"


@dataclass(frozen=True)
class _SupportUnit:
    candidates: tuple["_Candidate", ...]
    chunk: Chunk
    index: int
    count: int
    total_chunks: int

    @property
    def label(self) -> str:
        return f"c{self.chunk.global_index}/{self.total_chunks}:s{self.index}/{self.count}"


@dataclass
class _Candidate:
    source: SourceDocument
    chunk: Chunk
    start: int
    end: int
    model_quote: str
    statement: str
    original_statement: str | None
    kind: str
    stated_period: str | None
    stated_owner: str | None
    requirement_ids: tuple[str, ...]
    batch_label: str | None
    batch_index: int
    item_index: int
    origins: list[dict]
    kind_conflict: bool = False
    support: str | None = None
    needs_review: bool = False


@dataclass(frozen=True)
class _ParseFailure:
    pass


def _request(
    *, system: str, user: str, schema: dict, max_tokens: int
) -> dict:
    request = {
        "temperature": 0,
        "max_tokens": min(settings.llm_max_output_tokens_framework, max_tokens),
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if settings.v2_structured_output:
        request["response_schema"] = schema
    return _call_llm(tier="extract", stream=False, **request)


def _run_extraction(unit: _ExtractionUnit) -> list[dict] | _ParseFailure:
    system = prompts.build_extraction_system_prompt(unit.batch)
    user = prompts.build_extraction_user_prompt(unit.source, unit.chunk, unit.total_chunks)
    request = {
        "system": system,
        "user": user,
        "schema": prompts.EXTRACTION_SCHEMA,
        "max_tokens": settings.v2_extraction_max_tokens,
    }

    def attempt(label: str) -> list[dict]:
        with llm_client.call_tag(stage="claim_extraction", batch=label):
            response = _request(**request)
        return parse_extraction_response(response["text"])

    try:
        return attempt(unit.label)
    except ValueError as exc:
        if str(exc) != "parse_failure":
            raise
        try:
            return attempt(unit.label + "+retry")
        except ValueError as retry_exc:
            if str(retry_exc) == "parse_failure":
                return _ParseFailure()
            raise


def _run_support(unit: _SupportUnit, *, suffix: str = "") -> list[dict] | _ParseFailure:
    entries = [
        (f"c{index}", candidate.statement, candidate.source.text[candidate.start:candidate.end])
        for index, candidate in enumerate(unit.candidates, start=1)
    ]
    system = prompts.SUPPORT_SYSTEM_PROMPT
    user = prompts.build_support_user_prompt(entries)
    request = {
        "system": system,
        "user": user,
        "schema": prompts.SUPPORT_SCHEMA,
        "max_tokens": settings.v2_support_max_tokens,
    }
    label = unit.label + suffix

    def attempt(attempt_label: str) -> list[dict]:
        with llm_client.call_tag(stage="claim_support", batch=attempt_label):
            response = _request(**request)
        return parse_support_response(response["text"])

    try:
        return attempt(label)
    except ValueError as exc:
        if str(exc) != "parse_failure":
            raise
        try:
            return attempt(label + "+retry")
        except ValueError as retry_exc:
            if str(retry_exc) == "parse_failure":
                return _ParseFailure()
            raise


def _source_summaries(sources: Sequence[SourceDocument]) -> tuple[dict, ...]:
    result = []
    for source in sources:
        metadata = extract_metadata(source)
        result.append(
            {
                "source_id": source.source_id,
                "evidence_id": source.evidence_id,
                "evidence_version_id": source.evidence_version_id,
                "legacy_document_id": source.legacy_document_id,
                "filename": source.filename,
                "category": source.category,
                "mime_type": source.mime_type,
                "text_sha256": source.text_sha256,
                "char_count": len(source.text),
                "derived_from_image": source.derived_from_image,
                "metadata": {
                    "method": metadata.method,
                    "fields": [
                        {
                            "name": field.name,
                            "label": field.label,
                            "value": field.value,
                            "start": field.start,
                            "end": field.end,
                            "iso_date": field.iso_date,
                        }
                        for field in metadata.fields
                    ],
                },
            }
        )
    return tuple(result)


def _framework_requirement_map(framework_ids: Sequence[str]) -> dict[str, str]:
    result = {}
    for framework_id in framework_ids:
        for control in FrameworkRegistry.get(framework_id).all_controls():
            result[control.id] = framework_id
    return result


def _metric_template(sources, chunks, batches) -> dict[str, object]:
    return {
        "sources": len(sources),
        "empty_sources": sum(not source.text.strip() for source in sources),
        "chunks": len(chunks),
        "batches": len(batches),
        "extraction_calls_planned": len(chunks) * len(batches),
        "extraction_calls": 0,
        "extraction_retries": 0,
        "support_calls": 0,
        "support_retries": 0,
        "proposed": 0,
        "rejected_by_reason": {reason: 0 for reason in REJECTION_REASONS},
        "located": 0,
        "merged_duplicates": 0,
        "support": {key: 0 for key in ("yes", "partial", "no", "missing", "unusable", "unit_failed")},
        "verified": 0,
        "verified_by_framework": {},
        "requirements_with_claims": {},
        "unknown_requirement_ids": 0,
        "unverified_attributes_dropped": 0,
        "support_unknown_refs": 0,
        "delimiter_collisions": 0,
        "derived_from_image_claims": 0,
        "tokens": {
            "claim_extraction": {"input": 0, "output": 0},
            "claim_support": {"input": 0, "output": 0},
        },
        "failed_units": 0,
        "grounding_failure_rate": 0.0,
        "batch_system_prompt_sha256": {
            batch.label: hashlib.sha256(
                prompts.build_extraction_system_prompt(batch).encode("utf-8")
            ).hexdigest()
            for batch in batches
        },
    }


def _reject(
    rejected: list[RejectedClaim],
    metrics: dict[str, object],
    *,
    reason: str,
    source_id: str,
    chunk_id: str,
    batch: str | None,
    model_quote: str = "",
    statement: str = "",
    requirement_ids: Sequence[str] = (),
) -> None:
    rejected.append(
        RejectedClaim(
            reason=reason,
            source_id=source_id,
            chunk_id=chunk_id,
            batch=batch,
            model_quote=model_quote[:300],
            statement=statement[:300],
            requirement_ids=tuple(requirement_ids)[:20],
        )
    )
    metrics["rejected_by_reason"][reason] += 1


def _fold(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _marker_overlaps(text: str, start: int, end: int) -> bool:
    return any(match.start() < end and match.end() > start for match in _TRUNCATION_MARKER.finditer(text))


def _verify_items(
    *,
    items: Sequence[dict],
    unit: _ExtractionUnit,
    source_by_id: dict[str, SourceDocument],
    order: dict[str, tuple[int, int]],
    metrics: dict[str, object],
    rejected: list[RejectedClaim],
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    max_claims = settings.v2_max_claims_per_call
    for item_index, raw_item in enumerate(items, start=1):
        metrics["proposed"] += 1
        if item_index > max_claims:
            raw = raw_item if isinstance(raw_item, dict) else {}
            _reject(
                rejected,
                metrics,
                reason="over_call_cap",
                source_id=unit.source.source_id,
                chunk_id=unit.chunk.chunk_id,
                batch=unit.batch.label,
                model_quote=str(raw.get("quote", "")),
                statement=str(raw.get("statement", "")),
                requirement_ids=raw.get("requirement_ids", ()) if isinstance(raw.get("requirement_ids", ()), list) else (),
            )
            continue

        try:
            parsed = ExtractionItem.model_validate(raw_item)
        except Exception:
            raw = raw_item if isinstance(raw_item, dict) else {}
            _reject(
                rejected,
                metrics,
                reason="malformed_item",
                source_id=unit.source.source_id,
                chunk_id=unit.chunk.chunk_id,
                batch=unit.batch.label,
                model_quote=str(raw.get("quote", "")),
                statement=str(raw.get("statement", "")),
                requirement_ids=raw.get("requirement_ids", ()) if isinstance(raw.get("requirement_ids", ()), list) else (),
            )
            continue
        if not parsed.statement or len(parsed.statement) > 500:
            _reject(
                rejected,
                metrics,
                reason="malformed_item",
                source_id=unit.source.source_id,
                chunk_id=unit.chunk.chunk_id,
                batch=unit.batch.label,
                model_quote=parsed.quote,
                statement=parsed.statement,
                requirement_ids=parsed.requirement_ids,
            )
            continue

        valid_ids = set(unit.batch.requirement_ids)
        filtered_ids = []
        for requirement_id in parsed.requirement_ids:
            if requirement_id not in valid_ids:
                metrics["unknown_requirement_ids"] += 1
            elif requirement_id not in filtered_ids:
                filtered_ids.append(requirement_id)
        if not filtered_ids:
            _reject(
                rejected,
                metrics,
                reason="no_valid_requirement",
                source_id=unit.source.source_id,
                chunk_id=unit.chunk.chunk_id,
                batch=unit.batch.label,
                model_quote=parsed.quote,
                statement=parsed.statement,
                requirement_ids=parsed.requirement_ids,
            )
            continue
        filtered_ids.sort(key=order.__getitem__)

        normalized_quote, _ = normalize_with_offsets(parsed.quote)
        if len(parsed.quote) > settings.v2_max_quote_chars:
            _reject(rejected, metrics, reason="quote_too_long", source_id=unit.source.source_id, chunk_id=unit.chunk.chunk_id, batch=unit.batch.label, model_quote=parsed.quote, statement=parsed.statement, requirement_ids=parsed.requirement_ids)
            continue
        if len(normalized_quote) < settings.v2_min_quote_chars:
            _reject(rejected, metrics, reason="quote_too_short", source_id=unit.source.source_id, chunk_id=unit.chunk.chunk_id, batch=unit.batch.label, model_quote=parsed.quote, statement=parsed.statement, requirement_ids=parsed.requirement_ids)
            continue

        chunk_text = unit.source.text[unit.chunk.start:unit.chunk.end]
        local_span = locate_excerpt(chunk_text, parsed.quote)
        if local_span is None:
            if locate_excerpt(unit.source.text, parsed.quote) is not None:
                reason = "quote_outside_chunk"
            elif any(
                locate_excerpt(other.text, parsed.quote) is not None
                for source_id, other in source_by_id.items()
                if source_id != unit.source.source_id
            ):
                reason = "quote_in_other_document"
            elif _fold(normalized_quote) in _fold(normalize_with_offsets(chunk_text)[0]):
                reason = "quote_unicode_mismatch"
            else:
                reason = "quote_not_found"
            _reject(rejected, metrics, reason=reason, source_id=unit.source.source_id, chunk_id=unit.chunk.chunk_id, batch=unit.batch.label, model_quote=parsed.quote, statement=parsed.statement, requirement_ids=parsed.requirement_ids)
            continue

        start = unit.chunk.start + local_span[0]
        end = unit.chunk.start + local_span[1]
        if end - start > MAX_EXCERPT_CHARS:
            _reject(rejected, metrics, reason="quote_too_long", source_id=unit.source.source_id, chunk_id=unit.chunk.chunk_id, batch=unit.batch.label, model_quote=parsed.quote, statement=parsed.statement, requirement_ids=parsed.requirement_ids)
            continue
        if _marker_overlaps(unit.source.text, start, end):
            _reject(rejected, metrics, reason="quote_in_truncation_marker", source_id=unit.source.source_id, chunk_id=unit.chunk.chunk_id, batch=unit.batch.label, model_quote=parsed.quote, statement=parsed.statement, requirement_ids=parsed.requirement_ids)
            continue

        raw_slice = unit.source.text[start:end]
        stated_period = parsed.stated_period
        stated_owner = parsed.stated_owner
        for attribute in ("stated_period", "stated_owner"):
            value = getattr(parsed, attribute)
            if value is not None and locate_excerpt(raw_slice, value) is None:
                metrics["unverified_attributes_dropped"] += 1
                if attribute == "stated_period":
                    stated_period = None
                else:
                    stated_owner = None
        metrics["located"] += 1
        candidates.append(
            _Candidate(
                source=unit.source,
                chunk=unit.chunk,
                start=start,
                end=end,
                model_quote=parsed.quote,
                statement=parsed.statement,
                original_statement=None,
                kind=parsed.kind,
                stated_period=stated_period,
                stated_owner=stated_owner,
                requirement_ids=tuple(filtered_ids),
                batch_label=unit.batch.label,
                batch_index=unit.batch.index,
                item_index=item_index,
                origins=[{"batch": unit.batch.label, "chunk_id": unit.chunk.chunk_id}],
            )
        )
    return candidates


def _merge_into(existing: _Candidate, incoming: _Candidate, order: dict[str, tuple[int, int]], metrics: dict[str, object]) -> None:
    existing.requirement_ids = tuple(
        sorted(set(existing.requirement_ids) | set(incoming.requirement_ids), key=order.__getitem__)
    )
    for origin in incoming.origins:
        if origin not in existing.origins:
            existing.origins.append(origin)
    if incoming.stated_period is not None and existing.stated_period is None:
        existing.stated_period = incoming.stated_period
    if incoming.stated_owner is not None and existing.stated_owner is None:
        existing.stated_owner = incoming.stated_owner
    if incoming.kind != existing.kind:
        existing.kind_conflict = True
    existing.kind_conflict = existing.kind_conflict or incoming.kind_conflict
    if existing.original_statement is None:
        existing.original_statement = incoming.original_statement
    existing.needs_review = existing.needs_review or incoming.needs_review
    metrics["merged_duplicates"] += 1


def _merge_candidates(candidates: Sequence[_Candidate], order: dict[str, tuple[int, int]], metrics: dict[str, object]) -> list[_Candidate]:
    merged: dict[tuple[str, int, int, str], _Candidate] = {}
    for candidate in candidates:
        key = (candidate.source.source_id, candidate.start, candidate.end, _statement_norm(candidate.statement))
        existing = merged.get(key)
        if existing is None:
            merged[key] = candidate
        else:
            _merge_into(existing, candidate, order, metrics)
    return list(merged.values())


def _support_units(candidates: Sequence[_Candidate], total_chunks: int) -> list[_SupportUnit]:
    by_chunk: dict[int, list[_Candidate]] = defaultdict(list)
    for candidate in candidates:
        by_chunk[candidate.chunk.global_index].append(candidate)
    units: list[_SupportUnit] = []
    for global_index in sorted(by_chunk):
        group = sorted(by_chunk[global_index], key=lambda item: (item.start, item.end, _statement_norm(item.statement)))
        maximum = settings.v2_support_batch_max_claims
        if maximum <= 0:
            raise ValueError("v2_support_batch_max_claims must be positive")
        pieces = [group[offset:offset + maximum] for offset in range(0, len(group), maximum)]
        for index, piece in enumerate(pieces, start=1):
            units.append(_SupportUnit(tuple(piece), piece[0].chunk, index, len(pieces), total_chunks))
    return units


def _support_map(items: Sequence[dict], unit: _SupportUnit, metrics: dict[str, object]) -> dict[str, SupportItem]:
    refs = {f"c{index}" for index in range(1, len(unit.candidates) + 1)}
    result: dict[str, SupportItem] = {}
    for raw_item in items:
        try:
            item = SupportItem.model_validate(raw_item)
        except Exception:
            metrics["support_unknown_refs"] += 1
            continue
        if item.ref not in refs:
            metrics["support_unknown_refs"] += 1
            continue
        result.setdefault(item.ref, item)
    return result


def _apply_support(
    *,
    candidate: _Candidate,
    verdict: SupportItem | None,
    rejected: list[RejectedClaim],
    metrics: dict[str, object],
) -> bool:
    if verdict is None:
        metrics["support"]["missing"] += 1
        _reject(rejected, metrics, reason="support_missing", source_id=candidate.source.source_id, chunk_id=candidate.chunk.chunk_id, batch=None, model_quote=candidate.model_quote, statement=candidate.statement, requirement_ids=candidate.requirement_ids)
        return False
    if verdict.verdict == "no":
        metrics["support"]["no"] += 1
        _reject(rejected, metrics, reason="support_no", source_id=candidate.source.source_id, chunk_id=candidate.chunk.chunk_id, batch=None, model_quote=candidate.model_quote, statement=candidate.statement, requirement_ids=candidate.requirement_ids)
        return False
    if verdict.verdict == "partial":
        supported = verdict.supported_statement
        if not supported or len(supported) > 500:
            metrics["support"]["unusable"] += 1
            _reject(rejected, metrics, reason="support_partial_unusable", source_id=candidate.source.source_id, chunk_id=candidate.chunk.chunk_id, batch=None, model_quote=candidate.model_quote, statement=candidate.statement, requirement_ids=candidate.requirement_ids)
            return False
        candidate.original_statement = candidate.statement
        candidate.statement = supported
        candidate.support = "partial"
        candidate.needs_review = True
        metrics["support"]["partial"] += 1
        return True
    candidate.support = "yes"
    metrics["support"]["yes"] += 1
    return True


def _final_claims(
    candidates: Sequence[_Candidate],
    framework_ids: Sequence[str],
    requirement_frameworks: dict[str, str],
    source_positions: dict[str, int],
) -> tuple[VerifiedClaim, ...]:
    ordered = sorted(candidates, key=lambda item: (source_positions[item.source.source_id], item.start, item.end, _statement_norm(item.statement)))
    claims: list[VerifiedClaim] = []
    seen_ids: set[str] = set()
    for candidate in ordered:
        identifier = claim_id(candidate.source.source_id, candidate.start, candidate.end, candidate.statement)
        if identifier in seen_ids:
            raise AssertionError(f"duplicate claim id {identifier}")
        seen_ids.add(identifier)
        claim_frameworks = tuple(
            framework_id
            for framework_id in framework_ids
            if any(requirement_frameworks.get(requirement_id) == framework_id for requirement_id in candidate.requirement_ids)
        )
        raw_quote = candidate.source.text[candidate.start:candidate.end]
        citation = None
        if candidate.source.evidence_version_id is not None:
            citation = {
                "evidence_version_id": candidate.source.evidence_version_id,
                "location_type": "text_span",
                "location_ref": f"chars:{candidate.start}-{candidate.end}",
                "excerpt": raw_quote,
            }
        claims.append(
            VerifiedClaim(
                claim_id=identifier,
                source_id=candidate.source.source_id,
                evidence_id=candidate.source.evidence_id,
                evidence_version_id=candidate.source.evidence_version_id,
                filename=candidate.source.filename,
                chunk_id=candidate.chunk.chunk_id,
                start=candidate.start,
                end=candidate.end,
                quote=raw_quote,
                model_quote=candidate.model_quote,
                statement=candidate.statement,
                original_statement=candidate.original_statement,
                kind=candidate.kind,
                stated_period=candidate.stated_period,
                stated_owner=candidate.stated_owner,
                requirement_ids=candidate.requirement_ids,
                framework_ids=claim_frameworks,
                tag_status="suggested",
                support=candidate.support or "yes",
                needs_review=candidate.needs_review or candidate.kind_conflict or candidate.source.derived_from_image,
                kind_conflict=candidate.kind_conflict,
                derived_from_image=candidate.source.derived_from_image,
                origins=tuple(candidate.origins),
                citation=citation,
            )
        )
    return tuple(claims)


def _sort_calls(calls: Sequence[dict]) -> tuple[dict, ...]:
    stage_order = {"claim_extraction": 0, "claim_support": 1}
    return tuple(sorted(calls, key=lambda record: (stage_order.get(record.get("stage"), 99), record.get("batch", ""), record.get("status", ""))))


def _finish_metrics(metrics: dict[str, object], calls: Sequence[dict], claims: Sequence[VerifiedClaim], framework_ids: Sequence[str], failed_units: Sequence[FailedUnit]) -> None:
    extraction = [record for record in calls if record.get("stage") == "claim_extraction"]
    support = [record for record in calls if record.get("stage") == "claim_support"]
    metrics["extraction_calls"] = len(extraction)
    metrics["support_calls"] = len(support)
    metrics["extraction_retries"] = sum("+retry" in record.get("batch", "") for record in extraction)
    metrics["support_retries"] = sum("+retry" in record.get("batch", "") for record in support)
    for stage, records in (("claim_extraction", extraction), ("claim_support", support)):
        metrics["tokens"][stage]["input"] = sum(record.get("input_tokens", 0) for record in records)
        metrics["tokens"][stage]["output"] = sum(record.get("output_tokens", 0) for record in records)
    metrics["verified"] = len(claims)
    metrics["verified_by_framework"] = {
        framework_id: sum(framework_id in claim.framework_ids for claim in claims)
        for framework_id in framework_ids
    }
    metrics["requirements_with_claims"] = {
        framework_id: len({
            requirement_id
            for claim in claims
            if framework_id in claim.framework_ids
            for requirement_id in claim.requirement_ids
        })
        for framework_id in framework_ids
    }
    metrics["derived_from_image_claims"] = sum(claim.derived_from_image for claim in claims)
    metrics["failed_units"] = len(failed_units)
    locate_failures = sum(
        metrics["rejected_by_reason"][reason]
        for reason in (
            "quote_outside_chunk",
            "quote_in_other_document",
            "quote_unicode_mismatch",
            "quote_not_found",
        )
    )
    metrics["grounding_failure_rate"] = locate_failures / metrics["proposed"] if metrics["proposed"] else 0.0


def run_stages_0_1(sources: Sequence[SourceDocument], framework_ids: Sequence[str]) -> ClaimSet:
    """Run grounding without a DB; an enclosing call collector will not see these calls."""
    sources = tuple(sources)
    framework_ids = tuple(framework_ids)
    chunks = chunk_sources(sources)
    batches = extraction_batches(framework_ids)
    source_by_id = {source.source_id: source for source in sources}
    chunks_by_source: dict[str, tuple[Chunk, ...]] = {
        source.source_id: tuple(chunk for chunk in chunks if chunk.source_id == source.source_id)
        for source in sources
    }
    order = requirement_order(framework_ids)
    requirement_frameworks = _framework_requirement_map(framework_ids)
    metrics = _metric_template(sources, chunks, batches)
    metrics["delimiter_collisions"] = sum(
        "<<<" in source.text[chunk.start:chunk.end]
        or ">>>" in source.text[chunk.start:chunk.end]
        for chunk in chunks
        for source in sources
        if source.source_id == chunk.source_id
    )
    source_summaries = _source_summaries(sources)
    planned = len(chunks) * len(batches)
    if planned > settings.v2_max_extraction_calls:
        raise ClaimBudgetExceeded(planned, settings.v2_max_extraction_calls)

    def empty_claim_set() -> ClaimSet:
        return ClaimSet(
            schema_version=1,
            claim_set_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            framework_ids=framework_ids,
            pack_versions={framework_id: FrameworkRegistry.get(framework_id).version for framework_id in framework_ids},
            prompt_version=prompts.PROMPT_VERSION,
            prompt_fingerprints=prompts.prompt_fingerprints(),
            settings=_setting_snapshot(),
            sources=source_summaries,
            chunks=chunks,
            batches=batches,
            claims=(),
            rejected=(),
            failed_units=(),
            status="complete",
            metrics=metrics,
            llm_calls=(),
        )

    if planned == 0:
        return empty_claim_set()

    units = [
        _ExtractionUnit(
            batch=batch,
            chunk=chunk,
            source=source_by_id[chunk.source_id],
            total_chunks=len(chunks_by_source[chunk.source_id]),
            total_chunks_all=len(chunks),
        )
        for batch in batches
        for chunk in chunks
    ]
    rejected: list[RejectedClaim] = []
    failed_units: list[FailedUnit] = []
    located_candidates: list[_Candidate] = []
    with llm_client.collect_calls() as calls:
        extraction_results = run_bounded(
            _run_extraction,
            units,
            max_workers=settings.llm_max_concurrency,
        )
        for unit, (result, error) in zip(units, extraction_results):
            if error is not None:
                failed_units.append(
                    FailedUnit(
                        stage="claim_extraction",
                        label=unit.label,
                        chunk_id=unit.chunk.chunk_id,
                        requirement_ids=unit.batch.requirement_ids,
                        error=f"{type(error).__name__}: {error}"[:500],
                    )
                )
                continue
            if isinstance(result, _ParseFailure):
                failed_units.append(
                    FailedUnit(
                        stage="claim_extraction",
                        label=unit.label,
                        chunk_id=unit.chunk.chunk_id,
                        requirement_ids=unit.batch.requirement_ids,
                        error="parse_failure",
                    )
                )
                continue
            located_candidates.extend(
                _verify_items(
                    items=result,
                    unit=unit,
                    source_by_id=source_by_id,
                    order=order,
                    metrics=metrics,
                    rejected=rejected,
                )
            )

        merged = _merge_candidates(located_candidates, order, metrics)
        support_units = _support_units(merged, len(chunks))
        support_results = run_bounded(
            _run_support,
            support_units,
            max_workers=settings.llm_max_concurrency,
        )
        verdicts: dict[int, SupportItem] = {}
        missing_units: list[tuple[_SupportUnit, tuple[_Candidate, ...]]] = []
        failed_support_ids: set[int] = set()
        for unit, (result, error) in zip(support_units, support_results):
            if error is not None or isinstance(result, _ParseFailure):
                failed_units.append(
                    FailedUnit(
                        stage="claim_support",
                        label=unit.label,
                        chunk_id=unit.chunk.chunk_id,
                        requirement_ids=tuple(sorted({rid for candidate in unit.candidates for rid in candidate.requirement_ids}, key=order.__getitem__)),
                        error=("parse_failure" if isinstance(result, _ParseFailure) else f"{type(error).__name__}: {error}")[:500],
                    )
                )
                failed_support_ids.update(id(candidate) for candidate in unit.candidates)
                continue
            mapped = _support_map(result, unit, metrics)
            missing = tuple(
                candidate
                for index, candidate in enumerate(unit.candidates, start=1)
                if f"c{index}" not in mapped
            )
            for index, candidate in enumerate(unit.candidates, start=1):
                if f"c{index}" in mapped:
                    verdicts[id(candidate)] = mapped[f"c{index}"]
            if missing:
                missing_units.append((unit, missing))

        retry_units = [
            _SupportUnit(candidates, original.chunk, original.index, original.count, original.total_chunks)
            for original, candidates in missing_units
        ]
        retry_results = run_bounded(
            lambda retry_unit: _run_support(retry_unit, suffix="+missing"),
            retry_units,
            max_workers=settings.llm_max_concurrency,
        )
        for (_original, missing), retry_unit, (result, error) in zip(missing_units, retry_units, retry_results):
            if error is not None or isinstance(result, _ParseFailure):
                failed_units.append(
                    FailedUnit(
                        stage="claim_support",
                        label=retry_unit.label + "+missing",
                        chunk_id=retry_unit.chunk.chunk_id,
                        requirement_ids=tuple(sorted({rid for candidate in missing for rid in candidate.requirement_ids}, key=order.__getitem__)),
                        error=("parse_failure" if isinstance(result, _ParseFailure) else f"{type(error).__name__}: {error}")[:500],
                    )
                )
                failed_support_ids.update(id(candidate) for candidate in missing)
                continue
            mapped = _support_map(result, retry_unit, metrics)
            for index, candidate in enumerate(missing, start=1):
                if f"c{index}" in mapped:
                    verdicts[id(candidate)] = mapped[f"c{index}"]

        supported: list[_Candidate] = []
        for candidate in merged:
            if id(candidate) in failed_support_ids:
                metrics["support"]["unit_failed"] += 1
                _reject(rejected, metrics, reason="support_unit_failed", source_id=candidate.source.source_id, chunk_id=candidate.chunk.chunk_id, batch=None, model_quote=candidate.model_quote, statement=candidate.statement, requirement_ids=candidate.requirement_ids)
                continue
            verdict = verdicts.get(id(candidate))
            if _apply_support(candidate=candidate, verdict=verdict, rejected=rejected, metrics=metrics):
                supported.append(candidate)

        final_candidates = _merge_candidates(supported, order, metrics)
        claims = _final_claims(
            final_candidates,
            framework_ids,
            requirement_frameworks,
            {source.source_id: index for index, source in enumerate(sources)},
        )
        sorted_calls = _sort_calls(calls)
        _finish_metrics(metrics, sorted_calls, claims, framework_ids, failed_units)

    return ClaimSet(
        schema_version=1,
        claim_set_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        framework_ids=framework_ids,
        pack_versions={framework_id: FrameworkRegistry.get(framework_id).version for framework_id in framework_ids},
        prompt_version=prompts.PROMPT_VERSION,
        prompt_fingerprints=prompts.prompt_fingerprints(),
        settings=_setting_snapshot(),
        sources=source_summaries,
        chunks=chunks,
        batches=batches,
        claims=claims,
        rejected=tuple(rejected),
        failed_units=tuple(failed_units),
        status="complete" if not failed_units else "incomplete",
        metrics=metrics,
        llm_calls=_sort_calls(calls),
    )
