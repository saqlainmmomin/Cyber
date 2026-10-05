# Yozora S7: Codex handoff (continue from the Claude scaffold)

**For:** Codex, run with subagents (one per group below, in parallel). **Repo:** `saqlainmmomin/Cyber`, branch `claude/yozora-s7-a7a3f7` (off main at #111). Saqlain merges; do not merge. No attribution lines in commits or PR bodies.

Claude stopped on 5 Oct 2026 (Saqlain's call: out of Claude credits). Scaffold is committed; six groups were started and their unfinished work is saved as patches in `tasks/handoffs/s7-wip/<group>.patch`. **Treat the patches as untrusted drafts**: they were never gated or tested, and the `narrative` patch was stopped mid-repair (likely a mangled region in a template). Apply with `git apply --3way tasks/handoffs/s7-wip/<group>.patch` or just read them for ideas.

## Read first
1. `tasks/handoffs/2026-10-04-yozora-s7-orchestration.md` (scoping decisions, collision rules; wins over the brief).
2. `tasks/handoffs/2026-10-01-yozora-s7-handoff.md` (screens, must-keep ids / hx / data attributes, asserted strings, tests, guards).
3. `docs/product/yozora-design-system.md`, `yozora-fidelity-gate.md`, mockups in `docs/product/2026-10-01-app-design-mockups/screens/`.
4. Sibling conventions: `pages/desk_review.html`, `tests/test_yozora_s5.py`, `design/harness/seed_s5.py`.

## What the scaffold gives you (committed)
- `app/templates/components/seg_rows.html`: `review_seg(assessment, "queue"|"conclusions"|"findings"|"workpaper")` and `report_seg(assessment, "report"|"versions"|"applicability"|"narrative"|"board-inputs")` (Applicability only when ISO 27001 is in scope).
- `design/harness/seed_s7.py`: base data and CLI; each group adds `design/harness/seed_s7_<group>.py` with `SCREEN_STATES`, `apply(db, screen, state, assessment, engagement, data)` and `route(screen, state, assessment_id)`. `--list` shows registered states.
- `design/harness/gate_s7.py`: seeds a state, serves app and mockups (`/static/` mapped to `app/static/`), compares light/dark at 1440 and 1024 and appends to `<out>/results.md`. Run: `.venv/bin/python design/harness/gate_s7.py b5-xxx:state --out /tmp/s7-gate`. Chromium is preinstalled at `/opt/pw-browsers`; the gate works offline.
- `app/routers/design.py` auto-imports `app/routers/design_s7_*.py` so groups register `PREVIEW_PAGES` fixtures without sharing a file.
- All S7 templates are already in `MIGRATED_TEMPLATES` in `tests/test_design_lint.py` (so they must pass the lint: no uppercase, hex, arbitrary Tailwind values, lettered headings).
- Setup: Python 3.13 venv, `pip install -r requirements-dev.txt`, `npm ci && npm run css:build`. Known flake: `test_p6_8_board_report_v2::test_scenario_3`.

## Work split (one subagent each, separate worktrees, merge at the end)
| Group | Templates | Mockups and states |
|---|---|---|
| analysis | `partials/analysis_{running,complete,error,gate_blocked}.html`, `release_panel.html`, `report_basis_panel.html`, `review_finding_card.html` | b5-analysis (running, complete, error, error-all, gate, gate-no-override); b5-release (blocked, ready, confirm, released, stale); b5-basis (empty, filled, invalid, locked, saved); b5-review-finding-card (draft, needs-review, notes, accepted, rejected) |
| cards | `components/conclusion_card.html`, `requirement_card_body.html`, `partials/remediation_draft.html` | b5-requirement-card; b5-conclusion-card (11 states); b5-recommended-action (empty, drafting, drafted, edited, error, saved; toast states = header assertions only, add `X-Toast-Message` copy in `drafting.py::draft_recommended_action` where missing) |
| pages | `pages/review_queue.html`, `pages/conclusions.html` | b5-review-queue (default, shared, done, empty); b5-conclusions (default, legacy-bulk, empty). Re-gate after cards and analysis merge, since the card and panel regions come from them |
| findings | `pages/findings.html`, `components/finding_card.html` (also used by S4 pages: check `grep -rn finding_card app`) | b5-findings; b5-finding-card (9 states); b7-dark-dense (1440 dark is the gate) |
| report | `partials/report_tab.html`, `report_summary.html`, `remediation_panel.html`, `remediation_summary.html`, `no_report.html`, `framework_panel.html` | b5-report (released, not-released, loading); b5-no-report. Do not edit `pages/assessment.html` or `layout.html` |
| narrative | `pages/narrative.html`, `pages/board_inputs.html`, `app/routers/drafting.py` | b5-narrative (empty, generating, drafted, partly-accepted, accepted, not-released); b5-board-inputs (empty, partly, complete, dense, error). Generation failure and draft-limit toasts need `X-Toast-Message` copy from the mockup; busy = non-primary `.btn.loading` |

## Rules that bite
Keep every must-keep id, `hx-*`, `data-*`; one visible `.btn.primary` per state; sentence case; framework names only where in scope; keep the temporary `reviewer-name` input; keep `F1` finding aliases (record the mockup's `R-xx` as a copy exception); never touch scoring, analyzer, prompts, v2 flag, PDF code; never read `validation/companies/*/answer_key.json`. New CSS: append a delimited block to `design/yozora-patterns.css`, then `python design/tokens_tool.py build`. Toast states are header checks, not pixel checks (S9 restyles toasts).

## Finish line (the orchestrator tasks, not yet done)
1. Merge the group branches; resolve conflicts in `web.py` and `yozora-patterns.css` by keeping both sides.
2. Add `YOZORA_S7_PATHS` (every changed file outside `docs/product/` and `design/`) to `tests/yozora_paths.py` and into `YOZORA_ALL_PATHS`/`YOZORA_EXCLUDES`; run the full suite; for each stale scope guard splat `*YOZORA_EXCLUDES` (comment `# Yozora per-PR allowance`). Never delete or weaken a guard. `test_p6_10a_remediation_draft::test_scenario_9` already fails on the scaffold for this reason.
3. Update the three `docs/product/yozora-migration-map.md` rows (board inputs, narrative, remediation draft) to name their mockups.
4. Full suite, then the full gate over all states; record misses as real-data exceptions with reasons (do not loosen thresholds or hard-code mockup copy). Adversarial pass: unconditional framework copy, numeric priorities, more than one primary, combined cross-framework view.
5. Append `## Results` here (PR link, gate table, exceptions, tests changed old -> new, guards touched). One PR titled "Yozora S7: analysis, review, report, narrative and board inputs".
