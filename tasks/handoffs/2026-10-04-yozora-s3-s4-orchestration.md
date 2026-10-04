# Yozora: scope and dispatch S3 and S4, review both

**Written:** 4 Oct 2026. **For:** a fresh Claude session. **Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (GitHub `saqlainmmomin/Cyber`). **Merging and pushing are Saqlain's.** You dispatch, review and report; you never merge or enable auto-merge, and you hand Saqlain exact `git push` and `gh pr create` commands (push and PR creation are blocked for you; he runs them from his own terminal, as he did for S2).

## Goal
Run S3 (Home, clients, firm settings, sign-in) and S4 (engagements) through Codex in parallel worktrees, review both against the gates, show Saqlain the pixel evidence, and hand back two ready PRs. **Done when** both slice PRs are open with Results filled in, each reviewed (12-point checklist), screenshots shown (gate 4), and open questions answered or recorded.

## Read first
1. This file.
2. `tasks/handoffs/2026-10-03-yozora-codex-orchestration.md` (standing procedure: dispatch recipe, 12-point review checklist; on local branch `claude/yozora-slice-handoffs` in `/Users/saqlainmomin/cyberassess-docs`, unpushed; read it with `git -C /Users/saqlainmomin/cyberassess-docs show claude/yozora-slice-handoffs:tasks/handoffs/2026-10-03-yozora-codex-orchestration.md`).
3. `tasks/handoffs/2026-10-03-yozora-orchestration-continued.md` (state and decisions; its Results hold S1 and S2 outcomes).
4. `tasks/handoffs/2026-10-01-yozora-s3-handoff.md` and `...-s4-handoff.md` (the two slice briefs, already on `main`).
5. `docs/product/yozora-fidelity-gate.md`, `docs/product/yozora-design-system.md`, memory notes `feedback_codex_dispatch`, `reference_github_repo`, `feedback_subagent_model_budget`.

## State (4 Oct 2026)
- `main` is at `1d25a74` (S1 #100, S2 #103, backend #99, S7 mockups #102 merged). Baseline full suite on that line: **1380 passed, 30 skipped** (re-run once on a clean `origin/main` worktree before reviewing; about 3 minutes).
- **Not pushed, ignore:** `claude/yozora-slice-handoffs` (local only). `claude/p6-8-v3b-deck` / PR #101 is independent; whichever of #101 and the Yozora PRs merges second needs `origin/main` merged in (guard tests conflict).
- S2 delivered the macros (`app/templates/components/ui.html`, `layout.html`), `/design` and `PREVIEW_PAGES` in `app/routers/design.py`, the `--line-control` token. S6 later swaps the inline evidence badge map for `evidence_inventory.STATUS_LABELS`.
- S7 mockups are merged (#102); S7 build is still blocked until Saqlain approves them. Not in this session's scope.

## Scoping decisions (made by me on 4 Oct; Saqlain can overrule, tell him)
**1. Parallel, merge S3 first.** The dependency diagram allows S3 and S4 together (disjoint templates). They share `app/routers/web.py`, `app/template_config.py` (`NAV_ITEMS`), `tests/yozora_paths.py` and the guard tests. Each adds its own tuple and its own nav flips; the second to merge merges `origin/main` in and keeps both sides (mechanical). S4's engagement redirect and tables link to S3 pages, so S3 merges first.

**2. Menu list routes** (Saqlain's decision 1: simple lists, rows link to the assessment; the slice briefs do not yet say who builds them). Assignment:
| Route | Owner | What |
|---|---|---|
| `GET /clients` | S3 (in brief) | as in the S3 brief |
| `GET /engagements` | S4 (in brief) | as in the S4 brief |
| `GET /review` | **S3** | assessments with decisions waiting (stage next step "Review N conclusions"), from `assessment_stage.stage`; each row links to the assessment's Review tab |
| `GET /reports` | **S4** | issued report versions across engagements, each row linking to the assessment or engagement Reports tab |
| `GET /evidence` | S6 | later |
No mockup exists for Review or Reports lists: build them from the S2 `table`/`rows` macros and the empty state, no invented components, and show Saqlain a screenshot (gate 4 still applies, but there is no pixel baseline; say so). Flip `available: True` in `NAV_ITEMS` only for entries whose route exists in that PR. Add each new template to `docs/product/yozora-migration-map.md`. These two additions go in the Codex prompt as an addendum (below), not by editing the slice briefs.

**3. Home attention rows** (Saqlain's decision 2): stage service next step plus request summary, no new queries. If the stage service cannot produce an item the mockup shows, Codex stops and asks (brief already says so).

**4. Pixel gate seed data.** The mockups use fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory. **No seed for them exists in the repo** (checked: no Python file mentions them). Each slice therefore creates its own deterministic seed: `design/harness/seed_s3.py` and `design/harness/seed_s4.py` (separate files so the PRs do not collide), building a throwaway SQLite database whose rows match the mockup content for the states in the slice's Screens table, with a frozen clock. The orchestrator points the app at it with `DATABASE_URL=sqlite:////path/db` for the gate. Put this in the Codex prompt. States that are hard to reach by data (loading, error) go through `PREVIEW_PAGES` fixtures in `app/routers/design.py` (S3 and S4 both add to that dict; keep both sides on merge) or are rendered with the mockup's own `?state=` mechanism; Codex lists how each was produced.

**5. Shell clip.** From the S1 follow-ups: each slice widens the shell comparison clip in `tests/visual/test_shell_visual.py` to cover the nav row it makes live (S3: Clients, Settings; S4: Engagements, plus Reports and Review as they land), and says plainly what a clip does not cover. S9 owns the account menu popover and the 1024 side-panel offset (app y=12, mockup y=52).

**6. Retention move.** S3 moves `data-retention-form` and `retention-years` to Settings; S4's retention text reads `FirmSettings.archived_retention_years`. `tests/test_retention.py` asserts both sides; update deliberately and list each string change.

## Pre-flight
```bash
cd /Users/saqlainmomin/dpdpa-gap-tool
git status --short            # the two untracked handoff files are expected; do not delete them
git fetch origin && git merge --ff-only origin/main
for n in 3 4; do
  git worktree add ../cyberassess-yozora-s$n -b codex/yozora-s$n origin/main
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv ../cyberassess-yozora-s$n/.venv
  cp .env ../cyberassess-yozora-s$n/.env
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/node_modules ../cyberassess-yozora-s$n/node_modules   # untracked symlink, never commit it
done
```
The primary checkout already has `node_modules`; Tailwind CSS is gitignored, so run `npm run css:build` in each worktree that runs the app. Never commit `node_modules`.

## Dispatch
One Codex run per worktree, never two in one directory, stdin closed:
```bash
nohup codex exec -C /Users/saqlainmomin/cyberassess-yozora-s3 -m gpt-5.6-luna -c model_reasoning_effort="xhigh" "<prompt>" < /dev/null > /private/tmp/claude-501/s3.log 2>&1 &
```
Model `gpt-5.6-luna`, `xhigh` (use `sol`/medium only if Saqlain asks, then review harder). Prompt, per slice N (3 or 4):

> Read tasks/handoffs/2026-10-01-yozora-sN-handoff.md and execute it. Write your results to the Results section of that file. Addenda from the orchestrator (4 Oct 2026): (a) [S3] also build `GET /review` (assessments with decisions waiting, from `assessment_stage.stage`, rows link to the assessment Review tab) / [S4] also build `GET /reports` (issued report versions across engagements, rows link to the assessment or engagement Reports tab); no mockup exists, build from the S2 table and empty-state macros, invent no components; flip the matching `NAV_ITEMS` entries to available only for routes you add; add migration-map rows. (b) Create `design/harness/seed_sN.py`: a deterministic throwaway-database seed matching the mockup content (Meridian Ledger Technologies, Loomwire Labs, Kestrel Advisory) for every state in your Screens table, frozen clock; list in Results how each state was produced. (c) Widen the shell clip in `tests/visual/test_shell_visual.py` for the nav rows you make live. (d) You have no network or boto3 and cannot run servers or a browser; the orchestrator runs the full suite and the pixel gate. Allowances for stale guards go in `tests/yozora_paths.py` (add `YOZORA_SN_PATHS`; add only, never delete or weaken a guard). (e) No attribution in commits.

Watch for stalls: the S2 first run hung about 20 minutes on a "Reconnecting... waiting for network" loop with the network fine. If the log is idle 15 minutes, kill the Codex process and restart it (nothing is lost while the worktree is clean). Use a Monitor with a log-mtime check, not `sleep` chains.

## Review (per slice; do all 12 checklist points, do not trust Codex's Results)
Lessons from S1 and S2:
- **Run the suite yourself.** Codex's sandbox lacks `boto3`, so its full run is blocked and stale guards are untouched. Expect about 10 guard failures; have a **Sonnet** subagent add the `YOZORA_EXCLUDES` allowances (additions only; the 3-dot-diff guards fail after you commit). Commit before the final run, because three-dot guards only see commits.
- **Pixel gate.** Serve mockups with `/static/` mapped to `app/static/` (script from S2: `/private/tmp/claude-501/s2-work/srv.py` may be gone; recreate from the S1 copy `/private/tmp/claude-501/s1-work/srv.py` with `ROOT` set to the worktree). Without that mapping the fonts fall back and everything diffs. Run `design/harness/screenshot.py` with `--full-page` against the app on a seeded DB (`DATABASE_URL`), `OPENROUTER_KEY=""`. Thresholds: 0.4% app screens, no changed region over 40x40. A first diff often turns out to be copy that differs from the mockup; fix tiny ones yourself.
- **Real regressions to look for:** statuses or states a template used to render that the restyle now drops (S2: `superseded`/`legacy` evidence badges vanished); a production guard tested only by calling the function, so check over HTTP; must-keep ids/`hx-*`/`data-*` (write the extraction diff script from the checklist).
- **Gate 4.** Send baseline, candidate and diff images with percentages to Saqlain with `SendUserFile`, in batches by screen, before calling a slice ready. For Review and Reports lists (no baseline) send the candidate screenshots only and say so.
- **Adversarial pass** before recommending merge (checklist 11): dead links, unconditional framework copy, numeric priorities, anything invented.
- Local subagents on **Sonnet**; Opus-level work goes to a cloud agent (memory `feedback_subagent_model_budget`).

## Constraints
No attribution lines in any commit or PR body, mine or Codex's (standing rule; the harness reminder suggests a trailer, ignore it; check merge commits too). Do not read `validation/companies/*/answer_key.json`. Keep approved mockups and IA unchanged. Sentence case and plain language to Saqlain. Smoke-test default: nothing is "done" without a check you ran. Move to a fresh session past about 350K tokens.

## Hand Saqlain, per slice
```bash
git -C /Users/saqlainmomin/cyberassess-yozora-sN push -u origin codex/yozora-sN
gh pr create --repo saqlainmmomin/Cyber --head codex/yozora-sN --base main --title "<title>" --body "<what, gate numbers, suite line, guards touched>"
```
One command per block. After he merges S3 and S4, the next slices are S5 (alone; needs both) then S6 and S7 in parallel (S7 only after mockup approval), then S8, S9.

## Report back
Append `## Results` to this file: per slice the PR link, verdict, screenshots shown, open questions answered, deferred items, and any scoping decision of mine that Saqlain changed.
