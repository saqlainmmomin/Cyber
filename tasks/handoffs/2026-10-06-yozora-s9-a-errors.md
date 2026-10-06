# Yozora S9 group A: error pages and empty states

**Status: NOT DISPATCHED.** **Worktree:** `../cyberassess-yozora-s9-a`, branch `codex/yozora-s9-errors` (off `codex/yozora-s9` after the scaffold). One of three parallel Codex builds.

## Goal
404 and 500 pages with a reference code, and the empty states, so no route returns a bare JSON or default error page to a browser.

## You own
`app/main.py` (exception handlers only), new `app/templates/pages/error.html`, empty-state macro usage in templates that have none yet, the `design_s9_errors` preview module, tests. Not `app/static/js/app.js` or component CSS (group B) and not allow-list or Tailwind files (group C). Component CSS you need and B does not own (error page layout) goes in `design/yozora-patterns.css` in a delimited `/* S9 errors */` block.

## Mockups and states
`b7-404`: page, engagement. `b7-500`: error, down, upstream. `b7-empty-states`: engagements, evidence, review, search, findings, report (check which pages already render them; do not rebuild finished S3 to S8 empty states, only fill gaps and list them).

## Specifics
- Handlers for 404, 500 and a catch-all render `pages/error.html` for browser (HTML) requests. `/api/...` and `Accept: application/json` keep today's JSON body, unchanged.
- Reference code: short random id (not derived from the request), shown on the page, and logged with the request path and exception class. Never show the exception message or a stack trace to the user. Validation errors (422) on form posts must not regress.
- Engagement-scoped 404: when the path begins with `/engagements/<id>` show a link back to engagements; never confirm whether that engagement exists.
- `down` and `upstream` are 500 variants (database or LLM provider unavailable): choose by exception type only if a clean, existing type exists; otherwise render `error` for all and record `down`/`upstream` as preview-only states.
- Tests: 404 and 500 (forced exception) show a reference code; the logged record contains it and the path; JSON stays JSON; no exception text in the body; engagement 404 identical for existing and missing ids.
- Add `pages/error.html` to `docs/product/yozora-migration-map.md`.

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

Implemented the S9 group-A error and empty-state work.

- Added browser HTML exception handlers in `app/main.py` for 404, explicit 500, and unhandled exceptions. API paths and `Accept: application/json` retain JSON responses; validation errors remain unchanged.
- Added random `xxxx-xxxx-xxxx` reference codes, rendered them in `pages/error.html`, and logged each reference with request path and exception class. Exception messages and tracebacks are never included in the response body.
- Engagement-scoped 404s use the same generic response for existing and missing IDs and link only to `/engagements`; they do not disclose engagement existence.
- Added `app/templates/pages/error.html` with one primary action per state and reused existing Yozora shell/component styles. Added the delimited `/* S9 errors */` source CSS block and regenerated `app/static/css/yozora-patterns.css`.
- Added `app/routers/design_s9_errors.py` and `design/harness/seed_s9_errors.py` for `b7-404`, `b7-500`, and `b7-empty-states`. `down` and `upstream` remain preview-only, as no clean existing runtime exception types were available.
- Verified the six requested empty states (`engagements`, `evidence`, `review`, `search`, `findings`, `report`) already existed in the S3-S8 live templates; previews reuse those routes and no finished state was rebuilt.
- The `pages/error.html` migration-map row was already present in `docs/product/yozora-migration-map.md` before this change, so no duplicate edit was made.
- Added focused S9 tests and retained the S9 path allow-list entry. `tasks/todo.md` was not changed.

Verification:

- `.venv/bin/pytest -q --no-header -p no:cacheprovider tests/test_yozora_s9_errors.py` — 7 passed.
- `.venv/bin/pytest -q --no-header -p no:cacheprovider tests/test_yozora_s3.py tests/test_yozora_s6.py tests/test_yozora_s7_findings.py tests/test_yozora_s9_errors.py` — 44 passed.
- `.venv/bin/pytest -q --no-header -p no:cacheprovider tests/test_design_lint.py tests/test_design_tokens_in_sync.py` — 9 passed.
- `.venv/bin/python -m design.tokens_tool check` — generated files match `tokens.json`.
- Jinja parse of `app/templates/pages/error.html` — passed.
- `.venv/bin/python -m design.harness.seed_s9 --list` — lists all 11 required S9 states.
- `.venv/bin/pytest -q --no-header -p no:cacheprovider` — 1542 passed, 30 skipped, 458 warnings in 3:16.

The default system Python lacks `boto3`; verification used the repository `.venv`, where `boto3` is installed. The pixel gate was not run because the handoff explicitly prohibits localhost binding in this sandbox; the orchestrator should run it once. Changes remain uncommitted.
