# LLM Provider & Reliability Workstream — OpenRouter migration + hallucination guardrails

**Date:** 2026-09-16
**Plan:** `/Users/saqlainmomin/.claude/plans/binary-bouncing-liskov.md` (approved same session)
**Scope:** `app/services/claude_analyzer.py` only — the compliance-critical gap-analysis path,
and the one Claude call site with golden/recorded test coverage. `desk_review.py`,
`screening.py`, `context_profiler.py`, `followup_engine.py`, `rfi_generator.py`,
`document_processor.py`'s vision call are explicitly out of scope — no test harness exists for
any of them yet, so a provider swap there isn't safe until one does.

Status: **all three phases implemented, tested, and the judge-tier model default flipped based
on a real live comparison.** Not yet committed — this file documents what's ready to review.

---

## Phase A — Provider abstraction (transport swap)

New file `app/services/llm_client.py` — one function, `call_llm(tier, *, system, messages,
max_tokens, temperature, stream) -> {"text", "usage"}`, using the `openai` SDK (added to
`requirements.txt`, `openai==3.14.1`) pointed at OpenRouter. `tier` is `"extract" | "judge" |
"synthesize"`; the model string is resolved from `Settings.llm_model_*` — callers never name a
model directly.

`claude_analyzer.py` no longer imports `anthropic` at all; its `_call_claude` seam was renamed
to `_call_llm` (now a thin wrapper delegating to `llm_client.call_llm`) and all 4 call sites
updated to pass `tier=` instead of `model=settings.claude_model`.

**Test seam:** `tests/support/analyzer_mock.py` and `tests/support/fixture_capture.py` patch
`app.services.claude_analyzer._call_llm` (renamed from `_call_claude`). The two structural tests
in `tests/test_golden_dpdpa.py` that mocked the raw Anthropic SDK
(`test_missing_analyzer_recording_fails_before_any_live_call`,
`test_analyzer_call_seam_normalizes_create_and_stream`) were rewritten to mock the OpenAI-shaped
client instead.

**Important design property, confirmed working:** `analyzer_request_key()` hashes `(tier, ...)`,
not the resolved model string — so changing `Settings.llm_model_*` never invalidates a recorded
fixture. Verified twice: flipping `llm_model_extract`/`llm_model_synthesize` to DeepSeek V4 Flash
and later flipping `llm_model_judge` to DeepSeek V4 Pro both left the full suite green with zero
fixture changes needed.

**Offline fixture regeneration:** the canonical DPDPA golden fixture
(`tests/fixtures/canonical_dpdpa/`) is a *synthetic* characterization
(`tests/support/fixture_capture.py`'s non-`--live` path) — regenerating it after the request
shape changed cost nothing (`python tests/support/fixture_capture.py`, no network call). Only
the Phase C model comparison below needed real API spend.

---

## Phase B — Guardrails

New file `app/schemas/llm_output.py`:
- `GapAssessmentItem` / `GapAnalysisResponse` — Pydantic models for what a gap-analysis response
  must look like. Nothing validated this before; `app/routers/analysis.py` read
  `a["requirement_id"]`/`a["compliance_status"]` straight off Claude's raw parsed JSON.
- `validate_and_filter(parsed, known_requirement_ids)` — validates each assessment item
  individually (one malformed item no longer sinks the other ~40), drops items whose
  `requirement_id` isn't in the framework's real control set (previously became silent orphan
  `GapItem` rows), and coerces an out-of-enum `compliance_status` to `not_assessed` with a
  logged warning (same philosophy `scoring.py` already used one layer downstream — now applied
  at the actual ingestion boundary). Returns a plain dict in the exact shape callers already
  consume, so `app/routers/analysis.py` needed zero changes.

In `claude_analyzer.py`:
- `_ground_evidence_quotes(evidence, documents)` — after Call 1 (evidence extraction), verifies
  every extracted quote is a genuine (whitespace-normalized) substring of the source documents
  before it's threaded into Call 2's prompt. Drops fabricated citations deterministically, for
  free, regardless of which model produced them.
- `_flag_unsupported_compliant_items(assessments)` — a `compliant` verdict with no evidence
  quote backing it gets `needs_review: True` set (new field on `GapAssessmentItem`, additive,
  doesn't change `compliance_status` — `scoring.py` still owns that mapping). Not yet surfaced
  in the review UI; that's a natural follow-up, not done here.

New test file `tests/test_llm_output_validation.py` — 14 pure-logic unit tests (no network) for
both guardrails: unknown requirement ID, malformed item, unknown status coercion, `None`→default
field coercion, verbatim/whitespace/fabricated quote grounding, and the sanity-rule flag.

`tests/fixtures/canonical_dpdpa/expected/analyzer_output.json` (the golden comparison baseline)
was regenerated — the diff is exactly the two guardrail effects: `evidence_quote: null → ""`
and a new `needs_review` key per item.

---

## Phase C — Model tiering

Config defaults (`app/config.py`):
```python
llm_model_extract: str = "deepseek/deepseek-v4-flash"
llm_model_judge: str = "deepseek/deepseek-v4-pro"
llm_model_synthesize: str = "deepseek/deepseek-v4-flash"
```

**Extract/synthesize:** flipped without a comparison — low-stakes (extractive / summary of
already-validated results), and Phase B's grounding check catches a bad extraction regardless
of which model produced it.

**Judge tier — the one that sets `compliance_status`:** ran the real canonical-fixture inputs
live through `run_gap_analysis()` twice — once with `judge=anthropic/claude-sonnet-4`
(baseline), once with `judge=deepseek/deepseek-v4-pro` (candidate) — and diffed
`compliance_status` per requirement.

**Result: 39/41 (95%) agreement.** The 2 disagreements were both adjacent-category
(`partially_compliant` ↔ `non_compliant`), not a full flip in either case:
- `CH2.MINIMIZE.1`: claude=`partially_compliant`, deepseek=`non_compliant`
- `CH2.SECURITY.1`: claude=`non_compliant`, deepseek=`partially_compliant`

**Cost, measured (not list-price theory):**
| | input tokens | output tokens | cost this call |
|---|---|---|---|
| Claude (via OpenRouter) | 6,519 | 8,479 | ~$0.147 |
| DeepSeek V4 Pro | 6,032 | 11,677 | ~$0.047 |

~3.1x cheaper despite DeepSeek producing 38% more output.

**Decision (confirmed with Saqlain): flip the default to DeepSeek V4 Pro now**, not just
document it as validated-but-parked. One config line to revert (`llm_model_judge` in
`app/config.py`) if real assessments surface problems this one fixture didn't.

### Important side-finding: OpenRouter doesn't appear to pass through Anthropic prompt caching

Neither the Claude-via-OpenRouter call nor the DeepSeek call showed any
`cache_read_input_tokens` in the response, despite `app/dpdpa/prompts.py::build_system_prompt()`
still emitting `cache_control: ephemeral` blocks. The old module docstring's "~90% cost
reduction per framework" claim was true for the *direct Anthropic SDK* path this workstream just
replaced — it does not appear to hold for Claude accessed via OpenRouter with this request
shape. This means Phase A's transport swap may have already made **Claude itself** more
expensive per call than it used to be, independent of the DeepSeek decision. Not investigated
further here (would need OpenRouter-specific `extra_body`/header research) — worth a follow-up
if any tier goes back to Claude later, but doesn't change today's decision since DeepSeek is
cheaper than *even the old cached-Claude baseline* would have been.

---

## Verification

- Full suite: **91 passed** (77 baseline + 14 new guardrail tests), 0 failed, at every step —
  transport swap, guardrails, both tier-default flips.
- `tests/test_golden_dpdpa.py` (7 tests) green against the re-recorded synthetic fixture.
- Two live smoke tests against real OpenRouter (non-streaming and streaming) confirmed the
  transport works before touching guardrails or model choice.
- Live judge-tier comparison (above) — real inputs, real API calls, both models, diffed.
- Not done: a live smoke test through the actual FastAPI `/api/assessments/{id}/analyze` route.
  Reasoning: the golden test suite already exercises `run_gap_analysis()` → DB persistence →
  scoring end-to-end (just against a replayed/recorded response), and `analysis.py`'s dict-key
  consumption of the analyzer output is unchanged (`validate_and_filter` returns the same shape
  plus one new harmless key) — this workstream never touched `app/routers/analysis.py`. Spending
  another live call to re-prove what the golden suite plus the scratch comparison already jointly
  cover didn't seem worth it, given the whole point of this workstream is cost discipline. Worth
  doing once before this goes to production traffic, just not as part of this session.

## Out of scope / follow-ups

- The other 6 Claude call sites — need their own test harness before a provider/model swap is
  safe. Fast-follow, not this workstream.
- `needs_review` flag isn't surfaced anywhere in the UI yet — currently just persisted-adjacent
  data with no consumer. A natural next step, not done here.
- OpenRouter/Anthropic caching pass-through — unresolved side-finding above, worth its own
  investigation if a tier ever goes back to Claude.
- This decision rests on one fixture, one run, temperature=0. Worth revisiting after DeepSeek
  V4 Pro has run on a handful of real (non-synthetic) assessments.

## Files changed

- `requirements.txt` — added `openai==3.14.1`
- `app/config.py` — added `openrouter_key`, `openrouter_base_url`, `llm_model_extract`,
  `llm_model_judge`, `llm_model_synthesize`
- `app/services/llm_client.py` — new
- `app/services/claude_analyzer.py` — transport swap, guardrail wiring, `_call_claude` →
  `_call_llm`
- `app/schemas/llm_output.py` — new
- `tests/support/analyzer_mock.py`, `tests/support/fixture_capture.py` — patch target rename
- `tests/test_golden_dpdpa.py` — 2 structural tests rewritten for the new transport
- `tests/test_llm_output_validation.py` — new, 14 tests
- `tests/fixtures/canonical_dpdpa/mocked_analyzer_response.json`,
  `.../expected/analyzer_output.json` — regenerated (offline, synthetic)
