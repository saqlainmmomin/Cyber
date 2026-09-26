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

Calls may also carry an optional batch tag in their records when a large
framework is split into deterministic analysis units.
"""

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
) -> None:
    """Record one call, adding the optional batch key only for batched work."""
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
    return {
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


def call_llm(
    tier: Tier,
    *,
    system: str | list[dict],
    messages: list[dict],
    max_tokens: int,
    temperature: float = 0,
    stream: bool = False,
    response_schema: dict | None = None,
) -> dict:
    """Make one LLM request for the given tier and return a plain dict.

    Return shape matches the app's existing usage contract:
    {"text": str, "usage": {"input_tokens", "output_tokens",
    "cache_read_input_tokens", "cache_creation_input_tokens"}}
    """
    model = getattr(settings, _TIER_MODELS[tier])
    request_messages = [{"role": "system", "content": system}, *messages]
    request_kwargs = {
        "model": model,
        "messages": request_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_schema is None:
        request_kwargs["extra_body"] = _REQUEST_PREFS
    else:
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
    if stream:
        request_kwargs.update(stream=True, stream_options={"include_usage": True})

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
            result = {"text": text, "usage": usage}
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
            result = {"text": text, "usage": usage}
    except Exception as exc:
        _record_call(
            tier=tier,
            model=model,
            usage=None,
            latency_ms=int((time.monotonic() - started) * 1000),
            finish_reason=finish_reason,
            status="error",
            error_type=type(exc).__name__,
        )
        raise

    _record_call(
        tier=tier,
        model=model,
        usage=usage,
        latency_ms=int((time.monotonic() - started) * 1000),
        finish_reason=finish_reason,
        status="ok",
        error_type=None,
    )
    return result


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
