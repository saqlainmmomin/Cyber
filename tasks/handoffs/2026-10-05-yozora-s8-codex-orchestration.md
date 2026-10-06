# Yozora S8 on Codex: split, dispatch and review

**Status: NOT DISPATCHED (5 Oct 2026). Waits on S7 (PR #113) merging; S6 (#110) is already on `main`.** **For:** a Claude session on Saqlain's machine that dispatches several Codex instances. **Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (GitHub `saqlainmmomin/Cyber`). **Merging and pushing are Saqlain's**; you dispatch, review and hand him exact `git push` and `gh pr create` commands.

This file **replaces the "who builds" section** of `2026-10-05-yozora-s8-orchestration.md` (that one said a Sonnet cloud thread builds). Saqlain now wants Codex to implement, split across several instances for quality. **Everything else in the old file stands**: its 12 scoping decisions and its collision rules are binding and are not repeated here. Read it first.

## Goal
Build S8 (Requests view, RFI page, report versions, statement of applicability, comparison, client-facing pages) as three parallel Codex builds plus a scaffold before and an integration after, then three independent review instances. **Done when** one S8 PR is open with Results filled in, the three reviews are triaged, gate numbers and exceptions are shown to Saqlain, and the suite is green.

## Read first
1. `tasks/handoffs/2026-10-05-yozora-s8-orchestration.md` (decisions, collision rules, review points).
2. `tasks/handoffs/2026-10-01-yozora-s8-handoff.md` (screens, must-keep ids, asserted strings, tests).
3. The Results sections of the S7 PR's handoffs, **especially `2026-10-05-yozora-s7-fix-pass.md`** (what the pixel gate can and cannot tell you, below).
4. Memory notes `feedback_codex_dispatch`, `feedback_subagent_model_budget`, `feedback_no_attribution`.

## Lessons from S7 that change how S8 is run
- **Fix pass cost hours for little.** Half the S7 misses were not fixable: required controls the mockup omits, copy that tests pin, shared shell, real data vs mockup text. So each builder **records those as exceptions as it goes** (cause, evidence), not in a later pass.
- **Never game the gate.** No padding, margins or magic numbers to match a mockup scaffold; no mockup copy hard-coded; no loosened thresholds. If the miss comes from a mockup-only scaffold, change the gate, not the app.
- **Use the right gate mode.** Full-page screens: `--content` (clips to `.page`, hides the mockup "State" row). Partial panels render outside `.page`: full-page compare, expect a ~0.4% side-menu miss (Evidence is hidden on purpose, the review badge is live) and record it once as a shell exception.
- **Gate only what you touched.** About 35 to 40 s per state. Run groups in parallel with separate `--out` dirs. Never wait with `pgrep -f`: launch with `& echo $!`, wait with `while kill -0 <PID>`. macOS has no `timeout`.
- **Layout-identical but 1px paint shift** can happen; check element rects (probe) before editing CSS, and do not chase it.
- **Commit before the final suite run.** Three-dot file-set guards only see commits, and an untracked handoff file passes locally then fails CI. Add every new file (including handoffs) to `YOZORA_S8_PATHS` in `tests/yozora_paths.py` (add only).

## Phases
| Phase | Who | What | Branch / worktree |
|---|---|---|---|
| 0 Scaffold | one Codex instance | `seed_s8.py` base + CLI, `gate_s8.py` (copy of `gate_s7.py` with S8 mockups/seeds), `app/routers/design_s8_*.py` auto-import hook if `design.py` lacks it, `YOZORA_S8_PATHS` stub wired into `YOZORA_ALL_PATHS`/`YOZORA_EXCLUDES`, S8 templates added to `MIGRATED_TEMPLATES` in `tests/test_design_lint.py`. No template changes. | `codex/yozora-s8` in `../cyberassess-yozora-s8` |
| 1 Build | three Codex instances in parallel | groups A, B, C below, one file each | `codex/yozora-s8-requests`, `-versions`, `-client` off `codex/yozora-s8`, worktrees `../cyberassess-yozora-s8-{a,b,c}` |
| 2 Integrate | one Codex instance | merge the three branches into `codex/yozora-s8` (keep both sides in `web.py`, `magic.py`, `yozora-patterns.css`, `yozora_paths.py`), guards, full suite, full gate, migration-map rows, Results | `codex/yozora-s8` |
| 3 Review | three Sonnet 5.5 subagents (read-only), one per group, triaged by you | adversarial pass per the old file's Review section; each reports findings only | no branch |
| 4 Fix | Codex, one short run per accepted finding batch | fixes, re-gate touched screens, re-run suite | `codex/yozora-s8` |

Phase 1 groups own disjoint files, so they cannot collide except in `app/routers/magic.py` (A: consultant side, C: client side; different functions) and the shared files named in Phase 2. Do not start Phase 1 before Phase 0 is committed: the groups branch from it.

## Group briefs (each Codex instance is told to read exactly one)
- `tasks/handoffs/2026-10-05-yozora-s8-a-requests.md`: Requests page, RFI page, magic-link partials, removal of magic links and AWS link from the Overview, Evidence seg re-point.
- `tasks/handoffs/2026-10-05-yozora-s8-b-versions.md`: report versions, statement of applicability (one Save), comparison.
- `tasks/handoffs/2026-10-05-yozora-s8-c-client.md`: client upload page, invalid/expired/revoked page, 390 gate.

## Pre-flight
```bash
cd /Users/saqlainmomin/dpdpa-gap-tool
git fetch origin && git merge --ff-only origin/main        # S7 must be on main
git worktree add ../cyberassess-yozora-s8 -b codex/yozora-s8 origin/main
cd ../cyberassess-yozora-s8
ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv .venv
cp /Users/saqlainmomin/dpdpa-gap-tool/.env .env
ln -s /Users/saqlainmomin/dpdpa-gap-tool/node_modules node_modules   # untracked symlink, never commit
npm run css:build
cp /Users/saqlainmomin/cyberassess-s8-handoff/tasks/handoffs/2026-10-05-yozora-s8-*.md tasks/handoffs/   # until the handoff PR is on main
```
Record the baseline full suite there (`OPENROUTER_KEY="" .venv/bin/pytest -q --no-header -p no:cacheprovider -W ignore`, about 3 to 4 minutes). `test_p6_8_board_report_v2::test_scenario_3` is flaky: re-run before blaming S8. For Phase 1, after committing Phase 0:
```bash
for g in a:requests b:versions c:client; do k=${g%%:*}; n=${g##*:}
  git worktree add ../cyberassess-yozora-s8-$k -b codex/yozora-s8-$n codex/yozora-s8
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/.venv ../cyberassess-yozora-s8-$k/.venv
  cp .env ../cyberassess-yozora-s8-$k/.env
  ln -s /Users/saqlainmomin/dpdpa-gap-tool/node_modules ../cyberassess-yozora-s8-$k/node_modules
done
```

## Dispatch
Default `-m gpt-5.6-luna -c model_reasoning_effort="xhigh"` (sol/medium only if Saqlain says so, and then review harder). Always `< /dev/null`. Never two runs in one directory. Example (Phase 1, group A; B and C identical with their paths):
```bash
nohup codex exec -C /Users/saqlainmomin/cyberassess-yozora-s8-a -m gpt-5.6-luna -c model_reasoning_effort="xhigh" "Read tasks/handoffs/2026-10-05-yozora-s8-a-requests.md and execute it. Write your results to its Results section." < /dev/null > /private/tmp/claude-501/s8-a.log 2>&1 & echo $!
```
Phase 0 prompt: "Read tasks/handoffs/2026-10-05-yozora-s8-codex-orchestration.md, section Phases row 0, and tasks/handoffs/2026-10-05-yozora-s8-orchestration.md decision 10, and build only the scaffold. Commit it. Do not touch any template." Phase 2 prompt: "Read tasks/handoffs/2026-10-05-yozora-s8-codex-orchestration.md section Phases row 2 and execute it; the three group Results sections are your inputs."

Watch for stalls: if a log has not moved in 15 minutes, check `ps`, kill and restart that one run. Use a Monitor on log mtime, not sleep chains. Tell Saqlain up front that a Phase 1 build is roughly 1 to 2 hours per group and the gates add about 10 minutes each.

## Review (Phase 3), what each subagent gets
The matching group brief, the old file's Review section (must-keep extraction diff on every template edited, round trips over HTTP, privacy, adversarial pass), and the group's Results. Findings come back as a list (file, line, failure scenario); you triage. Do not trust any Results table: re-run the touched gates and the suite yourself.

## Constraints
No attribution lines in any commit or PR (merge commits too). Commits authored as Saqlain Momin. Never read `validation/companies/*/answer_key.json`. Never touch scoring, the analyzer, prompts, the v2 flag, PDF code, models or migrations; stop and ask instead. Sentence case. Keep the temporary `reviewer-name` input. Free-text requested items, no tick-box picker. One visible primary per state. Framework names only where in scope. Toasts are headers-only (S9).

## Hand Saqlain
```bash
git -C /Users/saqlainmomin/cyberassess-yozora-s8 push -u origin codex/yozora-s8
```
```bash
gh pr create --repo saqlainmmomin/Cyber --head codex/yozora-s8 --base main --title "Yozora S8: requests, RFI, report versions, applicability, comparison and client pages" --body "<what, gate numbers, suite line, guards touched, exceptions>"
```
Then S9 (system states, toasts, dark and mobile pass, `b7-dark-dense`).

## Results
(Filled in by the orchestrating session: PR link, review verdicts, gate table with exceptions, questions answered.)
