# Canonical DPDPA fixture

This fixture contains only synthetic company data and synthetic policy PDFs.
`mocked_analyzer_response.json` records its provenance in `_meta`; the checked-in
baseline is an offline characterization, not a genuine Claude response.

The fixture exercises the real screening prompt, parse, and persistence path
through a deterministic fake provider response. Desk-review findings are seeded
from the synthetic policy excerpts so analyzer evidence extraction has one stable
call. The desk-review provider call itself is outside this golden's coverage.
`expected/screening_output.json` freezes the parsed and persisted screening
result alongside the analyzer, score, and PDF outputs.

Regenerate the offline baseline with:

```bash
.venv/bin/python tests/support/fixture_capture.py
```

A genuine analyzer capture requires an explicit opt-in and valid API key:

```bash
USE_LIVE_ANALYZER=1 .venv/bin/python tests/support/fixture_capture.py --live
```

Review the provenance metadata and resulting diff before accepting a live update.
