# CyberAssess frontend migration: Next.js + Tailwind + shadcn/ui

Status: approved by Saqlain on 12 Oct 2026 for the audit and handoff steps only. Nothing is built. The audit is complete (12 Oct 2026) and sections 4, 6 and 7 are revised from it. The build waits for Saqlain's approval of this revision.

**What approval of this plan starts:** only Step 1 below, the UI audit on Codex (docs only). The migration build (sections 3 to 12) starts after the audit is reviewed and PRs #137 to #140 are merged. Sections 4, 6 and 7 (design system, page archetypes, phases, per-screen work) now follow the audit; sections 3, 5 and 8 (architecture, behaviours, tests) did not depend on it.

## Step 1. UI audit on Codex (do this first)

Saqlain supplied the audit prompt (15 phases, output in `docs/ui-audit/`). It goes to Codex with the changes below. His text is kept in full; these are additions and corrections.

### Already done, handed to Codex as input (verify, do not rediscover)

- **Phase 1 architecture:** done in this session. Stack, CSS files, tokens, macros and their call counts, `app.js` behaviours, inline scripts. Codex gets it as the starting `ARCHITECTURE.md` content.
- **Phase 2 route list:** done. 31 live screens with route, template, partials and purpose (section 7 below), plus 2 client pages and 44 state fixtures. Codex still has to run the app and capture every one.
- **Root causes already found:** 424 inline `style=` attributes, per-slice CSS families, the `field` macro bypassed by most forms, token gaps, no per-screen visual check. Codex confirms or refutes each with screenshots.

### Corrections to the prompt

- There is no Next.js code and no Tailwind in the repo. The "current Next.js migration code" and "Tailwind usage" lines are removed.
- The prompt says to avoid glass and gradients. Today's Yozora system is glass surfaces on a gradient canvas, with 10 written principles in `docs/product/yozora-design-system.md`. Codex must rule on each principle and on the canvas and glass: keep, change or retire, with the reason. This settles the "visual scope" decision.

### Additions

1. **Stack or oversight (Saqlain's question).** Every root cause is classified as one of: caused by the stack (Jinja, HTMX, no component model); a Yozora design decision; an implementation shortcut; or never designed. `ROOT_CAUSES.md` gets this column and `README.md` gets the totals.
2. **Measure, do not eyeball.** Contrast ratios computed for every text token on every surface, in both themes. Content column width in pixels and line length in characters read from the running page. A count of font sizes actually rendered per screen.
3. **Data and states without AI spend.** Run with `OPENROUTER_KEY=""`. Seed with `scripts/demo/seed_demo.py` (Veldhara, 93 ISO controls, 58 evidence files) so screens are full. Capture loading, empty, error, conflict and blocked states from the `/design/pages/{name}` fixtures. Do not trigger analysis, desk review, follow-ups or narrative generation.
4. **Viewports.** 1440 x 1000 and 1280 as written, full-page captures. Add 390 for the client upload page only (it is the one mobile-first screen). Light theme throughout; dark theme on the five Phase 15 screens.
5. **Prototypes (Phase 15).** Static HTML in `docs/ui-audit/prototypes/`, built with Tailwind and shadcn-style markup, using real Veldhara content. No Next.js scaffold and no change under `app/`.
6. **Reconcile with this plan.** Codex receives sections 4 and 7 of this plan and marks each page template and component: agree, change or drop. The audit's archetypes replace templates T1 to T7 where they differ.
7. **Stop point.** Codex stops after Phase 12 (issue register and priorities) and reports. Saqlain adds his own list of problems and answers the Yozora ruling. Phases 13 to 15 (migration spec, component inventory, prototypes) then run against the agreed issues.
8. **Project rules.** Docs-only PR on branch `codex/ui-audit` from `origin/main`. Never read `validation/companies/*/answer_key.json`. No attribution lines. No em dashes. Do not merge.

### How it runs

1. Write the handoff to `tasks/handoffs/2026-10-12-ui-audit.md`: Saqlain's prompt, the changes above, the survey results and a "Report back" section.
2. `git fetch`, then `git worktree add ../dpdpa-ui-audit -b codex/ui-audit origin/main`; link `.venv`, copy `.env`, copy the handoff in.
3. Seed the demo data and confirm the app serves on a spare port and Chromium launches from the harness (`design/harness/screenshot.py`).
4. Dispatch: `codex exec -m gpt-6.1-sol -c model_reasoning_effort="medium" --sandbox workspace-write -C ../dpdpa-ui-audit "<prompt>" < /dev/null`, in the background, with status updates while it runs.
5. If Codex's sandbox cannot launch a browser, Claude captures the screenshots with the harness and Codex audits from those.
6. On the stop point: Claude checks the issue register against the screenshots (adversarial review), then shows Saqlain the top issues and the stack-or-oversight totals.
7. After Saqlain's input: second Codex run for Phases 13 to 15. Claude then revises sections 4 and 7 of this plan and opens the docs PR.

**If #138 (E4 cards) is still unmerged at dispatch,** the review-card screenshots predate E4; the handoff says so and Codex notes it on those screens.

### Verification for Step 1

- All nine files and `screenshots/` exist under `docs/ui-audit/`; every one of the 31 screens has a 1440 and a 1280 capture.
- Every issue in `UI_ISSUES.md` cites a screenshot that exists and a source file or rule.
- Spot-check five contrast ratios and three column widths against the running app.
- `git diff --stat origin/main...HEAD` shows only `docs/ui-audit/` and `tasks/`.

## Step 1 status (12 Oct 2026): audit complete

- Codex ran audit phases 1 to 12. Output is committed locally on `codex/ui-audit` (commit `1d7d67b`, worktree `/Users/saqlainmomin/dpdpa-ui-audit`, not pushed): `docs/ui-audit/` with 24 issues, 12 root causes, measurements, 97 live captures.
- Claude ran the captures on the host (399 of 421) because Codex's sandbox cannot launch a browser.
- Saqlain reviewed the annotated page (https://claude.ai/artifact/KtVkvypbF5FsmB6g9thZyh) and answered every decision. His notes are below.
- Second half (same day): Codex produced the design system, page archetypes, migration UI spec, component inventory and seven prototypes; Claude fixed the failed captures, captured the client upload page at 390, screenshotted and measured the prototypes, and revised sections 4, 6 and 7 below. Results: `tasks/handoffs/2026-10-12-ui-audit-second-run-kickoff.md`.
- The demo app is still running on port 8011 against `data/demo/ui-audit-demo.db`.

## Step 2. Hand off to a fresh session (approving this plan does only this)

This session's context is full. On approval, Claude does four things and stops:

1. Save Saqlain's feedback verbatim to `docs/ui-audit/SAQLAIN_FEEDBACK.md` on `codex/ui-audit`, with the distilled requirements below.
2. Copy this plan to `docs/plans/2026-10-12-001-nextjs-frontend-migration-plan.md` on the same branch.
3. Write `tasks/handoffs/2026-10-12-ui-audit-second-run-kickoff.md` for a fresh Claude session (goal, state, key files, constraints, verification, report back) and commit all three.
4. Update the memory note `project_nextjs_migration.md` and print the one line to paste into the new session.

### What the fresh session does

1. Brief the second Codex run (audit phases 13 to 15: design system, page archetypes, migration UI spec, component inventory, five prototype screens) from the audit plus Saqlain's feedback. Model: `gpt-6.1-sol` for the spec; Luna at extra-high for grunt work; a Sonnet subagent for screenshots and other host-side captures.
2. Fix the 8 failed interaction captures first (selected queue item, conclusion edit mode, cited evidence, confirm dialog) so the spec is checked against them.
3. Review Codex's spec and prototypes against the screenshots, show Saqlain, then revise sections 4 and 7 of this plan and open the docs PR. No migration build in that session.

### Decisions Saqlain made (do not relitigate)

| Topic | Decision |
|---|---|
| Canvas and glass | Retire both. Opaque surfaces on a neutral background. |
| Accents | Keep the 8, for interaction and branding only. |
| Status colours | Rebuild as four families: severity, outcome, progress, provenance. |
| Control codes | Allowed beside titles in lists. |
| Questionnaire navigation | Single framework: that framework's own domains. Multi-framework: domains from the unified control framework, each requirement covered once. One master set of domains per framework. |
| Draft saving | Automatic, as you type. |
| Review queue order | Pending decisions first, then missing or contradictory evidence; sortable and switchable at any time. |
| Target width | Laptop, about 1440. |
| Navigation | Never two navigation bars stacked under each other. Sub-sections inside a tab need a different pattern. |

### Requirements from Saqlain's notes (inputs to the spec)

- **Questionnaire.** The question area must use the width; no narrow column with a blank side. Per question, in this order of weight: what the control requires, why it is asked, a hint on how to put it to the client. Rework help text and the text hierarchy. The answered state after assessment also needs redesign.
- **Review queue.** Each item is a finding. Title it with the gap itself ("Access reviews do not cover all systems"), not the control name. Show: gap statement, compliance status, risk or impact of the non-compliance, recommendation at full weight with its reasoning, and where the finding came from (what was reviewed, who was spoken to) as a short narrative, not an evidence extract. Remove the duplicate "Evidence" and "Evidence on this control" blocks. Settle one data hierarchy for every screen under Review.
- **Conclusions.** Same content as the queue with review mechanics removed: the final gap, in a table with domain, control ID, risk and status, like a standard assessment sheet. Deterministic layout. (Superseded 13 Oct 2026: this screen is now Gaps and also carries the workpaper and remediation; see 4.4.)
- **RFI.** Much simpler: a tight list with good sorting. An item already added to an RFI is not shown again in the same form.
- **Report.** Opens with an executive summary that sets the context (what the engagement was, what was reviewed, domains in scope), the gaps, where they lie, their criticality and overall posture, well written. Then gaps by domain (weakest and strongest), each with the non-compliance, impact if unresolved and risk, readable by a board. A summary view for the board and a detailed view for auditors and technical teams. Recommendations with their logic, following the flow of the exported report.
- **SoA.** Ask only which controls are not applicable and why; everything else is applicable with a standard justification. It does not need its own tab.
- **Content quality (separate track, flagged by Saqlain).** The content itself is not shaped for its reader: report writing, control wording, unified-framework structure, how AI output reads to a consultant. Each deliverable must suit its audience: workpapers for the auditor, reports for boards and executives. This is beyond layout and needs its own plan; the spec must leave room for it and not treat it as solved by redesign.
- **Pitch to hold to.** The tool is useful to consultants: less effort, and still good reports from what the AI can read.

### Scope note for the migration plan

Several of these change what screens show and how data is shaped (findings titled by gap, provenance narrative, master domains, SoA folded away, report restructured). They are more than a restyle. Section 12's "screen PRs change presentation only" no longer holds for Review, Report, RFI, SoA and Questionnaire; the fresh session revises sections 6 and 7 to separate presentation ports from these product changes and flags which need backend or content work.

## 1. Context

**Why.** The UI is 92 Jinja templates, hand-written CSS and HTMX. It does not look like a professional tool: gutters, spacing and text formatting are inconsistent from screen to screen. Saqlain wants reusable components, a modern stack, and no more building screens that will be rebuilt.

**What the survey found (the causes of the spacing and type problems).**
- 424 inline `style=` attributes in the app templates. Spacing is decided per element, not by the system.
- CSS is organised per build slice, not per component: `.cc-*`, `.dr-*`, `.f-*`, `.s8-*`, `.rp-*`, each with its own gaps and paddings.
- The `field` macro is used in 2 files; every other form hand-writes its markup. Macros exist but screens bypass them.
- Token gaps: no z-index tokens, literal radii (3, 7, 12px) beside the scale, heading rules defined twice, `--surface-2` used but never defined, no line-length rule for prose.
- Pixel baselines cover only the shell and the gallery. No screen has a visual check, so drift was never caught.

**What the audit added (12 Oct 2026).** 35 issues (9 P0) and 16 root causes, of which one is caused by the stack; the rest are design decisions, shortcuts or things never designed, so a framework change alone fixes almost nothing. Measured at 1440: the question column is 576px inside a 1040px page; questionnaire guidance is 12px at about 100 characters a line; the RFI page is 20,005px tall; the applicability page 17,481px; up to three navigation levels are stacked. Saqlain's review added that findings are titled by control instead of by gap, the recommendation is boxed small, evidence is shown twice, and the content itself is not written for its reader.

**Outcome.** A Next.js app in `web/` that owns every consultant screen, built from one component library whose layout primitives own all spacing and type. FastAPI stays as the JSON API and keeps scoring, the LLM pipeline and report generation. The Yozora gradient canvas and glass surfaces are retired for opaque surfaces on a neutral background; the 8 accents stay for interaction and branding; status colours are four typed families; layout, width and typography are rebuilt; navigation never stacks two bars. Inter stays. Five screens also change what they show (Questionnaire, Review, RFI, Scope applicability, Report); those changes are separate backend and content work (sections 6.2 and 6.3), not part of a restyle.

**Rules this changes on purpose.** The session record says "no rebuild" (E1) and fixes the sequence (rule 5). Step 0a records a new decision (E9) that edits both. Nothing here touches the judge prompt, the v2 park, scoring or the held-out answer keys.

## 2. Decisions

| # | Decision | Status |
|---|---|---|
| 1 | Plan now, build after #137 to #140 merge. No new Jinja screens after that. | Decided (Saqlain) |
| 2 | Cut over screen by screen; the app works throughout. | Decided (Saqlain) |
| 3 | FastAPI stays as the API. No Python port. See section 10 for the no-FastAPI estimate. | Decided (Saqlain) |
| 4 | Retire canvas and glass; keep accents for interaction and branding; rebuild status colours. See Step 2. | Decided (Saqlain) |
| 5 | Client magic-link page and the report HTML that feeds PDF stay in FastAPI/Jinja. | Recommended |
| 6 | Auth, CSRF and hosting stay in Track 4. Next and FastAPI run same-origin locally, so none is needed now. | Recommended |

## 3. Target architecture

```
browser -> Next.js (web/, port 3000)
             |- routes Next owns: rendered by React
             |- everything else: rewritten to FastAPI (port 8001)
                  /api/*  /static/*  /magic/*  file downloads  not-yet-migrated pages
```

- **Location:** `web/` at the repo root. `website/` (the marketing page on Vercel) is untouched.
- **Stack:** Next.js App Router, TypeScript strict, Tailwind v4, shadcn/ui (Radix), `lucide-react`, Inter through `next/font/local` using the existing woff2 files.
- **Strangler routing:** `next.config` fallback rewrites send any path Next does not own to FastAPI. A screen is "migrated" when its Next route exists and the Jinja route is deleted.
- **Legacy shell change (step 0b):** remove `hx-boost="true"` from `app/templates/base.html`. Boosted links would otherwise swap a Next page into a Jinja body.
- **Reads:** Server Components call FastAPI through one typed client (`web/lib/api.ts`).
- **Writes:** Server Actions post JSON to FastAPI, then revalidate. One error envelope: `{detail, field_errors?, blockers?, conflict?}`.
- **Polling:** one client hook (`usePoll`) for analysis and desk-review status, every 3 s, replacing `hx-trigger="every 3s"`.
- **Types:** `openapi-typescript` generates `web/lib/api-types.ts` from FastAPI's OpenAPI. A pytest check fails if a `/api/ui` route lacks a `response_model`.
- **Reviewer name:** today a free-text `#reviewer-name` input repeated on pages. Becomes "Working as" in the user menu, stored in a cookie and sent with every write. Real identity stays Track 4.

### Backend pattern (applied per screen)

1. Move the view-model code out of `app/routers/web.py` into `app/services/views/<area>.py`, returning Pydantic models. Examples to extract: `_home_attention_rows` (338), `render_assessment_detail` (1914), `report_summary` (3182), `_issued_report_rows` (970), `desk_review_status_view` (3648), `_inventory_fragment_context` (1632).
2. The Jinja route calls the new function, so legacy tests stay green.
3. Add `GET /api/ui/<screen>` returning the same model as JSON.
4. Mutations that return HTML today (`conclusions.py`, `findings.py`, `drafting.py`, `requirement_review.py`, `magic.py` consultant routes, most of `web.py`) get JSON variants. The 409 conflict diff from `conclusions._conflict_context` is returned as JSON.
5. In the cut-over PR: delete the Jinja route, template, partials and their HTML-asserting tests; add JSON tests for the endpoint.

Template globals that run queries during render (`engagement_period`, `latest_issued_version`, `engagement_assessment_meta`, `assessment_engagement_context`, the `review_count` badge) move into the view models or a `GET /api/ui/shell` endpoint. Regulatory content in `web.py` (DPDPA penalty and domain maps near 3040 to 3116) moves to `app/services/`, never to React.

## 4. Design system: how the components translate and how the mistakes stay fixed

Revised 12 Oct 2026 from the audit's second half. The detail lives in `docs/ui-audit/DESIGN_SYSTEM.md`, `PAGE_ARCHETYPES.md`, `NEXTJS_MIGRATION_UI_SPEC.md` and `COMPONENT_INVENTORY.md`; where this section and those files differ, the audit files win. Seven static prototypes in `docs/ui-audit/prototypes/` show the system on real Veldhara content.

### 4.1 Tokens

- `design/tokens.json` stays the single source. `design/tokens_tool.py` gains an output, `web/app/tokens.css` (CSS variables for light, dark and the 8 accents).
- The gradient canvas and the glass and blur tokens are removed. Surfaces are opaque steps on a neutral background, with borders for separation and elevation only for things that overlap (menus, dialogs).
- The 8 accents keep today's hues and are used for interaction, selection and branding only. The seven dark-theme accent text pairs that fail contrast are corrected. An accent never carries status.
- Status colours are four typed families: severity, outcome, progress, provenance. Each member has one label, one icon and one measured foreground and background pair (all 144 target pairs pass AA; `docs/ui-audit/target-contrast.json`). A status is always shown in words.
- Tailwind's `@theme` maps to these variables. The default Tailwind colour, spacing, radius and font-size scales are switched off, so only system values exist as utilities.
- Gaps filled: z-index scale, one mono font token, weights, the stray radii folded into the scale, `--surface-2` removed.
- Per-firm accent: wire the stored firm setting through `/api/ui/shell` (today only the env var works).

### 4.2 Layout and type primitives (the fix for gutters and text)

Screens are built only from these. A screen file may not set margin, padding, font size or colour.

| Primitive | Owns | Ruling on the earlier list |
|---|---|---|
| `AppShell`, `Sidebar` | Frame, 224px sidebar, 24px gutters, user menu, mobile drawer | Agree |
| `PageHeader`, `Breadcrumb` | Title row (the task name, never the client name repeated), period and cut-off line, actions | `TopBar` is dropped; it would be a second bar |
| `Page(mode)` | Width mode: inventory and task 1168px at 1440 and 1008px at 1280; document 880px | Changed: one width for every page caused the 576px question column |
| `Section` | Vertical rhythm; a bounded surface only when a region is a distinct work area | `Card` is dropped as a default wrapper |
| `Stack`, `Cluster`, `Grid`, `Split` | All gaps, from the spacing scale only | Agree |
| `Heading`, `Text`, `Prose` | Type roles. Audit content (questions, gaps, conclusions, quotes, criteria, recommendations, guidance) is 14px or more; body and recommendations 16px. Only identifiers, timestamps and table meta may be 12px. `Prose` caps lines at 72ch | Changed: roles, not sizes |
| `DataTable`, `KeyValue`, `Toolbar` | Table density, numeric alignment, sort and filter rows | Agree |

### 4.3 Page archetypes (replace templates T1 to T7)

Seven archetypes cover all 31 screens. Each is built once in the gallery with real seeded data and signed by Saqlain before any screen uses it. This is the single design pass at build (two-pass rule); the second pass is before exposure.

| Archetype | Used by | Replaces |
|---|---|---|
| Inventory | Home, Clients, Engagements, Reports, Evidence inventory (3 scopes), Evidence reuse, Requests, RFI, Remediation, Gaps, Versions, Comparison | T1 (agree); takes Conclusions from T4 and Versions and Comparison from T2 |
| Entity | Client, Engagement overview, Assessment overview | T2 (changed: no generic card pages) |
| Task | Questionnaire, Desk review, run states | T3 and T6 (changed: one stepper as navigation across stages, every step a link; the questionnaire is a workspace, not a forced wizard) |
| Queue | Review queue, Portfolio review | T4 (changed: only the queue needs a permanent selection pane) |
| Form | New engagement, New assessment, Scope with applicability, Settings, Board inputs, AWS evidence, Purge, Client upload | T5 (changed: SoA becomes a panel in Scope) |
| Document | Evidence record, Narrative, Report (board and auditor views), Integrated reports | T7 (agree) |
| Recovery | Error pages, invalid and expired client links | New |

### 4.4 Navigation

- **Decided 13 Oct 2026 (Saqlain): a stepper, not option A or B.** One sidebar that can be hidden, one context line (breadcrumb, period and cut-off), and one stepper inside an assessment (Overview, Scope, Evidence, Questionnaire, Review, Report). Entering an assessment replaces the engagement's navigation.
- Every step is a link. Completed stages show a tick. It is not a forced wizard.
- **Decided 13 Oct 2026 (Saqlain): Review is two screens, Queue and Gaps.** Conclusions, Findings and Workpaper stop being screens. A gap is an approved conclusion that is not compliant; its workpaper and its remediation are sections of the gap; compliant controls are an "All controls" filter on Gaps; the run trail moves to Overview and the report's auditor detail. Why: Queue and Conclusions rendered the same card twice, and a finding was a second record made by hand from an approved gap (in the demo, 28 of 34 gaps had none, so they were missing from the PDF findings section, the board deck, the narrative and the remediation tracker, all of which read findings).
- **Never a second bar under the stepper.** The open stage shows its sections inline beside its name (Review: Queue, Gaps; Evidence: Documents, Requests, Client links, plus Desk review and Reuse; Scope: Boundaries, Applicability; Report: Versions, Comparison, Narrative, Board inputs where they exist).
- The sidebar hide state persists per user. The questionnaire's domain rail stays when the sidebar is hidden.
- Full rules and type roles: the "Second-pass amendment" section at the top of `docs/ui-audit/DESIGN_SYSTEM.md` and `docs/ui-audit/NEXTJS_MIGRATION_UI_SPEC.md`. It overrides the rest of those documents and section 4.1 of this plan where they differ. Values: `docs/ui-audit/prototypes/prototype.css`.
- Report board summary and auditor detail are two views of one page, switched by a two-option toggle, not navigation.
- Steps and sections are links with `aria-current`. Section, framework, domain and selected finding are in the URL, so Back, reload and copied links restore them.
- The shell Search field is not ported until it has a result contract.

### 4.5 Components

The component inventory is `docs/ui-audit/COMPONENT_INVENTORY.md` (40 contracts with variants, states and where used). Rulings against the earlier lists are in the spec, "Component rulings". The changes that matter:

| Earlier | Now | Why |
|---|---|---|
| `Card` | `Section` | Cards everywhere flattened the hierarchy |
| `ToggleGroup` as sub-navigation | Section pattern from 4.4 | No stacked bars |
| `OutcomeBadge`, `SeverityBadge`, `EvidenceStatusBadge`, `StatusIndicator` | `StatusBadge(family, member)` | One typed mapping; a caller cannot pass an arbitrary colour |
| `ConclusionCard`, `RequirementBody`, `FindingCard`, `WorkpaperEntry` | `FindingDetail` with `ReviewDecision` | One data hierarchy for every screen under Review (spec, "Review hierarchy") |
| `RequestCard` | `RequestRow` | Tight sortable list with guidance on demand |
| `ScoreRing`, `Distribution` | Text score, `DomainSummary` | Labelled numbers, no decoration |
| `Stepper` | `Progress` on Overview only | Not a second navigation |
| `Form` | `Field` | Field-level label, help, error and draft state |

Unchanged from the earlier list: `Button`, `Field` inputs, `Choice`, `DataTable`, `Dialog`, `Sheet` (as `Inspector`), Sonner, `Alert`, `Skeleton`, `Tooltip`, `DropdownMenu`, `Breadcrumb`, `Pagination`, `Disclosure`, `CitationBlock`, `EvidenceViewer`, `QuestionCard`, `UploadDropzone`, `RunStatus`, `CodeBlock`, `lucide-react` icons.

### 4.6 Guard rails (so it does not drift again)

- ESLint, failing CI: no `style` prop; no Tailwind arbitrary values (`p-[13px]`, `text-[#...]`); no raw hex; no spacing, colour or font-size utilities in `web/app/**` (only inside `web/components/**`).
- Gallery route `/design` in Next: every component and every state (loading, empty, error, saving, locked, conflict), light and dark. The 44 existing preview fixtures in `app/routers/design*.py` are the state checklist.
- Pixel baselines for every screen at 1440, 1280 and 390 (client upload), both themes, reusing `design/harness/screenshot.py`. A PR that changes a screen updates its baseline in the same PR.
- Measured checks per screen, from the spec's P0 table: audit content at 14px or more; prose lines 60 to 80 characters; no horizontal overflow at 1280; exactly one horizontal navigation bar inside an assessment; every status visible in words; keyboard reaches every control.
- A new screen must name its archetype. A new archetype needs a decision.
- Framework-specific copy stays conditional (`has_dpdpa`), checked in review.

## 5. Client behaviours to re-implement

| Today (`app.js` and inline scripts) | In Next |
|---|---|
| Toasts from `X-Toast-*` headers | Sonner, fired from Server Action results |
| Button loading, 300 ms skeleton, inline request alert | `useTransition`, `loading.tsx`, `Alert` |
| `HX-Redirect`, `HX-Refresh` | `redirect()`, `revalidatePath()` |
| 409 conflict card (`X-Conclusion-Conflict`) | `ConclusionCard` conflict state from JSON |
| `hx-confirm` modal, typed purge confirm | `ConfirmDialog` |
| Menus, modal focus trap, tooltips | Radix |
| Row click `tr[data-href]` | `DataTable` row link |
| Copy to clipboard, checksum copy | `CopyButton` |
| Theme light/dark/system, pre-paint script | `next-themes` on `data-theme` |
| Context wizard state in `window._contextAnswers` | Wizard component state |
| Questionnaire validation, save indicator, collapsed sections | Form state, `localStorage` |
| Upload drag-drop and progress | `UploadDropzone` |
| SoA bulk save, evidence-reuse bulk confirm (sequential `fetch`) | One Server Action each |
| Review queue select and `j`/`k` | Client component |
| Polling every 3 s | `usePoll` |
| Dead code (dashboard filter, review filter, old shortcut help) | Not ported |

## 6. Phases (Saqlain clicks through each PR)

**On hold, 13 Oct 2026 (Saqlain).** The build does not start until the content problems found by the content audit are fixed, because a port would carry them across. Content first; then the prototypes are regenerated, this plan is finalised, and the port follows. The tracks, rows and PR counts below are the state before that work and will change. See `tasks/handoffs/2026-10-13-ui-thread-record-for-content-session.md`.

Revised 12 Oct 2026. The audit showed that five areas are more than a restyle: Questionnaire, Review, RFI, Scope applicability and Report change what the screen shows and how the data is shaped. So the work is split into three tracks that must not be mixed in one PR.

- **Track A, presentation ports.** The data exists today in the shape needed. A port changes layout and components only. Where a new slot has no data yet (for example a gap title), the screen shows the existing field or an honest "not recorded" state; it never invents text.
- **Track B, product changes.** A new field, data shape, endpoint or stored state. Each one is backend work with its own tests and lands before or after the port of its screen, never inside it.
- **Track C, content.** Writing and prompt work: what the tool says, to whom. It gets its own plan (section 6.3). The UI leaves the slots; the redesign does not claim to fill them well.

### 6.1 Track A: presentation ports (about 26 PRs)

| Phase | PRs | Content |
|---|---|---|
| P0 Foundations | 5 | Decision record; scaffold and proxy; tokens and base components; primitives, shell and the seven archetypes; API conventions |
| P1 Portfolio | 3 | Home, Clients, Client, Engagements, Portfolio review, Reports, error pages |
| P2 Engagement and firm | 4 | New engagement, Engagement, New assessment, Remediation, Integrated reports, Requests, AWS, Purge, Settings |
| P3 Evidence | 3 | Inventory (3 scopes), Evidence record, Reuse, Desk review |
| P4 Assessment workspace | 4 | Shell and overview, Scope, Questionnaire (two PRs), Report |
| P5 Review | 2 | Queue; Gaps (register, with the workpaper and remediation sections of a gap) |
| P6 Reporting | 3 | Versions and Comparison, Narrative and Board inputs, RFI |
| P7 Decommission | 2 | Remove Jinja UI, HTMX, old CSS, design routers, old tests; restyle the client upload page with the new tokens and fix its keyboard path; docs |

### P0 steps

- **0a** Decision E9 in `tasks/2026-10-08-session-record.md` (sequence edit, no new Jinja screens, rule 2 exception for backend-only work). Fix `CLAUDE.md` (Tailwind line, `tests/yozora_paths.py` line). Add `.claude/rules/web.md` scoped to `web/**`.
- **0b** Scaffold `web/`; fallback rewrites; remove `hx-boost`; CI job (lint, typecheck, build); `/run` skill starts both servers.
- **0c** Tokens output (opaque surfaces, four status families), Tailwind theme, shadcn base components, gallery page.
- **0d** Layout and type primitives, `AppShell`, the seven archetypes in the gallery, ESLint rules, measured checks, screenshot harness pointed at Next. **Saqlain signs the archetypes and picks the section pattern (4.4) here.**
- **0e** `/api/ui` conventions, error envelope, `GET /api/ui/shell` (nav, review count, branding, accent), OpenAPI type generation, `response_model` guard test.

### 6.2 Track B: product changes (10 backend PRs)

The audit classified 60 requirement parts: 32 presentation, 14 backend, 14 content (`docs/ui-audit/requirements.json`; spec, "Requirement classification"). The 14 backend parts group into these PRs.

| # | Product change | Backend work (checked against the code) | Needed by | Content it waits on |
|---|---|---|---|---|
| B1 | Questionnaire drafts save as you type; completing a section is a separate act | New `PATCH /api/assessments/{id}/questionnaire/drafts` (partial upsert, version check, 409 with diff). Today both save routes mark the questionnaire done (`app/routers/questionnaire.py`) | P4 Questionnaire | None |
| B2 | Questionnaire navigation by the framework's own domains; unified domains for multi-framework | Ordered domain tree from the registry (`app/frameworks/definitions/`); for multi-framework, one master list from `UnifiedControlCluster.domain_group` and `DOMAIN_GROUP_ORDER` (`cluster_engine.py`, `mapping.py`), with a check that each in-scope requirement is covered once | P4 Questionnaire | None |
| B3 | Per question: what the control requires, why it is asked, how to put it to the client | `why_asked` and `client_prompt_hint` on `QuestionDef` (`app/frameworks/schema.py`) and in the serializers | P4 Questionnaire | C1 |
| B4 | A finding is titled by its gap and carries impact and the reason for the recommendation | `gap_title`, `impact_statement`, `recommendation_reason` on `Conclusion` (today: `rationale`, `evidence_summary`, `gaps_identified`, `risk_level`, `recommended_action`); carried into the existing `Finding.title` and `Finding.business_impact` on approval. Analyzer output schema gains the three fields; **the v1 prompt path and the parked v2 pipeline are not retuned without a decision** | P5 Queue, Gaps; P4 Report | C2 |
| B5 | "Where this finding came from": what was reviewed and who was spoken to | Interview record (who, role, date, notes, linked evidence) as a new model, service and router; `provenance_narrative` on `Conclusion` built from revision citations and interview records. No interview is ever inferred | P5 Review | C2 |
| B6 | One typed `FindingDetail` read model for every Review screen | `/api/ui` DTO with the ordered field list in the spec; optional new fields have an explicit missing state | P5 | None |
| B7 | RFI: an item already in an RFI is not offered again | Common artifact identity across checklist items, conclusion requests and added requests; `included_ids`, issued and received state in JSON (`app/models/rfi.py`, RFI services) | P6 RFI | None |
| B8 | Applicability asks only for exclusions | Exclusion state (control, reason, actor, version) in Scope; `build_soa` uses a standard justification for the rest. Today justifications are audit-event metadata and do not change applicability | P4 Scope | C3 |
| B9 | Report opens with written context and has board and auditor views | Report JSON exposes engagement context, accepted narrative sections and their freshness (reuse `app/services/narrative.py` and `board_report.build_document`); board read model ordered weakest to strongest. `approved_report._summary_text` is a string of counts and is not the executive summary | P4 Report | C4 |
| B10 | Approving a gap creates its remediation record; no manual "Create finding" step | On approve or edit-and-approve of a conclusion whose outcome is a gap, create the `Finding` and its first `Action` from the conclusion (the prefill that `findings_page` in `app/services/findings.py` already computes: title, description, severity, priority, first action). One-off backfill for approved gaps with no finding. A reopened or rejected conclusion keeps its finding flagged, as `source_approved` does today. Readers do not change: `report_content.assessment_findings`, `board_report`, `narrative`, `board_inputs`, `remediation_rollup`, `actions_export`. Legacy bulk approvals stay excluded. The per-control workpaper fields (client response, mapped evidence, proposal checks, revisions from `workpaper.build_workpaper`) join the B6 read model; analysis runs are exposed to Overview, and exclusions and unconcluded requirements to the report's auditor detail | P5 Gaps | None |

Order: B1, B2, B6 and B10 have no content dependency and go first. B10 changes what the PDF, board deck and tracker contain for existing assessments (every approved gap appears, not only those someone created a finding for), so it needs a decision record before it lands. B4 is the largest and gates the Review ports reading well; the Review screens can port against existing fields before it lands. Analysis must also stop blocking the request (background task and polling) before the Questionnaire cut-over; that was already in this plan and stays in P4.

### 6.3 Track C: content (its own plan, not written here)

Saqlain flagged this separately: the content is not shaped for its reader. The redesign gives each piece a slot and a reader; it does not make the words good. A content plan must cover at least:

| # | Content | Authored once or per assessment | Reader |
|---|---|---|---|
| C1 | "Why we ask" and "how to put it to the client" for every question; control wording | Once per control | Consultant |
| C2 | Gap titles, impact statements, recommendation reasoning, provenance narrative | Generated per assessment, reviewed by the auditor | Auditor, then client |
| C3 | Standard applicability justification | Once | Auditor, certification body |
| C4 | Executive summary and domain narrative, board wording against auditor wording | Generated per assessment, accepted by the auditor | Board and executives |
| C5 | Unified control framework: domain names and structure | Once | Consultant |
| C6 | RFI request wording, examples and "good looks like" | Once per artifact | Client |

C6 detail from Saqlain's review (13 Oct 2026), handed to the parallel content session: a request titled for two things (a policy and review records) lists about fifteen documents, and the example and "good looks like" restate the title. The presentation needs, per request, a short list of documents that matches its title and, per document, the controls it supports as structured data (today the list is one paragraph, split mechanically). His idea of a first-level request (policy, procedure, record) with more requested after review is a product change: recorded here, not designed.

C2 and C4 touch prompts. They need a decision record before any prompt changes, and they are evaluated on the held-out set without reading the answer keys.

## 7. Every screen

Revised 12 Oct 2026. The per-screen regions, states and changes are in the spec ("Per-screen replacement for plan section 7"). This table keeps the routes and says, for each screen, which archetype it uses and whether it is a presentation port only or also waits on a product change (Track B) or content (Track C).

Legend: "API new" means a `/api/ui` read model must be added; "json" means a JSON endpoint already exists. "Port" means presentation only.

### P1 Portfolio

| Screen | Jinja today | Next route | Archetype | Work | Track |
|---|---|---|---|---|---|
| Home | `pages/dashboard.html`, `partials/engagement_list.html` | `/` | Inventory | API new (attention rows, engagement rows). Empty and legacy-client states. | Port |
| Clients | `pages/clients.html` | `/clients` | Inventory | API new. Search and industry filter in the URL. | Port |
| Client | `pages/client_detail.html` | `/clients/[id]` | Entity | API new. Engagements, retention and purge records. | Port |
| Engagements | `pages/engagements.html` | `/engagements` | Inventory | API new. Status filter, search. | Port |
| Review (all engagements) | `pages/review.html` | `/review` | Queue | API new. Feeds the sidebar count. Rows gain gap titles when B4 lands. | Port; B4 |
| Reports (issued) | `pages/reports.html` | `/reports` | Inventory | API new from `_issued_report_rows`. | Port |
| Errors | `pages/error.html` | `not-found.tsx`, `error.tsx` | Recovery | Three variants, reference code, one safe next step. FastAPI keeps JSON errors. | Port |

### P2 Engagement and firm

| Screen | Jinja today | Next route | Archetype | Work | Track |
|---|---|---|---|---|---|
| New engagement | `pages/new_engagement.html`, `partials/client_picker.html` | `/engagements/new` | Form | JSON create with field errors. The create button stays visible with its prerequisite stated (UI-018). Drop legacy `POST /assessments`. | Port |
| Engagement overview | `pages/engagement_detail.html` | `/engagements/[id]` | Entity | API new. Stage, next step, assessments, links summary. | Port |
| New assessment | `pages/new_assessment.html` | `/engagements/[id]/assessments/new` | Form | Framework multi-select; json create exists. | Port |
| Findings and actions | `pages/remediation_tracker.html` | `/engagements/[id]/remediation` | Inventory | API new. XLSX export stays a FastAPI download. | Port; B4 |
| Integrated reports | `pages/integrated_reports.html` | `/engagements/[id]/integrated-reports` | Document | Generate and issue (confirm dialog); json exists, drop `HX-Redirect`. | Port; B9, C4 |
| Requests | `pages/requests.html`, `partials/magic_links.html` | `/engagements/[id]/requests` | Inventory | JSON for create and revoke link. Token shown once with copy. Claude-owned (security boundary). | Port |
| AWS evidence | `pages/aws_evidence.html`, `partials/aws_evidence_panel.html` | `/engagements/[id]/aws-evidence` | Form | JSON for pull result. | Port |
| Purge | `pages/engagement_purge.html` | `/engagements/[id]/purge` | Form | Typed confirm. Claude-owned (destructive). 409 guard states. | Port |
| Settings | `pages/firm_settings.html` | `/settings` | Form | Firm identity, accent picker with the contrast rule, retention years, archive and unarchive. | Port |

### P3 Evidence

| Screen | Jinja today | Next route | Archetype | Work | Track |
|---|---|---|---|---|---|
| Evidence inventory (3 scopes) | `pages/evidence_inventory.html`, `partials/document_list.html`, `upload_status.html` | `/evidence`, `/engagements/[id]/evidence`, `/assessments/[id]/evidence` | Inventory | One component, three scopes. Upload dropzone, new version, archive, filters. The "supports" count opens the full mapping (UI-014). Read status per file from the reads plan lands here. | Port |
| Evidence record | `pages/evidence_detail.html` | `/evidence/[id]` | Document | New JSON for viewer blocks and cited span. An ambiguous filename match is shown as unresolved, not as a summary (UI-015). `/evidence-versions/{id}/span` redirect kept. | Port |
| Evidence reuse | `pages/evidence_reuse.html` | `/assessments/[id]/evidence-reuse` | Inventory | Bulk confirm as one action. | Port |
| Desk review | `pages/desk_review.html`, `partials/desk_review_*.html` | `/assessments/[id]/desk-review` | Task | `RunStatus` plus `usePoll` on the existing JSON status. Move the logic in `run_desk_review_web` into a service. | Port |

### P4 Assessment workspace

| Screen | Jinja today | Next route | Archetype | Work | Track |
|---|---|---|---|---|---|
| Workspace shell and Overview | `pages/assessment.html`, `partials/assessment_header.html`, `framework_tabs.html`, `framework_hub_panel.html`, `framework_panel.html` | `/assessments/[id]` (layout) | Entity | Layout holds header and the one stage bar. Title is the task, not the client name. Stages become real routes; old `?tab=` URLs redirect. | Port |
| Scope, with applicability | `partials/scope_tab.html`, `scope_form.html`, `scope_complete.html`, `pages/soa.html` | `/assessments/[id]/scope` | Form | Scope form; complete state with checklist links. Applicability becomes "controls that do not apply, and why" inside Scope; the SoA tab and its 17,481px page go. | Port; B8, C3 |
| Questionnaire | `partials/questionnaire_tab.html`, `question_step.html`, `context_complete.html`, `screening_form.html`, `questionnaire_sections.html`, `section_questions.html`, `section_saved.html`, `followup_questions.html`, `analysis_*.html` | `/assessments/[id]/questionnaire` | Task | Full-width question surface with a domain rail. Per question: requirement, why asked, how to ask, answer, notes. Answered state redesigned. **Analysis must stop blocking the request:** background task, then poll. Two PRs. | Port; B1, B2, B3, C1 |
| Report | `partials/report_tab.html`, `report_summary.html`, `no_report.html`, `remediation_panel.html`, `remediation_summary.html` | `/assessments/[id]/report` | Document | Opens with the written executive summary, then domains weakest to strongest, then recommendations with their logic. Board summary and auditor detail toggle. PDF download stays FastAPI. | Port; B4, B9, C4 |

### P5 Review

| Screen | Jinja today | Next route | Archetype | Work | Track |
|---|---|---|---|---|---|
| Review queue | `pages/review_queue.html`, `components/conclusion_card.html`, `requirement_card_body.html`, `partials/remediation_draft.html` | `/assessments/[id]/review` | Queue | Findings titled by the gap; outcome and risk in words in the list; decision bar attached to the selected finding; one provenance block; pending first, then evidence issues, switchable. `j`/`k`. | Port; B4, B5, B6, C2 |
| Gaps | `pages/conclusions.html`, `pages/findings.html`, `components/finding_card.html`, `pages/workpaper.html`, `components/workpaper_entry.html` | `/assessments/[id]/review/gaps` | Inventory | One register replaces Conclusions, Findings and Workpaper. Table: domain, control ID, gap, risk, status, owner; opens on controls with a gap, "All controls" as a filter in the URL. A row expands to the remediation section (recommendation, owner, actions, target, status, closure evidence; `expected_history_length`) and the workpaper section (client answer, evidence links, AI proposal and checks, decision, revisions). Reopen decision on the gap; conflict diff from JSON. "Export workpaper" calls the standalone workpaper HTML, which stays in Python. Report basis and release panels move to Report; analysis runs move to Overview. | Port; B4, B5, B6, B10 |

### P6 Reporting

| Screen | Jinja today | Next route | Archetype | Work | Track |
|---|---|---|---|---|---|
| Versions | `pages/report_snapshots.html` | `/assessments/[id]/report/versions` | Inventory | Generate, issue (confirm), downloads from FastAPI, checksum copy. Report type is in the URL. Claude-owned (immutable snapshots). | Port |
| Comparison | `pages/comparison.html` | `/assessments/[id]/report/compare/[otherId]` | Inventory | json exists (`reports.py` compare). | Port |
| Narrative | `pages/narrative.html` | `/assessments/[id]/report/narrative` | Document | Generate, accept, discard AI sections; a draft saves without being accepted (UI-019). | Port; C4 |
| Board inputs | `pages/board_inputs.html` | `/assessments/[id]/report/board-inputs` | Form | Observations, owners, initiatives, asks. json exists. | Port |
| RFI | `pages/rfi.html`, `partials/rfi_links.html` | `/assessments/[id]/evidence/requests` | Inventory | One tight sortable list, guidance on demand (document names only, controls supported behind a toggle, no slot that repeats the title), items already in the RFI grouped and not offered again; versions and client links as sections, not a third bar; 20-item limit on a link. | Port; B7, C6 |

### Stays in FastAPI and Jinja

| Item | Why |
|---|---|
| `magic/upload.html`, `magic/invalid.html` | Strict CSP, no-store headers, token redaction, works without JS. In P7: new tokens, a keyboard path to the file control (UI-011), the error placed on the item that failed, heading before the intro, one brand name. |
| `reports/board_report.html`, `reports/workpaper_standalone.html` | Input to WeasyPrint. PDF sections are additive-only. |

### Removed, not ported

`pages/login.html` (no login until Track 4), `pages/design*.html` and `app/routers/design*.py` (replaced by the Next gallery), `pages/soa.html` as its own page, `partials/status_timeline.html`, `partials/review_finding_card.html` (endpoint returns 410), the three unused `*_status_badge.html` files, `partials/yozora_page_controls.html`, the dead `documents_tab` include, legacy `POST /assessments`, the shell Search field until it has a result contract.

## 8. Tests

- **Backend:** each `/api/ui` endpoint gets JSON tests. Service and scoring tests are untouched.
- **Retired with their screen:** the HTML-asserting tests for that template (the mapping is in `docs/product/yozora-migration-map.md`). Roughly 25 to 45 percent of the 1,393 test functions assert HTML or template source; this is an estimate from grep.
- **Retired in P7:** `test_design_lint.py`, `test_yozora_*.py`, `test_design_tokens_in_sync.py` is extended, not removed.
- **Frontend:** Playwright smoke per screen (load, one write, one error state) and the pixel baselines. Vitest only for components with logic (`ConclusionCard`, `FindingCard`, wizard, `usePoll`).
- **Parity checklist per screen PR:** every action, state and link from the Jinja screen is listed and ticked in the PR body.
- **Coherence test:** each screen PR names its loop step and confirms AI output is still visible and checkable against the original in one click.

## 9. Ownership and process

- Claude: P0 design and API conventions, handoffs, review of every Codex PR, and the security or irreversible screens (Requests, Purge, Versions, release).
- Codex: screen ports from handoffs, one handoff per PR.
- Each PR: adversarial review by the other agent, then Saqlain's click-through. Claude opens PRs and does not merge.
- Reads-plan and flow-plan work that adds UI waits for its area in this plan. Backend-only stages may run alongside if their files are disjoint.

## 10. If FastAPI were removed too (asked by Saqlain)

Measured size of what would have to be rewritten in TypeScript:

| Area | Lines | Files |
|---|---|---|
| `app/services` | 30,621 | 76 |
| `app/frameworks` + `app/dpdpa` | 19,322 | 32 |
| `app/routers` | 11,129 | 34 |
| `app/utils`, `models`, `schemas` | 4,202 | 39 |
| `tests` | 58,372 | 152 |

Also replaced: SQLAlchemy and Alembic, `fpdf2`, WeasyPrint, `python-docx`, `python-pptx`, `openpyxl`, `pdfplumber`, `boto3`.

- **Effort (my estimate, not measured):** about 27 presentation PRs and 9 backend PRs for this plan, with the content track planned separately. A full port adds roughly 90 to 120 more, so four to five times the work.
- **Risk:** the approved board deck, PPTX, XLSX and PDF formats would be regenerated by different libraries and would not match. Deterministic scoring, the frozen v1 prompt path and the golden recordings would all need re-validation.
- **Benefit to the auditor:** none visible. The problems named (spacing, text, components) are all in the frontend.
- **Recommendation:** do not port. If one language is still wanted later, decide it after P7, when the API boundary is clean and the frontend no longer depends on Python templates.

## 11. Verification

- P0: `cd web && npm run lint && npm run typecheck && npm run build`; `pytest`; open `/design` in Next in light and dark; open a legacy page through port 3000 and confirm it still works and links cross over with full page loads.
- Each screen PR: `pytest`; `npm run lint typecheck build`; Playwright smoke for the screen; pixel baseline at 3 widths and 2 themes; run the Veldhara seed and click the screen through port 3000; confirm the Jinja route returns 404 and old URLs redirect.
- P7: `grep -r "hx-" app/templates` returns only `magic/`; `app/static/js/app.js` and `vendor/htmx` are gone; full Veldhara walkthrough from new engagement to issued report on the Next app.

## 12. Risks

| Risk | Handling |
|---|---|
| Two shells look different mid-migration | Accepted: the new shell is opaque and neutral, the old one is glass on a gradient. Move the highest-traffic areas in order (P1 to P6) so the overlap is short. |
| Analysis request blocks for minutes behind the proxy | Background task plus polling in P4, before the questionnaire cut-over. |
| Hidden behaviour lost in a port | Parity checklist from the migration map; adversarial review. |
| Test count drops as HTML tests retire | Each retired test is replaced by a JSON test or a Playwright check in the same PR. |
| Scope creep into redesigning features | Track A PRs change presentation only. The product changes the audit found are named in Track B (section 6.2), each its own backend PR; anything else goes to the parking lot. |
| A port ships a slot with no data and it gets filled with invented text | Slots show the existing field or "not recorded". New text arrives only through Track B fields and Track C content. |
| Content quality is assumed solved by the redesign | It is not. Track C has its own plan; C2 and C4 need a decision record before any prompt change. |
