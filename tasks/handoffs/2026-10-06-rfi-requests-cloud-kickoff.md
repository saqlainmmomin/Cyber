# Kickoff: RFI and Requests consolidation (cloud session)

Paste the prompt below into a fresh cloud session on the `saqlainmmomin/Cyber` repo. The spec is `tasks/2026-10-06-rfi-requests-consolidation.md`.

## Prompt

You are implementing one PR for CyberAssess. The complete spec is `tasks/2026-10-06-rfi-requests-consolidation.md` on branch `claude/rfi-requests-plan` (also on `main` once merged). Read it fully, then read the root `CLAUDE.md`. Follow the spec exactly; it was verified against the code and has been through one review pass. Do not redesign. If something in the spec is wrong or ambiguous, stop and report it instead of guessing.

### Setup
1. Start from `main` (`git fetch origin && git checkout -b claude/rfi-requests-consolidation origin/main`). If the spec file is not on `main` yet, `git checkout origin/claude/rfi-requests-plan -- tasks/2026-10-06-rfi-requests-consolidation.md tasks/handoffs/2026-10-06-rfi-requests-cloud-kickoff.md`.
2. Python 3.13 is required. Install with `pip install -r requirements-dev.txt`. Run `pytest -q` once to record the baseline before changing anything.

### How to work
- Run work packages A, B, C and D (spec section 4) as **parallel Sonnet subagents**, each in its own git worktree off the branch above, each restricted to the files its package owns. Brief each subagent with: the spec path, its package letter, the files it may touch, the tests it must run, and the rules below.
- Merge A-D into the branch (no textual overlap is expected), then do package E yourself on the merged branch.
- During A-D only the package's own tests are expected to be green. Guard tests that enumerate allowed paths fail until E adds the allowance.

### Hard rules
- No Claude attribution anywhere: no `Co-Authored-By`, no "Generated with" line in commits or the PR body.
- Do not merge the PR. Open it against `main` and stop.
- Never open or read `validation/companies/*/answer_key.json`.
- Do not touch `ANALYSIS_PIPELINE_VERSION`, the v2 pipeline or any prompt.
- `tests/yozora_paths.py` and the guard allowance lists are add-only. Never delete a path or a guard.
- No `'` character in `app/templates/pages/rfi.html` or `app/templates/partials/rfi_links.html` (tests enforce it). No `|safe`, no `display:none`, no hex colours, no new CSS files, no edits to `design/tokens.json`.
- Do not tune work to pass the pixel gates for `b6-rfi`, `b6-magic_links`, `b3-scope-complete`, `engagement_detail`, `b1-firm_settings`. They diverge on purpose and Saqlain signs them off by hand.
- Scope is exactly the spec. Domain grouping and link regenerate are out. No drive-by refactors.
- A separate local session is changing `app/routers/web.py`, `app/routers/questionnaire.py`, `app/services/context_profiler.py`, framework definitions and `tests/yozora_paths.py`. None of that is on `main`. Do not edit `web.py` unless the spec says so. If your branch conflicts with `main` later, keep both sides of add-only lists.

### Done means
1. All spec checklists in section 5 tick.
2. `pytest -q` is green on Python 3.13, with the output pasted in the PR.
3. You ran the section 6 smoke test (curl table and, if a browser is available, the browser steps) and pasted the actual output in the PR, including any row that differed from the expected value and why.
4. If Chromium is available, screenshots from `design/harness/screenshot.py` at 1440 and 390, light and dark, are listed in the PR for Saqlain's visual check.
5. PR description lists: what changed per package, tests added or changed (with the exact lines from the spec's table), deviations from the spec (ideally none) and anything you were unsure about.

### Report back
When the PR is open, reply with the PR URL, the full-suite result, the smoke-test result, and any deviation from the spec. Claude (local) will then do an adversarial review using spec section 7, and Saqlain will approve and merge.
