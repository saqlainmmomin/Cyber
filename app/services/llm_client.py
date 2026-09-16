"""Shared OpenRouter-backed LLM client.

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
"""

from typing import Literal

from openai import OpenAI

from app.config import settings

Tier = Literal["extract", "judge", "synthesize"]

_TIER_MODELS: dict[Tier, str] = {
    "extract": "llm_model_extract",
    "judge": "llm_model_judge",
    "synthesize": "llm_model_synthesize",
}

# Every request carries these documents (compliance policies, questionnaire
# answers) to OpenRouter. Without an explicit per-request policy, OpenRouter's
# default is data_collection="allow" — a provider behind a tier could store or
# train on client documents with nothing in this codebase recording it. Zero
# data retention is a hard requirement, not a preference: a provider/model
# combination that can't honor it should fail the request, not silently fall
# back to one that retains data.
_ZDR_PROVIDER_PREFS = {"provider": {"data_collection": "deny", "zdr": True}}

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_key,
            base_url=settings.openrouter_base_url,
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
) -> dict:
    """Make one LLM request for the given tier and return a plain dict.

    Return shape matches the app's existing usage contract:
    {"text": str, "usage": {"input_tokens", "output_tokens",
    "cache_read_input_tokens", "cache_creation_input_tokens"}}
    """
    model = getattr(settings, _TIER_MODELS[tier])
    client = _get_client()
    request_messages = [{"role": "system", "content": system}, *messages]

    if not stream:
        response = client.chat.completions.create(
            model=model,
            messages=request_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            extra_body=_ZDR_PROVIDER_PREFS,
        )
        text = response.choices[0].message.content
        return {"text": text, "usage": _usage_dict(response.usage)}

    chunks = client.chat.completions.create(
        model=model,
        messages=request_messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True},
        extra_body=_ZDR_PROVIDER_PREFS,
    )
    text_parts: list[str] = []
    usage = None
    for chunk in chunks:
        if chunk.choices:
            delta = chunk.choices[0].delta.content
            if delta:
                text_parts.append(delta)
        if getattr(chunk, "usage", None) is not None:
            usage = chunk.usage
    return {"text": "".join(text_parts), "usage": _usage_dict(usage)}
