# Yozora S1: Tokens, generator, vendored fonts, shell and navigation

**Rewritten:** 2026-10-03 (replaces the 2026-10-01 template). **Owner:** Codex builds; Claude reviews every diff and screenshot before merge; Saqlain merges. **Depends on:** Nothing in this series. PR #99 (backend) is not required, but if it is merged use its firm settings service for the accent (see Backend).
**Repo:** `/Users/saqlainmomin/dpdpa-gap-tool` (work in your own git worktree of it, one branch per slice, named `codex/yozora-s1-...`). Paths below are relative to your worktree root. The specs below exist on `main` once the docs PR for this series has merged; until then branch from `claude/yozora-slice-handoffs`.

**Read first, in this order:** `docs/product/yozora-design-system.md` (the design guide), `docs/product/yozora-fidelity-gate.md`, `docs/product/2026-10-01-app-design-mockups/screens/IA-SPEC.md`, `docs/product/yozora-migration-map.md` (rows for this slice), then the mockups listed under Screens (serve them with `python3 -m http.server` from the repo root and open `/docs/product/2026-10-01-app-design-mockups/screens/<file>?state=<name>` and `&dark`). Background if you need it: `tasks/agent-ownership.md`, `CLAUDE.md`.

## Goal

Make `design/tokens.json` the single source of every design value, replace the application shell with the Yozora shell (side menu, top bar, user menu, breadcrumb slot, mobile drawer), vendor Inter, and build the pixel-gate harness and the lint test that every later slice depends on. After this slice the app looks like Yozora around an unchanged page body.

## Definition of done

- `python3 design/tokens_tool.py check` and `tests/test_design_tokens_in_sync.py` pass; the generator writes `app/static/css/yozora-tokens.css` and a Tailwind theme file from `design/tokens.json`, and nothing else holds colour or spacing values.
- `base.html` renders the side menu, top bar, user menu and drawer to the mockups at 1440, 1024 and 390, light and dark, with `aria-current` on the right menu item for every existing page.
- Inter 400/500/600 is vendored under `app/static/fonts/` (woff2, SIL OFL licence file and the release version recorded in a README next to them); no request goes to a font CDN.
- The Playwright harness renders any approved mockup or app route at a given viewport and theme, writes baselines to `design/baselines/<screen>-<theme>-<width>.png`, and compares with pixelmatch at the fidelity-gate thresholds. `design/baselines/` has the shell baselines for this slice.
- `tests/test_design_lint.py` implements gate 5 and passes on the whole of `app/templates` and `app/static/css/src` (see Notes for how to handle templates that have not been migrated yet).
- `tests/yozora_paths.py` exists with the guard-allowance mechanism described under File-set guard.

## Screens

Mockups are in `docs/product/2026-10-01-app-design-mockups/screens/`. Match every state listed; the state names are the `?state=` values on the mockup.

| Mockup | States to match |
|---|---|
| `b7-mobile-shell.html` | page shell at 390: top bar, drawer trigger, content area. Compare clipped to `.top` and the first screenful only. |
| `b7-mobile-shell-sheet.html` | navigation closed; drawer open; drawer with account menu. The confirm dialog and toast specimens on that page belong to S9. |
| `b1-home.html` | state `default`, compared clipped to the side menu (`.side`) at 1440 and 1024 and to `.top` at 390. The page body is S3. |

## Templates, routes and view functions in scope

Routes were found by grepping `app/routers/` for each template (helper functions are traced to their routes). Verify with `grep -rn '<template>' app` before relying on a row; if a row is wrong, fix the migration map in your PR.

| Template | Served by (method path, function) |
|---|---|
| `base.html` | every page (layout) |

## Must-keep ids, `hx-*` and `data-*`

Copied from the templates as they are today (checked against `docs/product/yozora-migration-map.md`). A migration may restyle and move these but not rename, drop or re-target them. If markup must change so that one cannot stay, stop and ask.

- `base.html`: none.

## Build notes

**Token generator.** Flip the direction of `design/tokens_tool.py`: `write` currently parses CSS into JSON; after this slice `build` reads `design/tokens.json` and writes (a) `app/static/css/yozora-tokens.css` and (b) `tailwind.tokens.cjs`, a theme-extension object that `tailwind.config.js` requires (colours, radius, spacing, font sizes from the tokens; keep the existing `navy` and `brand` colours until S9 removes the last Tailwind template that uses them). `check` regenerates in memory and exits 1 on any diff against the files on disk. `design/yozora-tokens.css` is deleted in the same PR, and every reference to it (the gallery, the mockups under `docs/product/2026-10-01-app-design-mockups/`, `design/mockup-chrome.css`) is repointed to the generated app file or left as a documented relative copy. State which in the PR. Do not edit the approved mockups' markup; only their `<link>` path may change, and only if you must.

**Component and pattern CSS.** `design/yozora-components.css` and `design/yozora-patterns.css` must reach the app. Decision for this slice (confirm in the PR description): the generator also copies both files byte for byte into `app/static/css/`, and `tests/test_design_tokens_in_sync.py` fails if the copies drift. `design/` stays the place they are edited. `base.html` links tokens, components, patterns, in that order, then the Tailwind build output, then `style.css`. Do not delete `style.css` or the Tailwind build; unmigrated slice pages still need them until S9.

**Dark mode attribute.** The tokens use `[data-theme=dark]` and `[data-accent=...]` on `<html>`. The current shell uses a `dark` class and `localStorage.theme`. Switch the inline script and `toggleTheme` function in `base.html` (they live there, not in `app.js`) to set `data-theme` and keep the same `localStorage` key and the `prefers-color-scheme` fallback. Set Tailwind to `darkMode: ['selector', '[data-theme="dark"]']` so existing `dark:` utilities keep working on unmigrated pages.

**Page title format.** `tests/test_white_label.py` (lines 105 and 106) asserts titles such as `<title>Dashboard — Momin &amp; Co Compliance Assessment</title>`, built from the `title` block and `branding.firm_name` in `base.html`. Keep the format `<page> — <firm> Compliance Assessment`, or change the tests deliberately and list it. The same file also asserts the firm name on the redirected login page.

**Template globals.** Templates get `branding` from `web.templates.env.globals["branding"]` (a dict with `firm_name`, `firm_primary_hex`, `has_custom_nav_color`); `tests/test_white_label.py` monkeypatches it with exactly those keys. Do not add required keys to `branding`; add new globals (`firm_accent`, `NAV_ITEMS`) beside it.

**Accent.** `<html data-accent="...">` comes from a Jinja global `firm_accent`. Default `midnight`. If PR #99 has merged, read `FirmSettings.accent_theme` through `app/services/firm_settings.py` (`get(db)`); otherwise return the default and leave a one-line comment pointing at #99. A custom hex accent (`accent_custom_hex`) is applied by an inline `<style>` that sets only `--accent`, `--accent-text`, `--on-accent` (and the dark pair) on `:root`; it is the only inline style allowed in the shell.

**Side menu.** Items, in order: Home `/`, Clients `/clients`, Engagements `/engagements`, Review `/review` with a count badge, Evidence `/evidence`, Reports `/reports`; Settings `/settings` at the bottom. Most of those destinations do not exist yet (only `/` does; `/settings` arrives with PR #99). Do not ship dead links: drive the menu from one list, `NAV_ITEMS`, where each entry has `available: bool`, and render only available entries. Each later slice flips its entry: S3 Clients and Settings, S4 Engagements, S6 Evidence, S7 Review, S8 Reports. The Review badge is the number of conclusions awaiting a decision across non-archived assessments; compute it in one context processor with one query (look at `app/services/review_queue.py` for the pending states) and render nothing when zero. `aria-current="page"` rules are in `IA-SPEC.md`: inside an engagement or assessment, Engagements is current.

**User menu.** The mockups show a signed-in person ("Priya Sharma, Reviewing partner", Profile, Sign out). There is no auth until Track 4. Assumption to confirm in the PR: show the firm tile (initials of `branding.firm_name`) as the account area; its menu holds Settings and a Light, Dark, System choice. No Profile, no Sign out, no personal name.

**Breadcrumb and page header slots.** Today `base.html` has blocks `title`, `head`, `body`, `content`, `scripts`, and an inline breadcrumb (assessment name only, shown when `assessment` is defined). Add `{% block crumbs %}` and `{% block page_head %}` using the `.crumb` component, with `hide-sm` on the client crumb and its slash (so deep pages fit at 390; the overflow menu is a known gap, see the design guide). Pages move to the new blocks as their slice lands; until then keep the old inline breadcrumb as the default content of `crumbs` so no page breaks. Keep `data-shortcut-scope` working: `app/static/js/app.js` `Shortcuts` reads it (dashboard `n`, questionnaire), and S1 must not break it.

**Playwright harness.** Add `playwright` and an image-diff dependency (`pixelmatch` plus `Pillow`, or `pixelmatch` alone) to `requirements-dev.txt`, pinned. Harness lives in `design/harness/` (script) and `tests/visual/` (pytest, skipped unless `RUN_VISUAL=1` so the normal suite stays fast). Render rules from the fidelity gate: Chromium pinned, animations disabled, clock frozen, `deviceScaleFactor` 1, fonts vendored, seeded data, masks via `data-visual-mask`. Baselines are generated from the approved mockups served by `python3 -m http.server` over the repo root, at the same viewport, with `?dark` for dark and `?state=<name>` for a state (b1 to b4, b6 and b7 files switch state through the `data-s` buttons and the `state` query; b5 files use `?state=<name>` with `data-mock-state`). The harness must take a mockup path plus options and write a PNG, and must take an app URL the same way, so S2 to S9 reuse it unchanged. Write a short `design/harness/README.md` with the commands.

**Lint.** Implement the five checks of gate 5 in `tests/test_design_lint.py` as separate test functions over `app/templates` and `app/static/css/src`. Many existing templates fail them today. Keep the lint green by giving it an explicit allow-list file, `tests/design_lint_allowlist.txt`, naming every template that has not been migrated yet; each slice deletes its templates from that file as the final step, and S9 requires it empty. A template not in the allow-list must pass. The one-primary check runs in the screenshot run, not in the grep test.

## Backend dependency

PR #99, https://github.com/saqlainmmomin/Cyber/pull/99, carries the server-side work for the redesign; its spec is `tasks/handoffs/2026-10-03-yozora-backend-features.md` on branch `claude/yozora-backend-features`. **Do not re-specify or re-implement it here.** At the time this handoff was written #99 held only its spec (no code), so this file names the planned modules from that spec: if #99 has merged by the time you start, read the real function names from the code and use those; if it has not, follow the 'if not merged' instruction in the Build notes.

Optional: PR #99 `app/services/firm_settings.py` for the accent. Nothing else. S1 adds no routes.

## Tests

**Existing tests that exercise this slice** (route calls matched against this slice's routes, plus tests that name its templates). Run them first and again after each template change.

| Test file | Calls to this slice's routes | Mentions its templates |
|---|---|---|
| `tests/test_p6_7_requirement_card.py` | 0 | 1 |
| `tests/test_p6_7b_add_to_rfi.py` | 0 | 1 |
| `tests/test_p6_8_b2_docx_xlsx.py` | 0 | 1 |
| `tests/test_p6_8_board_report_v2.py` | 0 | 1 |
| `tests/test_p6_9_file_set.py` | 0 | 1 |

Strings such as `text-amber-700` are Tailwind classes that a test pins; the redesign removes Tailwind from the page, so those tests must be rewritten to assert the `data-*` attribute or the visible text instead, and the change listed in the PR.

**Asserted strings likely to change.** These literals appear in `assert ... in ...` lines of the tests above and also verbatim in this slice's templates today; if a restyle changes or removes one, edit the test deliberately and list the change in the PR description (old string, new string, reason).

- none found.

**Page text asserted by tests that fetch this slice's routes** (not necessarily from this slice's own templates; the test may be reading text that comes from an included partial or the shell). Check each one when you restyle the page it comes from.

- none found.

**New tests to add:**

- `tests/test_design_tokens_in_sync.py`: regenerates in memory and fails on any diff against `app/static/css/yozora-tokens.css`, the Tailwind theme file and the two copied CSS files.
- `tests/test_design_lint.py`: five checks of gate 5, honouring `tests/design_lint_allowlist.txt`.
- A shell test: `aria-current` on the right menu item for `/`, an engagement page and an assessment page; entries with `available: False` are not rendered; the Review badge shows the count and is absent at zero; `data-theme` and `data-accent` are set on `<html>`.

## File-set guard

Many tests are scope guards: they diff the branch against `main` and fail when a file outside an allow-list changes (the P6-2b scenario 11 guard in `tests/test_p6_2b_dpdpa_criteria.py`, the P6-9 file-set guard in `tests/test_p6_9_file_set.py`, and several older `:(exclude)` guards). They were written for earlier PRs and are stale for this one. **Never delete or weaken a guard.** Add a scoped allowance instead, the way `tests/p6_8_v3a_paths.py` does for V3-A:

1. S1 creates `tests/yozora_paths.py` with one tuple per slice (`YOZORA_S1_PATHS`, ...) and `YOZORA_EXCLUDES = [f":(exclude){p}" for p in ...]` over all tuples. Each later slice adds its own tuple (every file it adds or changes outside `docs/product/` and `design/`) to that module.
2. Run the full suite. For each guard that fails on your files, splat `*YOZORA_EXCLUDES` into its pathspec list (or import the tuple into its allow-list), exactly as `V3A_EXCLUDES` is imported by `tests/test_p5_6_rfi_rebuild.py`. Add a comment `# Yozora per-PR allowance`.
3. Keep this slice's handoff file and `YOZORA_DESIGN_FILES` allowed (already done for `tasks/handoffs/2026-10-01-yozora-s*-handoff.md`).
4. List every guard you touched in the PR description.

**This slice's `YOZORA_S1_PATHS` starts as:**

- `app/templates/base.html`
- `app/static/js/app.js`
- `app/main.py`
- `app/config.py`
- `tailwind.config.js`
- `requirements-dev.txt`
- plus every test, CSS, JS and fixture file you add or change.

**Guards found today that name this slice's files** (expect these to need the allowance; there may be more):

- `tests/test_p6_2b_dpdpa_criteria.py` names `app/main.py`, `app/config.py`
- `tests/test_p6_4_cap_upload_limit.py` names `app/main.py`, `app/config.py`
- `tests/test_p6_4_whats_missing.py` names `app/main.py`, `app/config.py`
- `tests/test_p6_6_report_foundations.py` names `app/config.py`
- `tests/test_p6_7_requirement_card.py` names `app/templates/base.html`, `app/templates/base.html`, `app/main.py`, `app/config.py`
- `tests/test_p6_7b_add_to_rfi.py` names `app/templates/base.html`, `app/templates/base.html`, `app/main.py`, `app/config.py`
- `tests/test_p6_8_b2_docx_xlsx.py` names `app/templates/base.html`, `app/templates/base.html`, `app/main.py`, `app/config.py`
- `tests/test_p6_8_board_report_v2.py` names `app/templates/base.html`, `app/templates/base.html`, `app/main.py`, `app/config.py`
- `tests/test_p6_9_file_set.py` names `app/templates/base.html`, `app/templates/base.html`, `app/main.py`, `app/config.py`, `requirements-dev.txt`
- `tests/test_p6_nist_csf2_alignment.py` names `app/config.py`
- `tests/test_retention.py` names `app/main.py`

## Screenshot gate

Use the harness from S1 (`design/harness/README.md`). Render each screen listed above in every state, light and dark, at 1440 and 1024, and 390 for the drawer states. Baselines are the approved mockups rendered at the same viewport with `?state=<name>` and `?dark`, saved as `design/baselines/<screen>-<state>-<theme>-<width>.png` (S1 defines the exact naming; include the state in the name when the screen has several). Candidates use seeded demo data (the fictional Meridian Ledger Technologies, Loomwire Labs and Kestrel Advisory companies from the mockups) with the clock frozen and fonts vendored.

Thresholds from the fidelity gate: colour tolerance 0.1 (pixelmatch); fail above **0.4%** differing pixels on app screens and **0.2%** on `/design`; fail on any single changed region over 40x40 px regardless of the total. Mask dynamic regions with `data-visual-mask`. Loosening a threshold needs a written reason in the PR.

In the PR, post for each screen and state: the baseline, the candidate and the diff image side by side, plus the differing-pixel percentage. Saqlain sees these before merge (gate 4). CI green is necessary, not sufficient.

## Dependency order

S1 shell, then S2 component layer and `/design`, then S3 to S8 (S3 and S4 first; S5, S6 and S7 can run in parallel worktrees only if they touch no shared template; S8 after S6 and S7), then S9 system states, dark and mobile pass. This is slice **S1**.

## Stop and ask

Stop and write the question in this file's Results section (and tell the orchestrating session) if:

- a visual detail is in neither the design guide nor the approved mockup;
- two mockups disagree;
- a must-keep id, `hx-*` or `data-*` cannot be kept;
- a mockup shows an action with no route behind it that this file does not cover;
- the work needs a model, migration, prompt, scoring or PDF change.
- Inter files: download them only from the official Inter release; if you cannot, stop and say so rather than substituting another font.
- If the shell needs an icon that is not in the mockup's SVG sprite, stop and ask.

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

### Built

- `design/tokens.json` is now the source for `app/static/css/yozora-tokens.css`, `tailwind.tokens.cjs`, and byte-identical generated copies of the component and pattern CSS. `design/yozora-tokens.css` was removed; the gallery, mockups, and mockup guides now point at the generated app token CSS. The deferred `--line-strong` values were preserved exactly.
- `base.html` now provides the Yozora shell: responsive side navigation/drawer, top bar, breadcrumb and page-header slots, firm account menu, theme choices, `data-theme`, `data-accent`, and IA-based `aria-current`. Only Home is available in S1; later-slice destinations are not rendered as dead links. Review-count calculation is a single context-processor query when a request database session is available.
- Inter 4.1 400/500/600, the supplied OFL licence/README, and `htmx-2.0.4.min.js` were preserved in place. The shell loads both locally; no app template requests Google Fonts or unpkg.
- Added the pinned visual harness (`design/harness/`), lint tests/allow-list, and `tests/yozora_paths.py`. The existing white-label assertion changed from `background-color: #8b0000` to the new custom-accent contract `--accent: #8b0000`.

### Verification

| Check | Result |
|---|---|
| `python3 design/tokens_tool.py check` | Pass |
| Focused design/shell tests | **13 passed, 6 skipped** (`RUN_VISUAL` is unset) |
| Python compilation and `git diff --check` | Pass |
| Tailwind config load | Pass; `darkMode` is the `[data-theme="dark"]` selector |
| Tailwind CSS build | Not rerun: this checkout has no local `node_modules`; the generated config loads successfully with Node, but `npx` could not complete offline. |
| Visual screenshots/baselines | Not run: this environment has neither the Playwright Python package nor a Chromium installation. The harness exits with the documented install instruction; no baseline images were fabricated. |
| Full `pytest -q` | Collection blocked by the pre-existing environment missing `boto3`: **34 errors during collection**. |

### Guards and decisions

- Added `YOZORA_S1_PATHS`, `YOZORA_DESIGN_FILES`, and `YOZORA_EXCLUDES` in `tests/yozora_paths.py`. No existing scope guard was weakened or deleted.
- Kept the S1 availability gate conservative: unavailable Clients, Engagements, Review, Evidence, Reports, and Settings links are omitted until their slices/routes land. The account menu is firm-level and theme-only while Settings is unavailable.
- The backend accent integration from PR #99 was not present, so S1 uses the approved `midnight` default and leaves the integration point in `template_config.py`.

### Open items

- Install the pinned dev dependencies and Chromium, then render the S1 mockup states and commit the approved shell baselines under `design/baselines/` before the visual gate can be closed.
