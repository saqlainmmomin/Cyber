# Status log: 2026-09-30

## Current phase
Phase 6. P6-5 (v2 A/B and flip) is closed out by the P6-5c decision to park v2 (see `tasks/2026-09-30-p6-5c-decision-park-v2.md`). Focus moves to deliverables.

## Merged / closed today
- #89 merged: wall-clock deadline on every LLM provider call (`llm_request_deadline_seconds=600`, daemon worker, `LLMRequestTimeout`, one retry). It fixes the earlier c3 hangs (httpx read timeout reset on keep-alive bytes). Also fixed `tests/test_p6_nist_csf2_alignment.py`.
- #90 closed unmerged: judge prompt p6-4.3. Gate fails; no better than p6-4.1. Kept for the record.
- main merged into `claude/p6-5-abstention` after #89 (1,217 passed, 10 skipped).

## Pipeline state
v1 is live. v2 is off and parked.

## Spend
c3 re-run after #89: 3 runs, 745 LLM calls, all ok, no timeouts, $0.334. v2-fix arm $0.758. Session total about $1.28, including two hung c3 attempts (~$0.529). Model deepseek-v4-flash at $0.14/M in, $0.28/M out.

## Open worktrees / branches (not removed)
- `~/cyberassess-abstain` (`claude/p6-5-abstention`)
- `~/cyberassess-llm-deadline` (`claude/llm-request-deadline`, merged)
- Run data in `~/cyberassess-runs/2026-09-30-p6-5-v2-abstain/` (`stuck-c3/`, `stuck-c3-2/` kept, never scored).

## Next session
Deliverables: P6-8 B2 (Word/Excel export) and P6-10 (narrative). The kickoff file still needs to be written.

## Parked
- v2 pipeline flip and any further judge-prompt work.
- Reopening needs Saqlain to choose criterion-aware evidence or a Decision 1 revisit (written sign-off).
- Optional free check: operating evidence in client-visible company documents.
