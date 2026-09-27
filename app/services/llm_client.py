"""Shared provider-agnostic LLM client.

One call boundary for every tiered LLM request. `tier` selects the model via
`Settings.llm_model_*` — callers never name a model directly, so swapping a
tier's model is a config change, not a code change.

OpenRouter's API is OpenAI-chat-completions-shaped for every provider it
proxies (including Anthropic), so this always speaks that shape regardless
of which model ends up behind a tier. `system` accepts either a plain string
or the Anthropic-style content-block list `app/dpdpa/prompts.py` already
builds for prompt caching (`[{"type": "text", "text": ..., "cache_control":
{...}}]`) — the blocks are forwarded as-is inside the system message's
content array, which OpenRouter passes through to Anthropic-backed models
for cache_control; other providers just see the text.

Image input (the `vision` tier) must be given in OpenAI's content-block
shape too — `{"type": "image_url", "image_url": {"url": "data:<media_type>;
base64,<data>"}}` inside a message's `content` list — not Anthropic's native
`{"type": "image", "source": {...}}`. OpenRouter translates that shape to
whatever the underlying vision model actually needs.

Callers describe structured output with a JSON schema only. This module maps
that provider-agnostic request to OpenRouter's response_format today; the
future Bedrock migration maps the same schema to Converse tool use.

Callers that parse free-form JSON pass `json_output=True`: the request asks
for a JSON object without narrowing the provider pool, and a reply that does
not parse is recorded as `status="parse_error"` and retried once.

Calls may also carry an optional batch tag in their records when a large
framework is split into deterministic analysis units.
"""

import json
import logging
import re
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Literal

from openai import OpenAI

from app.config import settings

Tier = Literal["extract", "judge", "synthesize", "vision"]

_TIER_MODELS: dict[Tier, str] = {
    "extract": "llm_model_extract",
    "judge": "llm_model_judge",
    "synthesize": "llm_model_synthesize",
    "vision": "llm_model_vision",
}

# Every request carries these documents (compliance policies, questionnaire
# answers) to OpenRouter. Without an explicit per-request policy, OpenRouter's
# default is data_collection="allow" — a provider behind a tier could store or
# train on client documents with nothing in this codebase recording it. Zero
# data retention is a hard requirement, not a preference: a provider/model
# combination that can't honor it should fail the request, not silently fall
# back to one that retains data.
#
# `reasoning: {"enabled": False}` turns hidden chain-of-thought off. The
# earlier `{"exclude": True}` only hid it from the response; the model still
# reasoned and billed it against max_tokens. Found live twice: deepseek-v4-pro
# (then the judge tier) spent up to ~94% of a 4096-token screening budget on
# invisible reasoning; and on 2026-09-26 deepseek-v4-flash (every text tier)
# still reasoned on some OpenRouter providers under `exclude` - 6 of 8
# identical context-profile calls exhausted a 1,024-token budget with no
# usable content, one 8,192-token call reasoned for all 8,192 tokens (342 s),
# and an ISO desk-review and a judge batch each ended "length" on hidden
# reasoning. With `enabled: False`, 16 of 16 calls used 0 reasoning tokens.
# No call site in this app wants hidden reasoning.
_REQUEST_PREFS = {
    "provider": {"data_collection": "deny", "zdr": True},
    "reasoning": {"enabled": False},
}

# JSON mode for callers that parse free-form JSON (desk review, evidence
# extraction), whose outputs (maps keyed by requirement id) can't be written
# as a strict json_schema. Seen live: 4 of 148 calls returned a Markdown
# report with finish_reason="stop" and were recorded "ok".
#
# Deliberately sent WITHOUT `provider.require_parameters`. With it,
# OpenRouter only routes to endpoints that support every parameter in the
# request, intersected with the ZDR + data_collection="deny" pool above; that
# intersection can be empty ("no endpoints found") and would turn a
# formatting nudge into a hard outage. Without it, endpoints that support
# response_format enforce JSON and the rest ignore the field, so the routable
# pool is exactly today's and ZDR is still enforced. The parse check and one
# retry in `call_llm` are the backstop for endpoints that ignore it.
# `response_schema` (strict json_schema + require_parameters) stays the
# stricter path, used only where it has been proven live (v2 grounding).
_JSON_OBJECT_FORMAT = {"type": "json_object"}
_JSON_ATTEMPTS = 2

logger = logging.getLogger(__name__)


class LLMOutputParseError(ValueError):
    """A `json_output=True` call returned non-JSON text on every attempt."""


_client: OpenAI | None = None
_collector: ContextVar[list[dict] | None] = ContextVar("llm_call_collector", default=None)
_tags: ContextVar[dict[str, str | None]] = ContextVar("llm_call_tags", default={})
_collector_lock = threading.Lock()


@contextmanager
def collect_calls():
    """Collect calls made in this context, including propagated worker contexts."""
    calls: list[dict] = []
    token = _collector.set(calls)
    try:
        yield calls
    finally:
        _collector.reset(token)


@contextmanager
def call_tag(
    *,
    stage: str | None = None,
    framework_id: str | None = None,
    batch: str | None = None,
):
    """Tag calls in this context; nested tags override only supplied values."""
    tags = dict(_tags.get())
    if stage is not None:
        tags["stage"] = stage
    if framework_id is not None:
        tags["framework_id"] = framework_id
    if batch is not None:
        tags["batch"] = batch
    token = _tags.set(tags)
    try:
        yield
    finally:
        _tags.reset(token)


def _record_call(
    *,
    tier: Tier,
    model: str,
    usage: dict[str, int] | None,
    latency_ms: int,
    finish_reason: str | None,
    status: str,
    error_type: str | None,
    attempt: int = 1,
) -> None:
    """Record one call, adding the optional batch key only for batched work,
    reasoning_tokens only when the provider reports it, and attempt only on a
    JSON-parse retry (attempt 2+)."""
    collector = _collector.get()
    if collector is None:
        return
    tags = _tags.get()
    record = {
        "tier": tier,
        "model": model,
        "stage": tags.get("stage"),
        "framework_id": tags.get("framework_id"),
        "input_tokens": usage["input_tokens"] if usage else 0,
        "output_tokens": usage["output_tokens"] if usage else 0,
        "cache_read_input_tokens": usage["cache_read_input_tokens"] if usage else 0,
        "latency_ms": latency_ms,
        "finish_reason": finish_reason,
        "status": status,
        "error_type": error_type,
    }
    if tags.get("batch") is not None:
        record["batch"] = tags["batch"]
    if usage and "reasoning_tokens" in usage:
        record["reasoning_tokens"] = usage["reasoning_tokens"]
    if attempt > 1:
        record["attempt"] = attempt
    with _collector_lock:
        collector.append(record)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_key,
            base_url=settings.openrouter_base_url,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    return _client


def _usage_dict(usage) -> dict[str, int]:
    """Normalize an OpenAI-compatible usage object to the app's usage shape."""
    if usage is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
    details = getattr(usage, "prompt_tokens_details", None)
    cache_read = getattr(details, "cached_tokens", 0) or 0
    result = {
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "cache_read_input_tokens": cache_read,
        # OpenAI-shaped usage has no separate "cache write" concept the way
        # Anthropic's native API does — providers that bill for cache
        # creation would need to surface it as a non-standard usage field.
        # Not observed yet; verify against a live response before relying
        # on this for cost accounting.
        "cache_creation_input_tokens": 0,
    }
    # Reasoning is turned off on every request; surface any that still gets
    # billed so a provider ignoring that shows up in the call records.
    reasoning = getattr(
        getattr(usage, "completion_tokens_details", None), "reasoning_tokens", None
    )
    if reasoning is not None:
        result["reasoning_tokens"] = reasoning
    return result


def call_llm(
    tier: Tier,
    *,
    system: str | list[dict],
    messages: list[dict],
    max_tokens: int,
    temperature: float = 0,
    stream: bool = False,
    response_schema: dict | None = None,
    json_output: bool = False,
) -> dict:
    """Make one LLM request for the given tier and return a plain dict.

    Return shape matches the app's existing usage contract:
    {"text": str, "usage": {"input_tokens", "output_tokens",
    "cache_read_input_tokens", "cache_creation_input_tokens"}}

    `json_output=True` asks for a JSON object (see `_JSON_OBJECT_FORMAT`) and
    checks the returned text parses as JSON. A reply that does not parse is
    recorded with `status="parse_error"` and retried once; if the retry does
    not parse either, `LLMOutputParseError` is raised. A reply truncated at
    `max_tokens` (finish_reason="length") is not retried: the identical
    request would truncate again at double the cost.
    """
    model = getattr(settings, _TIER_MODELS[tier])
    request_messages = [{"role": "system", "content": system}, *messages]
    request_kwargs = {
        "model": model,
        "messages": request_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_schema is not None:
        request_kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": response_schema["name"],
                "strict": True,
                "schema": response_schema["schema"],
            },
        }
        request_kwargs["extra_body"] = {
            **_REQUEST_PREFS,
            "provider": {
                **_REQUEST_PREFS["provider"],
                "require_parameters": True,
            },
        }
    elif json_output:
        request_kwargs["response_format"] = _JSON_OBJECT_FORMAT
        request_kwargs["extra_body"] = _REQUEST_PREFS
    else:
        request_kwargs["extra_body"] = _REQUEST_PREFS
    if stream:
        request_kwargs.update(stream=True, stream_options={"include_usage": True})

    attempts = _JSON_ATTEMPTS if json_output else 1
    for attempt in range(1, attempts + 1):
        result, finish_reason, latency_ms = _send(
            request_kwargs, tier=tier, model=model, stream=stream, attempt=attempt
        )
        parse_ok = not json_output or is_json_text(result["text"])
        _record_call(
            tier=tier,
            model=model,
            usage=result["usage"],
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            status="ok" if parse_ok else "parse_error",
            error_type=None if parse_ok else "JSONDecodeError",
            attempt=attempt,
        )
        if parse_ok:
            return result
        if finish_reason == "length":
            break
        logger.warning(
            "LLM reply for tier=%s model=%s was not JSON (finish_reason=%r, attempt %d/%d): %.200r",
            tier,
            model,
            finish_reason,
            attempt,
            attempts,
            result["text"],
        )
    raise LLMOutputParseError(
        f"LLM reply for tier={tier!r} model={model!r} was not valid JSON after "
        f"{attempt} attempt(s) (finish_reason={finish_reason!r}). "
        f"Last reply starts: {result['text'][:300]!r}"
    )


def _send(
    request_kwargs: dict, *, tier: Tier, model: str, stream: bool, attempt: int
) -> tuple[dict, str | None, int]:
    """Send one request. Records the call itself only when it raises."""
    started = time.monotonic()
    finish_reason = None
    try:
        response = _get_client().chat.completions.create(**request_kwargs)
        if not stream:
            choice = response.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            text = choice.message.content
            _require_content(text, tier=tier, model=model, finish_reason=finish_reason)
            usage = _usage_dict(response.usage)
        else:
            text_parts: list[str] = []
            usage_obj = None
            for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        text_parts.append(delta)
                    chunk_finish_reason = getattr(chunk.choices[0], "finish_reason", None)
                    if chunk_finish_reason:
                        finish_reason = chunk_finish_reason
                if getattr(chunk, "usage", None) is not None:
                    usage_obj = chunk.usage
            text = "".join(text_parts)
            _require_content(text, tier=tier, model=model, finish_reason=finish_reason)
            usage = _usage_dict(usage_obj)
    except Exception as exc:
        _record_call(
            tier=tier,
            model=model,
            usage=None,
            latency_ms=int((time.monotonic() - started) * 1000),
            finish_reason=finish_reason,
            status="error",
            error_type=type(exc).__name__,
            attempt=attempt,
        )
        raise
    return (
        {"text": text, "usage": usage},
        finish_reason,
        int((time.monotonic() - started) * 1000),
    )


def is_json_text(text: str) -> bool:
    """True when `text` parses as JSON after stripping one Markdown code fence,
    the same tolerance the analyzer and desk-review parsers apply."""
    text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    text = re.sub(r"\n?```\s*$", "", text).strip()
    try:
        json.loads(text)
    except json.JSONDecodeError:
        return False
    return True


def _require_content(text: str | None, *, tier: Tier, model: str, finish_reason: str | None) -> None:
    """Fail loudly at the provider boundary instead of letting `None`/empty text
    reach a caller's parser as a confusing `AttributeError`/`JSONDecodeError` far
    from the actual cause. Seen live: a reasoning model can hit its token budget
    (`finish_reason="length"`) with nothing but hidden reasoning tokens spent,
    leaving `content` empty even though the request "succeeded"."""
    if not text:
        raise RuntimeError(
            f"LLM returned no content for tier={tier!r} model={model!r} "
            f"(finish_reason={finish_reason!r}). If finish_reason is 'length', "
            "the model likely exhausted max_tokens — on a reasoning model check "
            "whether reasoning tokens consumed the budget before any answer was written."
        )
