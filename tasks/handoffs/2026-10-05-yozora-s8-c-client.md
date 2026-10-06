# Yozora S8 group C: client-facing pages (upload, expired, revoked, unknown)

**Status: NOT DISPATCHED.** **Worktree:** `../cyberassess-yozora-s8-c`, branch `codex/yozora-s8-client` (off `codex/yozora-s8` after the scaffold). One of three parallel Codex builds; A (requests) and B (versions) run beside you.

## Goal
Rebuild the pages a client sees through a magic link: a request card to upload against, and one invalid page for expired, revoked and unknown links. No side menu; touch-size controls; gated at 390 as well as 1440 and 1024.

## You own
`app/templates/magic/upload.html`, `magic/invalid.html`, and in `app/routers/magic.py` only the client side (`get_magic_link`, `post_magic_link`, `_render_upload`, `_render_invalid`). Do not touch group A's consultant functions or partials, or group B's files. `.touch` and `.dropzone` already exist in `design/yozora-components.css`/`yozora-patterns.css`: do not add new CSS for them.

## Mockups and states
`b6-magic_upload`: default, uploading, done, error (390 and 1440). `b6-magic_invalid`: expired, revoked, unknown. `b7-link-expired`: matched visually at 390 only; build to `b6-magic_invalid` with app-driven copy (decision 8): firm name from settings, expiry from the link, no invented "14 days" or named person.

## Group specifics
- Keep ids `file-upload` and `item-key`, the per-item upload forms and the token handling.
- Greeting uses the contact's first name only when `MagicLink.contact_name` is set. "Email <firm>" only when `FirmSettings.contact_email` is set, and the mailto **never contains the token**. The invalid page reveals no client or engagement name beyond what it shows today.
- Token never in a URL parameter, mailto, log line or screenshot baseline; fixtures use a fixed fake token. Add a test for each.
- Error copy asserted by tests must stay: "Choose a file to upload.", "Choose one of the requested items.", "This link has reached its upload limit. Contact your consultant." and the received/duplicate messages in `tests/test_magic_links.py`.
- Round trips to verify over HTTP: item chosen, no file, over the item limit, duplicate file, total size, then expired/revoked/unknown tokens.
- `uploading`, `done` and `error` may come from `PREVIEW_PAGES` fixtures or the mockup's own `?state=`; list which.

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

### Built

- Rebuilt `magic/upload.html` and `magic/invalid.html` as standalone Yozora client pages with the required `file-upload`, `item-key`, `data-*`, and upload form contracts intact. Upload states are `default`, `uploading`, `done`, and `error`; invalid states are `expired`, `revoked`, and `unknown`.
- Added app-driven client context in `magic.py`: firm name/contact settings, contact first-name greeting, received-item markers, expiry date, issued-link state copy, and firm-only invalid-page privacy. The token is never passed into template context, mailto links, or log text.
- Added deterministic fixed-token fixtures in `design/harness/seed_s8_client.py` and preview rendering in `app/routers/design_s8_client.py`. The live upload default uses the seeded database; transient upload states and invalid states use `PREVIEW_PAGES` fixtures. `b7-link-expired` shares the invalid-page template and app-driven copy.
- Added the delimited client-page pattern block to both design/source CSS copies and rebuilt the generated static copy.

### Pixel gate

The required threshold remained 0.4% differing pixels with no changed region over 40x40. The gate could not capture a screenshot in this managed environment: `b6-magic_upload:default` failed while starting its local server with `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`, before baseline/candidate comparison. The remaining states have the same recorded environment exception and therefore have no percentage to report.

| Screen | States | Result |
|---|---|---|
| `b6-magic_upload` | `default`, `uploading`, `done`, `error` | Not captured — localhost bind blocked before screenshot |
| `b6-magic_invalid` | `expired`, `revoked`, `unknown` | Not captured — same harness bind block |
| `b7-link-expired` | `expired` | Not captured — same harness bind block |

### Exceptions

- Pixel evidence is unavailable for the cause above; no threshold or region limit was loosened.
- Invalid-page copy intentionally differs from the mockup's sample expiry/person text: the orchestration decision requires firm settings and link expiry, forbids invented “14 days” and named-person copy, and keeps client/engagement names out of the response.
- The upload page keeps a visually hidden `<select>` option list because the existing validation harness discovers requested item keys from those options; the visible interaction remains per-item Yozora buttons targeting `item-key`.

### Tests changed (old → new)

- `test_invalid_tokens_are_indistinguishable` → `test_invalid_tokens_render_the_issued_state_without_context_leaks`: retained 404, security-header, generic-message, and no-context assertions; replaced byte-identical bodies with the expected expired/revoked/unknown heading for each issued state.
- The valid-page external-content assertion stopped rejecting same-origin `<link>`/`src=` references; it still rejects `http://`, `https://`, and form `action=` leakage because the client shell now loads the vendored Yozora styles and submits to the current URL.
- The contact invalid-page test stopped requiring an expired response to be byte-identical to an unknown response; it now asserts state-specific headings and an identical expired GET/POST response while retaining firm-only privacy checks.
- Added `tests/test_yozora_s8_client.py` for page structure, HTTP state copy, conditional mailto/contact behavior, token secrecy, and exact state registration.

### Guards touched

Added the client files and the two existing magic-link test files to `YOZORA_S8_PATHS`. Updated the stale add-only S8 allowances in `tests/p6_10_support.py`, `test_longitudinal_demo.py`, `test_p6_7_requirement_card.py`, `test_p6_7b_add_to_rfi.py`, `test_p6_8_b2_docx_xlsx.py`, `test_p6_8_board_report_v2.py`, `test_p6_8_v3a_data_capture.py`, `test_p6_9_file_set.py`, and `test_retention.py` so parallel-slice file-set guards recognize this authorized S8 work. No guard was deleted or weakened.

### Decisions and verification

- Fixed fake tokens are used only in fixtures; the default seeded route uses `AbCdEfGhIjKlMnOpQrStUv`.
- The invalid-page contact action appears only when `FirmSettings.contact_email` is present, and its mailto contains no token.
- Focused client/security regression set: 47 passed. Design lint, token sync, and client contract set: 13 passed. `git diff --check`, compileall, CSS sync, and deterministic S8 registry/seed checks passed.
- Full suite: **1,529 passed, 30 skipped in 201.86s (3:21)**.

Open questions: none. Browser/pixel re-run requires an environment that permits the harness to bind its local server.
