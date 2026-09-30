# P6-5 abstention: c3 re-run and the full A/B comparison

## Goal
Finish the live `v2-fix` arm (judge prompt `p6-4.3`) by running `c3-certified-fortress` three times, then run `ab_compare` over the full 4-company set and record the gate verdict. **Done means:** c3 run-1..3 finished and scored, `ab_comparison.md` recorded verbatim in the abstention Results with the gate verdict and a plain recommendation, and the draft PR either left as a draft or marked ready (see step 7). Do not flip v2 on; that stays Saqlain's decision (P6-5c).

## Read this first: the verdict is already known
The partial arm (c1, c2, c4; `tasks/handoffs/2026-09-30-v2-abstention-diagnosis-and-fix.md`, "Live arm (partial)") has clean FP 65/66. c3 contributes 30 of the 96 pooled clean-control runs, so even if every c3 clean control came back compliant, pooled clean FP would be 65/96 = 67.7%, above the 61.5% gate. **The gate cannot hold for this arm.** This run only completes the record (and gives c3's own numbers). Tell Saqlain this before asking him to approve the spend; he may reasonably skip it.

## Current state (2026-09-30)
- Branch `claude/p6-5-abstention` (worktree `~/cyberassess-abstain`), draft PR open. Fix: judge prompt `p6-4.3` in `app/services/grounding/judge_prompts.py`.
- Arm dir `~/cyberassess-runs/2026-09-30-p6-5-v2-abstain/`: c1, c2, c4 have `run-1..3`, scored. `stuck-c3/` and `stuck-c3-2/` are the two hung c3 attempts: **keep them, never score them**, and never point `score` or `ab_compare` at them (the `run-*` glob under `c3-certified-fortress/` does not reach them).
- c3 hung twice because `llm_client` had no wall-clock deadline (httpx's per-phase read timeout resets on OpenRouter keep-alive bytes). Fix: branch `claude/llm-request-deadline`, its own PR (`llm_request_deadline_seconds = 600`, one retry, then `LLMRequestTimeout`).
- Spend so far ~$0.95 (9 finished runs $0.418; the two hung c3 attempts $0.529). DeepSeek `deepseek/deepseek-v4-flash` at $0.14/M in, $0.28/M out.

## Constraints
- **Never read `validation/companies/*/answer_key.json`.** Aggregates only: no gap text, key facts or requirement IDs in any output or file. From `score.json` read only `caught`, `false_positive`, `gap_class`, `framework_id`, `outcome`.
- **Decision 1 scoring is frozen** (`score.py` `FLAGGED = {non_compliant, partially_compliant, insufficient_evidence}`). Do not change it.
- File-set guard tests list allowed paths per PR: add per-PR `:(exclude)` or allow entries for anything that trips; never delete a guard. `tests/test_retention.py` scenario 13 only fails on uncommitted edits under `tests/`; it passes once committed.
- Python 3.13 `.venv` (symlinked from `~/dpdpa-gap-tool`). Merging is blocked for Claude: hand Saqlain the `gh pr merge` commands.
- Live runs spend real money: **ask Saqlain to approve the spend first** (~$0.25-0.30 for three c3 runs). Test live-script no-key guards with `OPENROUTER_KEY=""`, never `env -u`.
- Do not run `report.py` on these arms.
- Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; PR bodies end with the Claude Code attribution line.

## Steps
1. **Deadline fix first.** Confirm the `claude/llm-request-deadline` PR is merged (`gh pr list --state merged --head claude/llm-request-deadline`). Then, in `~/cyberassess-abstain`: `git fetch origin && git merge origin/main` (guard files may conflict: keep both sides' exclude entries), rerun `.venv/bin/pytest -q -p no:cacheprovider` (green), commit, push. Check `grep -n llm_request_deadline_seconds app/config.py` prints the setting. **Do not run c3 without it.**
2. **Spend approval.** Tell Saqlain the verdict note above and the cost (~$0.25-0.30), and wait for a clear yes.
3. **Run c3** (from `~/cyberassess-abstain`, in the background):
   ```bash
   set -a && source .env && set +a && ANALYSIS_PIPELINE_VERSION=v2 V2_MISSING_PASS=false .venv/bin/python -m scripts.validation.run_company c3-certified-fortress --runs 3 --llm live --out ~/cyberassess-runs/2026-09-30-p6-5-v2-abstain
   ```
   **Stall check:** every ~5 minutes, look at the mtime of each `c3-certified-fortress/run-*/llm_usage.jsonl`. Flag any run whose file is unchanged for 15 minutes (with the deadline fix, a stuck call should now surface as an `LLMRequestTimeout` record within ~20 minutes: 600 s + one retry). If a run stalls anyway, stop it, move the folder to `stuck-c3-3/`, and report rather than retrying blindly.
4. **Score:** `.venv/bin/python -m scripts.validation.score ~/cyberassess-runs/2026-09-30-p6-5-v2-abstain/c3-certified-fortress/run-*`. Check each `run.json` has `analysis_pipeline_version == v2` and each judge record has `judge_prompt_version == p6-4.3`.
5. **Compare:**
   ```bash
   .venv/bin/python -m scripts.validation.ab_compare --baseline v1 --arm v1=$HOME/cyberassess-runs/2026-09-29-p6-5-v1-rescored:pipeline=v1 --arm v2-criteria=$HOME/cyberassess-runs/2026-09-29-p6-5-v2-criteria --arm v2-fix=$HOME/cyberassess-runs/2026-09-30-p6-5-v2-abstain --price-in 0.14 --price-out 0.28 --out $HOME/cyberassess-runs/2026-09-30-p6-5-ab-abstain
   ```
   `v2-fix` must come out comparable (no `non_ok`/stage failures, same pack versions).
6. **Record** in `tasks/handoffs/2026-09-30-v2-abstention-diagnosis-and-fix.md` `## Results`, new subsection "Live arm (full)": `ab_comparison.md` verbatim, the gate verdict, c3 spend and any `LLMRequestTimeout` records, and a plain recommendation. Gate (pooled, vs v1): catch >= 92.9%, decoy FP <= 58.3%, clean FP <= 61.5%, stability >= 81.6%. Copy the updated file to `~/dpdpa-gap-tool/tasks/handoffs/` (untracked copy; keep both in sync). Commit and push.
7. **PR:** mark the abstention draft PR ready (`gh pr ready`) **only if the fix is measurably better than v2-criteria** on the gated metrics. Given the partial numbers, expect it not to be: then leave it as a draft and say so, with the recommendation to close it or keep it for reference.

## Report back
To Saqlain, plain language: the full-arm numbers for v1, v2-criteria, v2-fix; the gate verdict; whether the deadline fix held (any timeouts, any stalls); the spend; and the recommendation (the Results "Open question" lists the two remaining levers: show the judge which criterion each claim was extracted for, or revisit Decision 1 with written sign-off).
