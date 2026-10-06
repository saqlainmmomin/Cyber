# Yozora S9 fix pass (6 Oct 2026)

Branch `codex/yozora-s9` (merged A+B+C). Functional fixes only, from the three read-only reviews; no pixel work. Same rules as the S9 group briefs: CSS only in `design/*.css` then `python -m design.tokens_tool build`; never weaken a guard; no backend/model/prompt/scoring/PDF/migration changes; no `innerHTML` of server text; leave changes uncommitted; revert stray `tasks/todo.md` edits. Fill Results at the bottom.

## Must fix (group B, `app/static/js/app.js`)
1. **Skeleton and error swap must never destroy content.** Today after 300 ms the skeleton does `target.replaceChildren(...)` and cleanup never restores it; `requestError` replaces the target with an alert on every 4xx/5xx. Effects: the 21 `hx-swap="none"` forms (target resolves to the form itself) are wiped by any request over 300 ms or any no-swap response; a 422 replaces a form and its typed input with an alert; narrative generate (200 JSON on LLM failure, no `HX-Redirect`) leaves a blank form. Fix: render the skeleton only for targets that will actually receive swapped content (not `hx-swap="none"`, not when the target is the triggering form/body), as an overlay or sibling that is removed on cleanup, never by replacing children. Show the `.alert` only where swapped content would have gone; otherwise toast only (the old behaviour).
2. **`hx-boost` on `<body>`** (`base.html:41`): boosted navigation and boosted form POSTs target `<body>`. Never skeleton or alert-replace `<body>` or `html`; for boosted requests, a slow load shows nothing destructive (a top progress cue is fine) and a 4xx/5xx gives a toast and leaves the page intact. Make sure htmx history snapshots never capture a skeleton or alert state (clean up before `htmx:beforeHistorySave`).
3. **SVG icons**: `toastIcon` and `swapAlert` use `document.createElement('svg'|'use')` (HTML namespace, nothing renders; the error toast's dismiss button is blank). Use `createElementNS('http://www.w3.org/2000/svg', ...)` and `setAttributeNS('http://www.w3.org/1999/xlink','href',...)` or `href`. Add a test that executes the JS in a minimal DOM if `node` with jsdom is not available: otherwise a documented manual check recorded in Results.
4. **Error flood**: every error fires a persistent error toast AND an alert (message twice); polling partials (`analysis_running`, `desk_review_running`, `every 3s`) stack a new never-expiring toast every 3 s while the server is down. De-duplicate identical toasts (same kind and message already visible: refresh instead of stacking) and cap the stack (oldest dismissed beyond 4).
5. **Modals/menus**: call `refreshModalLock()` on `htmx:load`/`afterSettle` and remove the lock when no modal is open after a swap; a click on a `[data-modal-open]` or `hx-post` item inside `.anchor .menu` must close the menu before the modal opens (focus returns to the modal opener on Esc).
6. `requestButton`: do not fall back to `document.activeElement` for non-button triggers (polls and `change` autosaves must not put `.loading` on an unrelated button).
7. `toast()`: map unknown `X-Toast-Type` to the neutral information style, not success.
8. `.htmx-settling` fade for `outerHTML` swaps: add `swap-in` to the new element (not the detached old target) or drop the opacity-0 settle so there is no blink. Verify by reading htmx 2.0.4 swap order, not by pixels.

## Must fix (group A, `app/main.py`, `pages/error.html`)
9. Log line: write the path with `%r` (or `scope["raw_path"]`) so a client cannot forge `reference=` text; add a test.
10. "Go back" must go back (`history.back()` with a `href` fallback to the previous safe page, no inline `onclick`: wire it in `app.js`) or be removed; "Try again" must not rely on an inline `onclick` either (use a data attribute handled in `app.js`; for a failed POST landing here, prefer a link to the referring page over reload).
11. Preview copy in `app/routers/design_s9_errors.py`: remove hard-coded framework names ("ISO 27001:2022", "DPDPA 2023") and mockup dates from the preview text, or make them neutral.

## Must fix (group C)
12. `package-lock.json` still lists `tailwindcss` and ~890 lines of tree while `package.json` has no dependencies (`npm ci` fails). Delete `package.json` and `package-lock.json` only if nothing references them (grep scripts, docs, CI, `.github`, Dockerfile); otherwise regenerate the lockfile to match. Also delete orphans: `app/static/css/input.css`, `tailwind.tokens.cjs` and its generation in `design/tokens_tool.py` (keep `tokens_tool check` passing; update the in-sync test minimally and say so), the `.gitignore` tailwind entry, and the stale comment at `app/static/css/src/shell.css:23-25`.
13. Bare `<ul>` lost its reset: `pages/narrative.html:63` and `pages/review_queue.html:58` (`rq-claims`) now show default discs outside the box. Add a minimal rule in `design/yozora-patterns.css` (list-style/padding) for those two.
14. `app/templates/base.html` still has the inert `class="h-full"`; leave it.

## Do not do
Convert the JS-injected Tailwind classes in `app.js` (the `?` shortcut modal, dashboard filter, save-indicator colours): they predate S9 (the old Tailwind build never scanned JS). List them in Results as a known follow-up with line numbers.

## Verify
Full suite (`OPENROUTER_KEY="" .venv/bin/pytest -q --no-header -p no:cacheprovider -W ignore`; if `boto3` is missing say so and the orchestrator runs it), `tests/test_design_lint.py`, `tokens_tool check`, `node --check app/static/js/app.js`, Jinja parse of changed templates. Add tests for 9 and (structurally) 1 to 4 where an executed test is possible.

## Results
(Codex fills in.)
