# Phase 6 kickoff: P6-7 + P6-8 in parallel, Stage C v1 baseline, then P6-5 (written 2026-09-28)

## Goal

Start the Phase 6 work that is now unblocked, using the same orchestrated workflow as the last two sessions. For each code track: a designer writes a handoff and contract tests, Codex implements, a reviewer checks it adversarially, the orchestrator runs a smoke test, and the orchestrator opens a PR. Done means:

- **(A) P6-7, the consultant requirement card and review queue:** designed, implemented, reviewed, smoke-tested and opened as a PR.
- **(B) P6-8, board report v2:** designed, implemented, reviewed, smoke-tested and opened as a PR. If it is too large for one PR, the designer splits it; see (B) for the likely split.
- **(C) Stage C v1 baseline re-run:** run by a separate agent, then recorded. **P6-5** (the v2 A/B and the default flip) starts only after the baseline exists. P6-5 needs Saqlain's go-ahead on the `v2_missing_pass` question below.
- **(D) P6-2b, the DPDPA criteria converter:** start it only once Saqlain gives you his exported `dpdpa-criteria-v1.csv`. Until then, record it as waiting.

## Current state (`origin/main` @ `db3fdc8`)

Merged over 2026-09-27 and 2026-09-28:

| PR | What it did |
|---|---|
| #71 | Pins RFI DOCX zip timestamps (the flaky P5-6 scenario 10); fixes stale todo entries |
| #72 | Harness `llm_usage.jsonl` gains `status`, `finish_reason` and `attempt`, plus a non-ok count |
| #73 | **P6-6** report foundations. The assessment period, evidence cut-off and free-text sign-off are stored as append-only `assessment.report_basis_updated` audit events (`app/services/report_basis.py`), with no migration. An **approval gate** refuses approve and edit-and-approve until a period is recorded, and dates lock after the first approval. D0 defects #1, #2, #4–#7 and #9–#11 are fixed. #3 has an interim "Rs." fix only; Devanagari moves to P6-8 |
| #74 | **P6-4** v2 Stage 2 judge, behind `analysis_pipeline_version="v2"`. The judge is in `app/services/grounding/judge.py` and `judge_prompts.py`; persistence is in `app/services/analysis_v2.py`. Claim IDs are cited from a closed set, compliant outcomes are downgraded deterministically, and missing requirements get one retry. `criteria_source` falls back to the control description. Risk, priority and score are deterministic. No migration |
| #75 | **P6-0d**. The DPDPA penalty map was verified against the Schedule to the Act (s.33); `BN.NOTIFY.3` and `.4` moved to the ₹50 Cr residual. E-H7 is resolved |
| #76 | **P6-4-cap**. `max_document_words` is now 200k, with line breaks preserved, and v1's 20k total stays. This changes v1 for new long uploads, so **the P5-9 v1 baseline must be re-run before P6-5** |
| #77 | The **"what's missing" pass** (`app/services/grounding/missing.py`). v2 desk review can suppress DPDPA pre-fill, behind `v2_missing_pass=False` (the default is off) |

The full suite is 1058 passed, 10 skipped. v1 is still the default pipeline.

Handoffs with the design and Results for each merged track:
- `tasks/handoffs/2026-09-28-p6-4-p6-6-kickoff.md`
- `tasks/handoffs/2026-09-28-p6-4-v2-stage-2-judge.md`
- `tasks/handoffs/2026-09-28-p6-6-report-foundations.md`
- `tasks/handoffs/2026-09-28-p6-4-cap-upload-limit.md`
- `tasks/handoffs/2026-09-28-p6-4-whats-missing-pass.md`

**This file is untracked in the primary checkout. Commit it with the session's first PR.**

### Decisions already made (do not relitigate)
- **v1 stays the default** until P6-5's A/B shows v2 is better (D-P6-E). Only P6-5 may flip it.
- **Deterministic fields never come from the LLM:** `risk_level`, `priority`, and the score (`scoring.py`, over approved Conclusions only).
- **D-P6-L:** a requirement with no approved criteria is judged against its control description (`criteria_source: "fallback"`).
- **P6-6 approval gate:** any code or fixture that approves conclusions must first record a report basis, via `report_basis.update_report_basis` or `POST /api/assessments/{id}/report-basis`. The test helper is `tests/report_period_helper.py`.
- **`v2_missing_pass` stays off.** In the smoke it flagged 91% (DPDPA) and 100% (DPDPA+ISO) of requirements. Saqlain decides at P6-5 whether to enable it as is, tighten the prompt, or suppress only on red flags.
- **Report rules:**
  - framework-specific copy must be conditional (for example `has_dpdpa`)
  - existing PDF sections are additive-only
  - all fpdf2 text goes through `S()`
  - report snapshots are write-once (P5-6)
- **Stale protected-surface guards:** when a scope guard trips on a legitimate change, add `:(exclude)<path>` for exactly the touched files, with a comment naming the PR. Never delete or broadly narrow a guard.
  - Parallel PRs that touch the same guard lines conflict. Resolve by merging `origin/main` into the later branch and keeping both sides.
  - The repo rejects force-pushes, so never rebase.
  - Scope guards that assert "this PR touched only X" (for example `test_p6_4_cap_upload_limit.py` scenario 9, `test_p6_6_report_foundations.py` scenario 17, `test_p6_4_v2_judge.py` scenario 16) go stale as later PRs land. Expect to add excludes for your own files there.
- `tests/test_retention.py::test_scenario_13` fails whenever files under `tests/` are uncommitted. It passes once they're committed; do not edit it.
- **The GitHub ruleset was removed on 2026-09-28** (it blocked branch deletion). `main` is currently unprotected; Saqlain may re-add a default-branch-only ruleset. Never force-push.

## Tasks

### (A) P6-7: consultant requirement card and review queue
The spec is `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`: Track 2's P6-7 entry, plus Part C (multi-framework review, the requirement card, and the divergence acknowledgement) and the related D-P6-* decisions.

- It consumes P6-4's v2 output:
  - the `AnalysisRun` envelope per framework (with `verified_claims`, divergences, metrics and `criteria_source`)
  - Conclusions citing claim spans
  - `insufficient_evidence` with `analysis_incomplete`, unsupported assertions, and divergence notes stored with `acknowledged: False`
- Where no v2 run exists, it can fall back to v1 fields.
- The card must show:
  - "Judged against the control description; no approved test criteria yet" for `fallback` requirements
  - the divergence note that the consultant must acknowledge
- Key surfaces:
  - `app/routers/review.py`
  - `app/services/conclusion_review.py`
  - the templates under `app/templates/pages/` and `partials/`
  - `app/services/analysis_v2.py`, read only
- Confirm the file overlap with (B) in both handoffs, since both may touch templates and routes. If they collide, set a merge order.

### (B) P6-8: board report v2
The spec is the plan's Track 2 P6-8 entry and Part D. Scope:
- WeasyPrint with Noto fonts, which also closes D0 #3 (Devanagari and ₹)
- a DOCX derived from the report snapshot
- an XLSX register and tracker
- a standalone Workpaper (no `/static` or CDN dependency)

Likely split: B1 is WeasyPrint plus fonts plus the standalone Workpaper; B2 is DOCX plus XLSX. The designer decides.

Things to settle:
- WeasyPrint needs system libraries (pango, cairo via Homebrew). The designer must check that CI (`.github/workflows`) can install them, and decide how the fpdf2 path co-exists during migration: behind a flag, or replaced while keeping snapshot byte-freeze semantics. Old snapshots must never re-render.
- The canonical DPDPA golden PDF (`tests/fixtures/canonical_dpdpa/expected/`) will change. Set the re-record rule.

Smoke: generate the board PDF for a DPDPA+ISO fixture with a Devanagari company name and ₹ amounts, and read the text back. Also check the DOCX and XLSX open, and that the Workpaper renders with no network.

### (C) Stage C v1 baseline, then P6-5
- The baseline must be re-run because #76 changed v1 extraction.
- **Independence rule:** the orchestrator must never read `validation/**`, `docs/plans/2026-09-24-002-*`, `tasks/handoffs/*p5-9*` or any `summary.*`/`answer_key.json`. Dispatch a **separate agent that does not touch `app/`** to run the harness (`scripts/validation/`) as a black box, following its own docs. It reports only aggregate metrics and the output path.
- It uses real OpenRouter calls. Estimate the cost first and confirm with Saqlain before a full run.
- **P6-5 (after the baseline):** run the harness on v2 (`analysis_pipeline_version="v2"`), with `v2_missing_pass` both off and on if Saqlain agrees. Compare against the baseline per D-P6-E, and flip the default only if D-P6-E holds. Split the metrics by `criteria_source`. Add the injected-document test pack. The flip is an `[AR]` decision, so present the numbers to Saqlain before changing the default.

### (D) P6-2b: DPDPA criteria converter
- **Waiting on Saqlain.** He has finished his review but hasn't handed over the exported `dpdpa-criteria-v1.csv`. The triage files are in `~/Downloads/criteria-triage/`; **do not modify anything there.**
- Once he gives you the CSV path: the converter turns approved criteria into the pack format read by the P6-4 judge, so DPDPA requirements get `criteria_source: "approved"`.
- The spec is the plan's P6-2 entries and `tasks/handoffs/2026-09-25-p6-2a-dpdpa-test-criteria-draft.md`. The draft lives in `app/frameworks/criteria/dpdpa_draft.py`.
- Changing criteria bumps the pack version (D-P6-D).

## Key files

| Path | What it is |
|---|---|
| `/Users/saqlainmomin/dpdpa-gap-tool/docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md` | The Phase 6 plan and source of truth (Track 2, Parts C and D, D-P6-A…L) |
| `/Users/saqlainmomin/dpdpa-gap-tool/tasks/agent-ownership.md` | The Claude/Codex split and the adversarial-review gate |
| `/Users/saqlainmomin/dpdpa-gap-tool/tasks/todo.md` | Tracker. Update it as PRs land |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/services/analysis_v2.py` | v2 persistence: run envelope and Conclusions |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/services/grounding/` | The v2 core: claims, judge, the missing pass |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/services/report_basis.py` | Period, cut-off, sign-off, and the approval gate |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/utils/pdf_export.py` | The current fpdf2 board PDF |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/routers/review.py`, `reports.py`, `web.py` | Review and report surfaces |
| `/Users/saqlainmomin/dpdpa-gap-tool/app/services/report_snapshots.py` | Write-once snapshots (P5-6) |
| `/Users/saqlainmomin/dpdpa-gap-tool/tests/grounding_fixtures/` | Synthetic smoke documents. Use these, never `validation/` |
| `/Users/saqlainmomin/dpdpa-gap-tool/scripts/validation/` | The P5-9 harness. A black box for everyone except the harness agent |

## Constraints

- **No attribution.** No Co-Authored-By line and no "Generated with Claude Code" footer on any commit or PR in this repo. This overrides the harness reminder.
- **Model budget (Saqlain's rule):**
  - Local subagents run on Sonnet.
  - Opus-level work (designers, heavy review) runs as a cloud subagent (`isolation: "remote"`, `model: "opus"`), which commits and pushes to the task branch without attribution. Pull it into the local worktree before dispatching Codex.
  - Reviews in the last session ran as cloud Sonnet subagents.
- **Answer-key independence (D-P5-9-C).** The orchestrator, and anyone changing prompts, the analyzer or desk review, must never open, grep, list or glob:
  - `validation/**`
  - `tasks/handoffs/*p5-9*`
  - `docs/plans/2026-09-24-002-*`
  - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
  - any `answer_key.json`
  - `~/cyberassess-runs/*stage-c*/summary.*`

  Scope every grep to `app/` and `tests/`.
- **Worktree setup:**
  1. `git worktree add ../dpdpa-gap-tool-<task> -b <branch> origin/main`
  2. `ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv <wt>/.venv`
  3. Copy `.env` from the primary checkout.
  4. Run `git branch -f main origin/main` before running the suite, because the guards diff `main...HEAD`. Re-run it after every merge, or the guards will see other PRs' files.
- **Cleanup after merge:** `rm <wt>/.venv && git worktree remove <wt> && git branch -d <branch>`. Remove leftover `.claude/worktrees/agent-*` worktrees created by subagents (`git worktree remove -f -f`).
- **The primary checkout** `/Users/saqlainmomin/dpdpa-gap-tool` is on the stale branch `codex/p5-9a-validation-harness` and holds untracked scratch files. Do not switch its branch or delete anything in it without asking.
- **Codex dispatch** (Codex can't write `.git`; the orchestrator commits the contract tests first and commits Codex's work afterwards):
  ```bash
  codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh -s workspace-write -c 'plugins."compound-engineering@compound-engineering-plugin".enabled=false' -C <worktree> "<prompt>" < /dev/null
  ```
  Its sandbox has no network, so the orchestrator runs live smokes.
- **Merging.** Saqlain merges, unless he explicitly asks you to merge a specific PR. In that case, check that it's `MERGEABLE` and CI is green first.

## Verification
Every change ships with a check you run yourself.
- **(A) and (B):** the contract tests pass unedited, the full suite is green, CI is green, and the smoke passes:
  - (A): render the card and queue for a v2 fixture run. The fallback label, the divergence acknowledgement and closed-set citations must be visible.
  - (B): a PDF text read-back with Devanagari and ₹, DOCX and XLSX that open, and an offline Workpaper.
- **(C):** the harness completes, and the aggregate metrics are recorded with the run path. No answer-key content may enter the orchestrator's context.
- **(D):** the converter round-trips the CSV. The judge then records `criteria_source: "approved"` for the DPDPA requirements in a fixture smoke.

## Pending on Saqlain (don't block on these)
- Export `dpdpa-criteria-v1.csv`, which unblocks (D).
- Decide how `v2_missing_pass` should behave at P6-5.
- Approve the harness cost before the full Stage C run.
- Re-add a `main`-only branch ruleset.
- Review the ISO clause titles, which gates P5-7.
- Track 4 security, before any real client data.

## Report back
Append a `## Results` section to this file. Cover:
- PR links and the merge order, with any conflict notes
- smoke numbers
- decisions made
- anything that still needs Saqlain

Also update `tasks/todo.md` and the auto-memory project status.

## Results

Session of 2026-09-28. Three PRs are open: (A) P6-7a, (B) P6-8 B1 and (D) P6-2b. Saqlain handed over the criteria CSV mid-session, which unblocked (D). (C) Stage C is prepared and cost-approved, but the environment's permission classifier blocked the live run, so Saqlain has to start it.

Workflow for each track:
- A cloud Opus designer wrote the handoff and contract tests. The exception is P6-2b, where the orchestrator designed it and a local Sonnet agent wrote the tests.
- Codex (`gpt-5.6-luna`, xhigh) implemented.
- A cloud Sonnet reviewer checked it adversarially.
- The orchestrator ran the smoke.

### PRs and merge order
1. **[#78](https://github.com/saqlainmmomin/Cyber/pull/78): P6-7a.** The requirement card, the divergence acknowledgement, the evidence span viewer and the review queue. This PR also commits this kickoff file.
2. **[#79](https://github.com/saqlainmmomin/Cyber/pull/79): P6-2b.** The DPDPA criteria converter. It attaches 150 approved criteria and bumps the pack to `2023+criteria-v1`.
3. **[#80](https://github.com/saqlainmmomin/Cyber/pull/80): P6-8 B1.** Board report v2 (WeasyPrint with Noto, Devanagari and ₹) and the standalone Workpaper.

**Conflict notes.** A trial merge of all three (#78 → #79 → #80) was run and then thrown away:
- The text conflicts are in the stale-guard exclude lists and `tasks/todo.md`: `test_p6_3a_grounding.py`, `test_p6_4_cap_upload_limit.py`, `test_p6_4_whats_missing.py`, `test_p6_nist_csf2_alignment.py` and `test_p6_6_report_foundations.py`. Resolve by keeping both sides.
  - For list-closing lines (`"],`), join the lists.
  - In `test_p6_4_whats_missing.py`, define both `p6_8_b1` and `p6_2b_app_files`, and pass `*p6_7a, *p6_8_b1` into the same `_git(...)` calls.
- With the conflicts resolved, the combined suite gave 1112 passed. The only failures were the three PRs' own "only my files" guards, which is expected in a combined diff and not the case after sequential merges.
- **One semantic conflict was found and fixed on #78:** P6-7a scenarios 1 and 12 assumed DPDPA had no criteria. They now pin the fallback explicitly and pass with and without #79.
- After each merge, merge `origin/main` into the next branch, resolve as above, and re-run the suite. Never rebase. The orchestrator can do these merges on request.
- **No migrations anywhere.**

### Smoke numbers
- **(A) P6-7a.** Rendered from real v2 fixture runs (a copy of the P6-4 flag-on smoke DB; no new spend):
  - DPDPA: 41 cards. DPDPA+ISO: 134 cards. Every card carries the fallback label (those runs predate P6-2b).
  - 194 claim links, 0 outside the verified set.
  - The span viewer returns 200 with `<mark>`. The queue renders 41 items in 22 groups. No confidence number anywhere.
  - Neither run produced a divergence, so the acknowledgement relies on contract scenario 6.
  - Review: one should-fix (a double context load passed the wrong object), now fixed.
  - Full suite 1072 passed. CI green before the scenario 1/12 fix; re-running now.
- **(B) P6-8 B1.**
  - DPDPA+ISO PDF: 13 pages, 42 KB.
  - The Title metadata round-trips the exact Devanagari name. The ₹ text reads back exactly, with 0 `?` and 0 `Rs.`. Every glyph comes from the Noto fonts. The cover PNG was inspected, and the conjuncts are correct.
  - The Workpaper has no external references, one inline `<style>` and all entries present.
  - Review: no blocking or should-fix findings.
  - Full suite 1072 passed. In CI, the ubuntu "Renderer smoke" step passed.
- **(D) P6-2b.**
  - `--check` passes, and the 150 criteria round-trip the signed CSV verbatim (the reviewer found 0 mismatches).
  - Live v2 DPDPA smoke:
    - `criteria_source` approved 41/41, with criterion IDs equal to the signed set
    - 2 calls, both `stop`/`ok`, with 13.8k input and 7.7k output tokens
    - 0 dropped IDs, 0 `criteria_incomplete`
  - Full suite 1089 passed. CI green.
- **(C) Stage C.** The harness agent estimated about $0.70–$1.00 for 4 companies × 3 runs, around 35 minutes in parallel. #76 has roughly zero token impact on these packs, because every rendered document is under 400 words. c4 is new, so this is the first 4-company baseline.
  - Saqlain approved the run, but the permission classifier denied the live launch. No calls were made and nothing was spent.

### Decisions made this session
- **P6-7a:** D-P6-7-A..M (see its handoff).
  - The "add to RFI" button is deferred to P6-7b.
  - The acknowledgement is an append-only audit event.
  - The queue risk mirrors the judge table.
- **P6-8:** D-P6-8-A..L.
  - fpdf2 and v2 run side by side as separate report types.
  - WeasyPrint is pinned to 70.0, with the fonts vendored and hash-pinned.
  - The golden is a normalised JSON document, not PDF bytes.
  - B2 (DOCX and XLSX) gets its own PR.
- **P6-2b** (orchestrator): D-P6-2b-A..G.
  - `FrameworkDefinition.pack_version` is `version` plus `criteria_version`.
  - `claims.py` staleness uses `pack_version` too. The designer left this out of scope; without it, every DPDPA claim set would read as stale forever.
- **Saqlain's answers:**
  - Run Stage C 4-way parallel.
  - The P6-5 A/B runs `v2_missing_pass` both off and on.
  - He approved the WeasyPrint and font downloads.

### Still needs Saqlain
- **Merge #78 → #79 → #80** in that order.
- **#79 disclosed guard change:** the orchestrator widened #79's own scope-guard allowed set to the 10 stale-guard and expectation test files it had to update. The reviewer flagged the process; please confirm.
- **Run Stage C yourself** (the classifier blocks it for agents), from `/Users/saqlainmomin/dpdpa-gap-tool-stagec`:
  ```bash
  cd /Users/saqlainmomin/dpdpa-gap-tool-stagec && set -a && source .env && set +a && OUT=~/cyberassess-runs/2026-09-28-stage-c-baseline-v1-rerun && for c in c1-app-startup c2-b2b-saas c3-certified-fortress c4-healthsaas; do .venv/bin/python -m scripts.validation.run_company $c --runs 3 --llm live --out "$OUT" > "$OUT/$c.log" 2>&1 & done; wait && .venv/bin/python -m scripts.validation.score "$OUT"/*/run-* && .venv/bin/python -m scripts.validation.report "$OUT" --baseline
  ```
  Alternatively, add a permission rule and ask the orchestrator to retry. A harness agent then records the aggregate metrics.
- **P6-5** starts after the baseline exists and #79 merges, so that v2 DPDPA runs on approved criteria. Watch DPDPA judge output against the 8,192-token ceiling: a full 15-requirement batch is estimated at about 6.4k tokens.
- **P6-8 open questions**, with defaults in its handoff:
  - issued-PDF marking (default: no)
  - when the fpdf2 report retires
  - penalty exposure (moves to P6-9)
  - the `_framework_label` "INDIA DPDPA" bug (a small separate PR)
- **P6-7 open questions:**
  - P6-7b timing
  - whether the acknowledgement note is optional or required
  - acknowledgement scope
  - the in-period chip
- **Carried over:** a `main` ruleset, the ISO clause titles (P5-7), and Track 4.
- **Worktrees left in place:**
  - `dpdpa-gap-tool-p6-2b`, `-p6-7`, `-p6-8`: remove after merge.
  - `dpdpa-gap-tool-stagec`: for the Stage C run.
