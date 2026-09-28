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
