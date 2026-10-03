# Yozora S9: System states, dark and mobile pass, print templates out of scope, Tailwind retirement

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** S3 to S8 merged.
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s9-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Finish the system layer and verify the whole app: error pages with a reference code, global toasts, modals, menus, skeleton and HTMX swap behaviour, then run the full dark and mobile pass across every migrated screen and retire the unmigrated-template allow-list. After this slice no template is exempt from the lint and every screen has baselines in both themes.

## Definition of done

- 404 and 500 pages exist (no error templates exist today), show a short reference code, and match the mockups; the code is also written to the server log with the request path so support can find it.
- Toasts: success and information dismiss after 4 s, errors stay until closed; stacked and with action (Undo) variants exist; the container is `.toasts`.
- Skeletons show for HTMX swaps over 300 ms; a failed swap shows an `.alert` in the target and never a blank (`b7-htmx-swaps`).
- Every migrated screen has baselines for light and dark at 1440 and 1024, and client-facing pages at 390; the full visual run passes.
- `tests/design_lint_allowlist.txt` is empty and deleted; the lint passes on every template.
- No page renders a visible `.btn.primary` count above one in any captured state.
- The Tailwind build and `style.css` are removed only if no template uses them; otherwise list the remaining users in Results and stop (see Notes).

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b7-404.html` | `page`, `engagement` (engagement-scoped not-found). |
| `b7-500.html` | `error`, `down`, `upstream`; the page shows a reference code. |
| `b7-empty-states.html` | `engagements`, `evidence`, `review`, `search`, `findings`, `report`. |
| `b7-skeleton-table.html` | `loading`, `loaded`. |
| `b7-skeleton-detail.html` | `loading`, `loaded`. |
| `b7-htmx-swaps.html` | `ok`, `bad`. |
| `b7-toasts.html` | all variants. |
| `b7-modals.html` | `delete` (typed name), `purge`, `send`, `invite`, `discard`, `failed`. |
| `b7-menus-popovers.html` | row actions, share, account menu; Esc closes, focus returns to the trigger. |
| `b7-mobile-shell.html` | 390 pass; the shell itself is S1. |
| `b7-dark-dense.html` | dark pass (compare to S7's findings page). |

## Templates, routes and view functions in scope

**New templates this slice creates:** `pages/error.html`. Add a row for each to `docs/product/yozora-migration-map.md`.

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `reports/board_report.html` | include or macro only, see including template |
| `reports/workpaper_standalone.html` | include or macro only, see including template |

Both templates are print templates rendered by `app/services/board_report.py` and `app/services/standalone_workpaper.py`: **out of scope**, listed so every template belongs to exactly one slice.

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `reports/board_report.html`: data-* `data-comparison-framework`, `data-framework`, `data-narrative`, `data-narrative-note`, `data-narrative-sentence`, `data-preview`, `data-roadmap-group`, `data-section`, `data-soa-control`
- `reports/workpaper_standalone.html`: ids `{{ entry.anchor }}`, `{{ row.anchor }}`; data-* `data-count`, `data-decision-state`, `data-in-scope`, `data-report-basis`, `data-revision-action`, `data-run-stale`, `data-run-status`, `data-workpaper-entry`, `data-workpaper-finding`, `data-workpaper-section`, `data-workpaper-unconcluded`

## Build notes

**Error pages.** Add exception handlers in `app/main.py` for 404 and 500 (and a catch-all for unhandled exceptions) that render `app/templates/pages/error.html` with a reference code (short random id, logged with the path and exception class). Browser requests (HTML) get the page; requests that send `Accept: application/json` or hit `/api/...` keep today's JSON error body. An engagement-scoped 404 shows the engagement link when the path begins with `/engagements/<id>`, without confirming the engagement exists. Test: 404, 500 with a forced exception, JSON still JSON, reference code present in page and log.

**HTMX swap behaviour.** Add the global behaviour once in `app/static/js/app.js`: the `.skel` placeholder after 300 ms, `htmx:responseError` and `htmx:sendError` replace the target with an `.alert` (never blank), `.htmx-swapping`/`.swap-in` fade, `.btn.loading` on the triggering button. Toasts: a small `toast(kind, message, action)` helper writing into `.toasts`; no template builds toast markup by hand.

**Mobile and dark pass.** Run the whole baseline set (every file in `screens/` that a slice migrated) in both themes at the widths each screen uses. Fix drift in CSS or templates; if the fix would touch a different slice's templates, make it here as a separate commit and list it. Check at 390: crumbs hide with `hide-sm` and nothing overflows horizontally.

**Allow-list and Tailwind.** When the allow-list is empty, search for remaining Tailwind utility classes in `app/templates`. If none remain, remove `tailwind.css` from `base.html`, drop `tailwind.config.js` and `package.json` scripts, and delete `style.css` if unused. If some remain (print templates under `app/templates/reports/` use their own CSS and are out of scope), keep the build for them and list them.

**Out of scope.** `reports/board_report.html` and `reports/workpaper_standalone.html` are print templates and share colour tokens only. Do not restyle them and do not touch their `data-*` attributes (many tests pin them).

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

None. Error handlers and the HTMX script are the only application code.

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_p6_9_file_set.py` | 0 | 2 |
| `tests/test_p6_7b_add_to_rfi.py` | 0 | 1 |
| `tests/test_p6_8_b2_docx_xlsx.py` | 0 | 1 |

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- "Board report": test_p6_8_b2_docx_xlsx.py:407

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- none found.

**New tests to add:**

- 404 and 500 pages show a reference code; the code is logged with the path; `Accept: application/json` still gets JSON.
- The lint allow-list file is gone and the lint passes on every template.
- A full-visual-run summary: number of screens, themes and widths compared, number failing (must be zero).

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S9_PATHS` starts as:**

- `app/templates/reports/board_report.html`
- `app/templates/reports/workpaper_standalone.html`
- `app/templates/pages/error.html`
- `app/main.py`
- `app/static/js/app.js`
- `tailwind.config.js`
- `package.json`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_p6_2b_dpdpa_criteria.py` names `app/main.py`
- `tests/test_p6_4_cap_upload_limit.py` names `app/main.py`
- `tests/test_p6_4_whats_missing.py` names `app/main.py`
- `tests/test_p6_7_requirement_card.py` names `app/main.py`
- `tests/test_p6_7b_add_to_rfi.py` names `app/templates/reports/board_report.html`, `app/main.py`
- `tests/test_p6_8_b2_docx_xlsx.py` names `app/templates/reports/board_report.html`, `app/main.py`
- `tests/test_p6_8_board_report_v2.py` names `app/main.py`
- `tests/test_p6_9_file_set.py` names `app/templates/reports/board_report.html`, `app/templates/reports/workpaper_standalone.html`, `app/main.py`
- `tests/test_retention.py` names `app/main.py`

## Screenshot gate

Use the harness from S1 (`design/harness/README.md`). Render each screen listed above in every state, light and dark, at 1440 and 1024, and 390 for client-facing pages and the mobile shell. Baselines are the approved mockups rendered at the same viewport with `?state=<name>` and `?dark`, saved as `design/baselines/<screen>-<state>-<theme>-<width>.png` (S1 defines the exact naming; include the state in the name when the screen has several). Candidates use seeded demo data (the fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory companies from the mockups) with the clock frozen and fonts vendored.

Thresholds from the fidelity gate: colour tolerance 0.1 (pixelmatch); fail above **0.4%** differing pixels on app screens and **0.2%** on `/design`; fail on any single changed region over 40x40 px regardless of the total. Mask dynamic regions with `data-visual-mask`. Loosening a threshold needs a written reason in the PR.

In the PR, post for each screen and state: the baseline, the candidate and the diff image side by side, plus the differing-pixel percentage. Saqlain sees these before merge (gate 4). CI green is necessary, not sufficient.

## Dependency order

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S9**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- If a baseline cannot be met without changing an approved mockup, stop and ask; do not edit mockups.
- If removing Tailwind breaks a template you did not migrate, restore it and list the template.

Do not invent. Do not touch `validation/companies/*/answer_key.json`. No attribution in commits.


## Rules that apply to every slice

- **Source of truth.** If this file, the design guide and a mockup disagree, the approved mockup wins for what the screen looks like, the application code wins for what the route does, and you stop and ask when they conflict (see Stop and ask).
- **Reviewer-name rule.** The designs assume a signed-in user and show no name field. The app has no auth until Track 4, so every route that needs a reviewer or consultant name keeps its temporary input (`reviewer-name` and similar ids). Restyle the input; do not remove it, do not pre-fill it with a real person, and do not show it in states where the mockup has no matching action. Track 4 deletes these fields.
- **Framework copy is conditional.** DPDPA, ISO 27001 and other framework names appear only where that framework is in scope for the assessment. Screening is DPDPA only. Scores are never combined across frameworks; the score ring is neutral.
- **One primary per state.** At most one visible `.btn.primary` in any page state, and none in a state with no real action (never a disabled primary).
- **Vocabulary.** Evidence status: Scanning, Available, Rejected, Out of date. Priority: Do first, Next, Planned, Backlog (never numbers). Answers: Fully implemented, Partially implemented, Planned, Not implemented, Not applicable. Control codes in small muted text in lists. Sentence case, no uppercase, no numbered or lettered headings, dates as 15 Oct 2026.
- **Never touch** `validation/companies/*/answer_key.json`, scoring, the analyzer, prompts, or the PDF code paths. All PDF text goes through `S()`. These slices change templates, CSS, small view code and tests.
- **Commits.** One logical change per commit, no attribution lines of any kind, no co-author trailer. Do not merge; Saqlain merges.
- **Python.** Python 3.13 (`python3.13 -m venv .venv`); Homebrew 3.14 breaks Jinja2. Run the full suite before opening the PR and paste the summary line into Results.

## Results

(Codex fills in: what was built, the screenshots table with percentages, tests changed with old and new strings, guards touched, decisions made, open questions, full-suite summary line.)
