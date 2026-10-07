# Flow rework: wave 1 kickoff (orchestrator handoff)

Owner: Claude, desktop app (orchestrator lane). Written 2026-10-07.

## Goal
Start implementing the flow rework plan `docs/plans/2026-10-07-001-flow-rework-plan.md` (read it fully first; it is the source of truth and its decisions are settled, so don't re-open them). You orchestrate wave 1:

1. **S0a** (Codex): retire the file-path guard tests. Small PR. It merges first so later slices carry no guard allowances.
2. Once S0a is merged, in parallel:
   - **S0b** (Codex): the hotfixes (follow-up storage, gradient, first-RFI copy, hide Live PDF until release, hide GDPR/HIPAA/PCI cards, remove the budget band).
   - **S1** (spec by the Claude terminal account → build by Codex): demo company.
   - **S2** (Claude terminal account): rules page + design-pass checklist + macros.
   - **S6-F1** (Codex): XLSX/CSV extraction + OCR fallback.

**Done when:** S0a merged; S0b, S1, S2 and S6-F1 each have an open PR that passed verification and one review pass. For S1, Saqlain has the demo-company walkthrough instructions (how to seed, which URLs to open).

## Current state
- The plan, owner comments, flow doc and review handoff are on branch `claude/flow-rework-plan` (PR #122). If #122 is merged, use `origin/main`. Otherwise branch slice worktrees from `origin/claude/flow-rework-plan`.
- **The primary checkout `/Users/saqlainmomin/dpdpa-gap-tool` is on `claude/v3c-mockup` with an unresolved merge conflict and uncommitted work belonging to another task. Don't checkout, stash, reset or commit there.** Do all work in fresh worktrees (`git worktree add ../dpdpa-<slice> -b <branch> origin/main`). Symlink `.venv` from the primary checkout and copy `.env` (see `feedback_codex_dispatch` memory).
- Verified bug: follow-up answers can't be saved. The textarea posts free text into `QuestionnaireResponse.answer`, which has a CHECK constraint allowing only the five answer values (`app/routers/web.py` ~2671-2695, `app/models/questionnaire.py:13-16`).
- PR #121 is closed (superseded).

## Key files
- `docs/plans/2026-10-07-001-flow-rework-plan.md`: the plan (slices, lanes, design pass, lean testing).
- `docs/product/2026-10-07-consultant-journey-comments.md`: owner comments (fixed).
- `docs/product/2026-10-06-consultant-journey-flow.html`: the target flow.
- `tasks/handoffs/2026-10-07-flow-rework-plan-review.md`: code-level findings with file:line refs (re-check refs; main moves).
- `tasks/agent-ownership.md`: Claude/Codex split criteria.
- `tests/yozora_paths.py` and the ~16 `tests/test_*` files that run `git diff main...HEAD`: S0a targets.

## Constraints
- **Lanes (plan, "Who does what"):** you write handoffs, dispatch Codex, verify, review and open PRs. The **Claude terminal account** writes S2 and the S1 spec. For those, write a handoff file and give Saqlain the one-line prompt to paste into that terminal (or launch it with `~/.claude/skills/handoff/scripts/run-handoff.sh claude <file>` if Saqlain confirms the terminal is logged into the second account). Codex builds.
- **Codex:** `gpt-5.6-luna` at xhigh by default. Separate worktree per run, `< /dev/null` on headless runs. Saqlain allows `gpt-5.6-sol` for heavier builds when quota allows. On a usage-limit error, don't loop. Check what's done, finish it or wait for the reset.
- **Lean testing:** keep the existing suite green. New tests only for data loss or silent score change. No new pixel gates, path guards or template snapshot tests. One Sonnet-subagent review per PR; a second only if the first finds a real bug.
- **Design pass:** any slice that changes a screen ends with the plan's design checklist and before/after screenshots in the PR. S0b's hotfixes are small; just include screenshots of the changed screens.
- **S1 demo company:** it's a walkthrough fixture, not an evaluation set. Nothing named `answer_key`. Stubbed LLM. Files are generated with openpyxl/Pillow. It must never read `validation/companies/*/answer_key.json`.
- **S0a:** delete only the `git diff`-based file-path checks and `tests/yozora_paths.py`. Keep every behaviour assertion in those files, plus `test_answer_key_isolation.py` and `test_remaining_llm_call_sites.py`.
- **S0b budget removal:** the `Initiative.budget_estimate_band` column stays (nullable, no migration). Old snapshots must still render.
- Never add Claude attribution or Co-Authored-By trailers to commits or PRs. Saqlain merges; you push and open PRs, never merge.
- Keep Saqlain posted at each phase change (dispatch, verify, PR open). Don't go silent during long Codex runs.

## Verification
- Per PR: full `pytest` green in the slice worktree (re-run it yourself; don't trust self-reports). Diff limited to the slice's files. One review pass done.
- S0b: a follow-up answer saves, survives a reload and shows in the workpaper (check in the running app via the `run` skill or browser pane). The PDF initiative line has no budget text.
- S1: the seed script runs from a clean DB. You open each seeded assessment in the browser and confirm the screens listed in plan S1 render.
- S6-F1: upload a generated xlsx and a scanned-style PDF. Both produce extracted text.

## Report back
Append `## Results` to this file: PR links per slice, what was verified and how, anything deferred, and the S1 walkthrough instructions for Saqlain.
