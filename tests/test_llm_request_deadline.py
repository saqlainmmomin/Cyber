"""LLM request deadline: a provider call that never finishes is cut off by a
wall-clock deadline, recorded as an error, and retried once.

Seen live (2026-09-30): OpenRouter kept a stuck request open with keep-alive
bytes, so httpx's per-phase read timeout never fired and every in-flight call
of a validation run hung for over an hour, twice.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from app.config import settings
from app.services import llm_client

DEADLINE = 0.2


def _usage():
    return SimpleNamespace(prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None)


def _reply(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason="stop")],
        usage=_usage(),
    )


def _stream(text, stall: threading.Event | None = None):
    yield SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason=None)],
        usage=None,
    )
    if stall is not None:
        stall.wait(5)  # keep-alive-style stall mid-stream
    yield SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=""), finish_reason="stop")],
        usage=_usage(),
    )


class _Client:
    """Fake OpenAI client: each `create` pops the next behaviour."""

    def __init__(self, behaviours):
        self.behaviours = list(behaviours)
        self.calls = 0
        self.release = threading.Event()
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls += 1
        behaviour = self.behaviours.pop(0)
        if behaviour == "hang":
            self.release.wait(5)
            return _reply("late")
        if behaviour == "stream_hang":
            return _stream("partial", stall=self.release)
        if kwargs.get("stream"):
            return _stream(behaviour)
        return _reply(behaviour)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "llm_request_deadline_seconds", DEADLINE)

    def install(*behaviours):
        fake = _Client(behaviours)
        monkeypatch.setattr(llm_client, "_get_client", lambda: fake)
        return fake

    yield install


def _call(stream=False):
    return llm_client.call_llm(
        "judge", system="s", messages=[{"role": "user", "content": "u"}], max_tokens=10, stream=stream
    )


def test_call_past_deadline_is_retried_once_then_raises(client):
    fake = client("hang", "hang")
    try:
        with llm_client.collect_calls() as calls:
            with pytest.raises(llm_client.LLMRequestTimeout, match="deadline"):
                _call()
    finally:
        fake.release.set()
    assert fake.calls == 2
    assert [(c["status"], c["error_type"]) for c in calls] == [("error", "LLMRequestTimeout")] * 2
    assert "attempt" not in calls[0]
    assert calls[1]["attempt"] == 2
    assert all(c["latency_ms"] >= DEADLINE * 1000 * 0.9 for c in calls)
    assert isinstance(llm_client.LLMRequestTimeout("x"), TimeoutError)


def test_retry_after_deadline_succeeds(client):
    fake = client("hang", "ok text")
    try:
        with llm_client.collect_calls() as calls:
            result = _call()
    finally:
        fake.release.set()
    assert result["text"] == "ok text"
    assert result["usage"]["input_tokens"] == 10
    assert [(c["status"], c["error_type"]) for c in calls] == [
        ("error", "LLMRequestTimeout"),
        ("ok", None),
    ]
    assert calls[1]["attempt"] == 2


def test_fast_call_unchanged(client):
    fake = client("quick")
    with llm_client.collect_calls() as calls:
        result = _call()
    assert result["text"] == "quick"
    assert fake.calls == 1
    assert len(calls) == 1
    assert calls[0]["status"] == "ok"
    assert "attempt" not in calls[0]


def test_fast_stream_unchanged(client):
    client("streamed")
    with llm_client.collect_calls() as calls:
        result = _call(stream=True)
    assert result["text"] == "streamed"
    assert result["usage"]["output_tokens"] == 5
    assert [c["status"] for c in calls] == ["ok"]


def test_stream_stalled_mid_read_hits_deadline(client):
    """The deadline covers reading the stream, not just opening it."""
    fake = client("stream_hang", "streamed")
    try:
        with llm_client.collect_calls() as calls:
            result = _call(stream=True)
    finally:
        fake.release.set()
    assert result["text"] == "streamed"
    assert [(c["status"], c["error_type"]) for c in calls] == [
        ("error", "LLMRequestTimeout"),
        ("ok", None),
    ]


def test_provider_error_still_raises_unchanged(client, monkeypatch):
    class Boom(RuntimeError):
        pass

    def create(**kwargs):
        raise Boom("provider down")

    monkeypatch.setattr(
        llm_client,
        "_get_client",
        lambda: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))),
    )
    with llm_client.collect_calls() as calls:
        with pytest.raises(Boom):
            _call()
    assert [(c["status"], c["error_type"]) for c in calls] == [("error", "Boom")]


def test_default_deadline_covers_longest_legitimate_call():
    from app.config import Settings

    assert Settings.model_fields["llm_request_deadline_seconds"].default == 600.0
