"""The live-run capture wraps the one provider boundary and changes nothing else."""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest

from app.services import llm_client
from scripts.live.capture import Capture, SpendCapExceeded, estimate_cost  # noqa: F401


class _FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        usage = SimpleNamespace(
            prompt_tokens=reply.get("in", 100),
            completion_tokens=reply.get("out", 10),
            prompt_tokens_details=SimpleNamespace(cached_tokens=reply.get("cached", 0)),
            completion_tokens_details=None,
        )
        choice = SimpleNamespace(
            finish_reason=reply.get("finish", "stop"),
            message=SimpleNamespace(content=reply["text"]),
        )
        return SimpleNamespace(choices=[choice], usage=usage)


@pytest.fixture
def fake_provider(monkeypatch, tmp_path):
    originals = (llm_client._send, llm_client._record_call)
    completions = _FakeCompletions([])
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr(llm_client, "_get_client", lambda: fake_client)
    yield completions
    llm_client._send, llm_client._record_call = originals


def _capture(tmp_path, monkeypatch, **kwargs):
    # tmp_path is outside the repo, as the real run folder must be.
    return Capture(tmp_path / "run", **kwargs)


def test_capture_writes_request_response_tags_and_matches_usage_records(fake_provider, tmp_path, monkeypatch):
    capture = _capture(tmp_path, monkeypatch)
    capture.install()
    fake_provider.replies.extend([{"text": '{"a": 1}', "in": 1000, "out": 50, "cached": 400}])
    capture.phase = "desk_review"

    with llm_client.call_tag(stage="desk_review", framework_id="iso27001", batch="b1"):
        result = llm_client.call_llm(
            "extract", system="SYSTEM TEXT", messages=[{"role": "user", "content": "USER TEXT"}],
            max_tokens=100, json_output=True,
        )

    assert result["text"] == '{"a": 1}'
    files = sorted((tmp_path / "run" / "calls").glob("*.json"))
    assert len(files) == 1
    record = json.loads(files[0].read_text())
    assert record["stage"] == "desk_review" and record["framework_id"] == "iso27001" and record["batch"] == "b1"
    assert record["phase"] == "desk_review" and record["tier"] == "extract" and record["attempt"] == 1
    assert record["request"]["messages"][0] == {"role": "system", "content": "SYSTEM TEXT"}
    assert record["request"]["messages"][1]["content"] == "USER TEXT"
    assert record["response"] == '{"a": 1}'
    assert record["usage"]["input_tokens"] == 1000 and record["usage"]["cache_read_input_tokens"] == 400
    assert record["status"] == "ok" and record["finish_reason"] == "stop"
    snapshot = capture.snapshot()
    assert snapshot["sends_captured"] == snapshot["usage_records"] == 1
    index = [json.loads(line) for line in (tmp_path / "run" / "index.jsonl").read_text().splitlines()]
    assert index[0]["input_tokens"] == 1000 and "request" not in index[0] and "response" not in index[0]


def test_images_become_placeholders_and_are_saved(fake_provider, tmp_path, monkeypatch):
    capture = _capture(tmp_path, monkeypatch)
    capture.install()
    fake_provider.replies.append({"text": "VISIBLE TEXT: x"})
    raw = b"\x89PNG fake image bytes"
    url = "data:image/png;base64," + base64.b64encode(raw).decode()

    llm_client.call_llm(
        "vision", system="s",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "read this"},
            {"type": "image_url", "image_url": {"url": url}},
        ]}],
        max_tokens=50,
    )

    record = json.loads(next((tmp_path / "run" / "calls").glob("*.json")).read_text())
    part = record["request"]["messages"][1]["content"][1]
    assert part["type"] == "image_placeholder" and part["bytes"] == len(raw)
    assert "base64" not in json.dumps(record)
    assert (tmp_path / "run" / part["file"]).read_bytes() == raw


def test_errors_are_captured_and_a_repeated_failure_stops_the_run(fake_provider, tmp_path, monkeypatch):
    capture = _capture(tmp_path, monkeypatch)
    capture.install()
    fake_provider.replies.extend([RuntimeError("boom"), RuntimeError("boom")])
    kwargs = dict(system="s", messages=[{"role": "user", "content": "same"}], max_tokens=10)

    for _ in range(2):
        with pytest.raises(RuntimeError):
            llm_client.call_llm("judge", **kwargs)

    assert capture.stop_reason and "failed twice" in capture.stop_reason
    records = [json.loads(path.read_text()) for path in sorted((tmp_path / "run" / "calls").glob("*.json"))]
    assert [record["status"] for record in records] == ["error", "error"]
    assert records[0]["error_type"] == "RuntimeError"
    with pytest.raises(RuntimeError, match="live run stopped"):
        llm_client.call_llm("judge", **kwargs)


def test_spend_cap_stops_the_next_call(fake_provider, tmp_path, monkeypatch):
    capture = _capture(tmp_path, monkeypatch, spend_cap_usd=0.01)
    capture.install()
    # 1M input tokens of the flash model is $0.14, far over a one cent cap.
    fake_provider.replies.append({"text": "ok", "in": 1_000_000, "out": 0})
    model = llm_client.settings.llm_model_judge
    assert estimate_cost(model, 1_000_000, 0) > 0.01

    llm_client.call_llm("judge", system="s", messages=[{"role": "user", "content": "x"}], max_tokens=5)

    assert capture.stop_reason and "cap" in capture.stop_reason
    with pytest.raises(RuntimeError, match="live run stopped"):
        llm_client.call_llm("judge", system="s", messages=[{"role": "user", "content": "y"}], max_tokens=5)


def test_capture_folder_inside_the_repository_is_refused():
    from scripts.live.capture import REPO_ROOT

    with pytest.raises(ValueError, match="outside the repository"):
        Capture(REPO_ROOT / "data" / "live-run")
