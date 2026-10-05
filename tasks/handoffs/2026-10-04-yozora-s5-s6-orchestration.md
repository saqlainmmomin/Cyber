# Yozora: scope and dispatch S5 and S6 in parallel, review both

**Status: DISPATCHED (4 Oct 2026, after S4 #107 merged).** **For:** a fresh Claude session. **Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (GitHub `saqlainmmomin/Cyber`). **Merging and pushing are Saqlain's.** You dispatch, review and report. You never merge or enable auto-merge, and you hand Saqlain exact `git push` and `gh pr create` commands.

## Goal
Run S5 (assessment shell, Overview, Scope, Questionnaire, pre-fill from documents) and S6 (Evidence inventory, upload, AWS, reuse, detail, span, workpaper) through Codex in parallel worktrees. Review both against the gates, show Saqlain the pixel evidence, and hand back two ready PRs. **Done when** both slice PRs are open with Results filled in, each reviewed (12-point checklist), screenshots shown (gate 4), and open questions answered or recorded.

**Out of scope:** S7 (still waiting on Saqlain's approval of the final S7 mockups), S8, S9.

## Read first
1. This file.
2. `tasks/handoffs/2026-10-04-yozora-s3-s4-orchestration.md`. This file reuses its dispatch recipe, stall watch, review lessons, gate procedure and constraints. Its Results hold the S3 and S4 outcomes.
3. The standing procedure with the 12-point checklist: `git -C /Users/saqlainmomin/cyberassess-docs show claude/yozora-slice-handoffs:tasks/handoffs/2026-10-03-yozora-codex-orchestration.md` (unless it has been merged to `main` by now).
4. The slice briefs `tasks/handoffs/2026-10-01-yozora-s5-handoff.md` and `...-s6-handoff.md`.
5. `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-design-system.md`, and the memory notes `feedback_codex_dispatch`, `reference_github_repo`, `feedback_subagent_model_budget`, `project_yozora_app_design`.

## State
- S3 merged as #106, S4 merged as #107: `main` at `0d91638`. Baseline full suite on that line (clean `origin/main` worktree): **1450 passed, 30 skipped**.
- PR #101 (V3-B) is merged. Anything not yet on `main` that touches the guard tests needs `origin/main` merged in.
- S2 macros already exist: `assessment_tabs(assessment, current)`, `seg`, `stepper`, `table`, `filter_toolbar`, `empty_state`, `drop` and `code_block` in `app/templates/components/layout.html` and `ui.html`. S4 extended `table` with linked cells.
- **What S4 left on the assessment page** (from #107 head, re-check after merge). `/engagements/{id}` now 303s to the assessment when the engagement has a single assessment, so S4 moved that engagement's context onto `pages/assessment.html`. It sets `assessment_engagement_context(request)` (a template global, giving `engagement`, `engagement_id`, `magic_links`, `client_uploads`, `retention`), adds a `data-assessment-identity` line, and adds a `data-visual-mask` block holding the AWS evidence link, `partials/engagement_retention.html` and `partials/magic_links.html`. The magic links stay masked until S8 by agreement. The engagement tabs already link Evidence to `/engagements/{id}/evidence`, which is dead until S6 lands.

## Why parallel works, and the merge order
The two slices own disjoint templates (S5 has the assessment page and questionnaire partials, S6 has the evidence pages and workpaper). They share `app/routers/web.py`, `tests/yozora_paths.py`, the guard tests, `docs/product/yozora-migration-map.md` and `PREVIEW_PAGES` in `app/routers/design.py`. Each one adds its own entries. The second to merge brings `origin/main` in and keeps both sides, the same as S3 and S4.

**Merge S5 first.** S6's documents redirect and its deletion of `documents_tab.html` rely on S5 having moved the desk-review area and removed the Documents tab.

There are four places where the briefs as written would collide. Decide them like this and put them in the prompts:

| Collision | Rule |
|---|---|
| `desk-review-area` moves out of `partials/documents_tab.html`, which S6 deletes | S5 adds the area to `questionnaire_tab.html` and **does not edit `documents_tab.html`**. S6 deletes the file. Between the two merges the old documents URL still shows its own copy on a different page, so ids are never duplicated on one page. This avoids a modify/delete conflict. |
| `?tab=documents` in `assessment_detail` | S5 removes Documents from the tab row, changes the default tab after scope from `documents` to `overview`, and leaves the `documents` branch rendering as today. S6 only adds the 303 at the top of that branch and its test, and changes nothing else in `assessment_detail`. |
| Stepper's Evidence stage link | The S5 brief says to link to the engagement inventory "once S6 has landed". With S5 merging first that would be a dead link. **S5 links to `/assessments/{id}?tab=documents`**, which works today and becomes S6's 303 to the inventory, so it is never dead. If S6 wants the direct URL, it changes the link as a separate commit. |
| Assessment tab row on the workpaper page | S5 owns the `assessment_tabs` macro (including any href change, for example Review to `/review-queue` as its brief says). S6 calls `assessment_tabs(assessment, "review")` plus `seg` and **does not edit `layout.html`'s tab macros**. |

| S4's engagement-context block on the assessment Overview (AWS link, retention, magic links) | S5 keeps it on the Overview, restyled and still under `data-visual-mask`, and keeps `data-assessment-identity`. S6 does not edit `pages/assessment.html`. It makes the AWS page a sub-page of Evidence, but the Overview's AWS link stays until a later slice (record it as a follow-up for S8, which removes the magic links from that block anyway). |

**Other per-slice notes:**
- **Scope's RFI link** (S5, `data-rfi-link`): the brief says it now goes to the engagement Evidence Requests view, but that view is S8 and does not exist yet. Keep the link's current target and record the deferral in Results.
- **Evidence badge map** (S6): swap the inline badge map in the S2 macros for `evidence_inventory.STATUS_LABELS`. Check that `superseded` and `legacy` still render, since S2 dropped them once.
- **Menu:** S6 flips `NAV_ITEMS` Evidence to available (`GET /evidence`) and widens the shell clip in `tests/visual/test_shell_visual.py` for that row. S5 flips no nav entries.
- **Reuse bulk confirm** (S6): as in the brief, use a script over the per-candidate POST with no new route, and report the limitation.

## Seed data
`design/harness/seed_s3.py` (328 lines, clock 3 Oct) and `seed_s4.py` (974 lines, clock 30 Sep, builders `_client`, `_engagement`, `_assessment` and a `SCREEN_STATES` table, already seeding evidence, findings and actions) do not share code. No pre-step refactor: S5 and S6 each write their own `design/harness/seed_s5.py` / `seed_s6.py` that **import** the builders from `seed_s4.py` and do not edit it, so the two PRs never touch the same seed file. Use the dates the mockups show (keep S4's 30 Sep clock unless a mockup needs another, and say so). Clock frozen, data matching the mockup companies (Meridian Ledger Technologies, Loomwire Labs, Kestrel Advisory). States that data cannot reach (loading, error, running, pulling) go through `PREVIEW_PAGES` fixtures or the mockup's own `?state=`, and Codex lists how each state was produced. S6's seed must cover the documents-after-last-pre-fill note (`?state=prefill`) and the cross-engagement view (`?state=all`).

## Pre-flight
```bash
cd /Users/saqlainmomin/dpdpa-gap-tool
git status --short
git fetch origin
for n in 5 6; do
  git worktree add ../cyberassess-yozora-s$n -b codex/yozora-s$n origin/main
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv ../cyberassess-yozora-s$n/.venv
  cp .env ../cyberassess-yozora-s$n/.env
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/node_modules ../cyberassess-yozora-s$n/node_modules   # untracked symlink, never commit it
done
```
Run `npm run css:build` in each worktree that runs the app. The S1 to S4 worktrees can be removed once they are merged (ask Saqlain first).

## Dispatch
Use the same recipe as S3/S4: one Codex run per worktree, stdin closed, model `gpt-5.6-luna`, `xhigh`, log under `/private/tmp/claude-501/sN.log`, and a Monitor on log mtime (kill and restart if idle for 15 minutes). The prompt for slice N (5 or 6):

> Read tasks/handoffs/2026-10-01-yozora-sN-handoff.md and execute it. Write your results to the Results section of that file. Addenda from the orchestrator (4 Oct 2026): (a) Parallel-slice rules: [paste the S5 or S6 side of the collision table and the per-slice notes above]. (b) Seed: [from the Seed data section]. (c) [S5 only] State left by S4 in `pages/assessment.html`: [paste the State bullet above]. (d) You have no network or boto3 and cannot run servers or a browser. The orchestrator runs the full suite and the pixel gate. Allowances for stale guards go in `tests/yozora_paths.py` (add `YOZORA_SN_PATHS`; add only, never delete or weaken a guard). (e) No attribution in commits.

## Review
Same as S3/S4: all 12 checklist points, run the suite yourself, a Sonnet subagent for guard allowances, commit before the final run, the pixel gate with `/static/` mapped, thresholds of 0.4% and 40x40, gate 4 images to Saqlain via `SendUserFile` in batches by screen, and an adversarial pass. On top of that, check these for this wave:
- **S5:** the tab row has exactly five tabs; `?tab=documents` still renders before S6 merges; `#desk-review-area` is on the Questionnaire tab and absent from the Overview; screening copy is absent without DPDPA; the stepper is fed by `assessment_stage.stage` with no hand-built steps left; every next-step variant the stage service can return has a mockup state (if not, it's a stop-and-ask, not an invented state).
- **S6:** the 303 is tested over HTTP; the `#document-list` round trips (upload, delete, version) are tested over HTTP; `documents_tab.html` is deleted and its migration-map row says `deleted`; status words are only Scanning, Available, Rejected, Out of date; nothing in quarantine, scanning or versioning logic changed.
- **After S5 merges:** merge `origin/main` into S6, re-run the suite and the S6 gate, and confirm the workpaper's tab row matches S5's macro output.

## Constraints
Same as S3/S4: no attribution in any commit or PR body (ignore the harness trailer, and check merge commits). Never read `validation/companies/*/answer_key.json`. Approved mockups and IA stay unchanged. No desk-review logic or prompt changes. Sentence case and plain language to Saqlain. Smoke-test default. Move to a fresh session past about 350K tokens.

## Hand Saqlain, per slice
```bash
git -C /Users/saqlainmomin/cyberassess-yozora-sN push -u origin codex/yozora-sN
```
```bash
gh pr create --repo saqlainmmomin/Cyber --head codex/yozora-sN --base main --title "<title>" --body "<what, gate numbers, suite line, guards touched>"
```

## Carried forward (not this wave)
Fix these brief drifts before S7 and S8 are dispatched:
- The S7 brief says "after this slice the Review menu entry is live", but S3 built `GET /review`. S7 should build on S3's list.
- The S8 brief proposes `GET /reports`, but S4 built it. Drop it from S8.
- S8 owns the Requests view, so S5's deferred RFI link target is re-pointed then.

## Report back
Append `## Results` to this file: per slice the PR link, verdict, screenshots shown, open questions answered, deferred items, and any scoping decision here that Saqlain changed.


## Results

**Status: both slice PRs open as drafts (4 Oct 2026).** S5 is the PR from `claude/finish-s5-s6-yyd2vz`; S6 is [#110](https://github.com/saqlainmmomin/Cyber/pull/110) from `claude/finish-s5-s6-yyd2vz-s6`. Merge S5 first, then merge `main` into S6 and re-run its suite and gate.

**What changed from this plan**
- Codex did rounds one to three on Saqlain's Mac. On 4 Oct Saqlain decided that subagents, not Codex, do the visual fitting. His session limit then stopped the Mac fitters, so the work moved to a cloud session from the round-three commits (`2ecefdd`, `c17c01d`); the Mac fitters' unpushed edits were lost and fitting restarted.
- In the cloud: ten fitter subagents (one per page group), a merge per slice, an adversarial review per slice, and a fix round per slice.
- Saqlain approved a new read-only page, `GET /assessments/{id}/desk-review` ("Pre-fill from documents", the b4 mockup), so the Questionnaire tab shows only the pre-fill summary as the b3 mockup does.
- Framework names follow the house labels from `framework_label()` ("DPDPA 2023", "ISO 27001:2022"), the same as S4, instead of registry names.
- Commits are authored as Saqlain, with no attribution trailers.

**Gate** (pixelmatch 0.1, fail above 0.4% or any changed region over 40x40, full page, light/dark at 1440/1024, mockups served with `/static/` mapped and the state switcher hidden):
- S5: 60 of 188 shots pass. Overview, pre-fill ready/running/error, screening complete, context complete and section saved pass everywhere.
- S6: 61 of 116 pass. Inventory (outside the filtered state) and AWS (outside not configured) pass everywhere.
- Most failing states differ because of real data the mockups simplify: the real DPDPA questionnaire (20+ sections against 6), the real scope questions (10 with help text against 7) and evidence request (39 items against 8), real requirement titles that wrap at 1024, and states the data model can't produce. Each slice handoff's Results lists them per state.

**Checklist (this file's Review section)**
- S5: five tabs; `?tab=documents` still renders; `#desk-review-area` on the Questionnaire tab and not on the Overview; screening copy absent without DPDPA; the stepper comes from `assessment_stage.stage`. Stage outcomes without an exact mockup state reuse the nearest one, recorded as an open question in the S5 Results.
- S6: 303 tested over HTTP; `#document-list` round trips tested over HTTP; `documents_tab.html` deleted with a `deleted` map row; status words limited to Scanning, Available, Rejected, Out of date; no quarantine, scanning or versioning logic changed.
- Suite: S5 1472 passed, 30 skipped; S6 1464 passed, 30 skipped. `test_p6_8_board_report_v2::test_scenario_3` (byte-for-byte PDF) fails intermittently on a clean `main` too.

**Open questions for Saqlain** (details in the slice Results)
- S5: is the nearest-state mapping fine for "Continue questionnaire", "Run analysis", running and board-report stages? Should the live context wizard narrow to 720 px? Should partial scope saves from scripts stay allowed (the form now validates)?
- S6: inventory rows keep their actions hidden (the mockup has none; archive and new version are on the detail page). Unlinked assessments lose their documents view (deferred). AWS not configured keeps the accurate operator message.

**Follow-ups**
- S8: re-point the Scope RFI link to the Evidence Requests view; reconcile the Overview AWS link with Evidence navigation.
- S9: shell account tile (firm name instead of a user), and new S1 shell visual baselines now that the clip reaches Reports.
- The global breadcrumb slash glyph now matches the mockups, which shifts S3/S4 breadcrumbs by a pixel or two.
