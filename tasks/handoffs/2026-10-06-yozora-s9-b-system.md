# Yozora S9 group B: global behaviour and system components

**Status: NOT DISPATCHED.** **Worktree:** `../cyberassess-yozora-s9-b`, branch `codex/yozora-s9-system` (off `codex/yozora-s9` after the scaffold). One of three parallel Codex builds.

## Goal
The shared behaviour layer: toasts, skeletons, failed-swap handling, button loading, menus and popovers, modals, `[hidden]` guard, breadcrumb overflow.

## You own
`app/static/js/app.js`, `design/yozora-components.css` (and generated copy via the build), `app/templates/components/ui.html` macros, `app/templates/pages/design.html` specimens, the `design_s9_system` preview module, tests. Not `app/main.py` (A), not allow-list or Tailwind files (C). `app/templates/base.html` is shared: you may add the `.toasts` container and nothing else; C removes Tailwind links.

## Mockups and states
`b7-toasts` (all variants), `b7-skeleton-table` and `b7-skeleton-detail` (loading, loaded), `b7-htmx-swaps` (ok, bad), `b7-modals` (delete typed name, purge, send, invite, discard, failed), `b7-menus-popovers` (row actions, share, account menu; Esc closes, focus returns to the trigger), `b7-mobile-shell` (390; the shell itself is S1, only fix real breakage).

## Specifics
- Toasts: replace `CyberToast` (Tailwind strings, `innerHTML`) with a `toast(kind, message, action)` helper writing Yozora `.toast` markup into a `.toasts` container; success and information close after 4 s, errors stay until closed, stacked, Undo/action variant. Keep reading the existing `X-Toast-Message` (URL-decoded) and `X-Toast-Type` headers so every router keeps working; add a test that a response with those headers is still honoured (JS logic can be covered by a small node-free structural test or a documented manual check; say which).
- Existing `htmx:responseError` behaviour must stay: 401 redirects to `/login`; `X-Conclusion-Conflict` 409 responses still swap. A failed or errored swap shows an `.alert` in the target, never a blank.
- Skeletons: `.skel` placeholder after 300 ms for swaps, removed on settle; `.htmx-swapping`/`.swap-in` fade; `.btn.loading`. One global script, no per-template code.
- Menus/popovers: anchored variant with Esc to close and focus return, flip near the viewport edge. Modals: scroll lock, bottom sheet under 600px, typed-confirmation variant (destructive button disabled until the name matches; a disabled destructive is allowed, a disabled primary is not).
- Wire modals only where a template already has a confirm (`hx-confirm`, purge page); add no routes. `invite` and `send` have no route: component plus `/design` specimen only.
- `[hidden]{display:none!important}`; breadcrumb collapse at 390 (`hide-sm`).
- Do not add date picker, pagination or tooltips unless a migrated page already needs one; list as deferred.

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

Implemented the shared Yozora S9 behaviour layer and system-component previews.

- Replaced `CyberToast` with a global safe-DOM `toast(kind, message, action)` helper. It supports success/information auto-dismiss, persistent errors with dismiss controls, action buttons, URL-decoded `X-Toast-Message`/`X-Toast-Type` headers, 401 redirects, conclusion-conflict 409 swaps, failed-swap alerts, and network-error alerts.
- Added one global HTMX interaction layer for 300 ms skeletons, button loading state, swap transitions, anchored menus/popovers with Escape/focus return/viewport flipping, modal scroll lock/focus trapping/bottom-sheet layout, typed confirmation, and accessible `hx-confirm` dialogs.
- Added the `.toasts` container to `base.html`, extended the UI toast/modal/menu macros, and added `/design` specimens plus the `design_s9_system` preview states and deterministic harness seed.
- Moved the existing page-controls interaction code into the global script so row navigation and checksum copy remain available without per-template script duplication.
- Updated CSS sources and generated copies through the required token/CSS builds. Added all touched S9 files to `YOZORA_S9_PATHS`; no existing guards were weakened or removed.

Verification:

- `pytest -q --no-header -p no:cacheprovider -W ignore tests/test_yozora_s9_system.py tests/test_design_lint.py tests/test_design_tokens_in_sync.py tests/test_design_harness.py`: **17 passed, 1 skipped**. The skipped test is the app-backed preview registry because this environment lacks `boto3`.
- `python -m design.tokens_tool check`: passed.
- `npm run css:build`: passed; only the existing Browserslist freshness warning was emitted.
- `node --check app/static/js/app.js`: passed.
- Raw Jinja rendering passed for all 15 S9 preview screen/state combinations; changed templates parse successfully.
- `git diff --check`: passed.
- Full `pytest` was attempted but stopped during collection with 60 errors because `boto3` is unavailable in the environment. The orchestrator should rerun app-backed tests with project dependencies installed.

Pixel gate/screenshots: not run. The orchestration rules prohibit attempting the localhost-bound pixel gate in this sandbox; the orchestrator runs it once. No additional mockup exceptions were identified. Date picker, pagination, and tooltip work remain deferred as instructed.

Changes remain uncommitted and unstaged for the orchestrator.
