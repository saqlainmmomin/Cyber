# Phase 5 kickoff: cleanup & non-DPDPA parity

**Read this first in a fresh session before touching Phase 5.** It is not a task spec — it points you at the plan and the process. Each of P5-1 through P5-8 still needs its own detailed handoff written the way every prior task's was.

## Where the project stands

`main` tip as of 2026-09-24 (commit `377b211`): Phases 1-4 are all complete and merged (PRs #16-#37). Full suite: **550 passed, 9 skipped** — verify yourself with `.venv/bin/pytest -q` before trusting that number.

## The plan

**Read in full first:** `docs/plans/2026-09-24-001-cleanup-and-non-dpdpa-parity-plan.md`. It's the source of truth for this phase — don't re-derive scope from this file. It contains:

- A gap-by-gap verdict on the 9 known gaps (8 from `docs/architecture/data-flow-and-processes.md#gaps`, plus a live-discovered DPDPA-only evidence-checklist gap), judged against the *current* product framing (consultant-operated multi-framework platform), not the old demo-pitch framing that originally tracked them.
- A broader audit that found **the most important thing in this phase**: the "reader migration" (scores/PDF/release gate still reading AI-proposed `GapItem`s instead of consultant-approved Conclusions, contradicting PR-045/PR-052/D3) was named in every handoff from P2-3 through P3-4 and never scheduled by any plan. It's now **P5-2**.
- 5 more untracked correctness bugs (e.g. a framework whose analysis call failed gets reported as a clean "0% Non-Compliant" score).
- Plan-level decisions `D-P5-A` through `D-P5-F` — don't relitigate these; if code forces a deviation, stop and report it in the task's own `## Results`, don't pick an alternative.
- 8 tasks (P5-1 through P5-8, with P5-7 reserved and deliberately unscheduled) with owners, dependencies, and a sequencing diagram.
- An explicit **deferred list** with reasons and revisit triggers (ISO clauses 4-10/SoA is flagged as the most urgent deferral, before any ISO-led pilot; CORS/CSRF hardening is flagged as required before any pilot reachable beyond localhost) — don't pull these in without checking why they were deferred first.

**Also check:** `tasks/agent-ownership.md` for the Claude-vs-Codex criteria the plan's per-task ownership calls were made against.

## Suggested order

Follow the plan's sequencing diagram: **P5-8** (mechanical cleanup, no dependencies) lands first and cheaply. **P5-1** (correctness bundle) gates both **P5-2** (reader migration) and **P5-3** (framework-aware desk review), because `D-P5-F` (how unconfirmed machine answers are treated) must be settled before either touches responses. **P5-5** (framework-aware scoping/evidence requests) has no dependencies and can run in parallel with the P5-1/2/3/4 lane. **P5-6** (RFI rebuild) comes last, after P5-2 and P5-5.

## Process — same as Phase 4, not reinvented

Follow `tasks/handoffs/2026-09-24-phase-4-kickoff.md`'s mechanics exactly (worktree-per-task, Opus subagent writes each handoff grounded in exact current code with numbered `D-P5-N-X` decisions, `codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh`, Codex can't commit so you commit on its behalf, independent Sonnet adversarial review before every PR, no Claude attribution on any Phase 5 commit/PR). The only things different this phase:

- **P5-2 gets a second, more skeptical review pass**, like P4-4 did — it changes what a client can be shown.
- **P5-1 and P5-3 share `analysis.py`.** Pre-declare the coordination rule in both handoffs before running them concurrently, the way Phase 2/3 parallel pairs did.
- **P5-8 should land before P5-4**, since both touch `question_engine.py`.

After each merge: update `tasks/todo.md`'s Phase 5 section, `CLAUDE.md`'s "Current phase" line, and project auto-memory (`project_status.md`, `MEMORY.md`).
