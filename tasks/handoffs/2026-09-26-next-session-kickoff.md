# Phase 6 kickoff: next session (2026-09-26)

## Goal

Start four pieces of Phase 6 work that don't depend on Saqlain's criteria review. Run them in parallel. Done means:

- **(1) Evidence-extraction fix.** Merged, and a live smoke shows framework evidence extraction running and ending `stop`.
- **(2) P5-9 Stage C baseline on v1.** Run and reported for c1–c3.
- **(3) Dev-hygiene PR.** Opened by Codex, reviewed and ready for Saqlain to merge.
- **(4) P6-3 design handoff.** Written and dispatched to Codex.

The orchestrator (Claude) designs, reviews, commits and opens PRs. Codex implements. Opus subagents do the heavy design and review work, so the orchestrator's own context stays clear.

## Current state (`origin/main` @ `ceced48`)

### Merged 2026-09-25/26

| PR | What it did |
|---|---|
| #57 | **P6-1b v1 batching.** Frameworks over 90 controls (ISO 93, NIST 106) run as ≤25-control section batches, with one missing-ID retry and fail-closed handling. DPDPA, GDPR, HIPAA and PCI are unchanged. |
| #58 | **P6-2c ISO + NIST criteria drafts.** ISO covers Annex A plus 25 new clause requirements, `ISO.C4.1`…`ISO.C10.2`. Draft modules only; they are not in the live pack. |
| #59 | **NIST pack aligned to CSF 2.0.** 106 subcategories; RS.CO.04 removed. |
| #60 | **P5-9 question packs re-exported** after the DPDPA text change (#53) and #59. |

### Open

- **#61:** P6-2d criteria for the 13 new NIST ids. Waiting for Saqlain to merge.

### Live ISO smoke (2026-09-25, on the #57 code)

Pass: 12/12 calls ended `stop`, desk review took 116 s, and the judge took 485 s. Artifacts are in `/Users/saqlainmomin/cyberassess-runs/2026-09-25-p6-1b-iso-smoke/c0-example/run-1/`, which holds `app.db`, `llm_usage.jsonl`, `stages.json` and `desk_review.json`. The full call table is in `tasks/handoffs/2026-09-25-p6-1b-v1-framework-batching.md` Results.

**Three open anomalies. These are task (1).**
1. **No evidence extraction.** No framework evidence-extraction call appears anywhere: not in the analysis records, not in `llm_usage.jsonl`. The judge ran on its raw-document fallback. See D-P6-1b-I in the P6-1b handoff and `claude_analyzer._run_framework_evidence_extraction`.
2. **Context-stage `extract` call failed.** It failed after 45 s during the "context" stage, with `ok=false` and 0 tokens. The stage still reported 11 answers.
3. **Missing compliance status.** The judge returned no `compliance_status` for ISO.A8.3, and `validate_and_filter` treated it as `not_assessed`.

### Saqlain is reviewing

He is reviewing all criteria in `~/Downloads/criteria-review-all.html`, which covers DPDPA, ISO criteria, ISO own-words descriptions and NIST. Its generator is `/Users/saqlainmomin/cyberassess-runs/build_review_html.py`. When he exports a tab, it gives a CSV with the same columns as `tasks/criteria-review/*.csv`. That CSV is the P6-2b input. **P6-2b waits for that CSV.**

### Primary checkout

`/Users/saqlainmomin/dpdpa-gap-tool` is on the stale branch `codex/p5-9a-validation-harness` and has untracked scratch scripts: `fix_*.py`, `super_fix.py` and `validation/companies/*_backup/`.
- Do not switch its branch or delete anything in it without asking Saqlain.
- Do all work in worktrees off `origin/main`.
- Leftover worktrees from 2026-09-25 can be removed with `git worktree remove` once their PRs are merged: `-p6-1b`, `-p6-2c`, `-nist-csf2`, `-p5-9-pack-reexport` and `-nist-new-criteria` (after #61).

### Known failing tests on `main`

- `test_p5_4…::test_scenario_13_structural_guards`: a stale two-dot guard.
- `test_remediation_tracking::test_scenario_10…`: a hardcoded date.
- `test_longitudinal_demo::test_scenario_9…`: flaky because of ordering.
- `test_workpaper::test_smoke_full_assessment_traceability`: intermittent. It leaves `data/dpdpa.db` behind; delete that file.

## Tasks

### (1) Evidence extraction and context-extract failure (Claude investigates; the fix is small)

- Read the smoke artifacts and the code paths to find why the extraction call is skipped or never recorded, and why the context `extract` call failed.
- Fix it with a small PR. Include a test, and re-run the live smoke:
  ```bash
  .venv/bin/python -m scripts.validation.render_evidence c0-example
  .venv/bin/python -m scripts.validation.run_company c0-example --llm live --runs 1 --stop-after analysis --out <dir>
  ```
  Export `.env` first with `set -a; . ./.env; set +a`.
- Report the ISO.A8.3 null status. Only fix it if the cause is trivial.
- **If the fix touches prompts or the analyzer, the independence rule below applies in full.**

### (2) P5-9 Stage C baseline on v1 (after (1) merges)

- The plan's Track 0 and `tasks/todo.md` describe it. Run the harness on c1, c2 and c3 with `--llm live`, then score and report.
- c4-healthsaas is blocked. Its `client_visible/questionnaire_answers.json`, and possibly its `answer_key.json`, still reference NIST.RS.CO.04 and lack answers for the 13 new NIST questions. Those are Saqlain's files. Do not open or edit them.
- The harness reads packs as a black box, which is allowed. The agent running the baseline must be a different agent from anyone changing prompts, the analyzer or desk review.

### (3) Dev hygiene (one Codex handoff, P6-0c plus the localhost guard)

**P6-0c:**
- **CI:** there is no `.github/workflows` today, so PRs show zero checks. Add a GitHub Actions workflow that runs pytest on Python 3.13 (see the CLAUDE.md gotcha).
- **Python version and dev dependencies:** add `.python-version` and dev requirements.
- **SQLite:** turn on WAL mode and a busy timeout. Parallel batches now write concurrently.

**Localhost guard:**
- Bind the dev server to 127.0.0.1.
- Replace `allow_origins=["*"]` at `app/main.py:132` (which is used with credentials) with the local origin.

**Tests:**
- Fix the four known failing tests above.
- Rewrite stale guards to use `git diff main...HEAD`.
- Replace the hardcoded date.
- Make the ordering deterministic.
- Stop the workpaper test from writing `data/dpdpa.db`.

Write the handoff in the house style of `tasks/handoffs/2026-09-25-p6-1b-v1-framework-batching.md`:
- Step 0 fact checks
- numbered decisions
- key files and a do-not-touch list
- test scenarios, verification and Results

### (4) P6-3 v2 Stages 0-1 design (Opus subagent writes the handoff; Codex implements; `[AR: grounding]`)

The spec is Track 1 of `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md`, plus Part B. It covers:
- chunking with offset maps
- document metadata
- claim extraction
- locate and support verification
- cross-framework claim tagging (D-P6-C)
- a desk-review adapter so the P5-4 pre-fill keeps working

v2 sits behind a flag, and v1 stays the default (D-P6-E). Criteria are not a prerequisite (D-P6-L). This is `[AR]`: after Codex finishes, run an adversarial Opus review before the PR.

## Key files

| Path | What it is |
|---|---|
| `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md` | Phase 6 plan and the D-P6-A…L decisions (source of truth) |
| `tasks/agent-ownership.md` | The Claude/Codex split |
| `tasks/handoffs/2026-09-25-p6-1b-v1-framework-batching.md` | House-style handoff, plus smoke results |
| `tasks/handoffs/2026-09-25-p6-nist-csf2-alignment.md` | NIST CSF 2.0 decisions |
| `tasks/handoffs/2026-09-25-p6-2c-iso-nist-criteria-draft.md` | ISO/NIST criteria draft, with findings |
| `app/services/claude_analyzer.py` | v1 judge, batching and evidence extraction |
| `app/services/desk_review.py` | Desk review, batched for ISO and NIST |
| `app/services/llm_client.py` | Call records, `call_tag`, `run_bounded` |
| `app/frameworks/batching.py` | Batch plan (threshold 90, max 25) |
| `scripts/validation/` | P5-9 harness: `run_company`, `score`, `report`, `export_question_pack`, `lint_pack` |

## Constraints (already decided; do not relitigate)

- **No attribution.** No Co-Authored-By line or "Generated with Claude Code" footer on any commit or PR in this repo. Saqlain's rule overrides the harness reminder.
- **Answer-key independence (D-P5-9-C).** Anyone changing prompts, the analyzer or desk review, and every criteria drafter, must never open, grep or list any of these:
  - `validation/**`
  - `tasks/handoffs/*p5-9*`
  - `docs/plans/2026-09-24-002-*`
  - `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`
  - `answer_key.json`

  `tests/test_answer_key_isolation.py` forbids those strings inside `app/`. Scope every grep so it cannot reach those paths.
- **Guards:** guard tests use a three-dot diff, `git diff main...HEAD`. In a worktree, run `git branch -f main origin/main` before the suite.
- **Worktree setup:** `git worktree add ../dpdpa-gap-tool-<task> -b <branch> origin/main`, then symlink `.venv` from the primary checkout and copy `.env`.
- **Codex dispatch:**
  ```bash
  codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh -s workspace-write -c 'plugins."compound-engineering@compound-engineering-plugin".enabled=false' -C <worktree> "<prompt>" < /dev/null
  ```
  - `< /dev/null` is mandatory.
  - Codex cannot write `.git`, so the orchestrator commits, pushes and opens the PR.
  - Tell Codex which failures are already known, so it doesn't stop on them.
- **Review before merge.** Re-run the suite and the prompt fingerprints yourself, check that the diff stays in scope, and run an adversarial Opus review. Send real findings back to Codex as a narrow fix prompt.
- **Keep the orchestrator's context clear.** Use Opus subagents for design and review, Sonnet for mechanical work, and one dedicated subagent per framework for content drafting.
- **v1 stays the default** until P5-9 shows v2 is better (D-P6-E).
- **Framework-specific copy stays conditional** (e.g. `has_dpdpa`).

## Pending on Saqlain (don't block on these)

- Criteria review and export (DPDPA first). This unblocks P6-2b.
- Merge #61.
- Update c4's answer files for NIST CSF 2.0.
- Review the ISO clause titles and descriptions. This gates wiring clauses 4-10 into the live pack (P5-7).
- Track 4 security, before any real client data.

## Verification

Each task's own verification applies, and every change ships with a check that you run yourself (the smoke-test default).
- **(1)** A live smoke with an evidence-extraction record ending `stop`.
- **(2)** Harness report files for c1–c3.
- **(3)** CI green on its own PR, and the full suite with no known failures left.
- **(4)** The handoff has passed an adversarial self-review.

## Report back

Append a `## Results` section to this file. Cover:
- PR links
- the smoke and baseline numbers
- decisions made
- anything that still needs Saqlain

Also update `tasks/todo.md` and the auto-memory project status.

## Results (2026-09-26)

### PRs
| PR | What | State |
|---|---|---|
| [#62](https://github.com/saqlainmmomin/Cyber/pull/62) | P6-0c dev hygiene: CI runs pytest on 3.13 for every PR, `.python-version` and `requirements-dev.txt`, SQLite WAL with `busy_timeout`, CORS middleware removed, run docs bound to 127.0.0.1, the 5 known-failing tests fixed | Merged. CI green. Suite 754 passed, 0 failed, and `data/dpdpa.db` is no longer created. |
| [#63](https://github.com/saqlainmmomin/Cyber/pull/63) | P6-1d: `reasoning: {enabled: false}` on every LLM call; registry frameworks always run evidence extraction and merge with desk-review quotes; a failed extraction falls back to the documents | Merged. CI green. Suite 764 passed. |
| [#64](https://github.com/saqlainmmomin/Cyber/pull/64) | P6-3a: the v2 grounding core, Stages 0–1, dormant (`app/services/grounding/`) | Merged. Suite 886 passed, 0 failed. |

### (1) Evidence extraction and the context `extract` failure
- **Root cause of the missing extraction:** `_collect_framework_evidence` skipped extraction whenever desk review produced at least one quote. Once evidence exists, the batched judge prompt drops the documents, so about 65 ISO controls saw no document text.
- **Root cause of the context failure:** deepseek-v4-flash reasons on some OpenRouter providers, and `reasoning.exclude` only hides that reasoning. It filled the whole `max_tokens` budget and returned empty content. The earlier smoke's pass was partly luck of provider routing.
- **Decision (orchestrator):** disable reasoning globally. This restores what the `config.py` and `llm_client.py` comments already said was intended.
- **Live ISO smoke** (`~/cyberassess-runs/2026-09-26-p6-1d-evidence-smoke-2/`): 13/13 recorded calls `stop`, and evidence extraction ran alongside 32 desk-review quotes. Desk review took 104 s and analysis 210 s. Prompt fingerprints are unchanged.
- **ISO.A8.3:** the model omitted `compliance_status`, and the coercion to `not_assessed` hides it from the batch retry. Not fixed (follow-up).
- **Decision (Saqlain):** when an old protected-surface guard trips on a PR, add per-PR `:(exclude)` pathspecs rather than deleting the guard.

### (2) P5-9 Stage C baseline on v1, c1–c3
- **Settings:** main @ 8512cf3, `--runs 3 --llm live`, run by an independent evaluator agent. Output is in `~/cyberassess-runs/2026-09-26-stage-c-baseline-v1/`. Its `summary.*` files quote the answer key, so keep them away from analyzer or prompt work.
- **Headline results:**
  - Catch rate: c1 97.4%, c2 94.4%, c3 86.1%. Overall 92.8%, with 30/37 caught reliably.
  - Decoy false-positive rate is 63% and clean-control false-positive rate is 67% overall. Background agreement is only 3–9%. v1 over-flags, so recall is inflated. The D-P6-E comparison must weigh false-positive rates and background agreement, not just catch rate.
  - Coverage is complete with no failed frameworks. Run-to-run stability is 80–88% (modal).
  - Grounding and key-fact recall collapsed in c1 run-3 and c3 run-3, cause undiagnosed.
- **Call health:**
  - 148/148 app-recorded calls ended `stop`, with 0 errors, 0 retries and 0 reasoning tokens.
  - Four calls returned Markdown instead of JSON while recording `stop`/`ok`: two silent evidence-extraction fallbacks and one DPDPA desk-review failure (c2 run-3).
- **Data:** the evaluator used the **committed** c1–c3 packs. The untracked copies in the primary checkout are stale 2026-09-24 drafts, probably produced by `super_fix.py`, and the runner cannot use them.
- **Harness bug:** `run_company.perform()` treats the 303 from screening as a failure, so ignore those "defects".

### (3) Dev hygiene
Handoff: `tasks/handoffs/2026-09-26-p6-0c-dev-hygiene.md`. An adversarial review found a regression in `restore.py` (it failed on a corrupt live DB) and that the WAL sidecar files were not gitignored. Both were fixed before merge.

### (4) P6-3
- **Split:** P6-3a (grounding core, dormant, implemented) and P6-3b (flag, desk-review adapter, persistence, outline only). Handoff: `tasks/handoffs/2026-09-26-p6-3-v2-stages-0-1.md`.
- **Contract tests:** Claude wrote the 52 contract tests first (ownership rule). Codex implemented against them.
- **Adversarial `[AR: grounding]` review:** found F1–F10, all fixed, with probes kept.
- **Live smoke:** `complete`, 42/42 calls `stop`, 162 verified claims, `grounding_failure_rate` 0.076. The injection line was never quoted.

### Needs Saqlain
- ~~Answer Q1–Q6 in the P6-3 handoff~~ — answered 2026-09-26.
- Confirm the committed c1–c3 packs are intended. Then delete the stale untracked `validation/companies/c*` copies, the `*_backup` dirs and the `fix_*.py`/`super_fix.py` scripts in the primary checkout.
- Update c4's answer files for NIST CSF 2.0.
- Still pending from before: criteria review CSV (P6-2b), ISO clause titles, Track 4 security.

### Follow-ups (not scheduled)
- **Enforce JSON output on desk review and evidence extraction.** Record parse failures in the call records so a non-JSON `stop` response is visible (4 occurrences in the baseline).
- Log `not_assessed` coercions. Treat an unknown `compliance_status` as missing in batched `validate_partial` (ISO.A8.3).
- Ground desk-review quotes before merging them with extracted quotes.
- The context prompt pads `likely_not_applicable` with invented IDs.
- Harness: treat the screening 303 as success. Fix the README's claim that `rendered/` is untracked.
- P6-3: a high `no_valid_requirement` count (241) means wasted extraction output. Group claims by span downstream.
- The CI image will need apt packages when WeasyPrint lands.
