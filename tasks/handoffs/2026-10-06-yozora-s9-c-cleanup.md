# Yozora S9 group C: allow-list pruning and Tailwind retirement

**Status: NOT DISPATCHED.** **Worktree:** `../cyberassess-yozora-s9-c`, branch `codex/yozora-s9-cleanup` (off `codex/yozora-s9` after the scaffold). One of three parallel Codex builds.

## Goal
Empty the lint allow-list as far as is honest, convert residual Tailwind utility classes in non-print templates, and retire the Tailwind build only if nothing needs it.

## You own
`tests/design_lint_allowlist.txt`, `tests/test_design_lint.py` (`MIGRATED_TEMPLATES`, add only), `app/templates/base.html` (Tailwind and `style.css` links only), `tailwind.config.js`, `package.json` scripts, `app/static/css/style.css`, and the residual-Tailwind templates. Not `app/main.py` (A), `app/static/js/app.js` or component CSS (B).

## Steps
1. Re-scan: list every template in `tests/design_lint_allowlist.txt` not in `MIGRATED_TEMPLATES`, and for each count Tailwind utility classes (text-, bg-, px-, py-, mt-, mb-, flex, grid, rounded, border-, w-, h-, gap-, etc.). Prior scan (6 Oct): about 30 allow-list entries are already migrated and stale; real residue is in `partials/questionnaire_tab.html`, `scope_complete.html`, `context_complete.html`, `section_questions.html`, `pages/assessment.html`, `clients.html`, `evidence_reuse.html`, `integrated_reports.html`, `partials/client_picker.html`, `followup_questions.html`, `questionnaire_sections.html`, `scope_form.html`; `reports/board_report.html` is a print template (out of scope).
2. Convert residual utility classes to existing Yozora classes/tokens. Mechanical and behaviour-preserving: no restyling beyond replacing a utility class, no changed ids, `hx-*` or `data-*`. If a template needs a layout decision, leave it listed and report it.
3. Remove stale entries from the allow-list; add the templates you finished to `MIGRATED_TEMPLATES`. Delete the allow-list file only if every non-print template then passes `tests/test_design_lint.py` (the test reads that file, so adapt the test minimally if you delete it, and say so).
4. Tailwind: scan `app/templates` (print templates included) and `app/utils`/services that render HTML for Tailwind utilities and for `tailwind.css`/`style.css` links. Remove the `base.html` links, `tailwind.config.js` and npm scripts only if no non-print template and no print template loads or needs them; otherwise keep the build and list each remaining user. Never edit the print templates. If removal breaks a template, restore it and list the template.
5. Add migration-map rows (`docs/product/yozora-migration-map.md`) for anything you converted.

## Read first
`tasks/handoffs/2026-10-06-yozora-s9-orchestration.md` (run rules, scoping decisions; they override the 3 Oct brief `2026-10-01-yozora-s9-handoff.md`, which you also read for must-keeps and tests), `docs/product/yozora-design-system.md`, `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/NEEDS-b7.md`.

## Rules
- Edit CSS only in `design/yozora-components.css` / `design/yozora-patterns.css` (source), then `python -m design.tokens_tool build` and `npm run css:build`; never edit only `app/static/css/yozora-*.css`.
- Do not game the gate: no padding or magic numbers to match a mockup, no hard-coded mockup copy. You cannot run the pixel gate (sandbox cannot bind localhost) and must not try; the orchestrator runs it once. Record anything the mockup omits as an exception (cause, evidence) in Results as you go.
- Never delete or weaken a test or guard. Add your files to `YOZORA_S9_PATHS` (add only).
- Never touch models, services, prompts, scoring, PDF, migrations, `validation/companies/*/answer_key.json`, or `app/templates/reports/*`. Stop and write the question in Results if a must-keep cannot be kept or the work needs any of those.
- One visible `.btn.primary` per state, never a disabled primary. Sentence case. Framework names only where in scope. No `innerHTML` of server text (use `textContent`).
- Leave changes uncommitted (git staging is blocked in your sandbox); do not revert unrelated files; revert any stray `tasks/todo.md` edit. If `boto3` is missing, say so; the orchestrator runs the app-backed tests.
- Run what you can: focused tests, `tests/test_design_lint.py`, `python -m design.tokens_tool check`, Jinja parse of every template you change, `node --check` for JS.

## Results

### Implemented

- Re-scanned the allow-listed templates. The 12 named S9 candidates contain no Tailwind utility classes; `mt-lg`, `form-grid`, `grow`, `inline`, `ring`, `sr-only`, `static`, and similar names are existing Yozora classes/tokens. No residual template class conversion was needed, so no ids, `hx-*`, `data-*`, or layout behavior changed.
- Removed `tests/design_lint_allowlist.txt` and adapted `tests/test_design_lint.py` minimally: print templates under `app/templates/reports/` remain excluded, every non-print template is explicit in `MIGRATED_TEMPLATES`, and the guard now asserts complete non-print migration.
- Fixed the one remaining non-print lint exception in `pages/firm_settings.html`: the custom-accent fallback now reads `accent_presets.get('midnight')` instead of hard-coding the same Midnight token. Existing migration-map coverage already includes this template; no new migration row was needed.
- Retired the Tailwind link, `tailwind.config.js`, and the `css:build`/`css:watch` package scripts and dependency. The pre-retirement `npm run css:build` completed successfully. `style.css` and its base link remain because live HTMX indicator/swap behavior and the Evidence inventory drop-zone use it; no print template loads either stylesheet. The base `h-full` class remains as an inert legacy marker because this handoff limits `base.html` edits to stylesheet links.
- No print templates were edited. No guard files, `tasks/todo.md`, backend code, services, prompts, scoring, PDF, models, migrations, or validation answer keys were touched. No migration-map rows were added because no template was converted in this pass.

### Verification

- Focused: `OPENROUTER_KEY="" .venv/bin/pytest -q tests/test_design_lint.py tests/test_yozora_firm_settings.py tests/test_p6_9_file_set.py tests/test_p6_7b_add_to_rfi.py tests/test_p6_8_b2_docx_xlsx.py --no-header -p no:cacheprovider -W ignore` — **57 passed**.
- Full suite: `OPENROUTER_KEY="" .venv/bin/pytest -q --no-header -p no:cacheprovider -W ignore` — **1535 passed, 30 skipped** in 201.33s.
- `python -m design.tokens_tool check` — generated design files match `tokens.json`.
- `node --check app/static/js/app.js` — passed.
- Jinja parse of all **92** templates — passed.
- `git diff --check` and `package.json` JSON parse — passed.
- Pixel gate was not run, as required by the sandbox rule; the orchestrator runs the single gate pass. Print-template differences remain intentionally out of scope.
