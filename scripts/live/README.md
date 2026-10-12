# Live run capture

Tooling for a measured, observed live run of the app against a real provider. No app file changes.

| File | Purpose |
|---|---|
| `capture.py` | Wraps `llm_client._send` and `_record_call`. Writes one JSON file per provider send (full request, full response, tags, usage, latency, errors), an `index.jsonl`, and saves images beside them. Hard stop on an estimated spend cap or a request that fails twice. |
| `drive.py` | Drives an upload pack through the real HTTP routes (engagement, context, scope, uploads, desk review, questionnaire, follow-ups, analysis). Needs `--confirm-spend`. |
| `report.py` | Builds `report.html`: per-stage table, measurements, and every call with what was sent and received. |

```bash
OPENROUTER_KEY="" .venv/bin/python scripts/demo/pack.py --output ~/cyberassess-runs/<run>/pack
.venv/bin/python -m scripts.live.drive --pack ~/cyberassess-runs/<run>/pack --out ~/cyberassess-runs/<run> --max-words 30000 --confirm-spend
.venv/bin/python -m scripts.live.report ~/cyberassess-runs/<run>
```

Rules:
- The run folder must be outside the repository. It holds client document text and is never committed.
- The driver reads only `evidence/`, `upload-manifest.csv` and `questionnaire-entry.json`. It never opens `scenario.json`, `coverage-matrix.csv` or anything under the held-out evaluation set.
- A run is an observation. Do not tune prompts, analyzer or desk review to what it finds.
- Spend comes from the provider's key usage before and after the run. The token estimate uses assumed prices and is for the hard stop only.
- To view a report, serve the run folder with `python3 -m http.server --bind 127.0.0.1` and open `report.html`. Do not publish it.
