# Yozora design system: mock every screen, write design.md, make drift impossible

**Written:** 2026-10-01, end of the app-design exploration session. **Branch/worktree:** `claude/app-design-kickoff` in `/Users/saqlainmomin/cyberassess-docs` (the files below are **uncommitted and not on `main`**; commit them first, see "Before you start").
**Decision log and history (read second):** `tasks/handoffs/2026-10-01-app-design-kickoff.md`. This file supersedes its "First steps" section.
**Owner split (per `tasks/agent-ownership.md`):** Claude owns design judgment, `design.md`, screen mockup review, build handoffs and fidelity review. Codex owns the mechanical build from those handoffs. Details in "Who does what".

## Goal

Produce the complete, approved design system for the Yozora app so that the implementation session cannot drift from it. Definition of done for the **design session** (no app code is shipped in it):

1. `docs/product/yozora-design-system.md` (the `design.md`): principles, tokens, components with every state, patterns, copy rules, accessibility, wordmark.
2. `design/tokens.json`: the machine-readable source of every value, plus the generator spec for `tailwind.config.js` and CSS variables.
3. **Every app screen mocked** in the system, light and dark, in `docs/product/2026-10-01-app-design-mockups/screens/`, approved by Saqlain.
4. A **migration map** (every template to a design pattern, with the HTMX target ids and `data-*` attributes that must not change).
5. The **fidelity gate** specified: Playwright screenshot baselines and diff thresholds.
6. A **slice plan** with one build handoff per slice, each with contract tests, ready for Codex.

Saqlain's reason for all this: past mockups drifted into something weird at implementation. Everything here exists to close that. "Cover all fronts so we don't spend time going back and forth."

## Decisions already made (do not relitigate)

- **Name: Yozora** (replaces CyberAssess). Trademark search in India (classes 9, 42, 45) and a registrar check are **still pending**; they must be done before Track 4 exposes the product. Not a design blocker.
- **Accent: Midnight** `#1C3A72` light; dark fill `#33508C`; dark text/rings/icons `#A9BCEE`. White on the light fill is 11.1:1.
- **Direction:** `v3-polish.html`. Clean, minimal, to the point, Linear-like in spirit (not its colours). A professional designer rejected the earlier "utilitarian" direction: no hierarchy, extra numbers and letters, small all-caps text, looked AI-generated.
- **Hard rules (carry into design.md as testable rules):**
  - Sentence case everywhere. No all-caps text, no eyebrow labels.
  - No serial lettering or numbering of sections, steps or nav. No ref codes in list views (ids only in detail views).
  - No subtext unless it earns its place.
  - Hierarchy from size, weight and spacing only, not caps, rules or colour.
  - One primary action per screen.
  - No glow blobs, gradient text, sparkle icons or rainbow borders. Gradient only on the page canvas (and an extremely subtle one on the primary button).
  - Dark mode is kept. Severity and outcome colours are fixed and never themed: critical `#9B1C1C`, high `#D9481E`, medium `#F0A030`, low `#3C9D6B`; compliant `#2F9466`, partially compliant `#F0A030`, non-compliant `#C0392B`, insufficient evidence `#9AA3B5`.
  - Scores are never combined across frameworks. Period and evidence cut-off are always visible. No numeric priority shown to clients. Framework-specific copy is conditional.
- **Firm theme (V3-A) themes the app chrome** as well as deliverables, via the accent token only. Severity and outcome stay fixed.
- **Client-facing pages are in scope** (`magic/upload.html`, `magic/invalid.html`).
- **Build waits for V3-A to merge** (it adds fields to the Finding, Action, roadmap and versions forms). Mockups and `design.md` do not wait.
- **Dark mode kept; fonts vendored** under `/static` (no CDN). Inter is the body face; the mockups load it from Google Fonts for convenience only.

## Locked tokens (from `v3-polish.html`; re-extract from the file, do not retype)

| Group | Value |
|---|---|
| Gradient, light | `#D3DAE5` to `#E6E5EE` (stop at 52%) to `#EBDDE3` (reference: muted blue-grey at top, pale lavender, dusty mauve at bottom; stops are tokens so they can be retuned) |
| Gradient, dark | `#1A2131` to `#1C1D2A` to `#28202C` |
| Panels | Frosted: 60% white, 18px blur, 16px radius, no hard border (soft white inner edge), very soft shadow. Solid panels (tables, review detail, user menu): 90% white. Dark: frosted 5.5% white; solid 88% deep blue-black. |
| Type | Inter 400/500/600. Scale 12/13/14/16/20/24/28, 40 only for framework scores. Tabular figures for numbers. |
| Radii | 4 chips and kbd, 6 list items, 10 inputs and nav, 16 panels, full round for buttons and pills |
| Spacing | 4, 8, 12, 16, 20, 24, 32, 40, 48 |
| Shadows | three levels: card, raised, popover/drawer |
| Buttons | Pill. Medium 34px high, 16px side padding, 13px/500. Small 28px high, 12px padding. Primary: accent fill, 14% white top highlight, soft accent-tinted shadow. Secondary: 88% white, soft border. Ghost. Reject: red text. Focus: 2px gap + 4px accent ring at 38%. Disabled 45%. Motion 140ms (colour, shadow), 80ms (press). Keycap hints 18px, 5px radius. |
| Status pills | Tinted fill, 6px dot, faint coloured edge, normal text colour (amber and orange fail contrast as text) |

## Current state

- **Canonical mockup:** `/Users/saqlainmomin/cyberassess-docs/docs/product/2026-10-01-app-design-mockups/v3-polish.html`. Three screens (Home, Assessment hub, Review queue), light and dark, accent switcher with 8 options (Midnight is chosen; switcher can be removed), mobile drawer, `?dark`, `?accent=<name>`, `#s1/#s2/#s3`. Renders in `shots-v3/`.
- `v2-clean.html` is the previous pass; `superseded/` holds the rejected first two directions. Do not reuse their visual language.
- **Baseline screenshots of the current app** (the "before"): `/Users/saqlainmomin/cyberassess-docs/docs/product/2026-10-01-app-design-baseline/` (20 populated screens, dark and mobile variants for key ones, README with gaps).
- To serve the mockups: `cd .../2026-10-01-app-design-mockups && python3 -m http.server 8010`.
- Playwright for screenshots: a scratch venv existed at the session scratchpad and is gone with it. Recreate: `python3.13 -m venv /tmp/pw && /tmp/pw/bin/pip install playwright`, then launch with `executable_path` set to the cached Chromium under `~/Library/Caches/ms-playwright/chromium-*/chrome-mac-arm64/` (or run `playwright install chromium`).
- To run the real app against realistic data: seed a **scratch** DB, never your dev DB: `DATABASE_URL=sqlite:////tmp/yozora-demo.db UPLOAD_DIR=/tmp/yozora-uploads OPENROUTER_KEY="" python scripts/seed_test_companies.py --longitudinal` from a scratch cwd. This gives fictional companies with findings, conclusions, evidence, a snapshot and a magic link. A fresh magic-link token can be made via `app.services.magic_links.create_link`; tokens are hashed in the DB.

## Known gaps in v3 to resolve

- Button states (hover, pressed, focus, disabled) are built but not shown in screenshots; the gallery must show them.
- Score ring uses the accent colour; if a score should signal good or bad, that needs a rule (decide in design.md; default: keep it neutral, never green or red).
- Mobile: sidebar drawer works; the sidebar search has no mobile shortcut. The mockup bar wraps at 390px (mockup chrome only).
- Only 3 of about 45 routes are mocked. See the next section.

## What to do (in order)

### 1. Before you start
Commit the uncommitted work on `claude/app-design-kickoff` (ask Saqlain; merging is theirs). Confirm V3-A's merge status (`git log origin/main`).

### 2. Extract shared tokens and components (so mockups compose, not reinvent)
From `v3-polish.html`, extract `design/yozora-tokens.css` (custom properties, light and dark) and `design/yozora-components.css` (buttons, pills, chips, inputs, cards, tables, nav, stepper, rings, kbd, empty states). Every later mockup must `<link>` these files and use only their classes and variables. Any new component is added to the shared file first. This is the main anti-drift mechanism for the mockup stage.

### 3. Mock every screen, in batches
Each batch is one Opus subagent (Saqlain approved Opus for mockup work; it did well), writing one HTML file per screen into `docs/product/2026-10-01-app-design-mockups/screens/`, using the shared CSS, with real content from the seeded demo, light and dark, 1440px and 1024px, plus the key states per screen (empty, loading, error where relevant). Review each batch yourself with screenshots (hostile senior designer lens, see Verification) before showing Saqlain. Reuse the agent via SendMessage to keep context.

| Batch | Screens (current templates in `app/templates/`) |
|---|---|
| 1. Shell and firm | App shell, Home, clients list and `client_detail`, `login` (placeholder, wired in Track 4), firm settings: logo, accent theme, data housekeeping (the legacy "unmigrated assessments" list lives here, not on Home), users and roles placeholder |
| 2. Engagements | Engagement list and `engagement_detail`, `new_engagement`, `integrated_reports`, `remediation_tracker`, `engagement_purge` |
| 3. Assessment, scope and questionnaire | `assessment` hub (framework tabs), `scope_*`, `questionnaire_*`, `section_*`, `question_step`, `screening_form`, `followup_questions` |
| 4. Documents, desk review and evidence | `documents_tab`, `document_list`, `upload_status`, `desk_review_*`, `evidence_detail`, `evidence_span`, `evidence_reuse`, `aws_evidence`, `workpaper`, `workpaper_entry` |
| 5. Analysis, report and review | `analysis_*`, `report_tab`, `report_summary`, `report_basis_panel`, `release_panel`, `framework_panel`, `conclusions`, `conclusion_card`, `review_queue`, `requirement_card_body`, `findings`, `finding_card`, `review_finding_card` |
| 6. RFI, versions and client-facing | `rfi`, `rfi_links`, `report_snapshots`, `comparison`, `soa`, **client-facing** `magic/upload` and `magic/invalid` (mobile-first; this is the only screen an outsider sees) |
| 7. System | Form controls (all input types), tabs, menus and popovers, modals and confirm dialogs (destructive confirm for purge), toasts, loading skeletons, empty states, 404/500 pages, HTMX-swap transitions, all of dark mode, a mobile pass |

Out of scope: `reports/board_report.html` and `reports/workpaper_standalone.html` are print templates, not app UI (the board deck has its own system, F1-F10 in `docs/product/2026-10-01-board-report-format.md`). Share colour tokens with them where it is free, but do not redesign them here.

Mockup rules: the hard rules above, plus each screen has exactly one primary action; no screen invents a component that is not in the shared CSS.

### 4. Write design.md (`docs/product/yozora-design-system.md`) and `design/tokens.json`
Derive from the shared CSS and the approved mockups; do not retype values. Contents: principles (the hard rules, written as checkable statements), tokens, a component spec for every component (anatomy, variants, all states, do and don't, accessibility, the token each property uses), patterns (page header, tables, forms, empty states, destructive confirmation, HTMX swap behaviour), copy rules (sentence case, voice, how to write empty states and errors), the wordmark and favicon (propose a typographic wordmark; a symbol only if Saqlain wants one), accessibility (contrast table for every text-on-surface pair, focus order, reduced motion), and "what is deliberately not in the system".

### 5. Migration map
For every template in the inventory: target pattern, components used, and a **must-keep list** (element ids, `hx-target`/`hx-swap` values, `data-*` attributes, exact strings) found by grepping `tests/` for assertions on each template. Contract tests pin many of these; any intended change is listed so tests are updated deliberately, not by accident.

### 6. Fidelity gate (the part that stops drift)
Specify and, if Codex builds it, require: (a) `design/tokens.json` is the only place values live; a script generates `tailwind.config.js` and the CSS variables, and a test fails if they diverge; (b) a `/design` component gallery route rendering every component in every state, light and dark, from the real templates; (c) Playwright screenshots of the gallery and each migrated screen against approved baselines (the mockups), light and dark, with a pixel-diff threshold written into the handoff; (d) a slice is not done until the diff passes and Saqlain has seen the screenshots; (e) lint rules: no hex values or arbitrary Tailwind values in templates, no `uppercase` class, no numbering or lettering patterns (grep-able).

### 7. Slice plan and build handoffs
Order, after V3-A merges: S1 tokens, generator, vendored fonts, shell and nav; S2 component layer and `/design` gallery; S3 Home, clients, firm settings; S4 engagements; S5 assessment hub, scope and questionnaire; S6 documents, desk review and evidence; S7 analysis, report and review queue; S8 RFI, versions and client-facing pages; S9 system states and dark-mode and mobile pass. One handoff per slice via the `handoff` skill, each with its own contract tests, a scoped file-set-guard allowance (add `:(exclude)` allowances, never delete guards), and the screenshot gate. Template files are covered by per-PR file-set guards.

## Who does what

- **Claude (you), directly:** steps 1, 2 (extraction), 4 (design.md), 5 (migration map), 6 (gate design) and 7 (slice handoffs), and reviewing every mockup batch and every slice's screenshots. These are judgment and invariant work.
- **Opus subagents (or the fresh session itself):** step 3 mockup batches, one per batch, run in parallel after step 2 so they all share the same CSS.
- **Codex:** the build. It is mechanical once the spec is fixed: tokens generator and gallery (S1, S2), then template migrations (S3 onward), and the Playwright gate harness. It builds from Claude's slice handoffs. **Claude reviews every diff and screenshot before merge** (adversarial review per `tasks/agent-ownership.md`). Codex does not decide visual details; if a detail is not in `design.md`, it stops and asks.
- **Saqlain:** approves each mockup batch, signs off `design.md`, owns the merge, and owns the trademark search.

## Constraints

- Jinja2 + HTMX + Tailwind. No SPA, no chart library (charts are SVG/CSS; the board-deck presenter `board_view.py` from V3-B can feed dashboards later).
- Local-only until Track 4. Design login, roles and settings as placeholders to wire in Track 4.
- No Claude attribution in commits. Merging is Saqlain's. Do not touch `validation/companies/*/answer_key.json`.
- Do not edit the old rejected mockups; leave `superseded/` alone.
- Credentials and real client names never go in docs or screenshots; the seeded demo companies are fictional.

## Verification (the design session is done only when)

- Every screen in the inventory has a light and dark mockup and Saqlain has approved them (list approvals in Results).
- `grep -rniE "uppercase|text-transform: *uppercase" design/` finds nothing, and no mockup contains lettered or numbered section headings.
- Each mockup passes a contrast check for every text-on-surface pair at 4.5:1, and the hostile-designer checklist: one focal point, one primary action, no removable subtext, consistent spacing scale, looks like a shipped product.
- `design/tokens.json` matches the shared CSS exactly (script-checked).
- The migration map accounts for every template under `app/templates/` and lists must-keep strings from `tests/`.
- Slice handoffs exist for S1 to S9, each naming its tests, file-set guard and screenshot gate.

## Report back

Append a `## Results` section to this file: what was built, the approval list, deviations from the plan, the screenshot gate thresholds chosen, and anything Saqlain still has to decide.

## Results

**Status: partial. Steps 1, 2, 4, 5, 6 and 7 are drafted; step 3 (screen mockups) is not done, so the definition of done is not met.** Nothing is committed (merging and committing are Saqlain's call).

### Built (all in `/Users/saqlainmomin/cyberassess-docs`)
- **Step 1:** the earlier work was already committed (`e13cb7d`). V3-A is merged to `main` (PR #94, `49417b4`). The branch has not been merged with current `main`.
- **Step 2:** `design/yozora-tokens.css` and `design/yozora-components.css` extracted from `v3-polish.html` (mockup chrome removed). Added components the mockup lacked: field variants (invalid, disabled, select, textarea), checkbox, radio, switch, tabs, alert, empty state, skeleton, toast, modal, destructive button, reduced-motion rule.
- **Gallery:** `docs/product/2026-10-01-app-design-mockups/screens/gallery.html` shows buttons (hover, disabled, focus), pills, chips, status, form controls, tabs, alert, table, empty state, skeleton, toast, modal. Checked in the browser in light mode; **dark mode and the static focus ring were not visually verified** (the focus-ring screenshot did not show the ring because programmatic focus does not trigger `:focus-visible`).
- **Step 4:** `docs/product/yozora-design-system.md` (draft) and `design/tokens.json`. `design/tokens_tool.py write|check` regenerates and verifies the JSON against the CSS (check passes). `grep` for `uppercase|text-transform` in `design/` finds nothing. Contrast computed for 15 text/surface pairs, all at least 4.5:1 (lowest: muted on the darkest canvas stop, 4.72).
- **Step 5:** `docs/product/yozora-migration-map.md`, generated by script: all 72 templates, with slice, target pattern, ids, `hx-target`, `hx-swap`, `data-*` and referencing test files. **It lists attributes and test files, not the individual asserted strings**; each slice handoff must grep those test files for strings before building.
- **Step 6:** `docs/product/yozora-fidelity-gate.md`.
- **Step 7:** `tasks/handoffs/2026-10-01-yozora-s1-handoff.md` through `-s9-handoff.md`. They are short and scoped (templates, tests, guard, gate), and generated from a template, so each needs a read-through before it goes to Codex.

### Screenshot gate thresholds chosen
Per-pixel tolerance 0.1; fail above 0.4% differing pixels on app screens, 0.2% on `/design`; any changed region over 40x40 px fails. Widths 1440 and 1024 (390 for client-facing), light and dark. Deliberately strict; untested against a real build.

### Approval list
None. No mockup batch has been shown to or approved by Saqlain.

### Deviations from the plan
- **Step 3 not executed.** Seven mockup batches (about 45 screens, light and dark, seeded data, Opus subagents, designer review, Saqlain approval per batch) cannot be finished or approved in one session. The shared CSS is ready so batches can run in parallel.
- Radii: the file uses 5 and 8 px; the kickoff table said 4 and 6. The file is canonical and the design doc says so.
- `tokens.json` is currently generated *from* the CSS, not the other way round; the flip is in S1.
- Playwright was not installed, so no pixel baselines exist yet; I used the built-in browser for the one gallery check.
- Added `.btn.destructive` (filled red) alongside the existing text `.btn.danger`, for modals only.

### Saqlain still has to decide
1. Commit this work on `claude/app-design-kickoff` and merge `main` into it.
2. Approve running mockup batches 1 to 7 (recommend starting with batch 1, shell and firm, and batch 7, system, since they unblock S1 to S3 and S9). Review the `design/` and gallery first; dark mode in the gallery is unchecked.
3. Sign off `yozora-design-system.md`, including: neutral score ring, accent-contrast rule for firm themes (4.5:1 enforced at upload), 4 s toast, destructive confirm wording.
4. The 40 px score size is in the type scale but not yet a token; confirm it is wanted.
5. Trademark search and registrar check for Yozora (before Track 4).
