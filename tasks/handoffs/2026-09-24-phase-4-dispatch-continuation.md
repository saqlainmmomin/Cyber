# Phase 4 dispatch continuation: execute the four task handoffs

**Read this first.** This is a continuation handoff, not a new task — the prior session ran low on session limits mid-Phase-4, not because of any blocker. All the design work (step 1 of the process below) is already done. Your job is to run steps 2-9: dispatch to Codex, review, merge. This runs on the local machine (`/Users/saqlainmomin/dpdpa-gap-tool`) — it needs local filesystem access, `git worktree`, and the local `codex` CLI, exactly like Phases 1-3 did. Do not run this from a cloud/remote session that lacks those.

## Goal

Get all four Phase 4 tasks (P4-1 AWS evidence adapter, P4-2 longitudinal demo, P4-3 performance benchmarks, P4-4 retention/purge) implemented by Codex, independently reviewed, and merged to `main`. Definition of done: four PRs merged, full test suite green on `main`, `tasks/todo.md` / `CLAUDE.md` / project auto-memory all updated to reflect Phase 4 complete.

## Current state

- `main` is at commit `53a12af` (Phase 1-3 complete, PRs #16-#33; baseline **502 tests pass** — re-verify yourself with `.venv/bin/pytest -q`, don't trust this number blindly).
- Four detailed implementation handoffs were just written (each by an isolated Opus subagent that read the plan, the decisions log, the ownership doc, and every prior Phase 2/3 handoff's Results section, then grounded its design against the actual current code) and committed in `53a12af`:
  - `tasks/handoffs/2026-09-24-p4-1-aws-evidence-adapter.md` — 18 decisions (D-P4-1-A through R). Designs the exact least-privilege IAM policy and AssumeRole + external-ID flow for pulling AWS Config rule evaluations and Security Hub findings into Evidence rows. **`boto3` is not installed yet** — run `.venv/bin/pip install boto3==1.43.101` in the P4-1 worktree before dispatching Codex (the handoff pins this version; Codex's sandbox has had no network access in prior phases, so this must happen before dispatch, not rely on Codex installing it).
  - `tasks/handoffs/2026-09-24-p4-2-longitudinal-demo.md` — extends `scripts/seed_test_companies.py` with 2 synthetic clients. The writing agent found the evidence-reuse age/scope-warning mechanism **does not exist in the codebase yet** (the plan assumed it did) — the handoff specs a small new module for it. Also note: **Client A has one engagement, not two** — evidence can only be mapped within a single engagement, so the "6 months later" reassessment is a second assessment inside the same engagement, and "multi-engagement" is demonstrated across the two clients instead.
  - `tasks/handoffs/2026-09-24-p4-3-performance-benchmarks.md` — seeds 5/10/30/500/3000 (clients/engagements/assessments/evidence-versions/conclusion-revisions) and times 4 operations against a 2s SQLite threshold. The writing agent found **evidence search across an engagement does not exist as a product feature** — the handoff benchmarks a reference query defined only in the benchmark script instead, and flags this as an open question for a future task. The benchmark test suite is **opt-in** via `CYBERASSESS_RUN_BENCHMARKS=1` so it doesn't slow down the normal `pytest -q` run.
  - `tasks/handoffs/2026-09-24-p4-4-retention-purge.md` — the destructive one. 21 decisions (D-P4-4-A through U). No schema migration needed (archive date is read from an `engagement.archived` audit event, not a new column). Purge order is DB-rows-then-blobs, with a two-phase completion mechanism (a `scripts/complete_purges.py` sweep) so a crash between the two steps can't leave an orphaned blob or a dangling DB reference. **Requires a second, more skeptical adversarial review pass beyond the standard one** — this is explicitly called out in the ownership doc as the most destructive code path in the plan.
- The general dispatch process (worktree setup, Codex invocation, commit/review/merge mechanics) is documented in `tasks/handoffs/2026-09-24-phase-4-kickoff.md`, steps 2 through 9. That file also has task-specific starting notes for all four tasks under "Task-specific starting notes" — read those too, they're short.
- Each of the four P4-* handoffs has its own "file overlap" / "files this task must not change" section that pre-declares exactly which files it might share with another Phase 4 task (typically `app/main.py` router registration and `tasks/todo.md`; P4-3/P4-1/P4-4 also flag conditional Alembic-revision-head overlap if more than one adds a migration). **Read each handoff's own section for the authoritative list — do not re-derive it from scratch.**

## Key files

- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/handoffs/2026-09-24-phase-4-kickoff.md` — the process document (steps 2-9 are what you execute; step 1, writing the handoffs, is already done).
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/handoffs/2026-09-24-p4-1-aws-evidence-adapter.md` — P4-1 spec.
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/handoffs/2026-09-24-p4-2-longitudinal-demo.md` — P4-2 spec.
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/handoffs/2026-09-24-p4-3-performance-benchmarks.md` — P4-3 spec.
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/handoffs/2026-09-24-p4-4-retention-purge.md` — P4-4 spec.
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/agent-ownership.md` — Phase 4 ownership table, criteria for what needs a Claude-designed spec vs. a Codex-standalone task.
- `/Users/saqlainmomin/dpdpa-gap-tool/CLAUDE.md` — "Current phase" line to update after merges.
- `/Users/saqlainmomin/dpdpa-gap-tool/tasks/todo.md` — task checklist to update after each merge.
- `~/.claude/projects/-Users-saqlainmomin-dpdpa-gap-tool/memory/project_status.md` and `MEMORY.md` — this project's auto-memory; update after merges (these are the same project's memory files this session should already have access to; if not, this path is on the host filesystem, not in the git repo).

## Constraints

- **Model:** dispatch Codex with `gpt-5.6-luna` at `xhigh` reasoning effort. Do **not** use `gpt-5.6-sol` — it burned through the account's Codex usage quota twice during Phase 3 at medium effort.
  ```
  codex exec -m gpt-5.6-luna -c model_reasoning_effort="xhigh" -s workspace-write \
    -C <worktree-path> --skip-git-repo-check "$(cat <prompt-file>)"
  ```
- **One worktree per task, never shared.** `git worktree add ../dpdpa-gap-tool-p4-N -b codex/p4-N-<slug> main`, symlink `.venv`, copy `.env`. Verify the baseline suite passes in each fresh worktree before dispatching (expect one known pre-existing teardown error in `tests/test_workpaper.py::test_smoke_full_assessment_traceability` — documented in every prior phase's handoffs, not a regression).
- **Codex cannot commit.** Its sandbox refuses `.git` writes (`Unable to create '.git/index.lock': Operation not permitted`). This is expected, not a bug — commit on Codex's behalf after verifying its diff.
- **No Claude attribution anywhere in Phase 4 commits or PRs** — no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" footer, in any commit message or PR body for this phase's work. Saqlain asked for this to stop after PR #31 and it applies to every commit/PR from Phase 4 onward. (This constraint is specific to work Codex produces under your supervision in this phase — it does not apply to this handoff file itself or other meta/process documents.)
- **Verify, don't trust.** Before committing Codex's work: `git diff --stat` against every file the handoff said not to touch (should be empty), and re-run `.venv/bin/pytest -q` yourself independently — don't trust a reported pass count.
- **If Codex hits a usage-quota error** partway through (distinct from the sandbox commit issue — look for `ERROR: You've hit your usage limit`), check whether implementation + tests already landed before the cutoff (they usually have, the quota tends to hit at the documentation/commit step). If so, finish the mechanical remainder yourself and write the `## Results` section from your own direct diff inspection, explicitly saying you wrote it (don't fabricate Codex's voice).
- **Independent Sonnet adversarial review required before any PR opens**, briefed to: read the handoff and its Results, read the actual diff, verify every stated invariant by tracing the code, run the test suite independently, and actively try to break it. Tell it explicitly what NOT to flag (pre-existing style, deferred features, missing auth by design) so it doesn't waste findings on noise.
- **P4-4 gets a second, more skeptical review pass** beyond the standard gate — do not settle for one clean review on that task alone.
- **Only after review comes back clean:** push and open the PR (`gh pr create`). No attribution footer in the PR body. State in the PR description exactly what was verified (test counts, invariants traced, protected-file zero-diffs confirmed) — match the detail level of PRs #30-#33, not a one-line "implements P4-N".
- **Rebase coordination:** if two tasks land PRs concurrently, merge one, then rebase the other onto the new `main` before merging. Conflicts should only occur in each handoff's pre-declared shared files — if a handoff didn't anticipate a conflict, that's a gap in the handoff to note, not a reason to skip the coordination step.
- **Don't relitigate design decisions** already numbered in the four handoffs (`D-P4-1-*`, `D-P4-2-*`, `D-P4-3-*`, `D-P4-4-*`). If the actual code forces a deviation from a decision, stop and report it in that handoff's `## Results` section rather than picking an alternative yourself.

## Verification

For each task, before considering it done:
1. `git diff --stat main` in the task's worktree matches the handoff's declared file scope (plus any pre-declared shared files).
2. `.venv/bin/pytest -q` passes at the same count as baseline plus the task's new tests (re-run yourself, don't trust Codex's report).
3. Task-specific checks from each handoff's own "Test scenarios" / "Done criteria" section (e.g. P4-1's boto3 mocked-response tests and documented least-privilege policy; P4-3's `CYBERASSESS_RUN_BENCHMARKS=1` run showing all four operations under 2s or a documented threshold-miss attribution; P4-4's archive/purge/crash-safety scenarios).
4. Independent Sonnet review comes back clean (or findings are addressed and re-reviewed).
5. After all four are merged: full suite green on `main`, `tasks/todo.md` Phase 4 section fully checked off, `CLAUDE.md` "Current phase" line updated, project auto-memory (`project_status.md`, `MEMORY.md`) updated.

## Report back

Append a `## Results` section to **this file** summarizing: which of the four tasks merged (with PR links), any deviations from the handoffs and why, the final full-suite test count, and anything that surprised you (a handoff's claim that didn't hold against the real code, an unanticipated file conflict, etc.).
