# P6-1: LLM plumbing

This task makes the LLM layer bounded, observable, concurrent and restart-safe without changing what v1 asks the model or how it scores. It adds the provider-agnostic plumbing that the v2 pipeline (P6-3/P6-4) and the Bedrock migration (P6-13) build on.

**Plan:** `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, Track 1, task P6-1. The design is in Part B.2 ("Reliability and plumbing"). Relevant decisions: **D-P6-E** (v1 stays the default until P5-9 proves v2) and **D-P6-K** (the provider moves to Bedrock `ap-south-1` later, so nothing outside `llm_client.py` may depend on OpenRouter-specific features).
**Product contract:** `docs/product/2026-09-21-cyberassess-product-requirements.md`. **PR-040** requires analysis runs to preserve "input references, pack/prompt/model configuration, outputs, validation results, and run status without naming a single provider in the domain."
**Owner:** Claude designs (this file) → Codex implements → Claude reviews (`tasks/agent-ownership.md`: foundational plumbing that later work assumes is correct).
**Branch / worktree:** `codex/p6-1-llm-plumbing`, from `main`.
**Depends on:** nothing. Written against `main` at `e0fbb52`.
**Blocks:** P6-3, P6-4 and P6-13. It also comes before the **P5-9 Stage C baseline**, which runs after this merges. That way the v1 baseline already includes timeouts and temperature fixes, and the later v1 → v2 comparison measures only the pipeline redesign.
**Runs in parallel with:** P6-2a (test criteria draft, which touches disjoint files).

> **If the code forces a deviation from this design, stop and report it in `## Results`. Do not pick an alternative.** That applies to every numbered decision, setting name, default, key name and test scenario below.

> **Behaviour-neutral for v1 is a hard constraint.** Only these v1 behaviour changes are allowed:
> - screening and vision temperature set to 0 (D-P6-1-F)
> - `estimated_score` removed from the synthesis prompt (D-P6-1-G)
> - frameworks run concurrently (D-P6-1-D), with output byte-identical to a sequential run
>
> No prompt text changes. No kwargs change at any `_call_llm` seam. No recorded fixture changes.

## Step 0 (before writing code)

1. Create the worktree: `git worktree add ../dpdpa-gap-tool-p6-1 -b codex/p6-1-llm-plumbing main`. Symlink `.venv` and copy `.env` into it.
2. Run `.venv/bin/pytest -q` there. Record the pass/skip/fail counts and the `main` commit in `## Results`. The last recorded number is 641 passed, 9 skipped (P5-6 results), with a known longitudinal ordering flake.
3. Confirm these facts (the numbers are `main` @ `e0fbb52`). **If any of 1–7 is false, stop and report:**
   - `app/services/llm_client.py` defines `call_llm(tier, *, system, messages, max_tokens, temperature=0, stream=False) -> dict` returning `{"text", "usage"}`, and `_REQUEST_PREFS` at ~L52.
   - `app/services/screening.py:117` and `app/services/document_processor.py:188` pass `temperature=1`.
   - `app/frameworks/prompts.py:575-586` asks for a "numeric score (0-100)" and shows `"estimated_score": 65`.
   - `git grep -n "estimated_score\|framework_comparison" -- app tests` matches only `app/frameworks/prompts.py`.
   - These three loops are sequential:
     - `app/services/claude_analyzer.py:295` (`_collect_framework_evidence`, one extraction per framework)
     - `app/services/claude_analyzer.py:417` (`run_multi_framework_analysis`, one judge call per framework)
     - `app/services/desk_review.py:115` (one desk-review call per framework)
   - `tests/support/analyzer_mock.py` keys recordings on a sha256 of the **full normalized seam kwargs** (`analyzer_request_key`). That is why no seam kwargs may change.
   - `app/main.py:106` `lifespan` runs `_run_alembic_upgrade()`, `_register_frameworks()` and `_assert_framework_catalog_complete()`. Nothing resets rows left in `running`/`analyzing`.

## Goal

1. Every LLM request has an explicit timeout and transport retry limit, set in config.
2. `llm_client.call_llm` can request schema-enforced JSON through a provider-agnostic parameter. No v1 call site uses it yet; v2 will.
3. Every LLM call is recorded (tier, model, stage, framework, tokens, latency, outcome). The record lands in the `AnalysisRun` envelope (per framework) and in the desk-review raw response. This satisfies PR-040 and gives P5-9 a cost read that doesn't depend on its own wrapper.
4. Per-framework LLM work in desk review, evidence extraction and multi-framework judgment runs concurrently, with a configurable bound. Results are identical to a sequential run.
5. Screening and vision run at temperature 0. The synthesis prompt no longer asks the model for a score.
6. A process restart can no longer leave an assessment, desk review or analysis run stuck in `analyzing`/`running` forever.

## Decisions (made here so they are not relitigated)

### D-P6-1-A: New settings (`app/config.py`, and documented commented-out in `.env.example`)

| Setting | Type | Default | Meaning |
|---|---|---|---|
| `llm_timeout_seconds` | float | `300.0` | Per-request timeout passed to the OpenAI client (large streamed judge calls are slow) |
| `llm_max_retries` | int | `2` | Transport retries (429/5xx/connection/timeout), passed to the OpenAI client's `max_retries` |
| `llm_max_concurrency` | int | `4` | Upper bound on concurrent per-framework LLM units. `1` means run inline in the caller's thread, exactly as today |
| `recover_interrupted_on_startup` | bool | `True` | Enable D-P6-1-H |

- `_get_client()` passes `timeout=settings.llm_timeout_seconds` and `max_retries=settings.llm_max_retries` to `OpenAI(...)`.
- Do not add any retry loop of your own around `call_llm`; the SDK's retries are the only ones.

### D-P6-1-B: `call_llm` gains `response_schema` (provider-agnostic structured output)

New signature: `call_llm(tier, *, system, messages, max_tokens, temperature=0, stream=False, response_schema: dict | None = None) -> dict`.

- **`response_schema=None` (the default).** The request sent to the provider must be **exactly** what is sent today, with the same kwargs and the same `extra_body`. Scenario 2 pins this.
- **`response_schema` given.** The shape is `{"name": str, "schema": dict}` (a JSON Schema object, typically from `PydanticModel.model_json_schema()`). The OpenRouter backend adds:
  - `response_format={"type": "json_schema", "json_schema": {"name": ..., "strict": True, "schema": ...}}`
  - `extra_body` = the existing `_REQUEST_PREFS` with `provider` extended by `"require_parameters": True`. Keep `data_collection: "deny"` and `zdr: True`. Build a new dict and never mutate the module constant.
- The return shape still has `"text"` (the raw JSON string). Callers parse and validate as today. There is no `"parsed"` key.
- **Module docstring addition.** Callers describe the output with a JSON schema only, and the client maps it to the provider's mechanism. Today that is OpenRouter `response_format`. After D-P6-K it is Bedrock Converse tool-use with a forced tool whose `inputSchema` is this schema. Nothing outside this module may reference `response_format`, `require_parameters` or any OpenRouter field.
- **No v1 call site passes `response_schema` in this task.** Passing it would change the seam kwargs and invalidate the golden recordings.

### D-P6-1-C: Call recording (collector + tags, via `contextvars`)

Add to `app/services/llm_client.py`:

- **`collect_calls()`.** A context manager that yields a list. Every `call_llm` invocation made while it is active, including from worker threads started through D-P6-1-D, appends exactly one record. Nested collectors: the innermost active collector receives the record. Outside any collector nothing is recorded, and there is no global state growth.
- **`call_tag(*, stage: str | None = None, framework_id: str | None = None)`.** A context manager that sets tags for calls made inside it. Nested tags merge, with inner values winning.
- **Record shape.** Plain JSON-serialisable dict. Keys are exactly:
  `{"tier", "model", "stage", "framework_id", "input_tokens", "output_tokens", "cache_read_input_tokens", "latency_ms", "finish_reason", "status", "error_type"}`.
  - `status` is `"ok"` or `"error"`. On error the record is appended with zero tokens and `error_type=type(exc).__name__`, and the exception is re-raised unchanged.
  - `latency_ms` is an int measured around the provider call, including stream consumption.
- **Where it runs.** Recording happens inside `call_llm` itself, so the P5-9 harness wrapper (which replaces `llm_client.call_llm` with a wrapper that calls the original) keeps working and the two do not double-count. When a test patches a service's `_call_llm` seam, `call_llm` never runs and nothing is recorded; that is intended.
- **Stage tags.** Wrap each call site's `_call_llm(...)` invocation in `call_tag(stage=...)` with these values:

  | Stage | Call site |
  |---|---|
  | `desk_review` | desk_review (both curated and framework paths) |
  | `evidence_extraction` | claude_analyzer `_run_evidence_extraction` / `_run_framework_evidence_extraction` |
  | `judge` | claude_analyzer `run_gap_analysis` main call and per-framework call |
  | `synthesis` | claude_analyzer synthesis |
  | `screening` | screening |
  | `followups` | followup_engine |
  | `context_profile` | context_profiler |
  | `vision` | document_processor |

  Tags wrap the call; they must not add kwargs to the seam.
- **Framework tags.** Per-framework work runs inside `call_tag(framework_id=...)`: the desk-review per-framework unit, per-framework extraction, and the per-framework judge. The DPDPA single-framework path (`run_gap_analysis`) is tagged `framework_id="dpdpa"`.

### D-P6-1-D: Bounded concurrency helper (`app/services/parallel.py`, new)

`run_bounded(fn, items, *, max_workers: int) -> list[tuple[Any, BaseException | None]]`:

- Returns one `(result, None)` or `(None, exc)` per item, **in input order**.
- Each task runs under its **own** `contextvars.copy_context()` (`ctx.run(fn, item)`), so collectors and tags propagate. The collector list object is shared by reference; guard appends with a `threading.Lock` inside `llm_client`.
- An exception in one item never cancels the others.
- `max_workers <= 1` or `len(items) <= 1` runs sequentially in the calling thread, with no executor.

Apply it with `max_workers=settings.llm_max_concurrency` at exactly these three places, and nowhere else:

1. **`desk_review.py:115` loop.** Parallelise only the per-framework `_normalize_result(framework_id, _desk_review_call(...))` unit, wrapped in `call_tag(framework_id=framework_id)`. Keep the `results`/`errors` dicts and all DB work in the caller thread, filled in `framework_ids` order. Worker threads never touch `db`.
2. **`claude_analyzer.py:295` `_collect_framework_evidence`.** Keep the "reuse desk-review evidence" branch sequential and unchanged. Run the frameworks that need extraction through `run_bounded`. Merge their evidence into the result dict in `framework_ids` order, so dict ordering and content are identical to sequential.
3. **`claude_analyzer.py:417` `run_multi_framework_analysis` judge loop.** The per-framework body (prompt build, call, parse, validate, flag) becomes a function run through `run_bounded`. `framework_results` and `total_usage` are assembled afterwards in `framework_ids` order. The existing per-framework `except Exception` → `{"error": ...}` behaviour is preserved exactly, including the error dict shape.
   - Synthesis stays after all frameworks, sequential.
   - Log lines may interleave; their text is unchanged.

**Equivalence requirement:** for the same seam responses, the returned dicts at concurrency 4 must be `==` to those at concurrency 1 (scenario 7).

### D-P6-1-E: Where the records are persisted

- **Analysis.** In `app/routers/analysis.py`, wrap each analyzer invocation (`run_gap_analysis(` ~L277, and `run_multi_framework_analysis(` ~L518) in `with llm_client.collect_calls() as calls:`.
  - `analysis_pipeline.record_framework_run` gains a keyword `llm_calls: list[dict] | None = None`. When it is not `None`, it is stored as `envelope["llm_calls"]`. When it is `None` the envelope is unchanged, which keeps `tests/test_analysis_pipeline.py:475` exact.
  - The router passes the records whose `framework_id` equals that run's framework.
  - Records with `framework_id is None` (synthesis) go **only** into the envelope of the run for `framework_ids[0]`, under a new key `"shared_llm_calls"`. Rule, written into the docstring: **the LLM cost of one trigger is the sum over its runs of `llm_calls` plus `shared_llm_calls`**.
  - Do not bump `CLAIMS_SCHEMA_VERSION`, because the keys are additive and optional. If an existing test asserts the exact envelope key set, stop and report.
- **Desk review.** Wrap the per-framework phase of `run_desk_review` in `collect_calls()`. `_raw_response(...)` gains an `llm_calls` argument, written as a top-level `"llm_calls"` key next to `"schema_version"`/`"frameworks"`. `RAW_RESPONSE_SCHEMA_VERSION` stays `2`, since the key is additive.
- **Failures.** When a framework fails, its records (with `status="error"` where applicable) are still persisted. `fail_runs` gains the same optional `llm_calls` keyword with the same per-framework rule.

### D-P6-1-F: Temperatures

- `app/services/screening.py:117` and `app/services/document_processor.py:188`: change `temperature=1` to `temperature=0`.
- Replace the "preserve the original default" comments with one line each. Screening: *"0: screening feeds pre-fill; run-to-run stability is measured by P5-9 (P6-1)."* Vision: the same idea for OCR.
- Neither call site is in a golden recording. Confirm with `git grep -n "screening\|vision" tests/fixtures`.

### D-P6-1-G: Synthesis prompt

In `app/frameworks/prompts.py` `build_synthesis_prompt`:

- Item 4 becomes: *"**framework_comparison**: For each framework, a 1-2 sentence posture summary. Do not estimate or state any numeric score; scores are computed deterministically elsewhere."*
- The JSON example becomes `"iso27001": {"summary": "..."}`.
- Nothing else in the prompt changes.

### D-P6-1-H: Startup recovery (`app/services/run_recovery.py`, new)

`recover_interrupted_work(db) -> dict[str, int]`, called from `lifespan` after `_assert_framework_catalog_complete()` and only when `settings.recover_interrupted_on_startup` is true. It uses its own `SessionLocal()`, commits once and logs one INFO line with the counts.

| Row | Condition | Change |
|---|---|---|
| `AnalysisRun` | `status == "running"` | `status="failed"`, `completed_at=now(UTC)`, envelope `claims=[]`, `error={"type": "Interrupted"}` (same mutation as `fail_runs`; factor out a shared helper instead of duplicating it) |
| `Assessment` | `status == "analyzing"` | `status="error"` |
| `Assessment` | `desk_review_status == "analyzing"` | `desk_review_status="error"` |
| `DeskReviewSummary` | `status == "analyzing"` | `status="error"`, `error_message="Desk review was interrupted by a restart. Run desk review again."` |

- Terminal rows are never touched. The function is idempotent.
- It returns counts keyed `analysis_runs`, `assessments`, `desk_review_assessments`, `desk_review_summaries`.
- Document the assumption in its docstring: **single-process deployment**. With multiple workers, one worker's startup would fail another worker's live run. That is acceptable in local-only use, and it is revisited when real job infrastructure arrives (plan Track 4).
- Do **not** change the synchronous execution model of `run_analysis_web`/`trigger_analysis`, or desk review's `BackgroundTasks`. The P5-9 harness drives these routes synchronously. Moving to a job queue is out of scope.

## Key files

| Path | Change |
|---|---|
| `app/config.py` | Settings (D-P6-1-A) |
| `.env.example` | Commented documentation of the four settings |
| `app/services/llm_client.py` | Timeout/retries, `response_schema`, `collect_calls`, `call_tag`, recording |
| `app/services/parallel.py` (new) | `run_bounded` |
| `app/services/run_recovery.py` (new) | Startup recovery |
| `app/main.py` | `lifespan` call only |
| `app/services/claude_analyzer.py` | Stage/framework tags; concurrency at the two loops |
| `app/services/desk_review.py` | Tags; concurrency at the per-framework loop; `llm_calls` in raw response |
| `app/services/screening.py`, `app/services/document_processor.py` | Temperature, tags |
| `app/services/followup_engine.py`, `app/services/context_profiler.py` | Stage tags only |
| `app/frameworks/prompts.py` | `build_synthesis_prompt` only |
| `app/services/analysis_pipeline.py` | `llm_calls` keyword on `record_framework_run`/`fail_runs`; shared fail helper |
| `app/routers/analysis.py` | Collector around analyzer calls; pass records through |
| `tests/test_p6_1_llm_plumbing.py` (new) | All scenarios below |

**Do not touch:**
- any other prompt text
- `tests/fixtures/**`, `tests/support/**`
- scoring, reports, PDF, templates
- `validation/**`, `scripts/validation/**`

## Non-goals

- Wiring `response_schema` into any v1 call site.
- Untrusted-content delimiters. That is a prompt change; it moves to P6-3 (v2 prompts) so the v1 goldens stay valid.
- Retries on parse or validation failure.
- A job queue, async analysis, or SQLite WAL (that is P6-0c).
- Bedrock (P6-13).

## Test scenarios (all required; you may add cases, not drop or weaken them)

1. **Client config.** `_get_client()` constructs `OpenAI` with `timeout` and `max_retries` from settings. Monkeypatch the settings, reset `_client`, and assert on the constructor kwargs through a fake.
2. **No-schema regression.** With a fake OpenAI client capturing kwargs, `call_llm(...)` without `response_schema` sends exactly today's kwargs (model, messages, max_tokens, temperature, `extra_body == _REQUEST_PREFS`), for both stream and non-stream.
3. **Schema request.** With `response_schema`, `response_format` matches D-P6-1-B, and `extra_body["provider"] == {"data_collection": "deny", "zdr": True, "require_parameters": True}`. `_REQUEST_PREFS` is unchanged afterwards.
4. **Recording.** Inside `collect_calls()` with `call_tag(stage="judge", framework_id="iso27001")`, one call yields one record with exactly the D-P6-1-C keys and correct values. A provider exception yields a `status="error"` record and re-raises. No record is produced outside a collector. Nested collectors: only the inner one receives the record.
5. **Context propagation.** Calls made inside `run_bounded` workers are recorded in the caller's collector with the tags set inside each worker.
6. **`run_bounded` semantics.**
   - input order preserved
   - one failing item returns `(None, exc)` and the others complete
   - `max_workers=1` runs in the calling thread (assert `threading.get_ident()`)
   - with `max_workers=3` and 3 items that block on a barrier, all three are in flight at once (the test would deadlock if they ran sequentially; use a timeout)
7. **Analyzer equivalence.** `run_multi_framework_analysis` over `["dpdpa", "iso27001", "nist_csf"]`, with the claude_analyzer `_call_llm` seam patched to return valid canned per-framework JSON keyed on the system prompt. The result at `llm_max_concurrency=4` is `==` to the result at `1`. The seam was invoked concurrently (max in-flight > 1) at 4. One framework raising yields the same error dict at both settings.
8. **Desk review.** A two-framework assessment where one framework's call raises. Status and partial-failure message are unchanged from today's behaviour. `raw_ai_response` contains `llm_calls`, and the per-framework results are identical at concurrency 1 and 4.
9. **Envelope persistence.** An analysis trigger over two frameworks through the route (the existing test harness pattern), with `llm_client.call_llm`'s underlying provider faked so records are produced. Each run's envelope has `llm_calls` for its own framework only. Synthesis records appear only in the first run's `shared_llm_calls`. The sum across runs equals the number of provider calls.
10. **Temperatures.** Screening and vision seams are invoked with `temperature=0`.
11. **Synthesis prompt.** `build_synthesis_prompt(...)` output contains neither `estimated_score` nor `0-100`, and still contains `framework_comparison`.
12. **Startup recovery.**
    - Seed one each of: running run, analyzing assessment, analyzing desk review (assessment + summary), plus one completed run and one completed assessment. After `recover_interrupted_work`, the first group is failed/error exactly as in D-P6-1-H and the completed rows are byte-identical.
    - A second call returns all-zero counts.
    - With the setting `False`, `lifespan` does not call it.
13. **Golden guard.** `git diff --stat main -- tests/fixtures tests/support` is empty, and `tests/test_golden_dpdpa.py` passes unmodified.
14. **Harness compatibility.** A wrapper that replaces `llm_client.call_llm` with `def w(tier, **kw): return original(tier, **kw)` still records exactly one record per call, not two. `inspect.signature(call_llm)` has `response_schema` defaulting to `None`.

## Verification (before reporting done)

1. Run `.venv/bin/pytest -q`. The full suite must pass at the Step 0 baseline plus the new tests, with only the known documented flake allowed.
2. **Live smoke, only if `OPENROUTER_KEY` is set in `.env`.** Run the app and one DPDPA assessment desk review and analysis via the routes (or `scripts/validation/run_company.py c0-example --llm live` if the P5-9a harness is on `main` by then).
   - Paste the resulting `AnalysisRun.claims_json["llm_calls"]` and the desk-review `llm_calls` (tokens, latency) into Results.
   - If no key is available, say so explicitly. Do not claim a live check.
3. **Restart smoke.** Start uvicorn, trigger desk review, kill the process mid-run, restart. The assessment shows the error state and the "run desk review again" message instead of a spinner. Record what you observed.

## Done criteria

- Every scenario passes.
- The full suite passes with the counts recorded.
- Scenario 13 is clean.
- The Results section is filled in.
- The PR is opened against `main` from `codex/p6-1-llm-plumbing`. **Claude reviews before merge** (`[AR]` per plan Part G).

## Report back

Append `## Results` to this file with:
- the Step 0 baseline
- files changed
- test counts
- smoke evidence
- any deviation stopped on (per the rule at the top)
- the PR link
