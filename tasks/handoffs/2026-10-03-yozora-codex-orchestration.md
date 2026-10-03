# Yozora: orchestrate Codex through slices S1 to S9 and review its work

**Written:** 2026-10-03. **For:** a fresh Claude session. **Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (GitHub `saqlainmmomin/Cyber`). **Merging is Saqlain's.** You dispatch, review and report; you never merge, and you never enable auto-merge.

## Goal
Saqlain approved the Yozora redesign (61 mockups, information architecture, design guide). Nine build slices turn the approved mockups into the running app. Codex builds each slice from its handoff; you check each slice against the gates, show Saqlain the evidence, and report. By the end, every screen in `docs/product/2026-10-01-app-design-mockups/screens/` is shipped in the app with passing pixel baselines in both themes.

**Done when** all nine slice PRs are open or merged with their Results filled in, each reviewed by you against the checklist below, with the screenshots shown to Saqlain and every open question answered or recorded. Your own Results go at the foot of this file.

## Read first
| Path | What |
|---|---|
| `docs/product/yozora-design-system.md` | Design guide (approved 3 Oct 2026) |
| `docs/product/yozora-fidelity-gate.md` | The five gates every slice must pass |
| `docs/product/yozora-migration-map.md` | All 75 templates, slice, must-keep attributes, tests |
| `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md` and `flow-map.html` | Binding information architecture |
| `tasks/handoffs/2026-10-01-yozora-s1-handoff.md` … `s9-handoff.md` | The nine slice briefs (rewritten 3 Oct; each is self-contained) |
| `tasks/handoffs/2026-10-03-yozora-backend-features.md` (branch `claude/yozora-backend-features`) | Spec for backend PR #99 |
| `tasks/agent-ownership.md` | Claude and Codex task split; adversarial review before merge |
| `tasks/handoffs/2026-10-03-yozora-design-guide-and-slice-handoffs.md` (Results) | What was decided and found while writing the handoffs |

## Pre-flight (do before dispatching S1)
1. **Docs PR merged?** The design guide, migration map and rewritten handoffs live on branch `claude/app-design-kickoff` (PR #98, plus the follow-up PR for the handoffs; check `gh pr list`). Codex branches from `main`, so these must be merged first. If they are not, ask Saqlain to merge them or tell Codex to branch from the docs branch.
2. **Backend PR #99** (https://github.com/saqlainmmomin/Cyber/pull/99): at writing it held only its spec, no code. Slices S3, S4, S5, S6 and S8 depend on it (firm settings and retention, Add assessment, actions export, stage, pre-fill freshness, evidence inventory, request summary, client contacts). Check whether it is implemented and merged. If not, tell Saqlain which slices are blocked and start with S1 and S2, which need nothing from it.
3. **P6-10 and V3-B.** The 1 Oct work order (`project_board_deck_format` in memory) put P6-10 and V3-A, then V3-B, ahead of the app build. State at writing: P6-10 (PR #95) and V3-A (PR #94) are merged; V3-B (the board deck) has only a handoff and contract tests on branch `claude/p6-8-v3b-deck` and no PR. Re-check with `gh pr list --state all` and `git log origin/main`. If V3-B is still unmerged, ask Saqlain once whether to start S1 anyway; the file sets barely overlap (V3-B lives under `app/templates/reports` and the board export code, S9 treats those as out of scope), but it is his call.
4. **Baseline tests.** In a clean worktree of `origin/main`, run the full suite and record the summary line. A slice's failures must be compared against that.

## Slice order and dependencies
```
S1 shell + tokens + harness
  -> S2 component layer + /design
       -> S3 Home, clients, settings   (needs #99)  ┐ may run in parallel
       -> S4 engagements               (needs #99)  ┘
            -> S5 assessment, scope, questionnaire, pre-fill (needs #99)
                 -> S6 evidence                      ┐ may run in parallel
                 -> S7 analysis, review, report      ┘
                      -> S8 requests, versions, SoA, compare, client pages (needs #99; after S6 and S7)
                           -> S9 system states, dark and mobile pass, Tailwind retirement
```
Run S1 then S2 alone. Pairs may run in parallel worktrees only as drawn, because they touch disjoint templates. They still share `app/routers/web.py`, `tests/yozora_paths.py` and the `NAV_ITEMS` list, so the second to merge rebases and keeps both sides. S5 runs alone because it removes the Documents tab that S6 later deletes. Do not start a slice until its predecessors are merged to `main`.

## How to dispatch
Follow the memory notes `feedback_codex_dispatch` and `reference_github_repo`.

- **Worktree per slice**, never two Codex runs in one directory:
  ```bash
  cd /Users/saqlainmomin/dpdpa-gap-tool
  git fetch origin && git branch -f main origin/main
  git worktree add ../cyberassess-yozora-sN -b codex/yozora-sN main
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv ../cyberassess-yozora-sN/.venv
  cp .env ../cyberassess-yozora-sN/.env
  ```
  Check the handoff file is in the worktree (commit it or `cp` it) before dispatch.
- **Model:** `gpt-5.6-luna` at `xhigh` by default. Switch to `gpt-5.6-sol` at medium only if Saqlain asks, and then give that diff a more sceptical review.
- **Run:**
  ```bash
  codex exec -C ../cyberassess-yozora-sN -m gpt-5.6-luna -c model_reasoning_effort="xhigh" "Read tasks/handoffs/2026-10-01-yozora-sN-handoff.md and execute it. Write your results to the Results section of that file." < /dev/null
  ```
  Always close stdin (`< /dev/null`) when backgrounded; confirm the log moves past the prompt within a minute or two.
- **No attribution:** commits and PR bodies carry no Claude, Codex or "generated by" line and no co-author trailer. The harness reminder will suggest one; the standing user rule wins. Check every commit before it is pushed, including merge commits.
- **Pushing and PRs:** push and PR creation can be blocked in auto mode. If so, hand Saqlain the exact `git push` and `gh pr create` commands.
- **Quota errors:** do not loop. Check `git status` and the test run in the worktree, finish mechanical leftovers (Results write-up) yourself, and report.
- **Stale guards:** many older file-set guards will fail on every slice. The handoffs tell Codex to add scoped allowances through `tests/yozora_paths.py`, never to delete or weaken a guard. Confirm that in review.

## Review checklist for each Codex PR
Do all of these; do not rely on Codex's own Results.

1. **Scope.** `git diff --stat main...HEAD` shows only the slice's templates, new routes and views, CSS/JS, tests and docs. No change to scoring, the analyzer, prompts, PDF code, models or migrations (except where the slice file explicitly allows a route or view change). `validation/companies/*/answer_key.json` untouched.
2. **Gate 1, tokens.** `python3 design/tokens_tool.py check` and `tests/test_design_tokens_in_sync.py` pass; no colour or spacing value defined anywhere but `design/tokens.json`.
3. **Gate 2, gallery.** `/design` renders; from S2 on, every new component appears there in all states.
4. **Gate 3, pixels.** Run the visual suite (`RUN_VISUAL=1`). Every screen and state in the slice's Screens table is at or under 0.4% (0.2% for `/design`) with no changed region over 40x40. Any loosened threshold has a written reason; reject a loosening without one.
5. **Gate 4, human.** For every screen and state, show Saqlain the baseline, candidate and diff image side by side with the percentage. Send them with `SendUserFile` (or open the images in the app) in batches by screen. Do not tell Saqlain a slice is ready until he has seen them.
6. **Gate 5, lint.** `tests/test_design_lint.py` passes; the slice's templates are removed from `tests/design_lint_allowlist.txt`. Run the grep checks yourself: no `uppercase`/`text-transform`, no hex or arbitrary Tailwind values, no numbered or lettered headings, no `background-clip:text`, no `blur-3xl`. Count visible `.btn.primary` per captured state: at most one, none in a state with no real action.
7. **Must-keep attributes.** Write a small script that extracts ids, `hx-*` and `data-*` from each slice template on `main` and on the PR branch and diffs them; any removal or rename fails the review unless the handoff names it (the S3 retention ids move to Settings; S5 and S6 move the desk-review and upload containers).
8. **Tests changed deliberately.** `git diff main...HEAD -- tests` must match the PR description's list of changed strings (old, new, reason). Reject assertions weakened to pass (for example `assert x` replacing a string check), and Tailwind-class assertions replaced by nothing. Guard tests may only gain lines.
9. **Behaviour.** Run the app (`run` skill: `uvicorn app.main:app --host 127.0.0.1` with Python 3.13, `OPENROUTER_KEY=""`) and click through the slice's flows: HTMX swaps still land in their targets, forms still post, the temporary reviewer-name fields still work, framework copy appears only for frameworks in scope, nothing 404s from the menu.
10. **Full suite.** Run it yourself and compare the summary line with the pre-flight baseline.
11. **Adversarial pass.** Per `tasks/agent-ownership.md`, one adversarial review of the diff before you recommend merge: look for dead links, copy that names a framework unconditionally, numeric priorities shown, tokens or contact details leaked into URLs or logs (S8), and anything invented that is in neither the guide nor a mockup.
12. **Report to Saqlain:** a short note per PR with what changed, the screenshots, test string changes, guards touched, open questions, and your verdict (ready or not, and why). He merges.

After each merge, `git branch -f main origin/main` in worktrees before the next dispatch, and update `tasks/` status as the project convention requires.

## Open backend and product decisions (ask Saqlain; do not decide silently)
These were found while writing the handoffs. Each slice file states the conservative default.

1. **Menu destinations with no route or no design.** The side menu shows Clients, Engagements, Review, Evidence and Reports, but only Home exists. Mockups exist for Clients (`b1-clients`), Engagements (`b2-engagement_list`) and the cross-engagement Evidence view (`b4-evidence?state=all`); PR #99 provides only the inventory read model, so S3, S4 and S6 add those list routes themselves. **Review and Reports have no cross-engagement mockup at all** (the mockup menu links point at one assessment). Proposed: `/review` lists assessments with decisions waiting, `/reports` lists issued report versions, each linking to the assessment. Confirm or drop the entries.
2. **Home attention rows** (S3): derived from the stage service's next step plus request summary. Confirm the rule.
3. **User menu before auth** (S1): firm tile with Settings and theme only; no Profile or Sign out.
4. **Narrative, board inputs and recommended-action draft** (S7) have no mockups (added after they were drawn); they are built from existing components only. Do they need mockups first?
5. **Evidence reuse with one confirm** (S6): today each candidate posts separately; the design wants tick boxes and one button. Default is a sequential script over the existing POST; a bulk route would be a backend decision.
6. **Review keycaps** (S7): the mockup shows A, E, X hints; only `j` and `k` exist. Default: leave the hints out.
7. **Sign-in template** (S3): no route renders it (`/login` redirects); previewed through `/design/pages/login`.
8. **Tick-box item picker for client links** (S8): left out of PR #99; free-text items stay unless Saqlain wants the picker.
9. **Accessibility gap** (design guide): unticked marker, checkbox, radio and drop-zone outlines are about 1.3:1 on the light panel; WCAG asks 3:1 for control boundaries. Raise `--line-strong` or accept?
10. **Component CSS delivery** (S1): decided as a byte-for-byte copy of the two component files into `app/static/css/` by the token generator, with a sync test. Overrule if he prefers serving `design/` directly.
11. **Mockup inconsistencies** (S8): `b6-magic_invalid` and `b6-magic_upload` use the firm name Kestrel Advisory; `b7-link-expired` uses Sharma and Rao Advisory, names a person and says links last 14 days. The app has one firm name and one expiry setting; build to `b6-magic_invalid`.
12. **htmx** still loads from unpkg; only fonts are vendored. Vendor it too?

## Constraints
- Do not read `validation/companies/*/answer_key.json`.
- Docs-only work on the docs branch; app code only in slice branches built by Codex.
- Keep the approved mockups and IA unchanged; record anything ambiguous as an open question.
- Sentence case and plain language in everything you write for Saqlain.

## Results
(The orchestrating session fills this in: per slice, PR link, verdict, screenshots shown, open questions answered, anything deferred.)
