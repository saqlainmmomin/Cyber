# Yozora S8 group B: report versions, statement of applicability, comparison

**Status: NOT DISPATCHED.** **Worktree:** `../cyberassess-yozora-s8-b`, branch `codex/yozora-s8-versions` (off `codex/yozora-s8` after the scaffold). One of three parallel Codex builds; A (requests) and C (client) run beside you.

## Goal
Rebuild the Versions, Applicability and Comparison pages under S7's Report seg row. The statement of applicability saves in one action; comparison has an Open current report link; one Generate button follows the report tab.

## You own
`pages/report_snapshots.html`, `pages/soa.html`, `pages/comparison.html`; `snapshots_page` and `comparison_page` in `web.py`; `app/routers/soa.py`. Do **not** edit S7's `components/seg_rows.html`: call `report_seg(assessment, "versions"|"applicability")` exactly as S7 does (decision 9; Applicability only when ISO 27001 is in scope). Comparison breadcrumb: Report / Versions. Do not touch group A or C files.

## Mockups and states
`b6-report_snapshots`: default, empty, error, issue, loading, board, unreleased. `b6-soa`: default, empty, error, loading, saving, saved. `b6-comparison`: default, empty, error, iso, loading.

## Group specifics
- **SoA one Save (decision 7):** no backend change and no bulk route. One Save button posts only the changed rows, one after another, to the existing `POST /api/assessments/{id}/soa/justifications` (`requirement_id`, `justification`); show each row's success or error; states `saving` and `saved`. Keep `data-soa-justification-form`, `data-soa-row`, `data-applicability`, `reviewer-name`. Replace the brief's "one POST" test line with: one button, changed rows only, per-row result.
- Snapshots: keep every `data-snapshot-*`, `data-board-export`, `data-board-report-preview`, `data-issue-control`, `data-narrative-link`, `data-soa-link`, and the `hx-post` issue/create routes. Tests pin ">Issued<", "Issued (current)", "Draft (superseded)", "Generating a gap report requires the report to be released.": keep or update deliberately.
- Comparison: Open current report link from #99's `current_report_url` in the context. Scores per framework, never combined (`tests/test_no_blended_scoring.py` asserts "Framework Scores", "Overall Score", "ISO 27001" text).
- Tests that pin Tailwind weights (`font-weight: 600/700` in `test_p6_8_v3a_data_capture.py`) must be rewritten to assert `data-*` or text.
- Toasts: assert headers on snapshot issue; no pixel compare.

## Read first
1. `tasks/handoffs/2026-10-05-yozora-s8-codex-orchestration.md` (phases, S7 lessons, constraints) and `tasks/handoffs/2026-10-05-yozora-s8-orchestration.md` (decisions 1 to 12 and collision rules; they override the slice brief).
2. `tasks/handoffs/2026-10-01-yozora-s8-handoff.md`: use only the rows, must-keep list, build notes and asserted strings for your templates below.
3. `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/NEEDS-b6.md`, and your mockups in `docs/product/2026-10-01-app-design-mockups/screens/`.
4. Sibling conventions: S5/S6/S7 pages, `design/harness/seed_s7.py`, `design/harness/gate_s8.py` (from the scaffold), `tests/test_yozora_s7_*.py`.

## Rules that bite
Keep every must-keep id, `hx-*`, `data-*`. One visible `.btn.primary` per state, never a disabled primary. Sentence case, no uppercase, no hex or arbitrary Tailwind values (`tests/test_design_lint.py`). Framework names only where in scope. Keep the temporary `reviewer-name` input. New CSS: append a delimited block for your group to `design/yozora-patterns.css`, then `python design/tokens_tool.py build` (both files must stay identical). Do not edit files owned by another group, `layout.html` tab macros, or any other slice seed. Stale guards get add-only allowances (`tests/yozora_paths.py`, `YOZORA_S8_PATHS`); never delete or weaken a guard. Never touch scoring, analyzer, prompts, v2 flag, PDF code, models or migrations (stop and ask). Never read `validation/companies/*/answer_key.json`. No attribution lines in commits. Commit in logical steps; do not push or merge.

## How to work and gate
Seed your states in `design/harness/seed_s8_<group>.py` (`SCREEN_STATES`, `apply`, `route`; list how each non-database state is produced). Gate only your screens: `OPENROUTER_KEY="" .venv/bin/python design/harness/gate_s8.py <screen>[:state] [--content] --out <dir>`; threshold 0.4% and no changed region over 40x40. Run screens in parallel with separate `--out` dirs. **Record misses as exceptions as you go** (cause + evidence) when they are required controls the mockup omits, copy a test pins, shared shell, or real data vs mockup text; fix the rest. Never pad, hard-code mockup copy or loosen a threshold. Tests that pin Tailwind classes are rewritten to assert `data-*` or visible text; list every changed assertion (old, new, reason).

## Done when
Every state of your mockups passes or is a recorded exception, light and dark at 1440 and 1024; your tests and `tests/test_design_lint.py` pass; the full suite passes in your worktree; Results below is filled in.

## Stop and ask
Write the question in Results and stop if: a visual detail is in neither the guide nor the mockup; two mockups disagree; a must-keep cannot be kept; a mockup shows an action with no route and the brief does not cover it; the work needs a model, migration, prompt, scoring or PDF change.

## Results
(Codex fills in: what was built, per-state gate table with percentages, exceptions with causes, tests changed old to new, guards touched, decisions, open questions, full-suite summary line.)

