"""Strict record/replay support for Claude analyzer calls."""

from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


def _normalize(value):
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    return value


def analyzer_request_key(args: tuple, kwargs: dict) -> str:
    """Hash the complete normalized request, including model and stream mode."""
    payload = json.dumps(
        _normalize({"args": args, "kwargs": kwargs}),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_recording(fixture_dir: Path) -> dict:
    path = fixture_dir / "mocked_analyzer_response.json"
    if not path.is_file():
        raise AssertionError(
            f"Analyzer recording missing: {path}. "
            "Run tests/support/fixture_capture.py to create it; live calls are disabled."
        )
    try:
        recording = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"Analyzer recording is unreadable: {path}: {exc}") from exc
    if not isinstance(recording.get("_meta"), dict) or not isinstance(recording.get("calls"), dict):
        raise AssertionError(f"Analyzer recording has an invalid schema: {path}")
    return recording


@contextmanager
def with_recorded_analyzer(fixture_dir: Path):
    """Replay every analyzer call and fail if any prompt is not recorded.

    Unknown calls are remembered and checked again on exit because production's
    optional evidence extraction path intentionally catches provider errors.
    """
    recording = _load_recording(fixture_dir)
    calls = recording["calls"]
    missing: list[str] = []

    def fake_call(*args, **kwargs):
        key = analyzer_request_key(args, kwargs)
        if key not in calls:
            missing.append(key)
            raise AssertionError(
                f"Analyzer made an uncached call. Key: {key}. "
                "Re-run tests/support/fixture_capture.py to update the recording."
            )
        return copy.deepcopy(calls[key])

    with patch("app.services.claude_analyzer._call_claude", side_effect=fake_call):
        try:
            yield recording["_meta"]
        finally:
            if missing:
                unique = ", ".join(dict.fromkeys(missing))
                raise AssertionError(
                    f"Analyzer made uncached call(s): {unique}. "
                    "Replay refused to fall back to a live Claude call."
                )


@contextmanager
def record_live_analyzer(fixture_dir: Path, metadata: dict):
    """Record genuine calls through the analyzer seam for an explicit live capture."""
    from app.services import claude_analyzer

    original = claude_analyzer._call_claude
    calls: dict[str, dict] = {}

    def passthrough(*args, **kwargs):
        result = original(*args, **kwargs)
        calls[analyzer_request_key(args, kwargs)] = copy.deepcopy(result)
        return result

    with patch("app.services.claude_analyzer._call_claude", side_effect=passthrough):
        yield calls

    payload = {"_meta": metadata, "calls": calls}
    (fixture_dir / "mocked_analyzer_response.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
