# WS #3 — Golden-output tests for the DPDPA path (handoff for Codex)

**Plan reference:** `tasks/multi-framework-demo-plan.md` §3 WS #3.
**Branch:** open `ws/3-golden-dpdpa` off `main`.
**Effort:** 2 days.
**Preconditions:**
- **WS #1 (white-label) must be merged first.** Branding text is captured in the PDF golden; if #1 lands after #3, the golden invalidates immediately.
- WS #2's `app/schemas/scoring.py` is helpful but not blocking — if it's not merged when you start, use plain dicts and tighten later.

## 1. Goal

Freeze the current DPDPA-only pipeline behaviour (screening → analyzer → scoring → PDF) as golden files, so the refactors in WS #4 (framework-agnostic services), WS #7 (per-cluster analyzer) and WS #8 (evidence citations) cannot silently change output. Any real behavioural change forces a deliberate golden update.

Analyzer calls are **mocked** in golden runs (recorded Claude response replayed from JSON). Live analyzer testing is a separate concern.

## 2. Files in scope

| File / directory | Change |
|---|---|
| `tests/fixtures/canonical_dpdpa/` | New. Fully-seeded assessment inputs + expected outputs. |
| `tests/fixtures/canonical_dpdpa/evidence/` | 3 small policy PDFs (< 200KB each). |
| `tests/fixtures/canonical_dpdpa/screening_answers.json` | Answers to all 9 screening domains. |
| `tests/fixtures/canonical_dpdpa/questionnaire_answers.json` | Answers to every DPDPA question. |
| `tests/fixtures/canonical_dpdpa/env.json` | `FIRM_NAME`, `FIRM_LOGO_PATH`, `FIRM_PRIMARY_HEX` used during capture. |
| `tests/fixtures/canonical_dpdpa/mocked_analyzer_response.json` | Recorded Claude output the mock replays. |
| `tests/fixtures/canonical_dpdpa/expected/score.json` | Golden: scoring output. |
| `tests/fixtures/canonical_dpdpa/expected/analyzer_output.json` | Golden: analyzer struct (post-mock). |
| `tests/fixtures/canonical_dpdpa/expected/pdf_text.sha256` | Golden: hash of extracted PDF text. |
| `tests/fixtures/canonical_dpdpa/expected/pdf_meta.json` | Golden: `{"page_count": N, "byte_length_lower_bound": N}` (bytes are a floor to catch truncation, not exact). |
| `tests/conftest.py` | New session-scoped fixture `canonical_dpdpa_assessment(tmp_path_factory)`. |
| `tests/test_golden_dpdpa.py` | The four golden tests. |
| `tests/support/analyzer_mock.py` | Reusable Claude-call mock. |
| `tests/support/fixture_capture.py` | Script Claude/Saqlain runs to (re)generate the golden files. |

## 3. Comparison contract (settled — do not renegotiate)

| Artefact | Comparison | Why |
|---|---|---|
| Score JSON | Exact dict equality (`==`). | Deterministic. |
| Analyzer output | Exact dict equality after mock replay. | Mock removes non-determinism. |
| PDF | SHA-256 of **extracted text** (via `pypdf` / `pdfplumber`), **not** byte hash. Plus page-count exact, plus byte-length floor. | fpdf2 embeds timestamps and font subset IDs; byte hash is too brittle. Text hash catches every real content change. |

Byte-hash comparison is **rejected** — text-hash + page-count is the standard.

## 4. Analyzer mock

`tests/support/analyzer_mock.py`:

```python
import json, pathlib
from unittest.mock import patch

def with_recorded_analyzer(fixture_dir: pathlib.Path):
    """Context manager that patches every Claude call inside claude_analyzer
    to replay recorded JSON. Fails loudly if the analyzer makes a call the
    recording doesn't cover."""
    recording = json.loads((fixture_dir / "mocked_analyzer_response.json").read_text())

    def fake_call(*args, **kwargs):
        key = _cache_key(args, kwargs)          # stable key from prompt hash
        if key not in recording:
            raise AssertionError(
                f"Analyzer made an uncached call. Key: {key}. "
                f"Re-run tests/support/fixture_capture.py to update the recording."
            )
        return recording[key]

    return patch("app.services.claude_analyzer._call_claude", side_effect=fake_call)
```

`_cache_key` hashes the prompt string (or a normalised version — Codex, decide during implementation and document the choice inline). The point: mock must be *deterministic* and *failing-open safer than failing-silent* — an uncached call raises, does not fall back to live.

If `app.services.claude_analyzer` doesn't expose a single call site to patch, extract one first (small refactor, single function `_call_claude(prompt, system, messages) -> dict`, all Anthropic-SDK calls route through it). That extraction is in-scope for this WS.

## 5. Fixture capture procedure

Claude (or Saqlain running Claude) executes `tests/support/fixture_capture.py` once, producing the `expected/` and `mocked_analyzer_response.json` files. Codex does not need to run this — the golden files are checked into git.

Sequence the capture script performs:

1. Spin up an ephemeral SQLite DB.
2. Set env `FIRM_NAME`, `FIRM_LOGO_PATH`, `FIRM_PRIMARY_HEX` to fixture values (in `env.json`).
3. Seed an assessment with `frameworks=["dpdpa"]`, upload the 3 evidence PDFs.
4. Run desk review.
5. Submit screening answers, then questionnaire answers (from JSON).
6. Trigger analyzer with a **live** Claude call — record every prompt/response pair via a passthrough interceptor into `mocked_analyzer_response.json`.
7. Run scoring, dump `ScoringResult` (or the current dict) to `expected/score.json`.
8. Dump analyzer output to `expected/analyzer_output.json`.
9. Generate PDF, extract text via pypdf, hash → `expected/pdf_text.sha256`, page count + byte length → `expected/pdf_meta.json`.
10. Print a summary; user reviews and commits.

Codex writes the *skeleton* of this script and marks the live-call section clearly (`# LIVE_CALL: replaced by mock in tests`). Claude runs it and commits the outputs in a separate follow-up commit on the same branch before requesting review.

## 6. Test to pass

`tests/test_golden_dpdpa.py`:

```python
import json, hashlib, io, pathlib
import pytest
from pypdf import PdfReader
from tests.support.analyzer_mock import with_recorded_analyzer

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "canonical_dpdpa"

@pytest.fixture(scope="session")
def canonical_env(monkeypatch_session):
    env = json.loads((FIXTURE / "env.json").read_text())
    for k, v in env.items():
        monkeypatch_session.setenv(k, v)

def test_scoring_matches_golden(canonical_dpdpa_assessment, canonical_env):
    with with_recorded_analyzer(FIXTURE):
        from app.services.scoring import score
        result = score(canonical_dpdpa_assessment.id, ["dpdpa"])
    expected = json.loads((FIXTURE / "expected" / "score.json").read_text())
    assert result.model_dump() == expected

def test_analyzer_output_matches_golden(canonical_dpdpa_assessment, canonical_env):
    with with_recorded_analyzer(FIXTURE):
        from app.services.claude_analyzer import analyze_assessment
        out = analyze_assessment(canonical_dpdpa_assessment.id)
    expected = json.loads((FIXTURE / "expected" / "analyzer_output.json").read_text())
    assert out == expected

def test_pdf_text_matches_golden(canonical_dpdpa_assessment, canonical_env):
    with with_recorded_analyzer(FIXTURE):
        from app.utils.pdf_export import generate_pdf
        pdf_bytes = generate_pdf(canonical_dpdpa_assessment.id)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(p.extract_text() or "" for p in reader.pages)
    got = hashlib.sha256(text.encode("utf-8")).hexdigest()
    expected = (FIXTURE / "expected" / "pdf_text.sha256").read_text().strip()
    assert got == expected

def test_pdf_meta_matches_golden(canonical_dpdpa_assessment, canonical_env):
    with with_recorded_analyzer(FIXTURE):
        from app.utils.pdf_export import generate_pdf
        pdf_bytes = generate_pdf(canonical_dpdpa_assessment.id)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    meta = json.loads((FIXTURE / "expected" / "pdf_meta.json").read_text())
    assert len(reader.pages) == meta["page_count"]
    assert len(pdf_bytes) >= meta["byte_length_lower_bound"]
```

`monkeypatch_session` is a session-scoped monkeypatch shim (add it to `tests/support/`; three lines using `pytest.MonkeyPatch()`).

## 7. Adversarial self-checks Codex must run before claiming done

1. Break `scoring.py` locally by flipping one status→score mapping. Run `pytest tests/test_golden_dpdpa.py`. Every relevant test must FAIL loudly. Restore.
2. Rename a private variable in `scoring.py` (semantic no-op). Every test must still PASS. If any fails, the golden is over-tight — remove the failing assertion or normalize.
3. Delete the mock file. Tests must fail with a clear "recording missing" error, not a live Claude call.

Codex reports these three results in the PR description.

## 8. Non-goals

- Multi-framework fixtures (WS #4 / #7 will add ISO/NIST goldens later).
- Snapshot-updating CLI. Re-generation is a manual re-run of the capture script.
- Coverage of screening timeline, RFI generation, or any UI route.
- Live-Claude regression tests. That's a separate concern (opt-in via `USE_LIVE_ANALYZER=1`, not built here).
- Any change to source files under `app/` except the tiny `_call_claude` extraction needed for mocking.

## 9. Done criteria

1. `pytest -q` green including the four golden tests.
2. Adversarial self-checks in §7 all pass.
3. Fixture directory ≤ 5 MB total (small evidence PDFs).
4. `mocked_analyzer_response.json` is present, complete, and deterministic across three consecutive runs.
5. Golden generation script is runnable: `python tests/support/fixture_capture.py` regenerates the `expected/` and `mocked_analyzer_response.json` files with no manual intervention.

## 10. Rollback

```bash
git revert <commit-sha-of-ws3-merge>
```

No app-code behaviour change beyond the `_call_claude` extraction. If revert leaves the extraction dangling, revert that commit too — it's isolated.

## 11. Adversarial review (post-PR)

Reviewer: Codex (yes, Codex reviews Claude's fixture; that's the protocol).

Prompt:
```
Adversarial review of ws/3-golden-dpdpa. Verify:
1. Adversarial self-checks in §7 all pass. Run them yourself.
2. Golden PDF-text hash is stable across two consecutive captures on the
   same env — if not, non-determinism is leaking through.
3. Analyzer mock will not silently fall back to a live call under any code
   path (grep for calls to Anthropic SDK not routed through _call_claude).
4. Fixture directory is committed AND small AND does not contain any real
   client data.
5. Single most likely production failure mode.

Output: PASS / FAIL with numbered failures. No hedging.
```
