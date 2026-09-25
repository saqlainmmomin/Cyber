# Phase 6 kickoff — next session

**Date:** 2026-09-25

## Where things stand (2026-09-25)

Phases 1–5 are complete. Phase 6 plan: `docs/plans/2026-09-25-001-grounded-analysis-and-deliverables-plan.md` (decisions D-P6-A to D-P6-L; D8 amended). Security and Bedrock `ap-south-1` residency are Track 4, scheduled after v2 pipeline validation.

Merged today:
- #47 P5-9 harness + 4 packs (C1, C2, C3, C4)
- #48 Phase 6 plan with D-P6-A through D-P6-L
- #49 DPDPA test-criteria draft (inert until sign-off)
- #50 answer-key isolation test (`tests/test_answer_key_isolation.py`)
- #51 untracked `.venv` symlink fix (`.gitignore` now has `.venv`)
- #52 P6-0e DPDPA correctness
- #53 P6-0f DPDPA follow-ups (Saqlain's decisions)
- #54 P6-1 LLM plumbing (provider-agnostic structured output, timeouts/retry, concurrency, temperature 0, cost records, durable jobs)

`main` @ `b7ddcf7` at time of writing.

## Open PRs

**#55 P6-1b handoff (batch frameworks >50 controls into ≤25-control section batches on the v1 pipeline)**
- ISO → 6 batches, NIST → its 6 functions; DPDPA unchanged.
- Fail closed per framework after one missing-ID retry.
- Deterministic executive summary.
- Handoff: `tasks/handoffs/2026-09-25-p6-1b-v1-framework-batching.md`.
- Also includes plan amendment D-P6-L: v2 judge runs without test criteria via a fallback, recording `criteria_source`.
- Also includes P6-1c notes.
- Needs Saqlain's merge.

**#56 P6-1c configurable output ceiling**
- Framework desk review, framework evidence extraction and the multi-framework judge use `llm_max_output_tokens_framework` (default 65536) instead of hard-coded 16,384.
- Curated DPDPA path unchanged.
- Live smoke findings in the task.
- Needs Saqlain's merge.

## Live finding (2026-09-25)

ISO/NIST analysis fails on v1: judge was truncated at 16,384 tokens (first smoke), then after raising the ceiling the single judge stream dropped with `APIConnectionError` after 354 s.

**Desk review:** needed 24,591 tokens / 17 min (`stop`).  
**Judge (single call):** dropped at 354 s; at ~24 tokens/s, a full ISO judge answer would be ~20 minutes in one stream.

Therefore, batching (P6-1b) is required for reliability and latency, not only for the token limit.

**DeepSeek V4 Flash pricing on OpenRouter:** $0.049/M input, $0.098/M output, $0.0098/M cached input; 384k max output.

## Next actions in order

1. **Saqlain merges #55 and #56** to `main`.
2. **Dispatch P6-1b to Codex:**
   ```bash
   codex exec -m gpt-5.6-luna -c model_reasoning_effort=xhigh -s workspace-write \
     -c 'plugins."compound-engineering@compound-engineering-plugin".enabled=false' \
     -C <worktree> "<prompt>" < /dev/null
   ```
   The `< /dev/null` is mandatory or it hangs on stdin. Codex cannot write `.git`, so the orchestrator reviews, commits, and opens the PR.
3. **Orchestrator live smoke:** `python -m scripts.validation.render_evidence c0-example` then `python -m scripts.validation.run_company c0-example --llm live --runs 1 --stop-after analysis --out <dir>` with `.env` exported — every call must finish `stop`.
4. **Run P5-9 Stage C baseline.**
5. **Start ISO criteria draft** (with own-words ISO rewrite, D-P6-J) and NIST criteria draft — who signs them off is Saqlain's open decision.
6. **P6-3 design** (claims pipeline).

## Pending on Saqlain

- Review DPDPA criteria CSV `tasks/criteria-review/dpdpa-criteria-v1.csv` (150 rows; low → medium first) to unblock P6-2b.
- Start task chips for PNG-upload 500s in the harness, integrated-report assessment ordering (`test_longitudinal_demo` scenario 9 fails ~3/4), and two stale tests on main.
- Decide ISO/NIST criteria signer.
- Decide ISO clauses 4–10 (P5-7).
- Re-export P5-9 question packs (DPDPA question text changed in #53 — agents designing prompts must not touch `validation/`).
- Track 4 before real client data (auth, encryption, Bedrock ap-south-1).

## Known failing tests on main

- `test_remediation_tracking::test_scenario_10…` (hardcoded 2026-09-24)
- `test_p5_4…::test_scenario_13_structural_guards` (stale `git diff main` guard)
- `test_longitudinal_demo::test_scenario_9…` (nondeterministic ordering)
- Intermittent `test_workpaper::test_smoke_full_assessment_traceability`

## Working rules learned today

- No Co-Authored-By / "Generated with" lines in commits or PRs in this repo.
- New guard tests must use three-dot `git diff main...HEAD`.
- In worktrees run `git branch -f main origin/main` before the suite.
- Symlinked `.venv` must never be committed (`.gitignore` now has `.venv`).
- Status page artifact: https://claude.ai/artifact/1zQ4ZbQWS8hdrF4gvD8uVx.
