# Yozora: scope and dispatch S7, review it

**Status: NOT DISPATCHED (4 Oct 2026). Waits on S5 merging and on Saqlain's approval of the S7 mockups.** **For:** a fresh Claude session on Saqlain's machine. **Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (GitHub `saqlainmmomin/Cyber`). **Merging and pushing are Saqlain's.** You dispatch, review and report; you never merge or enable auto-merge, and you hand Saqlain exact `git push` and `gh pr create` commands.

## Goal
Run S7 (analysis states, review queue and cards, conclusions, findings, report tab, release and basis, narrative, board inputs, recommended-action draft) through Codex in its own worktree, review it against the gates, show Saqlain the pixel evidence, and hand back one ready PR. **Done when** the S7 PR is open with Results filled in, reviewed (12-point checklist), screenshots shown (gate 4), and open questions answered or recorded.

**Out of scope:** S5 and S6 (their own orchestration file), S8, S9.

## Read first
1. This file.
2. `tasks/handoffs/2026-10-03-yozora-codex-orchestration.md` (standing procedure: dispatch recipe, 12-point review checklist; if it is still only on the local branch `claude/yozora-slice-handoffs`, read it with `git -C /Users/saqlainmomin/cyberassess-docs show claude/yozora-slice-handoffs:tasks/handoffs/2026-10-03-yozora-codex-orchestration.md`).
3. `tasks/handoffs/2026-10-04-yozora-s3-s4-orchestration.md` (dispatch recipe, stall watch, review lessons, gate procedure, constraints; this file reuses them) and `tasks/handoffs/2026-10-04-yozora-s5-s6-orchestration.md` (its collision rules for the assessment page and its Results). Read both Results sections: what S3 to S6 actually shipped and which scoping decisions Saqlain changed. Where they differ from this file on a file S5 or S6 owns, theirs win.
4. `tasks/handoffs/2026-10-01-yozora-s7-handoff.md` (the slice brief Codex executes) and `tasks/handoffs/2026-10-03-yozora-s7-mockups.md` (the mockup review and Saqlain's answers A to D).
5. `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-design-system.md`, memory notes `feedback_codex_dispatch`, `reference_github_repo`, `feedback_subagent_model_budget`.

## State (4 Oct 2026)
- `main` is at `7bc7b00` (S3 #106, S4 #107 and V3-B #101 merged on top of S1, S2, backend #99 and the S7 mockups #102). Baseline full suite: **1450 passed, 30 skipped**. Re-run it on a clean `origin/main` worktree once S5 has merged, since that is the line S7 branches from.
- S5 and S6 are dispatched in parallel from `2026-10-04-yozora-s5-s6-orchestration.md`, S5 merging first. S7 has not started.
- **Approval gate.** The status log (`tasks/2026-10-04-status-log.md`) still says the S7 build needs Saqlain's approval of the merged mockups' final state (commit `279d1ef` revisions, now on `main` via #102). Ask him once before dispatch; do not dispatch until he says yes.
- Already done elsewhere, do not rebuild: `GET /review` (S3, `app/routers/web.py::review_page`, lists assessments whose `assessment_stage.stage` is `review`, `NAV_ITEMS` entry available). Review keycaps are settled (decision 6: leave A, E, X out; only `j` and `k`).

## Dependencies on S5 and S6
S7 shares templates and view code with both. The slice briefs allow parallel worktrees only when no shared template is touched, and these do overlap:

| Shared piece | Owner | What S7 needs from it |
|---|---|---|
| `pages/assessment.html` tab row (Overview, Scope, Questionnaire, Review, Report) and the `assessment_tabs` macro in `layout.html` | S5 | Every S7 page sits under that row; the Report tab content (`partials/report_tab.html`, `#report-content`) is hosted by the S5 shell. |
| S4's engagement-context block on the Overview (`data-assessment-identity`, the masked AWS link, retention and magic links) | S5, then S8 | Nothing; S7 leaves it alone. |
| `partials/questionnaire_tab.html` and `#analysis-area` | S5 | The four analysis partials S7 restyles render into it. |
| `partials/framework_tabs.html` (`#framework-panel`) | S5 | Wraps `partials/framework_panel.html`, which S7 restyles. |
| Review `.seg` row (Queue, Conclusions, Findings, Workpaper) via the S2 `seg` macro | S6 (workpaper) and S7 (the other three) | Same items, same order, same macro on all four pages. |
| Evidence detail and cited-span pages, `evidence_inventory.STATUS_LABELS` | S6 | The requirement card links to the span view and shows evidence status words. |
| `app/routers/web.py`, `tests/yozora_paths.py`, the file-set guards, `PREVIEW_PAGES` in `app/routers/design.py` | all three | Mechanical merges; keep both sides. |

**Collision rules** (same shape as the S5/S6 table; put the S7 side in the prompt):

| Collision | Rule |
|---|---|
| Assessment tab row on every S7 page | S7 calls `assessment_tabs(assessment, "review")` or `assessment_tabs(assessment, "report")` plus `seg`, and **does not edit `layout.html`'s tab macros or `pages/assessment.html`**. If the Report tab needs a change in `pages/assessment.html`, stop and ask. |
| Review seg row shared with S6's workpaper | Both use the S2 `seg` macro with Queue, Conclusions, Findings, Workpaper. Whichever of S6 and S7 merges second matches the first exactly (items, order, hrefs). |
| `framework_panel.html` inside S5's `framework_tabs.html` | S7 restyles the panel body only and keeps `#framework-panel` and the S5 strip untouched. |
| `#analysis-area` inside S5's `questionnaire_tab.html` | S7 restyles the four analysis partials only; it does not edit `questionnaire_tab.html`. |

**Order (my scoping default; Saqlain can overrule).** Dispatch S7 only after S5 has merged, so the shell, `#analysis-area` and the framework strip exist. S7 may run in parallel with S6. Whichever of S6 and S7 merges second merges `origin/main` in and makes its Review seg row match the first one's exactly (items, order, `current` keys). If S6 is still open when S7 starts, S7 builds the seg row with the S2 `seg` macro and links Workpaper to the existing `/assessments/{id}/workpaper` route. S8 waits for both S6 and S7.

## Scoping decisions (made by me on 4 Oct; Saqlain can overrule, tell him)
**1. The three new mockups replace "No mockup".** The slice brief predates #102. Its "No mockup: narrative, board inputs, recommended-action draft" note and the open question in it are superseded. Add these rows to the brief's Screens table (Codex does this in the PR):

| Mockup | States to match |
|---|---|
| `b5-narrative.html` | `empty`, `generating`, `drafted`, `partly-accepted`, `accepted`, `not-released`. `error` is a toast specimen (see 4). |
| `b5-board-inputs.html` | `empty`, `partly`, `complete`, `dense`, `error`. |
| `b5-recommended-action.html` | `empty`, `drafting`, `drafted`, `edited`, `error` (in-field), `saved`. `gaps-required`, `limit`, `stale`, `not-open`, `not-draftable` are toast specimens (see 4). It is drawn as the conclusion edit form, where `remediation_draft.html` is included from `conclusion_card.html`. |

Update the three `yozora-migration-map.md` rows (`pages/board_inputs.html`, `pages/narrative.html`, `partials/remediation_draft.html`) to name these mockups instead of "no approved mockup".

**2. Report seg row.** Report, Versions, Applicability (only when ISO 27001 is in scope), Narrative, Board inputs, in that order (mockup choice 2, accepted). Narrative and Board inputs pages sit under it. Versions (`snapshots_page`) and Applicability (`soa_page`) are S8 screens; S7 only links to their existing routes.

**3. Busy states.** Saqlain's answer C: a non-primary `.btn.loading` ("Drafting…"), no primary until the response returns, never a disabled primary. The shared `.btn.loading` rule sets `color: transparent`, so the label is invisible; the mockup uses the same CSS, so it will match. Keep the label in the markup for screen readers and record it as an S9 follow-up; do not edit shared CSS in S7.

**4. Toast states are behaviour checks, not pixel checks in S7.** Toasts are restyled in S9 (`b7-toasts.html`, the `toast()` helper in `app.js`). In S7, test that each toast case returns the right `X-Toast-Type` and a non-empty `X-Toast-Message` with the mockup's copy, and leave the pixel compare of those states to S9. Narrative generation today sets `X-Toast-Type: error` on a failed or limit-reached section with **no message** (`app/routers/drafting.py`, generate route): S7 adds the message header with the mockup's copy (small view change, in scope).

**5. Finding reference aliases.** The mockups label references `R-xx`; the app emits `F1`, `F2`... (`narrative.finding_refs`, `alias=f"F{index}"`), and those aliases are embedded in the narrative prompt and in the 422 accept error ("[F1, F3]"). Renaming them is a prompt change, which S7 must not make. Default: keep `F` aliases, accept the text diff in the narrative and recommended-action states as a recorded copy exception, and ask Saqlain whether he wants `R-xx` as a separate prompt-owning change.

**6. Pixel gate seed.** As in S3/S4: `design/harness/seed_s7.py`, a deterministic throwaway SQLite seed matching the mockup content (Meridian Ledger Technologies, Loomwire Labs, Kestrel Advisory) for every state in the Screens table, frozen clock. States hard to reach by data (loading, generating, drafting, error) go through `PREVIEW_PAGES` fixtures or the mockup's own `?state=`; Codex lists how each was produced. Like S5 and S6, **import** the builders from `seed_s4.py` (`_client`, `_engagement`, `_assessment`, `SCREEN_STATES`, which already seed findings and actions) and do not edit it or any other slice's seed. Keep S4's 30 Sep clock unless a mockup shows other dates, and say so.

**7. Shell clip.** S7 makes no new nav entry live (Review already is), so `tests/visual/test_shell_visual.py` needs no widening unless the assessment shell clip from S5 misses the Review or Report seg rows; extend it to cover them if so.

## Pre-flight
```bash
cd /Users/saqlainmomin/dpdpa-gap-tool
git fetch origin && git merge --ff-only origin/main     # S5 must already be on main
git worktree add ../cyberassess-yozora-s7 -b codex/yozora-s7 origin/main
ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv ../cyberassess-yozora-s7/.venv
cp .env ../cyberassess-yozora-s7/.env
ln -s /Users/saqlainmomin/dpdpa-gap-tool/node_modules ../cyberassess-yozora-s7/node_modules   # untracked symlink, never commit it
```
Run `npm run css:build` in the worktree before running the app (Tailwind CSS is gitignored).

## Dispatch
One Codex run in the worktree, stdin closed:
```bash
nohup codex exec -C /Users/saqlainmomin/cyberassess-yozora-s7 -m gpt-5.6-luna -c model_reasoning_effort="xhigh" "<prompt>" < /dev/null > /private/tmp/claude-501/s7.log 2>&1 &
```
Prompt:

> Read tasks/handoffs/2026-10-01-yozora-s7-handoff.md and execute it. Write your results to the Results section of that file. Addenda from the orchestrator (see tasks/handoffs/2026-10-04-yozora-s7-orchestration.md, Scoping decisions; they override the brief where they differ): (a) Collision rules: [paste the S7 collision table above]. The review inbox `GET /review` already exists (S3); do not build or change it, and drop it from your done list. Keycaps: leave A, E, X out. (b) The "No mockup" note is superseded: build narrative, board inputs and the recommended-action draft to `b5-narrative.html`, `b5-board-inputs.html` and `b5-recommended-action.html`; add their states to the Screens table and update their three migration-map rows. (c) Report seg row: Report, Versions, Applicability (ISO 27001 only), Narrative, Board inputs. Review seg row: Queue, Conclusions, Findings, Workpaper, with the S2 `seg` macro; if S6 has merged, match its row exactly. (d) Busy buttons are non-primary `.btn.loading`; no disabled primaries; do not edit shared CSS. (e) Toast states: assert `X-Toast-Type` and a non-empty `X-Toast-Message` with the mockup's copy; add the missing message on narrative generation failures and limits in `app/routers/drafting.py`. No pixel compare for toast states. (f) Keep the `F` finding aliases; do not touch `app/services/narrative.py` prompts; record the R-xx text diff in Results. (g) Create `design/harness/seed_s7.py` (deterministic throwaway seed, mockup companies, frozen clock); list how each state was produced. (h) You have no network or boto3 and cannot run servers or a browser; the orchestrator runs the full suite and the pixel gate. Allowances for stale guards go in `tests/yozora_paths.py` (add `YOZORA_S7_PATHS`; add only, never delete or weaken a guard). (i) No attribution in commits.

Watch for stalls: if the log is idle 15 minutes, kill the Codex process and restart it. Use a Monitor with a log-mtime check, not `sleep` chains.

## Review (do all 12 checklist points, do not trust Codex's Results)
- **Run the suite yourself.** Expect stale guard failures; a **Sonnet** subagent adds the `YOZORA_EXCLUDES` allowances (additions only). Commit before the final run, because three-dot guards only see commits.
- **Pixel gate.** Serve mockups with `/static/` mapped to `app/static/` (recreate `srv.py` from the S1/S2 copy with `ROOT` set to the worktree). Run `design/harness/screenshot.py --full-page` against the app on the S7 seed (`DATABASE_URL`, `OPENROUTER_KEY=""`). Thresholds: 0.4% on app screens, no changed region over 40x40. `b7-dark-dense.html` is 1440 dark only.
- **This slice's regression risks.** It carries the most `data-*` and the most test assertions in the app: run the must-keep extraction diff on every template in the brief's list. Check over HTTP that approve, edit, reject, reopen, RFI add/withdraw, divergence acknowledge, action close/reopen/verify, release, report basis, narrative accept/discard and board-input saves still swap the right target. Check every card state the old templates rendered (superseded, locked, conflict, legacy bulk, migrated, source-changed) still renders.
- **Gate 4.** Send Saqlain baseline, candidate and diff images with percentages via `SendUserFile`, batched by screen, before calling the slice ready. List the toast states and the R-xx copy exception separately.
- **Adversarial pass** (checklist 11): unconditional framework copy (DPDPA, ISO 27001), numeric priorities, more than one visible primary, a combined cross-framework view, anything invented.
- Local subagents on **Sonnet**; Opus-level work goes to a cloud agent.

## Constraints
No attribution lines in any commit or PR body (check merge commits too). Do not read `validation/companies/*/answer_key.json`. Never touch scoring, the analyzer, prompts, the v2 pipeline flag or the report snapshot PDF code. Keep approved mockups and IA unchanged. Sentence case and plain language to Saqlain. Move to a fresh session past about 350K tokens.

## Hand Saqlain
```bash
git -C /Users/saqlainmomin/cyberassess-yozora-s7 push -u origin codex/yozora-s7
```
```bash
gh pr create --repo saqlainmmomin/Cyber --head codex/yozora-s7 --base main --title "Yozora S7: analysis, review, report, narrative and board inputs" --body "<what, gate numbers, suite line, guards touched, copy exceptions>"
```
After S6 and S7 merge, S8 is next, then S9.

## Open questions for Saqlain (ask before dispatch)
1. Are the S7 mockups approved as merged in #102? (Blocks dispatch.)
2. Keep `F1`-style finding aliases in the app, or plan a separate change to `R-xx`? (Default: keep.)
3. Dispatch S7 after S5 merges, in parallel with S6? (Default: yes.)

## Report back
Append `## Results` to this file: the PR link, verdict, screenshots shown, answers to the open questions, deferred items (S9: toast pixel states, `.btn.loading` hidden label), and any scoping decision Saqlain changed.
