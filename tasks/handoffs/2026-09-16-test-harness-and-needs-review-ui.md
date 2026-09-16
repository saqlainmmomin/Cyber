# Test harness for the remaining Claude call sites + needs_review UI — Codex

**Date:** 2026-09-16
**Repo:** `saqlainmmomin/Cyber`, local `~/dpdpa-gap-tool/`
**Context:** Follow-up to `tasks/handoffs/2026-09-16-llm-provider-reliability-workstream.md`
(PR #9), which migrated `app/services/claude_analyzer.py` to a tiered OpenRouter client and
added a validation/guardrail layer, but deliberately scoped out 6 other Claude call sites
because none of them have test coverage — a provider/model swap there isn't safe without one
first. This handoff is that fast-follow, plus a separate, unrelated small feature (surfacing the
new `needs_review` flag in the review UI) bundled in because both are small enough to land
together.

Two independent tasks below. Do them as separate commits (or separate PRs if you'd rather) —
they don't depend on each other.

---

## Task 1 — Test harness for the 6 remaining Claude call sites

**Files, each with its own direct `anthropic.Anthropic(api_key=settings.anthropic_api_key)` call
and zero test coverage today:**

| File | Function | What it does |
|---|---|---|
| `app/services/desk_review.py` | `_call_claude_desk_review` (line ~143) | Desk review findings from documents — evidence, signal flags, absence findings |
| `app/services/screening.py` | `run_screening_pass` (line ~31) | Domain screening inferences from context/documents |
| `app/services/context_profiler.py` | `derive_risk_profile` (line ~15) | Risk profile signals from context answers |
| `app/services/followup_engine.py` | `generate_followups` (line ~25) | Follow-up questions from desk-review triggers |
| `app/services/rfi_generator.py` | `_call_claude_rfi` (line ~192) | RFI document content/enhancements |
| `app/services/document_processor.py` | `_extract_image` (line ~170) | Vision call — OCR/extraction from uploaded images |

**Goal:** each file gets a patchable seam and at least a baseline characterization test, so a
future provider/model swap (same OpenRouter migration `claude_analyzer.py` already got) has
something to prove parity against — the same reason `claude_analyzer.py`'s golden tests exist.

**Reference pattern — read these first, don't reinvent the approach:**
- `app/services/claude_analyzer.py`'s `_call_llm` — the seam shape (`tier`, `stream`, `**request`
  in, `{"text", "usage"}` dict out) that made the OpenRouter migration mechanical there.
- `tests/support/analyzer_mock.py` — record/replay harness (`with_recorded_analyzer`,
  `record_live_analyzer`), hash-keyed on normalized request kwargs, refuses to fall back to a
  live call on a cache miss.
- `tests/test_golden_dpdpa.py` — how the harness gets used in an actual test.

**Don't copy the golden-fixture machinery wholesale for all 6** — that's a lot of ceremony
(canonical fixture directory, PDF rendering, synthetic-vs-live capture modes) built for one
specific high-stakes pipeline. For these 6, a lighter version is enough: for each file,

1. Rename its direct-call function to a seam consistent with `claude_analyzer.py`'s naming
   (e.g. `_call_llm` if/when it also migrates to `llm_client.py`, or at minimum a clearly-named
   private function that wraps the `anthropic.Anthropic()` call so it's a single patchable point
   — don't change the transport in this task, just make each file testable in isolation).
2. Write 2-4 unit tests per file using `unittest.mock.patch` on that seam, covering: the happy
   path (valid response parses correctly into whatever shape the caller expects), a malformed/
   non-JSON response (does it error cleanly or crash somewhere unexpected), and one
   file-specific edge case worth locking down (e.g. `document_processor.py`'s vision call with
   an empty/corrupt image; `screening.py`'s enum validation in `_parse_inferences`, already
   partially there — extend it, don't duplicate it).
3. If a file already does its own ad-hoc JSON-fence-stripping (check `desk_review.py:249`'s
   `_parse_json_response` — it's a near-duplicate of `claude_analyzer.py`'s old one, already
   flagged as tech debt in the WS4 review), this is a reasonable moment to consolidate it, but
   don't let that scope-creep into a bigger refactor than the task needs — a test harness that
   locks down current behavior is the deliverable, not a rewrite.

**Explicitly not in this task:** migrating any of the 6 to `llm_client.py`/OpenRouter, or
changing which model they call. That's the next step after this lands, not this one.

**Verification:** `pytest -q` full suite green, plus the new tests actually fail if you
temporarily break the function they cover (sanity-check they're not vacuously passing).

---

## Task 2 — Scope and build the `needs_review` UI

**Context:** `app/schemas/llm_output.py`'s `GapAssessmentItem` now has a `needs_review: bool`
field (set by `claude_analyzer.py::_flag_unsupported_compliant_items` when a `compliant` verdict
has no evidence quote backing it). Right now this is a dead end — it exists on the dict that
`app/routers/analysis.py` receives, but:

- `GapItem` (`app/models/report.py`) has no `needs_review` column — it's never persisted.
- Nothing in `app/routers/analysis.py`'s `GapItem(...)` construction (two call sites, ~line 295
  and ~line 484) reads or stores it.
- Nothing in `app/templates/partials/review_finding_card.html` renders it.

**Scope this yourself and implement it** — this is a real design decision (see below), not a
mechanical wire-up. Land it as a small, additive feature, not a redesign of the review workflow.

**What to decide and implement:**

1. **Persistence.** Add `needs_review` as a nullable/defaulted column via the existing DIY
   migration pattern — see `app/main.py::_run_migrations`, the `"gap_items"` list (line ~158),
   e.g. `("needs_review", "BOOLEAN DEFAULT 0")`. Follow the existing style exactly (nullable adds,
   no destructive changes, matches how `review_status` and the `ai_*` shadow columns were added).
2. **Set it on creation.** Both `GapItem(...)` construction sites in `app/routers/analysis.py`
   need `needs_review=a.get("needs_review", False)` (or however you choose to read it off the
   validated dict — check the exact key name in `app/schemas/llm_output.py`).
3. **Surface it visually.** `app/templates/partials/review_finding_card.html` already has a
   `review_status` badge (accepted/rejected/draft) and a compliance-status color scheme
   (`status_colors` dict, referenced around line 38). `needs_review` is a *different* axis — it's
   not "has a human reviewed this," it's "the model itself flagged this verdict as
   under-supported." Don't conflate the two or overload the existing badge. A small, distinct
   visual marker (icon + tooltip, or a second small badge) next to the compliance-status text
   when `item.needs_review` is true is probably the right scope — something that makes an
   under-supported `compliant` verdict visibly different from a well-supported one, without
   restructuring the card. Use your judgment on the exact visual treatment; keep it minimal.
4. **Consider (your call, not mandatory):** does the review queue/listing (check
   `app/routers/review.py` for how findings get queried and ordered for the reviewer) benefit
   from being able to filter or sort by `needs_review`? Only add this if it's a small, natural
   extension of what's already there — don't build a new filtering system for one flag.

**Constraints:**
- Don't touch `review_status`'s existing accept/reject workflow logic (`app/routers/review.py`)
  beyond what's needed to read/display `needs_review` — it's a separate, established concept.
- Match the existing card's Tailwind/dark-mode conventions (`dark:` variants throughout
  `review_finding_card.html`) — don't introduce a one-off style that breaks in dark mode.
- This is additive — no existing reviewer-facing behavior should change for items where
  `needs_review` is false/absent (which is every item created before this migration runs).

**Verification:**
- `pytest -q` full suite green.
- Manually run the app (`uvicorn app.main:app --reload`), trigger analysis on a test assessment
  that produces at least one flagged item (or seed one directly via the DB for a quick check),
  and confirm the marker actually renders — screenshot or describe what you see, don't just
  claim the template change is correct from reading it.

---

## Report back

Append a `## Results` section to this file covering both tasks: what you built, the design
decisions you made for Task 2 (and why), test output, and anything you deliberately deferred.

## Results

### Task 1 — Test harness for the remaining Claude call sites

Added one patchable provider seam per service without changing the Anthropic transport or
model selection:

- `screening.py`: `_call_claude_screening`
- `context_profiler.py`: `_call_claude_context_profile`
- `followup_engine.py`: `_call_claude_followups`
- `document_processor.py`: `_call_claude_vision`
- `desk_review.py` and `rfi_generator.py` already had suitable `_call_claude_*` seams, so
  their existing boundaries were retained.

Added 18 characterization tests in `tests/test_remaining_llm_call_sites.py` — three per
service — covering valid responses, malformed/non-JSON responses, and service-specific edge
cases. The new tests were run before the implementation and produced 11 expected failures
(missing seams plus the uncharacterized screening assertion); after the seams were added, all
18 passed. Existing behavior was intentionally preserved: screening malformed JSON still
returns `{}`, context-profile malformed JSON still raises `JSONDecodeError`, RFI malformed JSON
falls back to empty enhancements, and vision text remains opaque text rather than being treated
as JSON.

### Task 2 — `needs_review` persistence and review UI

Added `GapItem.needs_review` as a nullable boolean with Python/server defaults of `False`/`0`,
plus the additive DIY migration `BOOLEAN DEFAULT 0`, matching the existing additive migration
style and keeping pre-migration rows safe. Both single-framework and
multi-framework `GapItem(...)` creation paths now copy `a.get("needs_review", False)` from the
validated analyzer output.

The review card renders a separate amber `⚠ Needs review` marker beside the AI compliance status,
with an explanatory tooltip and accessible label. It uses the existing light/dark Tailwind
conventions and leaves the human `review_status` badge and accept/reject workflow untouched.
I did not add queue filtering or sorting: the existing client-side filter bar has no natural
flag-filter abstraction, and a new filter would be disproportionate for this additive signal.

Added five tests in `tests/test_needs_review_ui.py` covering model default/persistence, migration
against an existing table, single-framework route persistence, and true/false template output.

### Verification

- Focused tests: `pytest -q tests/test_remaining_llm_call_sites.py tests/test_needs_review_ui.py` — **23 passed**.
- Full suite: `pytest -q` — **114 passed**, with 20 pre-existing collection/deprecation warnings.
- `git diff --check` and Python 3.13 `compileall` passed; `ruff`/`mypy` were unavailable in the environment.
- Runtime smoke: launched CyberAssess with Python 3.13 against an isolated SQLite database,
  seeded one `needs_review=True` gap item, and opened the real review page in the browser. The
  rendered card visibly showed `Compliant` followed by the amber `⚠ Needs review` marker; the
  accessibility tree exposed the tooltip text, and a full-page screenshot was captured.

### Deliberately deferred

- Migrating these six call sites to `llm_client.py`/OpenRouter or changing their models.
- Consolidating the duplicate JSON-fence parsers; this work keeps the requested characterization
  scope small.
- Adding a review-queue filter/sort for `needs_review`.
