# Yozora S7: finish the pixel-gate fix pass (PR #113)

**Status: READY TO RUN (5 Oct 2026).** **For:** a fresh Claude session on Saqlain's machine. **Worktree:** `/Users/saqlainmomin/cyberassess-yozora-s7`, branch `codex/yozora-s7`, PR https://github.com/saqlainmmomin/Cyber/pull/113 (open, not merged). **Pushing and merging are Saqlain's**; you commit locally, and hand him the exact `git push` command when a batch is done.

## Goal
Close the remaining S7 pixel-gate misses on PR #113 without gaming the gate. For each failing screen either (a) fix the template or CSS so it matches the approved mockup, or (b) prove the miss is a legitimate exception (real data vs mockup copy, a must-keep element the mockup does not draw, a file owned by another slice, behaviour a test requires) and record it. **Done when** every failing state is either passing or listed as an exception with its cause, the full suite is green, the PR body gate table is updated, and Saqlain has seen before and after numbers.

**Out of scope:** `b7-dark-dense` (the mockup is a different page: framework tabs, severity tiles, search, filters, pager; matching it needs new UI and would regress `b5-findings`; ask Saqlain, do not build), S8, S9, and any file owned by S5 (`pages/assessment.html`, `assessment_header.html`, layout tab macros).

## Current state
- `main`-based branch at `a338df2` ("Yozora S7: pixel-gate pass ..."), pushed. Full suite at that commit: **1510 passed, 30 skipped, 0 failed**.
- Gate has two modes. **Full-page comparison** is for partial-panel screens (analysis partials, release, basis, requirement/conclusion/recommended-action cards, review finding card). **`--content`** is for full-page screens: it clips both pages to the main column (`.page`), hides the mockup-only "State" scaffold row (a div holding `span.chip` "State" plus a heading) and zeroes the mockup's spec-sheet `margin-top` on `[data-mock-state]` sections. This is why no compensating padding is ever needed in the app. Saqlain chose this (option 1).
- Last gate numbers (pass/fail, worst diff; threshold 0.4% differing pixels and no changed region over 40x40):

| Screen | Mode | Pass | Fail | Worst |
|---|---|---|---|---|
| basis, release, board-inputs, recommended-action | n/a | all | 0 | under 0.3% |
| analysis | full | 20 | 4 | 1.7% |
| conclusion-card | full | 38 | 6 | 2.7% |
| review-finding-card | full | 15 | 5 | 0.45% |
| requirement-card | full | 12 | 8 | 1.1% |
| narrative | content | 19 | 9 | 6.8% |
| findings | content | 4 | 8 | 3.6% |
| conclusions | content | 4 | 8 | 8.8% |
| review-queue | content | 4 | 12 | 8.6% |
| finding-card | content | 5 | 31 | 9.5% |
| no-report | content | 0 | 4 | 0.6% |
| report | content | 0 | 12 | 25.7% |

Re-run the baseline yourself first (below); do not trust these numbers or any scratchpad files from the earlier session.

## What is known about each miss (start here)
1. **finding-card (31 fails, biggest win).** Heights now match except `no-evidence`. (a) A ~1px border/outline drift starting at the action card (regions about 876x11) hits `open`, `in-progress`, `verify`, `source-changed`, `migrated`, `add-action` at 0.5 to 1.0%: find the border/shadow/radius token that differs from the mockup. (b) `no-evidence`: app is 62px taller at 1440 (819 vs 757); the mockup has no primary and no "Add action" there, but the one-primary rule and an existing test require a primary Add action: check whether the extra height comes from that button row or from something else. (c) `legacy` at 1024 misses by 1.4 to 3.3%. (d) The icon sprite in `app/templates/base.html` lacks `i-history`, and `i-link` has a slightly different path; the card draws the history icon inline as a workaround. Fixing the sprite is the proper fix but `base.html` is shared: ask Saqlain before editing it.
2. **findings (8 fails).** `default` is 0.48 to 0.52% at 1440 (the real conclusion title "Reasonable security safeguards implemented" wraps; the mockup says "Security safeguards": exception, or change the seed title in `design/harness/seed_s7_findings.py`, which is fixture data) and 2.9 to 3.6% at 1024 (title wrap plus the reviewer-name input and Board inputs link, now in a row beside the seg control). `create` is 1.0 to 1.3% (text rows).
3. **review-queue (12 fails) and conclusions (8 fails).** Chrome lines up. Remaining diffs are card contents (requirement titles and order, legacy-evidence warning, a wrapped "Workpaper trace" row), release blocker text, and the reviewer-name input. Decide per state which are exceptions; fix anything that is genuine layout.
4. **requirement-card (8 fails).** Caused by restoring pre-redesign behaviour on purpose: the visible criterion id (`.cc-crit-id`, v2-draft and contradiction at 1024) and the AI proposal block for v1. Behaviour wins. Look for a layout-only fix (e.g. id placement) before declaring an exception.
5. **conclusion-card (6 fails), analysis (4), review-finding-card (5).** `conclusion-card:edit` is 40px taller because `data-remediation-draft-button` is must-keep and the mockup edit state has no such button; `blocked` at 1024 is 18px shorter because the real `PERIOD_REQUIRED_MESSAGE` is shorter than the mockup text; `analysis:gate` has no "Your name" input in the mockup and preselects a different override reason. These are exceptions unless a layout trick avoids them without hiding must-keeps. Check the 5 review-finding-card fails (0.5%).
6. **narrative (9 fails).** `generating` (4): disabled controls and the restored "Drafting narrative…" alert (behaviour restored on purpose). `accepted` dark 1024 is 0.418% (try a token-level tweak). `error` (4): the mockup draws two static toast cards; toasts are S9, header checks only.
7. **no-report (4 fails, 0.44 to 0.60%).** One 23x22 region is the h1 and meta line ("Head office" and the real assessment name vs "Report"): comes from `pages/assessment.html` (S5), an exception.
8. **report (12 fails).** `released` is about 2% (page head from S5, "Live PDF" copy required by `test_correctness_bundle`, real counts and summary text). `not-released` is about 210px taller than the mockup because `test_p6_0e` requires the DPDPA readiness note and tests require the RFI/versions footer. `loading` differs by 21px. Mostly exceptions; confirm each and check nothing else adds height.

## Key files
- `design/harness/gate_s7.py`: the gate (`--content`, `--out`); `design/harness/screenshot.py` (has a small `prep_js` hook); `design/harness/seed_s7.py` and `seed_s7_<group>.py` (deterministic seeds; `--list` prints states); `app/routers/design_s7_*.py` (PREVIEW_PAGES fixtures).
- Templates: `app/templates/components/{finding_card,conclusion_card,requirement_card_body,seg_rows}.html`, `pages/{findings,conclusions,review_queue,narrative,board_inputs}.html`, `partials/{report_summary,framework_panel,remediation_panel,remediation_summary,report_tab,no_report,analysis_*,release_panel,report_basis_panel,review_finding_card,remediation_draft}.html`.
- CSS: edit `design/yozora-patterns.css` only (delimited blocks per group, small Edit calls), then `.venv/bin/python design/tokens_tool.py build`, which writes `app/static/css/yozora-patterns.css`; both must stay identical (`cmp`).
- Mockups: `docs/product/2026-10-01-app-design-mockups/screens/b5-*.html`. Rules and history: `tasks/handoffs/2026-10-04-yozora-s7-orchestration.md`, `tasks/handoffs/2026-10-01-yozora-s7-handoff.md` (must-keep ids, `hx-*`, `data-*`), `tasks/handoffs/2026-10-05-yozora-s7-codex-handoff.md`, `docs/product/yozora-fidelity-gate.md`.

## Constraints (decisions already made, do not reopen)
- **Never game the gate.** No padding, margins or magic numbers added to the app to match a mockup scaffold; no hard-coded mockup copy in templates; no loosened thresholds. If a miss comes from a mockup-only scaffold, change the gate, not the app. Real data differing from mockup copy is a recorded exception (seed data in the harness may mirror the mockup).
- Behaviour beats the mockup: keep every must-keep id, `hx-*`, `data-*`; exactly one visible `.btn.primary` per state; sentence case; framework names only behind a framework-in-scope condition; no combined cross-framework view.
- Keep the `F1` finding aliases (mockup `R-xx` is a recorded copy exception). Keycaps A, E, X stay out; only `j` and `k` (decision 6). Keep the temporary `reviewer-name` input.
- Never touch scoring, the analyzer, prompts, `services/narrative.py`, the v2 pipeline flag or PDF/snapshot code. Never read `validation/companies/*/answer_key.json`.
- Do not edit S5-owned files (`pages/assessment.html`, `assessment_header.html`, layout tab macros). Toasts are S9. Shared `base.html`: ask first.
- Stale guards get add-only allowances in `tests/yozora_paths.py`; never delete or weaken a guard. Lint rules: `tests/test_design_lint.py` (no uppercase, hex, arbitrary Tailwind values).
- No attribution lines in commits or the PR body. Sentence case and plain language to Saqlain.

## Process lessons from the last session (these cost hours)
- **Never wait with `pgrep -f <name>`**: it matches your own wait loop and hangs forever. Launch with `& echo $!`, save the PID, wait with `while kill -0 <PID> 2>/dev/null; do sleep 15; done`.
- macOS has no `timeout`. zsh does not word-split an unquoted `$VAR`: build argument lists inside `bash -c`.
- The gate costs about 35 to 40 seconds per state and there are about 120 states. Gate only screens you touched, in parallel groups with separate `--out` dirs, and run the full gate once at the end. Tell Saqlain the expected time up front.
- Local subagents run on **Sonnet** (Saqlain's instruction); give each group separate files and its own CSS block, say "no git commit/stash" to them and review their diffs before accepting. An earlier agent gamed the gate with a 22.4px literal and later a 48px token margin; both were reverted. Check for that in every diff.

## Setup
```bash
cd /Users/saqlainmomin/cyberassess-yozora-s7
git status -sb   # expect clean, in sync with origin/codex/yozora-s7 at a338df2
ls node_modules .env >/dev/null   # node_modules is a symlink, .env a copy, both ignored; recreate from ../dpdpa-gap-tool if missing
npm run css:build
```
Baseline gate (separate PIDs, one per group; example for two groups):
```bash
B=/private/tmp/claude-501/<session>/scratchpad/gate; mkdir -p $B/A $B/B
OPENROUTER_KEY="" nohup .venv/bin/python design/harness/gate_s7.py b5-finding-card b5-findings --content --out $B/A > $B/A/run.log 2>&1 & echo $! > $B/A/pid
OPENROUTER_KEY="" nohup .venv/bin/python design/harness/gate_s7.py b5-requirement-card b5-conclusion-card --out $B/B > $B/B/run.log 2>&1 & echo $! > $B/B/pid
```
Results land in `<out>/results-content.md` (content mode) or `results.md`; PNGs are `<screen>-<state>-<theme>-<width>-{baseline,candidate,diff}.png` (baseline is the mockup). Open them with the Read tool. Python: `.venv/bin/python` (3.13).

## Verification
- After each batch: `OPENROUTER_KEY="" .venv/bin/pytest -q tests/test_design_lint.py tests/test_yozora_s7_*.py` plus the suites for the templates you touched (`test_findings.py`, `test_remediation_tracking.py`, `test_workpaper.py`, `test_correctness_bundle.py`, `test_p6_7_requirement_card.py`, `test_p6_9_file_set.py`).
- Before reporting done: full suite once (`OPENROUTER_KEY="" .venv/bin/pytest -q --no-header -p no:cacheprovider`, about 3 to 4 minutes; expect 1510 passed, 30 skipped) and one final gate over every touched screen. Known flake: `test_p6_8_board_report_v2::test_scenario_3` (rerun once).
- Show Saqlain before and after numbers per screen and the exception list; send images with `SendUserFile` for any screen whose look changed (gate 4).
- Adversarial pass on the diff: unconditional framework copy, numeric priorities, more than one primary, combined cross-framework view, invented content, removed must-keep tokens (diff `id`, `hx-*`, `data-*` against `a338df2` on every template you edit), blocks moved inside an `{% if %}` that change what renders.

## Report back
Append `## Results` to this file: before and after gate table, the exception list with causes, files changed, tests changed (old to new), anything you needed Saqlain's decision on (`b7-dark-dense`, `base.html` sprite). Update the PR #113 body table (`gh pr edit 113 --repo saqlainmmomin/Cyber --body-file ...`; no attribution lines) after Saqlain approves the push. Hand him:
```bash
git -C /Users/saqlainmomin/cyberassess-yozora-s7 push
```

## Results (5 Oct 2026, partial: stopped early, no code changed)

**State:** worktree clean apart from this file; no commits, nothing to push. I re-ran the baseline gate (5 parallel groups, about 10 minutes wall clock) and started on the finding-card drift. I stopped there because the cause is not a layout difference and I did not want to burn hours on it.

### Baseline re-run (pass / fail)
| Screen | Mode | Pass | Fail | Handoff said |
|---|---|---|---|---|
| finding-card | content | 5 | 31 | 5 / 31 |
| findings | content | 4 | 8 | 4 / 8 |
| conclusions | content | 4 | 8 | 4 / 8 |
| review-queue | content | 4 | 12 | 4 / 12 |
| narrative | content | 19 | 9 | 19 / 9 |
| no-report | content | 0 | 4 | 0 / 4 |
| report | content | 0 | 12 | 0 / 12 |
| analysis | full | 20 | 4 | 20 / 4 |
| requirement-card | full | 12 | 8 | 12 / 8 |
| review-finding-card | full | 15 | 5 | 15 / 5 |
| **conclusion-card** | full | **0** | **44** | 38 / 6 |

Everything matches the handoff except **conclusion-card**, which is far worse in my run. Every state fails at 0.40 to 0.60% with a 186-wide region at the left edge: the side menu. The mockup shows an "Evidence" item and a "3" badge on Review; the app preview shell shows neither (stand-in assessment, no data). That is shell/S5 territory and not caused by the card; I did not find out why the earlier session saw it pass. The non-sidebar diffs (edit +40px, blocked at 1024) are the exceptions already listed in the handoff.

### finding-card drift: what I established
- DOM layout is identical to 1/1000 px between mockup and app for the `open` state (same tops, heights, `.page` rect and height, `.solid` offset inside `.page`). So the 0.5 to 1.0% misses are paint-level, not a spacing or border token difference.
- Pixel scan down a column: the two renders agree until the Status select's top border, which is 1px higher in the app (row 400 vs 401). Everything below it shifts with it.
- Ruled out: `.solid` is `overflow-x:auto` in shell.css (S3) while the mockup is visible. I overrode it for `.f-card` and the gate numbers did not change, so I reverted it.
- Not yet checked: the inline History svg (sprite lacks `i-history`), the closed "Edit details" form inside the action card, and whether the app's compositing differs (sticky shell). Next step is to bisect by removing those from the app render one at a time.

### Not started
findings, review-queue, conclusions, requirement-card, narrative, report, no-report, analysis, review-finding-card fixes and exception list; PR #113 body update. `b7-dark-dense` and the `base.html` sprite still need Saqlain's decision.

### Needs from Saqlain
1. Keep going on the finding-card paint bisect (about 31 states, likely one cause), or accept it as an exception?
2. conclusion-card sidebar: treat as shell exception, or investigate why it passed before?

## Results, part 2 (same day, after Saqlain agreed to record the 1px shift as an exception)

**Still no code changed, nothing to push.** I checked the cheap, high-count items and recorded exceptions. I did not fix any template or CSS: every miss I inspected is either paint-level with identical layout, a must-keep control, copy a test requires, or shared shell.

### Exceptions confirmed (with cause)
| Screen / states | Cause | Evidence |
|---|---|---|
| finding-card: open, in-progress, verify, source-changed, migrated, add-action (about 28 fails, 0.5 to 1.0%) | 1px paint shift on the Status select and everything below it. Layout is identical to 1/1000 px (tops, heights, `.page` rect, `.solid` offset). Not an `overflow` issue (`.solid{overflow-x:auto}` in shell.css; overriding it for `.f-card` changed no number, reverted). Cause not isolated. | probe script, pixel column scan |
| finding-card: no-evidence (62px taller at 1440) | The app draws two things the mockup omits in this state: the must-keep "Edit details" control and the required primary "Add action" button (one-primary rule). | side by side image |
| finding-card: legacy at 1024 (1.4 to 3.3%) | App warning reads "Closed without closure evidence (legacy). ..." (one line); the mockup text is longer and wraps. Tests require the app wording (`test_remediation_tracking.py`, `test_findings.py`, `test_yozora_s7_findings.py`). | grep, image |
| conclusion-card, requirement-card, review-finding-card, analysis (the 0.4 to 0.6% fails, and the 44 conclusion-card fails) | Shell side menu: mockup draws an "Evidence" item and a "3" badge on Review; the app preview shows neither. Shared frame, not the card. Plus the items already listed in the handoff (criterion id, AI proposal block, remediation draft button, required messages). | diff images |

### Not looked at (carried forward as likely exceptions per the handoff, unconfirmed)
findings, conclusions, review-queue, narrative, no-report, report, and the remaining requirement-card / analysis / review-finding-card misses. The handoff's causes (real data vs mockup copy, required notes/footers, S5-owned page head, S9 toasts) are plausible but I did not verify them this session.

### Tried and discarded
Re-running the four panel screens with `--content`: invalid, they are not inside `.page`, so every state fails with size mismatches. Use full-page mode for them.

### Open for Saqlain
1. Why the conclusion-card side menu lost "Evidence" and the badge since the earlier session (worth a look before Track 4; probably the preview shell, not S7).
2. If you want the finding-card 1px shift actually removed, the next step is bisecting the app render (History icon, closed "Edit details" form, shell compositing).
3. `b7-dark-dense` and the `base.html` sprite decisions are still open.
4. PR #113 body table not updated; I did not want to edit it without a full pass.

### Side menu check (answer to open question 1): not a bug
- "Evidence" is missing on purpose: `NAV_ITEMS` in `app/template_config.py` has `"evidence"` with `"available": False` (no cross-engagement route yet), so it is filtered out of the menu.
- The "3" badge is the live `review_count` (conclusions not yet approved or edited). The mockup hard-codes 3; the seeded preview has a different count.
- So the conclusion-card, requirement-card, review-finding-card and analysis side-menu diffs are shell exceptions. No change needed. I did not find why the earlier session saw them pass; likely a different gate setup, not a regression.
