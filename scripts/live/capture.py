"""Capture every LLM request and response of a live run, with no app change.

`llm_client.call_llm` sends each provider request through `llm_client._send`.
`install()` wraps that one function, so the full request body, the assembled
response text, the usage and the call tags are written to one JSON file per
send. It also wraps `llm_client._record_call` to count the app's own usage
records, so a run can prove that captured files equal usage records.

Captured files hold client document text. The output folder must be outside
the repository and is never committed. No API key or header is captured: the
wrapped function only sees the request body, and the client holds the key.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# USD per million tokens (input, output). Assumptions used only for the live
# spend meter and the hard stop; the provider's key usage is the ground truth.
PRICES_PER_MILLION: dict[str, tuple[float, float]] = {
    "deepseek/deepseek-v4-flash": (0.14, 0.28),
    "anthropic/claude-sonnet-4": (3.0, 15.0),
}
UNKNOWN_MODEL_PRICE = (3.0, 15.0)
_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/webp": "webp"}


class SpendCapExceeded(RuntimeError):
    """The running spend estimate passed the cap; the run stops."""


class RepeatedCallFailure(RuntimeError):
    """The same request failed twice; the run stops."""


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES_PER_MILLION.get(model, UNKNOWN_MODEL_PRICE)
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Capture:
    def __init__(self, out_dir: Path, *, spend_cap_usd: float = 5.0) -> None:
        out_dir = Path(out_dir).expanduser().resolve()
        if REPO_ROOT in (out_dir, *out_dir.parents):
            raise ValueError(f"capture folder must be outside the repository: {out_dir}")
        self.out_dir = out_dir
        self.calls_dir = out_dir / "calls"
        self.images_dir = out_dir / "images"
        for directory in (self.calls_dir, self.images_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.index_path = out_dir / "index.jsonl"
        self.spend_cap_usd = spend_cap_usd
        self.phase = ""
        self.estimated_spend = 0.0
        self.sends = 0
        self.usage_records = 0
        self.stop_reason: str | None = None
        self._failures: dict[str, int] = {}
        self._lock = threading.Lock()
        self._installed = False

    # -- install ---------------------------------------------------------

    def install(self) -> None:
        from app.services import llm_client

        if self._installed:
            return
        original_send = llm_client._send
        original_record = llm_client._record_call
        capture = self

        def captured_send(request_kwargs, *, tier, model, stream, attempt):
            return capture._send(
                original_send, llm_client, request_kwargs,
                tier=tier, model=model, stream=stream, attempt=attempt,
            )

        def counted_record(**kwargs):
            with capture._lock:
                capture.usage_records += 1
            return original_record(**kwargs)

        llm_client._send = captured_send
        llm_client._record_call = counted_record
        self._installed = True

    # -- the wrapped send -----------------------------------------------------

    def _send(self, original_send, llm_client, request_kwargs, *, tier, model, stream, attempt):
        if self.stop_reason:
            raise RuntimeError(f"live run stopped: {self.stop_reason}")
        tags = dict(llm_client._tags.get())
        request = self._scrub_request(request_kwargs)
        request_hash = hashlib.sha256(
            json.dumps(request, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        with self._lock:
            self.sends += 1
            number = self.sends
        record: dict[str, Any] = {
            "n": number,
            "ts": _now(),
            "phase": self.phase,
            "stage": tags.get("stage"),
            "framework_id": tags.get("framework_id"),
            "batch": tags.get("batch"),
            "tier": tier,
            "model": model,
            "attempt": attempt,
            "stream": stream,
            "request_hash": request_hash,
            "request": request,
        }
        started = time.monotonic()
        try:
            result, finish_reason, latency_ms = original_send(
                request_kwargs, tier=tier, model=model, stream=stream, attempt=attempt
            )
        except BaseException as exc:
            record.update(
                status="error",
                error_type=type(exc).__name__,
                error=str(exc)[:2000],
                latency_ms=int((time.monotonic() - started) * 1000),
                response=None,
                usage=None,
                finish_reason=None,
                est_cost_usd=0.0,
            )
            self._write(record)
            self._note_failure(request_hash, exc)
            raise
        usage = result.get("usage") or {}
        cost = estimate_cost(model, usage.get("input_tokens", 0), usage.get("output_tokens", 0))
        record.update(
            status="ok",
            error_type=None,
            error=None,
            latency_ms=latency_ms,
            response=result["text"],
            usage=usage,
            finish_reason=finish_reason,
            est_cost_usd=round(cost, 6),
        )
        self._write(record)
        with self._lock:
            self.estimated_spend += cost
            if self.estimated_spend > self.spend_cap_usd and not self.stop_reason:
                self.stop_reason = (
                    f"estimated spend ${self.estimated_spend:.2f} passed the "
                    f"${self.spend_cap_usd:.2f} cap"
                )
        return result, finish_reason, latency_ms

    def _note_failure(self, request_hash: str, exc: BaseException) -> None:
        with self._lock:
            count = self._failures.get(request_hash, 0) + 1
            self._failures[request_hash] = count
            if count >= 2 and not self.stop_reason:
                self.stop_reason = (
                    f"the same request failed twice ({type(exc).__name__}: {str(exc)[:200]})"
                )

    # -- files ----------------------------------------------------------------

    def _scrub_request(self, request_kwargs: dict) -> dict:
        """JSON-safe copy of the request body; image data URLs become files."""
        body = {
            key: value
            for key, value in request_kwargs.items()
            if key not in {"api_key", "extra_headers"}
        }
        body = json.loads(json.dumps(body, default=str))
        for message in body.get("messages", []):
            content = message.get("content")
            if isinstance(content, list):
                message["content"] = [self._scrub_part(part) for part in content]
        return body

    def _scrub_part(self, part: Any) -> Any:
        if not isinstance(part, dict) or part.get("type") != "image_url":
            return part
        url = (part.get("image_url") or {}).get("url", "")
        if not url.startswith("data:") or ";base64," not in url:
            return part
        header, data = url.split(",", 1)
        media_type = header[len("data:"):].split(";", 1)[0]
        raw = base64.b64decode(data)
        digest = hashlib.sha256(raw).hexdigest()
        name = f"{digest}.{_EXTENSIONS.get(media_type, 'bin')}"
        path = self.images_dir / name
        if not path.exists():
            path.write_bytes(raw)
        return {
            "type": "image_placeholder",
            "media_type": media_type,
            "bytes": len(raw),
            "sha256": digest,
            "file": f"images/{name}",
        }

    def _write(self, record: dict) -> None:
        stage = record.get("stage") or "untagged"
        framework = record.get("framework_id") or "none"
        name = f"{record['n']:05d}_{stage}_{framework}_{record['tier']}.json"
        record["file"] = f"calls/{name}"
        (self.calls_dir / name).write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary = {key: value for key, value in record.items() if key not in {"request", "response"}}
        usage = record.get("usage") or {}
        summary.update(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_read_input_tokens=usage.get("cache_read_input_tokens", 0),
            reasoning_tokens=usage.get("reasoning_tokens", 0),
        )
        summary.pop("usage", None)
        with self._lock, self.index_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(summary, ensure_ascii=False, sort_keys=True) + "\n")

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "sends_captured": self.sends,
                "usage_records": self.usage_records,
                "estimated_spend_usd": round(self.estimated_spend, 4),
                "spend_cap_usd": self.spend_cap_usd,
                "stop_reason": self.stop_reason,
            }


def key_usage_usd(api_key: str) -> float | None:
    """Total usage on the provider key, from its key endpoint. None on any
    failure. The key is sent as a bearer token and never printed or stored."""
    import urllib.request

    if not api_key:
        return None
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            data = json.loads(response.read().decode("utf-8"))
        usage = data.get("data", {}).get("usage")
        return float(usage) if usage is not None else None
    except Exception:  # noqa: BLE001 - spend lookup is best effort
        return None
