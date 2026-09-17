# Migrate remaining 6 Claude call sites off Anthropic SDK + judge-tier reliability fix — Claude

**Date:** 2026-09-17
**Repo:** `saqlainmmomin/Cyber`, local `~/dpdpa-gap-tool/`
**Source:** follow-up to `tasks/handoffs/2026-09-16-test-coverage-review.md` (test harness for the
6 remaining Claude call sites, merged via PR #10) — this session did the actual provider
migration those tests were built to make safe.

## Goal

Migrate the 6 Claude call sites that still used the Anthropic SDK directly
(`desk_review.py`, `screening.py`, `context_profiler.py`, `followup_engine.py`,
`rfi_generator.py`, `document_processor.py`) onto the shared OpenRouter client
(`app/services/llm_client.py`) that `claude_analyzer.py` already used — same pattern PR #9
established. Verify it actually works against the live provider, not just mocked tests.

## What changed

### Migration

- Each of the 5 text call sites got a per-module `_call_llm` seam (mirrors
  `claude_analyzer.py`'s own `_call_llm`) that delegates to `llm_client.call_llm`, tiered:
  `desk_review`/`screening` → `judge`, `context_profiler`/`followup_engine` → `extract`,
  `rfi_generator` → `synthesize`.
- `document_processor.py`'s vision call moved to a new `vision` tier
  (`llm_client.py` gained a 4th `Tier`, `settings.llm_model_vision`). Its image content block
  also had to change shape — from Anthropic's native `{"type": "image", "source": {...}}` to
  OpenAI/OpenRouter's `{"type": "image_url", "image_url": {"url": "data:...;base64,..."}}` —
  `llm_client.call_llm` forwards message content as-is and OpenRouter expects the OpenAI shape
  regardless of which model ends up behind the tier.
- Removed `anthropic` entirely: no more `import anthropic`, `anthropic_api_key`, or
  `claude_model` anywhere in `app/`. Updated `requirements.txt`, `.env.example`, `CLAUDE.md`.
  `Settings.model_config` now sets `extra: "ignore"` so a developer's leftover
  `ANTHROPIC_API_KEY`/`CLAUDE_MODEL` in their local `.env` doesn't hard-crash startup.
- One deliberate parity decision: `screening.py` and the vision call had no explicit
  `temperature` on their original Anthropic calls (defaults to 1.0 there), but
  `llm_client.call_llm` defaults to 0 — preserved `temperature=1` explicitly on both rather than
  silently changing their output distribution as a migration side effect.
- Updated `tests/test_remaining_llm_call_sites.py` and `tests/support/canonical_dpdpa.py`'s
  golden-fixture screening mock to patch each module's `_call_llm` seam instead of
  `anthropic.Anthropic` (same convention `claude_analyzer.py`'s golden tests already used).

### Judge-tier reliability bug (found via live smoke testing, not a mocked test)

Smoke-tested the vision call and screening live against the real OpenRouter API (`OPENROUTER_KEY`
already present in `.env`). Vision worked cleanly first try (see live output in conversation —
correct model resolution, correct request shape, sensible compliance-aware transcription).
Screening did not: `run_screening_pass` crashed intermittently with
`AttributeError: 'NoneType' object has no attribute 'strip'` deep inside `_parse_inferences`.

Root cause: `llm_model_judge` (`deepseek/deepseek-v4-pro`) is a reasoning model. Its hidden
chain-of-thought "reasoning" tokens count against `max_tokens`, and on the real screening prompt
(41 requirements, structured JSON output) it sometimes consumed the *entire* budget before
writing any visible answer, leaving `response.choices[0].message.content` as `None` — silently
propagated into `llm_client.call_llm`'s return value with no guard.

Two intermediate fixes were applied and individually verified live, but a 5-call diagnostic
against the real screening prompt (same prompt, same params, back to back) showed the real
picture:

| Run | finish_reason | reasoning_tokens | content_chars | valid JSON |
|---|---|---|---|---|
| 1 | length | 8192 (100% of budget) | 0 | no |
| 2 | stop | 4292 | 9523 | yes |
| 3 | stop | 0 | 11306 | yes |
| 4 | length | 6573 | 6664 (truncated) | no |
| 5 | length | 7955 | 976 (truncated) | no |

`reasoning: {"exclude": true}` (OpenRouter's control to suppress hidden reasoning tokens) is
**not reliably honored** by this model/provider combination — reasoning-token usage ranged from
0 to 8192 across identical requests, a 60% failure rate that more `max_tokens` doesn't fix,
since reasoning can simply expand to fill whatever budget it's given (run 1).

**Also evaluated and explicitly rejected:** `stealth/union-alpha`, a free OpenRouter model the
user asked about as a possible replacement. It has no zero-data-retention endpoint — `llm_client.py`'s
`_REQUEST_PREFS` ZDR requirement is a deliberate hard requirement (this app processes real
compliance documents/PII), so wiring it into any tier's default config was ruled out. An ad hoc,
synthetic-data-only smoke test (never wired into the repo) also showed it was slower (178–199s
vs. ~85s) and left roughly half the requirements `not_assessed` vs. 1–8 for the eventual fix,
before hitting a rate limit on its 3rd call — not adopted.

### Fix

1. `llm_client.py` now sends `reasoning: {"exclude": true}` on every request (kept as
   defense-in-depth even after the model swap below — harmless on non-reasoning models).
2. `llm_client.call_llm` now raises `RuntimeError` with tier/model/finish_reason context instead
   of letting `None`/empty text reach a caller's parser as a confusing, hard-to-place
   `AttributeError`/`JSONDecodeError`. Both the streaming and non-streaming paths guard this.
3. `screening.py`'s `max_tokens` bumped 4096 → 8192 (kept as headroom; not the root fix).
4. **Root fix:** `llm_model_judge` switched from `deepseek/deepseek-v4-pro` →
   `deepseek/deepseek-v4-flash` (same non-reasoning model already used for `extract`/`synthesize`).
   Since `judge` is a shared tier config, this one change also fixes `desk_review.py` and
   `claude_analyzer.py`'s main gap analysis, not just screening.

Re-ran the same 5-call diagnostic against the new model: **5/5 succeeded**, `finish=stop`,
`reasoning_tokens=0` every time, valid JSON every time, latency tightened to 75–97s (down from a
40–207s spread). Also re-ran the full `run_screening_pass` pipeline end-to-end: 41/41 requirements
inferred, sensible status distribution, no errors.

## Tests added

- `tests/test_golden_dpdpa.py::test_call_llm_raises_on_empty_content_instead_of_returning_none` —
  regression test for the new empty-content guard. Verified it fails without the guard (reverted
  locally, confirmed `DID NOT RAISE RuntimeError`, re-applied).
- `tests/test_golden_dpdpa.py::test_analyzer_call_seam_normalizes_create_and_stream` updated to
  assert the new `reasoning: {"exclude": true}` key is present in `extra_body` on both the
  streaming and non-streaming call sites, alongside the existing ZDR assertion.

## Verification

- `pytest -q` (full suite): **128 passed, 0 failed**.
- Live smoke tests against the real OpenRouter API (not mocked): vision call (synthetic
  consent-banner image), screening pipeline (5-call raw diagnostic + full `run_screening_pass`,
  both before and after the model swap).
- `python -m compileall app/ tests/` clean; `python -c "import app.main"` boots without error.

## Deliberately deferred

- `stealth/union-alpha` — evaluated, not adopted (see above). No code references it.
- Further judge-tier model comparison beyond DeepSeek Flash vs. Pro — Flash's live results were
  clean enough (5/5, consistent latency) that a broader model search wasn't pursued this session.
- Prompt-cache passthrough verification for the newly-migrated call sites (same open item
  `claude_analyzer.py` already has — `cache_read_input_tokens` was 0 on a live call there too).
