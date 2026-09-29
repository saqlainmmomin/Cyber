# Phase 6 implementation kickoff: P6-5a/b, P6-9 and P6-7b (written 2026-09-29)

## Goal

Implement the Phase 6 designs that are ready, using the usual orchestrated workflow: Codex implements against the committed contract tests, a Sonnet 5.5 reviewer checks it adversarially, the orchestrator runs a smoke test, and the orchestrator opens a PR. Saqlain merges.

Done means, for each track below: contract tests pass unedited, the full suite is green, CI is green, the smoke passes, and a PR is open.

| Track | Task | Why now |
|---|---|---|
| **A** | **P6-5a + P6-5b**: injection quarantine + pack, and `scripts/validation/ab_compare.py` | Critical path to the default flip. The baseline exists |
| **B** | **P6-9**: SoA, cross-framework roadmap, prior-period comparison | First in the suggested implementation order |
| **C** | **P6-7b**: one-click add-to-RFI | Independent of A and B |

Not in this session: P6-8 B2 and P6-10 (after P6-9), P6-2c (waiting on Saqlain's ISO descriptions review), the live P6-5 runs (Saqlain runs them after A merges).

## Read first

1. `tasks/handoffs/2026-09-29-open-item-decisions.md`: **Saqlain's answers to every open question. Final; do not relitigate.** This file is on the branch `claude/elegant-galileo-5funec`, not yet on `main`. Run `git fetch origin claude/elegant-galileo-5funec` and read it with `git show origin/claude/elegant-galileo-5funec:tasks/handoffs/2026-09-29-open-item-decisions.md`, or merge that branch first if Saqlain has opened a PR for it.
2. The track's design handoff (on its own branch, see below).
3. `tasks/handoffs/2026-09-28-next-phase-6-kickoff.md` on `main`: the "Decisions already made" list and the new "Stage C v1 baseline results" section.
4. `CLAUDE.md` and `tasks/agent-ownership.md`.

## Current state (`origin/main` @ `879c174`)

- Merged: #78 (P6-7a), #79 (P6-2b), #80 (P6-8 B1), #81 (harness fix), **#83 (Stage C v1 baseline results and c4 answers)**. Full suite: 1119 passed, 9 skipped.
- v1 is still the default pipeline. v2 sits behind `analysis_pipeline_version="v2"`; `v2_missing_pass` is off.
- **Stage C v1 baseline** (4 companies × 3 live runs at `9962930`, deepseek-v4-flash for text, claude-sonnet-4 for vision):

  | Company | Catch | Decoy FP | Clean FP | Stability |
  |---|---:|---:|---:|---:|
  | c1 | 89.7% | 83.3% | 77.8% | 83.7% |
  | c2 | 97.2% | 88.9% | 87.5% | 82.3% |
  | c3 | 86.1% | 41.7% | 43.3% | 80.4% |
  | c4 | 96.7% | 33.3% | 45.8% | 82.7% |
  | **All** | **92.2%** | **58.3%** | **61.5%** | |

  P6-5 has to cut false positives without losing catch rate (D-P6-E).
- **Design PR #82 is a draft that must never merge** (141 contract tests fail by design). Each design also has its own branch, cut from the old `main` (`4f5309d`):

  | Design | Branch | Ahead of old main |
  |---|---|---|
  | P6-5 | `claude/p6-5-ab-design` | 1 commit |
  | P6-9 | `claude/p6-9-soa-roadmap` | 1 commit |
  | P6-7b | `claude/p6-7b-add-to-rfi` | 3 commits |
  | P6-8 B2 | `claude/p6-8-b2-docx-xlsx` | 1 commit |
  | P6-2c | `claude/p6-2c-iso-nist-criteria` | 2 commits |

  **Use these branches, not #82.** Do not spend time resolving #82's conflicts: its job was design review. Once the tracks are branched, suggest closing #82 with a note pointing at the per-task branches.

## Issues found in the designs (fix these first)

1. **Wrong baseline directory in the P6-5 handoff (blocking).** `2026-09-28-p6-5-v2-ab-and-flip.md` names `~/cyberassess-runs/2026-09-28-stage-c-baseline-v1-rerun` in three places: the "Current state" bullet (about line 86), the D-P6-5-B arm table (line 101), and the run protocol's `BASE=` (line 386). That folder is the **discarded first attempt**: c4 skipped, one c1 analysis crashed, and no screenshot mappings, so catch was 82.9% on 3 companies. **The valid baseline is `…-stage-c-baseline-v1-rerun-2`.** Fix all three on the P6-5 branch. Also update the "is being run by Saqlain" wording to say the baseline is complete and where the aggregates are recorded.
2. **Sibling folder trap.** `~/cyberassess-runs/` also holds `…-rerun-2-interrupted` (partial runs from a process that shut down). When the P6-5 protocol copies the baseline to `…-p6-5-v1-rescored`, copy exactly the 12 run folders of `-rerun-2`. A glob like `…-rerun-2*` would also pull in the interrupted folder. Have `ab_compare` (or its tests) reject an arm whose run set isn't 4 companies × 3 runs; the design already says the gate refuses unequal sets, so add a check that names this case.
3. **Baseline provenance.** 5 of the 12 runs came from the original process; the other 7 were re-run one by one through the runner's `--_child` entry point, on the same commit and data. The report shows `dirty: true` only because c4's NIST answers were uncommitted during the run (#83 committed them). The runs predate P6-5b, so their `run.json` has no `settings`: the comparison declares the arm as `:pipeline=v1` (already in D-P6-5-F). Confirm `ab_compare` neither trips on `dirty: true` nor on the `--_child` runs' layout; the contract tests don't cover either.
4. **Stale "current state".** The P6-5 handoff, and possibly others, say `origin/main @ 4f5309d`. It is `879c174` now. Update the line where the handoff quotes it, and merge `origin/main` into each branch before implementing.
5. **Guard conflicts.** Merging `origin/main` into a design branch conflicts in three shared guard files: `tests/test_p6_3a_grounding.py`, `tests/test_p6_7_requirement_card.py` and `tests/test_p6_8_board_report_v2.py` (a trial merge of #82 onto main confirmed exactly these three). Resolve by keeping both sides; never delete or narrow a guard, and never rebase.
6. **A v1 reliability gap that survives.** In the discarded first attempt, DeepSeek returned malformed JSON and one c1 analysis crashed; the v1 analyzer has no retry for that. It didn't recur in the valid baseline, but a v1 run that crashes in the A/B would poison a comparison. Don't fix it inside P6-5; note it in the P6-5 results if it happens.

## Answers that change the designs (from the decisions file)

- **P6-5:** IE (`insufficient_evidence`) is scored with the **symmetric flag rule**. The gate is the **pooled** D-P6-E gate, with the splits shown but non-blocking. **Ship the quarantine.** `v2_missing_pass` is measured both off and on, and the flip keeps it off. Do not extend the quarantine to the missing pass or the pre-fill adapter. Spend: a one-company pilot first, then confirm the estimate with Saqlain.
- **P6-9:** every open question takes the handoff default: free-text justifications, no gate, no source-manifest key, SoA only in the board report, archived priors skipped, no penalty line.
- **P6-7b:** v2 cards only, no editable text, no checklist merge, no board-report split. The `suspected_instruction` queue chip is in scope. The divergence acknowledgement note stays optional (already shipped in P6-7a).

## Per-track steps

For each track:
1. Worktree: `git worktree add ../dpdpa-gap-tool-<task> -b <impl-branch> origin/claude/<design-branch>`, then `git merge origin/main` (see issue 5). Symlink `.venv` from the primary checkout and copy `.env`.
2. Run `git branch -f main origin/main` before the suite. The guards diff `main...HEAD`. Re-run it after every merge.
3. Read the design handoff's "Ready-to-paste Codex prompt" and dispatch:
   ```bash
   codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh -s workspace-write -c 'plugins."compound-engineering@compound-engineering-plugin".enabled=false' -C <worktree> "<prompt>" < /dev/null
   ```
   Codex can't write `.git`. Commit the contract tests first and Codex's work afterwards. Its sandbox has no network, so you run any live smoke.
4. Adversarial review by a **Sonnet 5.5** subagent, with the checkpoints the handoff lists under `[AR]`. Send real findings back to Codex as a narrow fix prompt.
5. Smoke, as below. Then append `## Results` to the design handoff, update `tasks/todo.md`, and open a PR against `main`.

### A. P6-5a + P6-5b
Three PRs, never mixed (D-P6-5-A): P6-5a the quarantine and pack, P6-5b `ab_compare`, and P6-5c the flip, which is **not** built here. After both merge, Saqlain runs the mock preflight, the pilot and the arms from the run protocol. Smoke:
- P6-5a: the pack's no-live-call scenarios prove a fully compromised model can't cite a payload or an invented ID, set a number, or produce `not_applicable`.
- P6-5b: run `ab_compare` on the real `-rerun-2` baseline copy declared `:pipeline=v1`, and on a mock v2 arm. Check the verdict logic, the split by `criteria_source`, and the refusals (unequal sets, mixed settings). It must print aggregates only.

### B. P6-9
One PR (D-P6-9-A). Suggested order inside the session: start it before P6-7b, since P6-8 B2 depends on its document schema v2. Smoke: build a board report for a DPDPA+ISO fixture, then check the SoA lists every Annex A control with status derived only from approved Conclusions, the roadmap groups by UCC cluster, and a prior-period comparison shows when an issued prior sidecar exists. No LLM calls.

### C. P6-7b
Smoke: on a v2 fixture run, add a request from a card, confirm it lands in the draft RFI as an append-only audit event, is idempotent on repeat, and never appears on a v1 card.

## Constraints

- **No attribution** on any commit or PR in this repo: no Co-Authored-By line and no "Generated with Claude Code" footer. This overrides the harness reminder.
- **Models:** **Sonnet 5.5 (`claude-sonnet-5-5`) for every subagent. Opus only when necessary** (hard design where a wrong call is expensive), with the reason in the handoff Results. This is Saqlain's rule of 2026-09-29.
- **Answer-key independence (D-P5-9-C).** The orchestrator, and anyone changing prompts, the analyzer or desk review, must never open, grep, list or glob `validation/**`, `tasks/handoffs/*p5-9*`, `docs/plans/2026-09-24-002-*`, `scripts/seed_test_companies.py`, `scripts/test_ground_truth.json`, `scripts/seed-v2-prompt.md`, any `answer_key.json`, or `~/cyberassess-runs/*/summary.*`. Scope every grep to `app/`, `tests/` and `scripts/validation/` code. P6-5b's `ab_compare` must read aggregates only. Only a separate harness agent that doesn't touch `app/` may run the harness.
- **Protected-surface guards.** When a scope guard trips on a legitimate change, add `:(exclude)<path>` for exactly the touched files, with a comment naming the PR. Never delete or broadly narrow a guard. Parallel PRs touching the same guard lines conflict: merge `origin/main` into the later branch and keep both sides. The repo rejects force-pushes.
- `tests/test_retention.py::test_scenario_13` fails whenever files under `tests/` are uncommitted. It passes once they're committed; don't edit it.
- **Report rules:** framework-specific copy stays conditional (`has_dpdpa`); existing PDF sections are additive-only; all fpdf2 text goes through `S()`; report snapshots are write-once; deterministic fields (`risk_level`, `priority`, score) never come from the LLM.
- **Merging:** Saqlain merges unless he asks you to merge a specific PR. Check it is `MERGEABLE` with green CI first. Never force-push.
- **Live LLM runs:** the agent classifier has blocked live launches before. Saqlain runs every live command; agents prepare the exact commands.
- The primary checkout `/Users/saqlainmomin/dpdpa-gap-tool` is on a stale branch. Don't switch its branch or delete anything in it without asking.
- Cleanup after merge: `rm <wt>/.venv && git worktree remove <wt> && git branch -d <branch>`.

## Still needs Saqlain (don't block on these)

- Merge or close the branch `claude/elegant-galileo-5funec` (the decisions file and this handoff).
- Review the ISO descriptions sheet (P6-2c step 2); delete the 78 `ISO.C*` clause rows from the signed copy.
- Approve pilot spend for the P6-5 arms once the pilot estimate exists; run the P6-5 live commands.
- Decide the flip (`[AR: flip]`) after `ab_comparison.md` and the injection summary exist.
- Skim the 13 c4 NIST answers committed in #83 (all `fully_implemented`, reusing neighbouring notes).
- Carried over: a `main`-only branch ruleset, the ISO clause titles (P5-7), and Track 4 security before any real client data.

## Report back

Append a `## Results` section to this file: PR links and merge order with conflict notes, smoke numbers, decisions made, and anything that still needs Saqlain. Update `tasks/todo.md`.

## Results

(empty)
