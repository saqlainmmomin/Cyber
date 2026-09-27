# Phase 6 kickoff: next session (2026-09-27)

## Goal

Start the Phase 6 work that is now unblocked, running tracks in parallel where they touch different files. Done means:

- **(A) P6-3b.** Its handoff is written by an Opus designer, with contract tests written by Claude, implemented by Codex, passed through an adversarial review, and opened as a PR. A flag-off parity check and a flag-on live smoke both pass.
- **(B) LLM JSON reliability fix.** Merged. It needs a test and a live smoke showing that non-JSON responses are now recorded and handled.
- **(C) Small follow-ups.** Merged as one or two small PRs, or explicitly deferred with a reason.

The orchestrator (Claude) designs, reviews, commits and opens PRs. Codex implements. Opus subagents do the heavy design and review work, so the orchestrator's own context stays clear.

## Current state (`origin/main` @ `e12f61a`)

### Merged 2026-09-26

| PR | What it did |
|---|---|
| #61 | Criteria for the 13 new NIST CSF 2.0 IDs. |
| #62 | **P6-0c dev hygiene.** GitHub Actions now runs pytest on Python 3.13 for every PR. Adds `.python-version` and `requirements-dev.txt`. SQLite runs in WAL mode with `busy_timeout`. CORS middleware removed. The dev server binds to 127.0.0.1. The previously known-failing tests are fixed, **so the full suite is expected to be fully green.** |
| #63 | **P6-1d.** Every OpenRouter call now sends `reasoning: {"enabled": false}`, because deepseek-v4-flash was reasoning invisibly and burning its whole `max_tokens` budget. Registry frameworks (everything except curated DPDPA) always run evidence extraction and merge the result with the desk-review quotes. A failed or empty extraction falls back to the full documents. `reasoning_tokens` is recorded whenever the provider reports it. |
| #64 | **P6-3a.** Adds the v2 grounding core as the package `app/services/grounding/`, which nothing imports yet. It covers chunking with offset maps, metadata, cross-framework batches, claim extraction, locate and support verification, and the `ClaimSet`. Adds `v2_*` settings and `scripts/grounding_smoke.py`. |
| #65, #66 | Session results, plus Saqlain's answers to P6-3 Q1–Q6. |

The full record of the last session is in the Results section of `tasks/handoffs/2026-09-26-next-session-kickoff.md`.

### P5-9 Stage C baseline on v1 (2026-09-26, main @ 8512cf3, c1–c3 × 3 runs)
- **Catch rate:** 92.8%.
- **False positives:** 63% on decoy controls and 67% on clean controls. Background agreement is only 3–9%. v1 over-flags, so the recall number is inflated.
- **Output:** in `~/cyberassess-runs/2026-09-26-stage-c-baseline-v1/`. Its `summary.*` files quote the answer key, so **the orchestrator and anyone working on prompts, the analyzer or desk review must not open them.**
- **Call health:** 148/148 recorded calls ended `stop`, with no reasoning tokens. But **4 calls returned Markdown instead of JSON while being recorded as `stop`/`ok`.**
  - Two NIST and one ISO evidence extraction fell back to documents silently.
  - One DPDPA desk review failed (c2 run-3).
  - That is the defect task (B) fixes.

### Decisions already made (do not relitigate)
- **P6-3 Q1–Q6** (Answers section of `tasks/handoffs/2026-09-26-p6-3-v2-stages-0-1.md`):
  - **Q1:** v2 Stage 1 coverage is capped at `partial`, and a requirement with no claims is `not_covered`.
  - **Q2:** no absence or red-flag findings until P6-4.
  - **Q3:** keep screenshot claims, flagged `derived_from_image` and `needs_review`.
  - **Q4:** lifting the 5k-word upload cap is its own task, alongside P6-4. Not in this session.
  - **Q5:** no NFKC folding.
  - **Q6:** v2 concurrency is 6, set by its own v2 setting; v1's `llm_max_concurrency` stays at 4.
- **Reasoning is off for every call** (#63).
- **v1 stays the default** until P6-5's A/B test shows v2 is better (D-P6-E).
- **Stale protected-surface guards:** when an old PR's `test_protected_surface_guard_uses_three_dot_diff` trips on a PR that legitimately touches a protected path, add `:(exclude)<path>` entries for exactly the touched files, with a comment naming the PR. See `tests/test_p6_nist_csf2_alignment.py` and `tests/test_p6_1b_framework_batching.py`. Never delete or broadly narrow a guard.
  - Saqlain has approved this convention. The auto-mode classifier may still block these edits as "security test removal"; if it does, ask him once.

### Primary checkout
`/Users/saqlainmomin/dpdpa-gap-tool` is on the stale branch `codex/p5-9a-validation-harness`. It also holds untracked scratch files: `fix_*.py`, `super_fix.py`, stale `validation/companies/c1–c4` copies and `*_backup` dirs.
- Do not switch its branch, and do not delete anything in it, without asking Saqlain; he is cleaning it up.
- Do all work in worktrees off `origin/main`. No other worktrees exist right now.

## Tasks

### (A) P6-3b: the v2 flag, desk-review adapter and persistence `[AR]`

The spec is the "P6-3b outline" section of `tasks/handoffs/2026-09-26-p6-3-v2-stages-0-1.md` (around line 671), together with the Answers section and Track 1 / Part B of `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`. In scope:
- the `analysis_pipeline_version` flag, defaulting to v1
- the v2 branch of desk review, which calls `run_stages_0_1`
- persisting the claim set, kept out of `AnalysisRun.claims_json["claims"]` (v1 already uses that key)
- the desk-review adapter that maps v2 claims onto desk-review findings, so the P5-4 pre-fill keeps working. Coverage is capped at `partial` (Q1). `absence_findings` and `signal_flags` stay `[]` (Q2).
- the `_persist_findings` path that accepts a precomputed citation
- the LLM metadata fallback
- the v2 concurrency setting of 6 (Q6)
- failure mapping: every framework named by `affected_framework_ids()` fails its desk review with a message

**Process** (per `tasks/agent-ownership.md:77`):
1. An Opus subagent writes `tasks/handoffs/2026-09-27-p6-3b-v2-flag-and-adapter.md` in house style. Model it on the P6-3 handoff: Step 0 fact checks with file:line, numbered decisions `D-P6-3b-A…`, key files, a do-not-touch list, test scenarios, verification, and an empty Results section.
2. The same designer writes the **contract tests** first. They must fail only because the code is missing, and they must be verified against a throwaway reference implementation in the scratchpad.
3. **P6-3a's scenario-17 dormancy guards will fail by design**, because P6-3b imports the grounding package. Narrowing those guards is a designer-owned edit to `tests/test_p6_3a_grounding.py`, committed with the contract tests. Codex must not edit that file.
4. Commit the handoff and contract tests, then dispatch Codex.
5. Run an adversarial Opus review focused on:
   - **flag-off parity:** byte-identical v1 prompts and fingerprints, and the golden DPDPA tests
   - **pre-fill behaviour:** DPDPA-only and UCC-cluster pre-fill from v2 output
   - **error mapping**
6. Send real findings back to Codex as a narrow fix prompt, then open the PR.

**Live smoke (orchestrator):** a flag-on desk review of the synthetic fixtures in `tests/grounding_fixtures/` through the real route or service. It must show:
- grounded `text_span` citations reaching `question_engine` pre-fill
- no pre-fill above `partial`
- every call ending `stop`

**Do not use `validation/` for this smoke.**

### (B) LLM JSON reliability (Claude investigates; the fix is small)

Symptom from the baseline: a model returned a Markdown report instead of JSON with `finish_reason=stop`. The call record said `ok`, and the caller either silently fell back to documents (evidence extraction) or failed the framework (desk review). Investigate `app/services/llm_client.py` (`call_llm`, `_record_call`, the `response_schema` path, `_REQUEST_PREFS`) and the call sites in `app/services/claude_analyzer.py` and `app/services/desk_review.py`. Then:
1. **Enforce structured output** for desk review and evidence extraction wherever the provider supports it (`response_format` / `json_schema`, which the judge may already use). Watch that `require_parameters` does not shrink the ZDR provider pool into "no endpoints".
2. **Record parse failures in the call record,** for example `parse_ok: false` or `status: "parse_error"`, so a non-JSON `stop` is visible in the stored records and in `llm_usage`.
3. **Retry once** on a JSON parse failure, where the call site doesn't already do so.
4. **Keep DPDPA golden recordings byte-identical where possible.** If the request shape must change for DPDPA, update the golden pin deliberately and say why.

Add tests with a fake client that returns Markdown. For the live smoke, run c0-example ISO through the harness as a black box, as in the last session, writing to `~/cyberassess-runs/2026-09-27-json-enforcement-smoke/`:
```bash
set -a; . ./.env; set +a
.venv/bin/python -m scripts.validation.render_evidence c0-example
.venv/bin/python -m scripts.validation.run_company c0-example --llm live --runs 1 --stop-after analysis --out <dir>
```
**The independence rule applies in full** (see Constraints).

### (C) Small follow-ups (bundle, or defer with a reason)
1. **ISO.A8.3 missing `compliance_status`.** `GapAssessmentItem._coerce_permissive_fields` (`app/schemas/llm_output.py:64-70`) turns a missing or unknown status into `not_assessed`, and that counts as "covered", so the batch retry never fires. Fix: in the batched `validate_partial` path only, treat an unknown or missing status as a missing ID so the existing single retry covers it. Log every coercion. Do not change the unbatched or DPDPA paths, which would be a policy change via `IncompleteAssessmentError`.
2. **Desk-review quotes are never grounded.** `_evidence_from_desk_review` (`claude_analyzer.py` around line 175) passes `source_quote`/`content` through. Run the reused quotes through `_ground_evidence_quotes(reused, documents)` for registry frameworks before merging them.
3. **The context prompt invents IDs.** The context profiler's prompt (`app/services/context_profiler.py`) pads `likely_not_applicable` with made-up IDs, up to "CH4.SDF.100", until it hits `max_tokens`. Constrain it to the framework's real IDs, or filter against them, and cap the list.
4. **Harness bug.** In `scripts/validation/run_company.py`, `perform()` (lines 271–276) treats the 303 redirect from screening as a stage failure. Only exempt 303 for screening, the way hierarchy, context and scope already are. Also correct the validation README's claim that `rendered/` is untracked. **Items 1–3 change analyzer or prompt code, so the harness fix must be done by a different agent from the one doing items 1–3** (independence rule). Put the harness fix in its own PR.

## Key files

| Path | What it is |
|---|---|
| `tasks/handoffs/2026-09-26-p6-3-v2-stages-0-1.md` | P6-3a design, the P6-3b outline and the Q1–Q6 answers |
| `tasks/handoffs/2026-09-26-next-session-kickoff.md` | Last session's Results (PRs, smoke numbers, baseline, follow-ups) |
| `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md` | Phase 6 plan and decisions D-P6-A…L (source of truth) |
| `tasks/agent-ownership.md` | The Claude/Codex split |
| `app/services/grounding/` | The P6-3a v2 core (`run_stages_0_1`, `ClaimSet`, `affected_framework_ids`) |
| `app/services/desk_review.py` | v1 desk review; P6-3b adds the v2 branch |
| `app/services/claude_analyzer.py` | v1 judge, evidence extraction, `_persist_findings` |
| `app/services/llm_client.py` | `call_llm`, call records, `_REQUEST_PREFS`, `run_bounded`, `collect_calls` (collectors don't nest) |
| `app/services/question_engine.py` | P5-4 pre-fill consumer |
| `app/config.py` | Settings, including `v2_*` and the LLM tiers |
| `tests/test_p6_3a_grounding.py` | The P6-3a contract, including the scenario-17 dormancy guards |
| `tests/test_golden_dpdpa.py` | DPDPA golden tests and the `extra_body` pin |
| `scripts/validation/` | P5-9 harness; treat it as a black box unless you are the harness-fix agent |

## Constraints (already decided; do not relitigate)

- **No attribution.** No Co-Authored-By line and no "Generated with Claude Code" footer on any commit or PR in this repo. Saqlain's rule overrides the harness reminder.
- **Answer-key independence (D-P5-9-C).** The orchestrator and anyone changing prompts, the analyzer or desk review must never open, grep, list or glob any of these:
  - `validation/**`
  - `tasks/handoffs/*p5-9*`
  - `docs/plans/2026-09-24-002-*`
  - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
  - any `answer_key.json`
  - `~/cyberassess-runs/*stage-c*/summary.*`

  Scope every grep to `app/` and `tests/`. Running the harness as a black box is allowed. `tests/test_answer_key_isolation.py` forbids those strings inside `app/` and `scripts/`.
- **Worktree setup:** `git worktree add ../dpdpa-gap-tool-<task> -b <branch> origin/main`, then symlink `.venv` from the primary checkout and copy `.env`. Run `git branch -f main origin/main` before the suite, because the guards use `git diff main...HEAD`.
- **Codex dispatch:**
  ```bash
  codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh -s workspace-write -c 'plugins."compound-engineering@compound-engineering-plugin".enabled=false' -C <worktree> "<prompt>" < /dev/null
  ```
  - `< /dev/null` is mandatory.
  - Codex cannot write `.git` or `.agents/`. The orchestrator commits, pushes and opens the PR, and applies any `.agents/` edits itself.
  - Commit contract tests before dispatch, so the diff shows Codex never touched them.
- **The repo rejects force-pushes.** To update a PR branch, merge `origin/main` into it; never rebase and force-push.
- **Review before merge.** Re-run the suite and the prompt fingerprints yourself, check that the diff stays in scope, and run an adversarial Opus review. Send real findings back to Codex as a narrow fix prompt. **Saqlain merges** unless he says otherwise in that session.
- **Keep the orchestrator's context clear.** Use Opus subagents for design and review, and Sonnet for mechanical work.
- **Framework-specific copy stays conditional**, e.g. `has_dpdpa`. Scoring stays deterministic and never uses the LLM. All PDF text goes through `S()`.

## Pending on Saqlain (don't block on these)
- Clean up the primary checkout: stale `validation/companies/c*` copies, `*_backup` dirs and the `fix_*.py`/`super_fix.py` scripts. First confirm that the committed c1–c3 packs are the intended data.
- Update c4's answers for NIST CSF 2.0. c4 can't be baselined until that's done.
- Criteria review CSV export, DPDPA first. It unblocks P6-2b.
- Review the ISO clause titles and descriptions. This gates P5-7.
- Track 4 security, before any real client data.

## Verification
Every change ships with a check you run yourself (the smoke-test default).
- **(A):** contract tests pass without being edited; the full suite is green; v1 fingerprints and the golden DPDPA tests are unchanged with the flag off; the flag-on fixture smoke passes.
- **(B):** tests with a fake Markdown response pass, and the live c0 smoke shows every call parsed or visibly recorded as a parse failure.
- **(C):** each fix has a test. Harness fix: a c1 run no longer reports screening as a defect. That run is done by the harness-fix agent only.
- CI must be green on every PR, since #62 added it.

## Report back
Append a `## Results` section to this file. Cover:
- PR links
- smoke numbers
- decisions made
- anything that still needs Saqlain

Also update `tasks/todo.md` and the auto-memory project status. Commit this file with the first PR of the session.

## Results

Session run 2026-09-27 by the Claude orchestrator. Codex (gpt-5.6-luna, xhigh) implemented, Opus subagents designed and reviewed, and a separate Sonnet agent did the harness fix. All four PRs have CI green. None is merged: Saqlain merges.

### PRs
| PR | Task | State |
|---|---|---|
| [#67](https://github.com/saqlainmmomin/Cyber/pull/67) | (C4) Harness: screening 303 counts as success; README `rendered/` note corrected | open, CI green |
| [#68](https://github.com/saqlainmmomin/Cyber/pull/68) | (B) LLM JSON reliability. Also carries this file | open, CI green |
| [#69](https://github.com/saqlainmmomin/Cyber/pull/69) | (C1–C3) batched status retry, grounded desk-review quotes, profiler ID cap | open, CI green |
| [#70](https://github.com/saqlainmmomin/Cyber/pull/70) | (A) P6-3b: v2 flag, desk-review adapter, claim-set persistence | open, CI green |

**Merge order.** Any order works. #68, #69 and #70 each add `:(exclude)` entries to the same lines in `tests/test_p6_3a_grounding.py` and `tests/test_p6_nist_csf2_alignment.py`. #67 also touches the first of those files. Whichever PR merges later needs a keep-both resolution, done by merging `origin/main` into the branch (never a rebase).

### (A) P6-3b (#70)
- **Handoff and contract tests.** An Opus designer wrote `tasks/handoffs/2026-09-27-p6-3b-v2-flag-and-adapter.md` and 25 contract tests (`tests/test_p6_3b_v2_flag.py`, `tests/test_p6_3b_metadata_fallback.py`).
  - The tests were checked against a throwaway reference implementation. That reference passed a full suite of 911 tests, and the tests caught all 18 deliberate mutations made to it.
  - The tests were committed before Codex was dispatched, and Codex did not modify them.
  - The P6-3a scenario-17 dormancy guard was narrowed to exactly one permitted importer, `desk_review_v2.py`.
- **Adversarial review found three real defects:**
  - the source load ran outside the `try`, so the summary could be stuck in `analyzing`
  - the metadata fallback's exceptions could discard a completed Stage-1 claim set
  - the `"citation" in item` check was too broad for v1 output

  Codex fixed all three. I amended the citation check to accept only a dict or `None`, because the contract pins `None`.
- **Flag off.** Golden DPDPA and the fingerprint tests are unchanged. Full suite: 914 passed, 10 skipped.
- **Live flag-on smoke** (synthetic `tests/grounding_fixtures/`, real `run_desk_review` → `question_engine`; output in `~/cyberassess-runs/2026-09-27-p6-3b-flag-on-smoke/`):
  - DPDPA-only: 57 of 57 findings have grounded `text_span` citations. Coverage is 23 partial and 18 not_covered. 23 questions were pre-filled, all `partially_implemented`.
  - DPDPA+ISO (UCC): 236 of 236 findings are grounded. Coverage is 79 partial and 55 not_covered. 19 cluster and single-control questions were pre-filled, all `partially_implemented`.
  - No pre-fill was above `partial`. Every call ended `ok`/`stop`, with 0 reasoning tokens.

### (B) JSON reliability (#68)
- **Root cause.** Desk review and evidence extraction never asked for JSON. `call_llm` recorded `ok` for any non-empty reply, and the parse failed later, outside the call record.
- **Fix.**
  - `json_output=True` sends `response_format: json_object` **without** `require_parameters`, so the ZDR pool stays exactly as it was.
  - A reply that doesn't parse is recorded as `status: "parse_error"` with `error_type: "JSONDecodeError"`, then retried once. The retry's record carries `attempt: 2`.
  - A second failure raises `LLMOutputParseError`, a `ValueError`, into the existing fallbacks.
  - A `finish_reason="length"` reply is not retried (review finding).
- **Golden DPDPA recording.** Byte-identical. The DPDPA desk-review request pin in `test_p5_3` was changed deliberately. The test proves that the request minus the new flag still hashes to the old key.
- **Tests.** 14 new tests with a fake client that returns Markdown or truncated JSON. Full suite: 900 passed.
- **Live smoke** (c0-example ISO through the harness, `~/cyberassess-runs/2026-09-27-json-enforcement-smoke/`):
  - all 8 stages ok
  - 13 of 13 stored call records `ok`/`stop` on the first attempt, with 0 reasoning tokens
  - no parse failure occurred live, so the retry path is covered by tests only

### (C) Follow-ups (#69 and #67)
1. **Batched missing or unknown status.** On the first pass, status is normalised (strip, lowercase) and a missing or unknown status is treated as a missing ID, so the existing retry covers it. On the retry pass it is coerced to `not_assessed`, so one bad item can't fail a whole framework (review finding). Unbatched and DPDPA paths are unchanged.
2. **Desk-review quotes.** For registry frameworks they are now grounded against the **untruncated** documents, not the reordered 20k-word window (review finding). Desk findings with no source quote now fail grounding.
3. **Context profiler.** `likely_not_applicable` is filtered to real DPDPA IDs and capped at 20, and the prompt lists the allowed IDs. The profiler is DPDPA-only: its signals are SDF and children's data, and its only consumer is `app/dpdpa/questionnaire.py`. I removed Codex's dead non-DPDPA branch.
4. **Harness (#67).** A separate Sonnet agent fixed this, so it was not the agent that did items 1–3. Its live c1 run (`--stop-after screening`) shows every stage ok and screening ok with no non_success. I reverted its unnecessary edit to the `test_retention` guard: that guard only checks uncommitted edits.

### Decisions made this session
- JSON enforcement uses `json_object` without `require_parameters`, not strict `json_schema`. The dynamic `{requirement_id: [...]}` maps can't be written as a strict schema, and `require_parameters` risks leaving no endpoints.
- A reply truncated at `max_tokens` is never retried.
- The context-profiler cap is 20, below DPDPA's 41 IDs.
- P6-3b defaults were taken from the handoff: screenshot claims count toward `partial`, flagged `needs_review`, and the metadata fallback is on.

### Needs Saqlain
- Merge #67–#70, resolving the guard-exclude conflicts with keep-both.
- Two P6-3b questions (#70): should screenshot-derived claims pre-fill, and should the metadata fallback stay on by default (about one cheap call per non-image document)?
- The harness's `llm_usage.jsonl` has its own `ok` field and no `status`. It was not checked whether a `parse_error` record would show up there. The stored `raw_ai_response["llm_calls"]` records do show it. A small harness follow-up if wanted, owned by the harness agent.
- `test_p5_6_rfi_rebuild.py::test_scenario_10` failed intermittently when several suites ran at once (seen twice, passes on rerun). Probably a shared-resource or timing race. Worth a look.
- The earlier pending items still stand: primary-checkout cleanup, c4's NIST 2.0 answers, the criteria CSV review, the ISO titles review, and Track 4.

### Saqlain's answers (2026-09-27, recorded before merge)
- **Screenshot claims (P6-3b):** yes. They count toward `partial` and can drive pre-fill, flagged `derived_from_image` and `needs_review`. The handoff default stands.
- **v2 metadata fallback:** on by default (`v2_metadata_fallback=True`). The default stands.
- **Harness `llm_usage.jsonl` status:** a small follow-up task. The harness agent adds `status`/`finish_reason` to `llm_usage.jsonl` in its own PR.
- **Flaky `test_p5_6_rfi_rebuild.py::test_scenario_10`:** investigate next session.
