"""Build one HTML report for a captured live run.

    .venv/bin/python -m scripts.live.report <run folder>

Reads `index.jsonl`, `calls/*.json`, `run.json` and `uploads.json` from the run
folder and writes `report.html` beside them: a per-stage table, the
measurements the document-reads plan needs, and every call with what was sent
and what came back. The page embeds the call data, so it holds client document
text. Keep the folder private and never commit it.
"""

from __future__ import annotations

import html
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def _load(run: Path) -> tuple[dict, list[dict], dict]:
    run_json = json.loads((run / "run.json").read_text(encoding="utf-8")) if (run / "run.json").exists() else {}
    uploads = json.loads((run / "uploads.json").read_text(encoding="utf-8")) if (run / "uploads.json").exists() else {}
    calls = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((run / "calls").glob("*.json"))]
    return run_json, calls, uploads


def _words(request: dict) -> int:
    total = 0
    for message in request.get("messages", []):
        content = message.get("content")
        if isinstance(content, str):
            total += len(content.split())
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += len(str(part.get("text", "")).split())
                elif isinstance(part, str):
                    total += len(part.split())
    return total


def _usage(call: dict, key: str) -> int:
    return int((call.get("usage") or {}).get(key, 0) or 0)


def _stage_key(call: dict) -> str:
    return " / ".join(
        part for part in (call.get("stage") or "untagged", call.get("framework_id") or "") if part
    )


def _pct(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(pct * (len(ordered) - 1))))]


def _fmt(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}"


def stage_rows(calls: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for call in calls:
        groups[_stage_key(call)].append(call)
    rows = []
    for key, items in groups.items():
        ok = [c for c in items if c["status"] == "ok"]
        seconds = [c["latency_ms"] / 1000 for c in items]
        words = [_words(c["request"]) for c in ok]
        in_tokens = [_usage(c, "input_tokens") for c in ok]
        per_word = [t / w for t, w in zip(in_tokens, words) if w]
        rows.append({
            "stage": key,
            "calls": len(items),
            "errors": len(items) - len(ok),
            "length": sum(1 for c in items if c.get("finish_reason") == "length"),
            "input": sum(in_tokens),
            "output": sum(_usage(c, "output_tokens") for c in ok),
            "cached": sum(_usage(c, "cache_read_input_tokens") for c in ok),
            "reasoning": sum(_usage(c, "reasoning_tokens") for c in ok),
            "cost": sum(c.get("est_cost_usd", 0) for c in items),
            "seconds_total": sum(seconds),
            "seconds_mean": statistics.fmean(seconds) if seconds else 0,
            "seconds_p50": _pct(seconds, 0.5),
            "seconds_max": max(seconds) if seconds else 0,
            "out_mean": statistics.fmean([_usage(c, "output_tokens") for c in ok]) if ok else 0,
            "out_max": max([_usage(c, "output_tokens") for c in ok], default=0),
            "tokens_per_word": statistics.fmean(per_word) if per_word else 0,
        })
    return sorted(rows, key=lambda r: r["stage"])


def _call_summary(call: dict) -> str:
    return (
        f"#{call['n']} {html.escape(call.get('phase') or '')} · {html.escape(_stage_key(call))}"
        f"{' · ' + html.escape(str(call['batch'])) if call.get('batch') else ''}"
        f" · {html.escape(call['model'])} · in {_usage(call, 'input_tokens'):,} / out {_usage(call, 'output_tokens'):,}"
        f" · {call['latency_ms'] / 1000:.1f}s · {html.escape(call['status'])}"
        f"{' · attempt ' + str(call['attempt']) if call.get('attempt', 1) > 1 else ''}"
        f"{' · LENGTH' if call.get('finish_reason') == 'length' else ''}"
    )


def build(run: Path) -> Path:
    run_json, calls, uploads = _load(run)
    rows = stage_rows(calls)
    capture = run_json.get("capture", {})
    reconciled = (
        f"{capture.get('sends_captured')} captured, {capture.get('usage_records')} usage records"
        if capture
        else "not recorded"
    )
    match = capture and capture.get("sends_captured") == capture.get("usage_records")
    total_cost = sum(c.get("est_cost_usd", 0) for c in calls)
    total_words = uploads.get("total_words")
    wall = sum(stage.get("seconds", 0) for stage in run_json.get("stages", []))

    def table_row(r: dict) -> str:
        return (
            "<tr>" + "".join(
                f"<td class='{cls}'>{value}</td>" for value, cls in (
                    (html.escape(r["stage"]), ""),
                    (r["calls"], "n"), (r["errors"], "n"), (r["length"], "n"),
                    (f"{r['input']:,}", "n"), (f"{r['output']:,}", "n"), (f"{r['cached']:,}", "n"),
                    (f"{r['reasoning']:,}", "n"), (f"${r['cost']:.3f}", "n"),
                    (_fmt(r["seconds_total"], 0), "n"), (_fmt(r["seconds_mean"]), "n"),
                    (_fmt(r["seconds_p50"]), "n"), (_fmt(r["seconds_max"]), "n"),
                    (_fmt(r["out_mean"], 0), "n"), (f"{r['out_max']:,}", "n"),
                    (_fmt(r["tokens_per_word"], 2), "n"),
                )
            ) + "</tr>"
        )

    stage_table = (
        "<table><thead><tr><th>Stage / framework</th><th>Calls</th><th>Errors</th><th>Cut at length</th>"
        "<th>Input tok</th><th>Output tok</th><th>Cached tok</th><th>Reasoning tok</th><th>Est. cost</th>"
        "<th>Call s (sum)</th><th>s mean</th><th>s p50</th><th>s max</th><th>Out mean</th><th>Out max</th>"
        "<th>Tok/word</th></tr></thead><tbody>"
        + "".join(table_row(r) for r in rows)
        + "</tbody></table>"
    )

    phase_rows = "".join(
        f"<tr><td>{html.escape(s['stage'])}</td><td class='n'>{s.get('seconds', 0):,.0f}</td>"
        f"<td>{'ok' if s.get('ok') else 'FAILED: ' + html.escape(str(s.get('error', '')))}</td></tr>"
        for s in run_json.get("stages", [])
    )
    settings = run_json.get("settings", {})
    settings_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{html.escape(str(v))}</td></tr>" for k, v in settings.items()
    )

    payload = json.dumps(
        [
            {k: c.get(k) for k in (
                "n", "ts", "phase", "stage", "framework_id", "batch", "tier", "model", "attempt",
                "status", "error_type", "error", "finish_reason", "latency_ms", "usage", "request", "response",
            )} | {"summary": _call_summary(c)}
            for c in calls
        ],
        ensure_ascii=False,
    ).replace("</", "<\\/")

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Veldhara live run</title>
<style>
:root {{ --bg:#fafaf8; --fg:#1d1d1b; --muted:#6b6b66; --line:#dcdcd5; --card:#fff; --warn:#a4321c; --ok:#1d6b3a; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#16161a; --fg:#ececea; --muted:#9a9a94; --line:#33333a; --card:#1e1e24; --warn:#ff8a73; --ok:#6fcf8c; }} }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,sans-serif; margin:0; padding:24px 16px 80px; }}
main {{ max-width:1200px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:32px 0 8px; }}
.sub {{ color:var(--muted); margin:0 0 16px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }}
.stat {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px; }}
.stat b {{ display:block; font-size:20px; }} .stat span {{ color:var(--muted); font-size:13px; }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; background:var(--card); font-size:13px; }}
th,td {{ border:1px solid var(--line); padding:5px 8px; text-align:left; white-space:nowrap; }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
details {{ background:var(--card); border:1px solid var(--line); border-radius:6px; margin:6px 0; }}
details > summary {{ cursor:pointer; padding:8px 10px; font-size:13px; }}
details.err > summary {{ color:var(--warn); }}
.body {{ padding:0 10px 10px; }}
.body h4 {{ margin:12px 0 4px; font-size:13px; color:var(--muted); }}
pre {{ white-space:pre-wrap; word-break:break-word; background:var(--bg); border:1px solid var(--line); border-radius:6px; padding:8px; font-size:12px; max-height:520px; overflow:auto; margin:0; }}
img {{ max-width:100%; border:1px solid var(--line); }}
.warn {{ color:var(--warn); }} .ok {{ color:var(--ok); }}
input[type=search] {{ width:100%; max-width:420px; padding:6px 8px; border:1px solid var(--line); border-radius:6px; background:var(--card); color:var(--fg); }}
</style></head><body><main>
<h1>Veldhara live run</h1>
<p class="sub">Started {html.escape(str(run_json.get('started_at', '')))} · finished {html.escape(str(run_json.get('finished_at', '')))}
 · code {html.escape(str(run_json.get('git_sha', '')))} · contains client document text, keep private.</p>

<div class="grid">
<div class="stat"><b>{len(calls)}</b><span>calls captured</span></div>
<div class="stat"><b class="{'ok' if match else 'warn'}">{html.escape(reconciled)}</b><span>capture vs app usage records</span></div>
<div class="stat"><b>${total_cost:.3f}</b><span>estimated from tokens (plan prices)</span></div>
<div class="stat"><b>{html.escape(str(run_json.get('key_usage_delta_usd')))}</b><span>provider key usage delta, USD</span></div>
<div class="stat"><b>{wall:,.0f} s</b><span>sum of stage wall time</span></div>
<div class="stat"><b>{total_words if total_words is not None else 'n/a'}</b><span>words extracted from uploads</span></div>
</div>
{'<p class="warn">Stopped: ' + html.escape(str(capture.get('stop_reason'))) + '</p>' if capture.get('stop_reason') else ''}

<h2>Stages (driver)</h2>
<div class="scroll"><table><thead><tr><th>Stage</th><th>Seconds</th><th>Result</th></tr></thead><tbody>{phase_rows}</tbody></table></div>

<h2>Calls by stage</h2>
<p class="sub">Tok/word = provider input tokens divided by the words in the request text (system and user), averaged per call. Cost uses the plan's assumed prices, not the invoice.</p>
<div class="scroll">{stage_table}</div>

<h2>Settings</h2>
<div class="scroll"><table><tbody>{settings_rows}</tbody></table></div>

<h2>Every call</h2>
<p><input type="search" id="q" placeholder="Filter calls by text in the summary (stage, model, error)"></p>
<div id="calls"></div>
<script id="data" type="application/json">{payload}</script>
<script>
const calls = JSON.parse(document.getElementById('data').textContent);
const box = document.getElementById('calls');
function esc(s) {{ return String(s ?? '').replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c])); }}
function show(content) {{
  if (typeof content === 'string') return '<pre>' + esc(content) + '</pre>';
  if (Array.isArray(content)) return content.map(p => {{
    if (p && p.type === 'text') return '<pre>' + esc(p.text) + '</pre>';
    if (p && p.type === 'image_placeholder') return '<p>Image ' + esc(p.media_type) + ', ' + p.bytes + ' bytes, sha256 ' + esc(p.sha256.slice(0, 12)) + '<br><img src="' + esc(p.file) + '" alt="sent image"></p>';
    return '<pre>' + esc(JSON.stringify(p, null, 2)) + '</pre>';
  }}).join('');
  return '<pre>' + esc(JSON.stringify(content, null, 2)) + '</pre>';
}}
function pretty(text) {{
  try {{ return JSON.stringify(JSON.parse(text.replace(/^```(?:json)?\\s*/, '').replace(/\\s*```$/, '')), null, 2); }} catch (e) {{ return text; }}
}}
calls.forEach(c => {{
  const d = document.createElement('details');
  if (c.status !== 'ok' || c.finish_reason === 'length') d.className = 'err';
  const s = document.createElement('summary'); s.textContent = c.summary; d.appendChild(s);
  d.addEventListener('toggle', () => {{
    if (!d.open || d.dataset.done) return; d.dataset.done = 1;
    const req = c.request || {{}};
    const sent = (req.messages || []).map(m => '<h4>' + esc(m.role) + '</h4>' + show(m.content)).join('');
    const params = {{model: req.model, max_tokens: req.max_tokens, temperature: req.temperature, response_format: req.response_format, stream: req.stream, extra_body: req.extra_body}};
    const out = c.response == null ? '<pre class="warn">' + esc((c.error_type || '') + ': ' + (c.error || '')) + '</pre>' : '<pre>' + esc(pretty(c.response)) + '</pre>';
    const b = document.createElement('div'); b.className = 'body';
    b.innerHTML = '<h4>Parameters</h4><pre>' + esc(JSON.stringify(params, null, 2)) + '</pre><h4>Sent</h4>' + sent
      + '<h4>Received (finish_reason ' + esc(c.finish_reason) + ', usage ' + esc(JSON.stringify(c.usage)) + ')</h4>' + out;
    d.appendChild(b);
  }});
  box.appendChild(d);
}});
document.getElementById('q').addEventListener('input', e => {{
  const q = e.target.value.toLowerCase();
  [...box.children].forEach(d => {{ d.style.display = d.firstChild.textContent.toLowerCase().includes(q) ? '' : 'none'; }});
}});
</script>
</main></body></html>"""
    target = run / "report.html"
    target.write_text(page, encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m scripts.live.report <run folder>", file=sys.stderr)
        return 2
    print(build(Path(args[0]).expanduser().resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
