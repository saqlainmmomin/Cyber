# App (UI/UX) design kickoff

**Status:** kickoff only. No design work has started. Written 2026-10-01, at the end of Phase 6 Track 2.

**Order of work (decided by Saqlain):** Track 2 deliverables, then **app design**, then Track 4 (P6-11 to P6-14: identity/auth, CSRF, encryption, upload hardening, Bedrock `ap-south-1`, deploy). App design comes first so that Track 4's login, role and settings screens are built into the new design, not retrofitted.

## Goal

Redesign the consultant-facing app (Jinja2 + HTMX + Tailwind) so it feels like one product with the board deck: same palette, type and component language, and a clearer path through the core flow. Follow the two-pass design rule from the global instructions: one design pass at build, one before exposure.

## Current app inventory

**Shell.** `app/templates/base.html`: a dark-navy top bar (`brand` = `#1e1e50`, `navy-50..950` scale in `tailwind.config.js`), firm name from `branding`, dark-mode toggle persisted in `localStorage`, `max-w-7xl` content, assessment breadcrumb. Tailwind is built to `app/static/css/tailwind.css`; custom CSS is only 53 lines (`app/static/css/style.css`). HTMX 2.0.4 from unpkg with `hx-boost` on `body`. No logo (a shield glyph is hard-coded). `branding.firm_primary_hex` already overrides the nav colour, so firm theming has a foothold.

**Pages (`app/templates/pages/`) by flow:**

| Flow | Pages | Routes (mostly `app/routers/web.py`) |
|---|---|---|
| Dashboard and clients | `dashboard.html`, `client_detail.html`, `login.html` (placeholder; no auth yet) | `/`, `/clients/{id}`, `/clients/{id}/engagements-list` |
| Engagement | `new_engagement.html`, `engagement_detail.html`, `integrated_reports.html`, `engagement_purge.html`, `remediation_tracker.html` | `/engagements/new`, `/engagements/{id}`, `.../integrated-reports`, `.../remediation` |
| Assessment hub | `assessment.html` with framework tabs | `/assessments/new`, `/assessments/{id}`, `/assessments/{id}/tab/{framework_id}` |
| Scope, questionnaire, screening | partials: `scope_*`, `questionnaire_*`, `section_*`, `question_step`, `screening_form`, `followup_questions` | `/assessments/{id}/scope`, `.../questionnaire/*`, `.../screening` |
| Documents and desk review | partials: `documents_tab`, `document_list`, `upload_status`, `desk_review_*` | `.../upload`, `.../run-desk-review`, `.../desk-review-status` |
| Analysis and report tab | partials: `analysis_*`, `report_tab`, `report_summary`, `report_basis_panel`, `release_panel`, `framework_panel` | `.../run-analysis`, `.../analysis-status`, `.../report`, `.../report-summary` |
| Review queue, requirement cards, conclusions | `review_queue.html`, `conclusions.html`, `findings.html`; components `conclusion_card`, `requirement_card_body`, `finding_card`, `review_finding_card` | `.../review`, `.../conclusions`, `.../findings`; `/api/assessments/{id}/rfi-requests/*` |
| Evidence | `evidence_detail.html`, `evidence_span.html`, `evidence_reuse.html`, `aws_evidence.html`, `workpaper.html`; components `evidence_status_badge`, `workpaper_entry` | `/evidence/{id}`, `.../workpaper` |
| RFI | `rfi.html`, `partials/rfi_links.html`, `magic/upload.html` (client-facing upload link), `magic/invalid.html` | `.../rfi`, `.../generate-rfi`, `.../rfi/pdf`, `.../rfi/docx` |
| Reports and versions | `report_snapshots.html`, `comparison.html`, `soa.html`; `reports/board_report.html` and `reports/workpaper_standalone.html` are print templates, not app UI | `.../snapshots`, comparison routes, SoA routes |

Roughly 45 web routes plus 18 router modules, about 85 templates. Total template count is a rough measure of design surface; many partials are HTMX swap targets, so a redesign has to keep their ids and `hx-target` contracts or update tests that pin them (several contract tests assert on `data-*` attributes and exact strings).

## Visual system the board deck established

Source: `docs/product/2026-10-01-board-report-format.md` (F1-F10, section 3) and the mockups in `docs/product/2026-10-01-board-report-mockup/` (`deck_template.html`, `board-deck-PROPOSED.pdf`).

- **Theme tokens (firm-configurable, F5).** Default indigo/royal/teal: `p1` indigo `#161A5C`, `p2` royal `#2D3FD3`, `p3` sky `#3FA9F5`, `acc` teal `#12B3A6`. The app's current `brand` `#1e1e50` is already close to `p1`.
- **Ink and surface neutrals.** Ink `#0B0E26`, secondary text `#3A4060`, muted `#6E7591`, line `#DDE1EB`, panels `#F1F3F8` / `#E6E9F2`.
- **Severity (fixed, not themeable).** Critical `#9B1C1C`, High `#D9481E`, Medium `#F0A030`, Low `#3C9D6B`.
- **Outcome colours (fixed).** Compliant `#2F9466`, partially compliant amber `#F0A030`, non-compliant `#C0392B`, insufficient evidence `#9AA3B5`, not applicable `#D5D9E3`.
- **Type.** Display: Barlow Condensed (OFL, to be vendored by V3-A) for titles, big numbers and section markers. Body: Noto Sans with Devanagari fallback. The app currently uses the Tailwind default stack.
- **Components.** Title banner with a section-number wedge; one-line computed takeaway under each title; KPI tiles (solid fill, big condensed number, small label); outcome donut and 100%-stacked outcome bars per framework (never combined across frameworks); domain **status board** (one column per framework, score bar, pill such as "No gaps" or "3 gaps · 1 crit/high"); severity ring panels; pills for severity/outcome; responsibility markers (client / consultant / shared); R-xx finding refs and I-n initiative refs; horizon columns (short, medium, long).
- **Rules to carry over.** Scores are never combined across frameworks; numeric priority is not shown to clients (priority is derived High/Medium/Low); period and evidence cut-off are always visible; framework-specific copy is conditional.
- **Charts are SVG/CSS only**, produced by a pure presenter (`board_view.py`, V3-B). The app could reuse that presenter for dashboards rather than adding a chart library.

## Constraints that stay

- Jinja2 + HTMX + Tailwind. No SPA rewrite.
- Local-only until Track 4; there is no auth yet, so design login/roles screens as placeholders to be wired in Track 4.
- Contract tests pin many template strings and `data-*` attributes. Plan the redesign as a re-skin of structure first, then of copy, and update pinned tests deliberately.
- Template files under `app/templates/` are covered by per-PR file-set guards; add scoped allowances, never delete guards.
- No Claude attribution in commits. Merging is Saqlain's.

## Open questions for Saqlain

1. **Scope of the redesign.** (a) A visual re-skin only (palette, type, components, same page structure); (b) re-skin plus restructure the core flow (engagement to assessment to review to report) with a clearer stepper and a single "what needs me" inbox; (c) both, but in two PRs. Recommendation: (c).
2. **Who is the design user?** The consultant running an assessment day to day, the reviewing partner who approves, or both? This decides whether the review queue or the dashboard leads.
3. **Dark mode.** Keep it (it exists today and the deck is light-only), or drop it to halve the design surface?
4. **Fonts.** Is vendoring Barlow Condensed for the app (not just the PDF) acceptable, given it is loaded from `/static` and needs no CDN?
5. **Tooling.** Design in Stitch or an HTML mockup pass first (like the board-report mockups), or go straight to Tailwind templates? Recommendation: one mockup pass for the three hub screens (dashboard, assessment hub, review queue), then implement.
6. **Firm theming in the app.** Should the V3-A firm theme settings (logo, primary/secondary/accent) also theme the app chrome, or only the deliverables?
7. **Client-facing surfaces.** The magic-link upload page is the only client-facing screen today. In scope for the redesign?
8. **Sequencing with V3-A.** V3-A adds fields to the Finding, Action, roadmap and versions forms. Redesign after V3-A merges so the new fields are included.

## First steps for the design session

1. Answer the open questions above (grill if useful).
2. Screenshot the current app (the `run` skill) for the 8 to 10 core screens as the baseline.
3. Produce the mockup pass in the deck's visual system for the hub screens.
4. Write a handoff with contract tests for the shared component layer (tokens in `tailwind.config.js`, base template, pill/KPI/status components), then implement via the usual Codex flow.
