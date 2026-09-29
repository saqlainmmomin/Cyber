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
5. Smoke, as below. Then append `## Results

Orchestrated 2026-09-29. Codex (`gpt-5.6-luna`, xhigh) implemented each track against the unedited contract tests. A Sonnet subagent reviewed each one adversarially, and the orchestrator ran the smoke and opened the PR. No Opus was used. Each handoff's `## Results` has the detail.

### PRs (all open against `main`, CI pending at time of writing)

| Track | PR | Branch | Full suite (committed) | Review |
|---|---|---|---|---|
| P6-7b add-to-RFI | [#84](https://github.com/saqlainmmomin/Cyber/pull/84) | `claude/p6-7b-impl` | 1130 passed, 10 skipped | 7/7 `[AR]` pass; 2 NITs |
| P6-5a quarantine + pack | [#85](https://github.com/saqlainmmomin/Cyber/pull/85) | `claude/p6-5a-quarantine` | 1138 passed, 10 skipped | 8/8 pass; 2 NITs |
| P6-9 SoA / roadmap / prior period | [#86](https://github.com/saqlainmmomin/Cyber/pull/86) | `claude/p6-9-impl` | 1135 passed, 10 skipped | 10/10 pass; 1 dead helper removed |
| P6-5b ab_compare | [#87](https://github.com/saqlainmmomin/Cyber/pull/87) | `claude/p6-5b-ab-compare` | 1148 passed, 9 skipped | 2 BLOCKING + 1 should-fix, fixed by Codex, re-review resolved |

**Merge order (suggested):** #85 → #87 → #86 → #84. Any order works; the rules are:
- A trial merge of all four onto `main` shows every later PR conflicting in shared guard files: `test_p6_2b_dpdpa_criteria.py`, `test_p6_4_*`, `test_p6_7_requirement_card.py` and `test_p6_8_board_report_v2.py`.
- #87 also conflicts in the P6-5 handoff, which #85 adds with different Results.
- After each merge, merge `origin/main` into the next branch and keep both sides; never rebase or force-push. The orchestrator can do this on request.

### Deviations from this kickoff
- **P6-5 is on two branches cut from `origin/main`, not one branch from the design.** The design commit carries both suites, so a P6-5a PR with the ab_compare suite would be red. The design commit was cherry-picked into both branches:
  - P6-5a drops `test_p6_5_ab_compare.py`.
  - P6-5b drops the injection pack and its suite.
  - The guard edits and the handoff text are identical on both.
- **The `suspected_instruction` queue chip is not in P6-7b.** The flag only exists after P6-5a, and P6-7b's own file-set guard forbids `review_queue.py`. It becomes a small follow-up PR after #85 merges.

### Kickoff issues 1-6
1. The baseline directory is fixed to `…-rerun-2` in all three places of the P6-5 handoff (both branches), with the "complete; aggregates in #83" wording.
2. The sibling-folder trap is pinned by a test: an extra run gives `run_count_mismatch` and `holds: null`, and the smoke confirmed it on a real copy.
3. Provenance: the real baseline copy (no `settings`, `dirty: true`, 7 `--_child` runs) declared `:pipeline=v1` is comparable with 0 defects, and a fixture test covers it.
4. The stale base is noted in the three handoffs, and `origin/main` is merged into P6-9 and P6-7b.
5. The guard conflicts were resolved by keeping both sides. Three further stale guards were found once the work was committed, and each got exactly-scoped excludes:
   - P6-7b: `test_p6_nist_csf2_alignment.py`
   - P6-5b: `test_p6_2b` `P6_5_FILES` gained the extra test file
6. The v1 malformed-JSON crash did not arise here (no live runs).

### Numbers for P6-5
The v1 baseline, re-scored with the P6-5b scorer (Decision 1 literal: IE and partial-on-non-compliant count as flagged), declared `:pipeline=v1`:
- catch **131/141 = 92.9%** (92.2% under the old threshold)
- decoy FP **21/36 = 58.3%**, clean FP **59/96 = 61.5%**
- IE rate 1.1%, stability 0.816 over 521 requirements
- by `criteria_source`: approved catch 90.8%, fallback 96.3%
- $0.95 for the 12 runs at $0.20/$0.80 per 1M tokens

These are the numbers the v2 arms must meet (D-P6-E, pooled; ties pass).

### Incident
While checking the P6-5a live script's no-key guard, the orchestrator ran `env -u OPENROUTER_KEY scripts/injection_pack_live.py --runs 1`. `Settings` still read the key from the worktree `.env`, so the script ran live against OpenRouter for about 4 minutes before it was killed. No output was written; expected spend is cents. The guard was then verified with `OPENROUTER_KEY=""`, and a feedback memory was saved.

### Still needs Saqlain
- Merge #85, #87, #86 and #84 (or ask the orchestrator to merge a specific one once CI is green); merge or close this branch; close draft #82 with a note pointing at the per-task branches.
- After #85 and #87: run the P6-5 protocol (mock preflight → c1 pilot → approve the spend estimate → both v2 arms → `ab_compare`), then the flip decision (#5).
- Carried over: the ISO descriptions review (P6-2c), the c4 NIST answers skim, a `main`-only ruleset, the ISO clause titles (P5-7), and Track 4 security.
