# App (UI/UX) design kickoff

> **Superseded for next steps:** the next session follows `tasks/handoffs/2026-10-01-app-design-system-handoff.md`. This file stays as the decision log and history; its "First steps" section is replaced by that handoff.


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

## Decisions (Saqlain, 2026-10-01)

| # | Question | Decision |
|---|---|---|
| 1 | Scope | Both, in two PRs: PR 1 re-skins palette, type and components on the existing structure; PR 2 restructures the core flow (stepper, "what needs me" inbox). |
| 2 | Design user | Both consultant and reviewing partner. One shell, role-aware landing screen and inbox. Until Track 4 adds roles, the role switch is a placeholder. |
| 3 | Dark mode | Keep. Every new component needs a dark variant, and severity/outcome colours need contrast re-checks in dark mode. |
| 4 | Fonts | Yes. Vendor Barlow Condensed (display) and Noto Sans (body, Devanagari fallback) under `/static`, no CDN. |
| 5 | Tooling | One HTML mockup pass for dashboard, assessment hub and review queue in the deck's visual system, then implement in Tailwind. |
| 6 | Firm theming | The V3-A firm theme (logo, primary, secondary, accent) themes the app chrome as well as deliverables. Severity and outcome colours stay fixed. |
| 7 | Client-facing surfaces | In scope: `magic/upload.html` (and `magic/invalid.html`). |
| 8 | Sequencing with V3-A | Mockups now; Tailwind implementation waits until V3-A merges so its new Finding/Action/roadmap/versions fields are designed in. |

## Design bar (Saqlain, 2026-10-01)

The app must read as a professional, premium tool, not a vibe-coded one. Avoid the generic AI-product look seen everywhere on the web. Every component and every heading is designed with a purpose: nothing is decorative, and each element earns its place by carrying information or guiding a decision.

How this is applied:

- **Design from the work, not from a template.** Start from what a consultant or partner is trying to decide on each screen, and let that set hierarchy, density and what gets emphasis. The deck's visual system (condensed display type, solid KPI tiles, section-number wedge, status board) is the source language.
- **Component inventory first.** Before mockups, list every component and heading level the app uses (about 85 templates) and give each one a stated job. Anything with no job is cut.
- **Generic-AI patterns are off the table:** gradient hero blobs, glassmorphism cards, purple-to-blue gradients, emoji or sparkle icons, identical rounded card grids, centred marketing-style headings, and uniform soft shadows.
- **Typography and data carry the premium feel:** a strict type scale, tabular figures for numbers, real alignment and spacing rhythm, and colour reserved for meaning (severity and outcome are fixed, the firm theme is for chrome).
- **Copy is part of the design.** Headings, labels, empty states and errors are written to the audience. Examples from the baseline: "Conclusions: individual approval" and the "Unmigrated assessments" block.

## Style direction (in progress, 2026-10-01)

Source vocabulary: the "50 Design Styles" article (uxplanet.org). Filtered against the brief, these are out: Glassmorphism, Aurora, Ethereal, Neo Frutiger Aero, Bento Box (the generic-AI look), Cybercore/Synthwave/Y2K (security clichés), and all ornamental or whimsical styles.

**Not decided yet:**
- **Brand colour.** The deck's indigo/royal/teal is not final and is not binding. Mockups use a neutral ink/paper palette with one swappable `--accent` token. Severity and outcome colours stay fixed.
- **Product name.** "CyberAssess" is being replaced. Mockups use a `[Name]` wordmark slot.
- **Direction.** Two candidates were mocked up for comparison, with the same data on the same three hub screens, in light and dark:
  - Direction 1, Utilitarian × Modular Typography with a Luxury Typography finish: `docs/product/2026-10-01-app-design-mockups/direction-1-utilitarian.html` (left rail, condensed display type, hairline grid, petrol accent).
  - Direction 3, Neoclassical restraint × Luxury Typography: `docs/product/2026-10-01-app-design-mockups/direction-3-neoclassical.html` (centred masthead, serif display, ledger tables with dotted leaders, brass accent, roman numerals).
- Screenshots of both are in `docs/product/2026-10-01-app-design-mockups/shots/`. Mockups load Google Fonts for convenience; the app will vendor its fonts.

**Both mockups already apply the shared design moves:**
- The portfolio lands on "what needs you", driven by role.
- The legacy "Unmigrated assessments" list leaves the landing page.
- Period and evidence cut-off are always visible.
- The review queue becomes a list plus a single decision pane, with evidence quoted next to the conclusion and keyboard actions.
- Scores are never combined across frameworks.
- The status board and progress stepper replace the dots-only pipeline.

## Direction reset (2026-10-01, after expert designer feedback)

Directions 1 and 3 above are **superseded** (files moved to `docs/product/2026-10-01-app-design-mockups/superseded/`). A professional designer reviewed Direction 1 and rejected it: no hierarchy, extra numbers and letters everywhere, small all-caps text, and it looked AI-generated. The stylistic signals I used (condensed caps labels, section letters and numerals, mono ids, rule-everything layout, stat tiles) were decoration, not hierarchy.

**New brief: clean, minimal, to the point, in the spirit of Linear without copying its colour theme.**

Rules that carry into `design.md`:
- Sentence case everywhere. No all-caps text, no eyebrow labels.
- No serial lettering or numbering of sections, steps or nav items. No ref codes in list views; ids only in detail views.
- No subtext unless it earns its place.
- Hierarchy from size, weight and spacing only, not from caps, rules or colour.
- Rounded cards (about 10px), 6px buttons, tinted severity and outcome pills with a dot. One clearly primary action per screen.
- Accent: indigo (accepted for now). Dark mode kept.
- Palette and product name are still open.

Current mockup: `docs/product/2026-10-01-app-design-mockups/v2-clean.html`, with renders in `shots-v2/`. Tokens: accent #4B3FC4 light and #5F55E0 dark, Inter 400/500/600 at 12/13/14/16/20/24 (40 only for framework scores), radii 4/6/10, spacing 4 to 48.

## Pass 2 and accent decision (2026-10-01)

Current mockup: `docs/product/2026-10-01-app-design-mockups/v3-polish.html` (renders in `shots-v3/`, accent contact sheets `accent-*.png`). It supersedes `v2-clean.html`.

**Accent decided by Saqlain: Midnight.** Light `#1C3A72`; dark fill `#33508C`; dark text/rings/icons `#A9BCEE`. Contrast: white on the light fill is 11.1:1, and the light value as text on the lightest glass card is 9.8:1. Hover, soft fill, focus ring and ring track are mixed from the base accent.

Direction in v3: soft blue-grey to mauve page gradient (light stops `#D3DAE5 → #E6E5EE → #EBDDE3`; dark `#1A2131 → #1C1D2A → #28202C`), frosted translucent cards and sidebar (60% white, 18px blur, 16px radius) with more solid panels for tables and the review detail, pill buttons with a soft highlight, SVG score rings, a stepper with progress rails, and one icon set (1.5px stroke, 16px). Reference image supplied by Saqlain: an iPad-style home screen on a muted blue-grey to mauve gradient with soft frosted cards.

**Still open:** the product name. Plain dictionary words are all registered as domains.

An earlier shortlist (Assize, Assayer, Probata, Corroba, Substanta, Lanternline, Concordly, Cairnly) was withdrawn: Assize and Assayer open with "ass", and the DNS check I used to call domains "free" was unreliable (it reported probata.com as free; it is registered and parked for sale since 2004). Web searches found these collisions, so these names are **out**:
- Probata: Probata Corporation (calibration and metrology, with audit-readiness and compliance software).
- Attesta: attestagrc.com, an AI GRC platform for consultants, a direct competitor.
- Vigilis: Vigilis AI, security compliance.
- Certa: a funded third-party-risk and compliance company.

Checked and not clean: Mensura (Belgium's largest occupational health service, est. 1968), Gnomon (several software firms), Veritum (near-names Veritus, Veritium, Veriti).

Least-collision candidates from the same search: **Pondus** (Latin "weight", as in weight of evidence; nothing found in compliance software) and **Aequa** (Latin "fair, impartial"; only a small Italian NLP startup, aequa-tech). Neither is verified. The search tool is US-only and is not a trademark search, so any pick needs a proper search in India (classes 9, 42, 45) and a registrar check before commitment. The product can proceed with the `[Name]` wordmark slot in the meantime.

## Naming update (2026-10-01)

Saqlain wanted to keep **Akira**. Rejected on collisions: the Akira ransomware group (active CISA/FBI advisories; toxic for a cyber/compliance brand) and Akira AI's AgentGRC.ai (an AI GRC platform, same category).

Names with the same short, soft-vowel, Japanese-leaning feel, checked by web search:
- **Out (collisions):** Mamori (mamori.io, zero-trust security and compliance), Takumi (Takumi Cloud, security consulting; TakumiSafe, EHS compliance), Akari (Akari Software, plus AKARION GRC cloud), Kagami (Kagami ERP, Hyderabad), Hoshi (Hoshi HRMS, Mumbai), Noren (Noren.AI, Noru compliance), Minato (Intility Minato platform).
- **No GRC collision found, shortlist:** Yozora ("night sky", matches the Midnight palette), Kaede (closest sound to Akira; only small Japanese system-dev and marketing firms), Shirube ("guidepost"; a 2-person Tokyo analytics startup). Lower: Tatsu (Brazilian ERP), Mizu (small unrelated firms).

None is verified: search is US-only and shallow. Before commitment, run an India trademark search (classes 9, 42, 45) and a registrar check. A Japanese-word name for an Indian product should also be tested for how clients pronounce and read it.

## Decisions locked (2026-10-01)

- **Product name: Yozora** (replaces CyberAssess). Trademark search in India (classes 9, 42, 45) and a registrar check are still pending and must be done before Track 4 exposes the product.
- **Accent: Midnight** (`#1C3A72` light, `#33508C` dark fill, `#A9BCEE` dark text).
- **Direction:** `v3-polish.html` (clean, minimal, Linear-like in spirit; blue-grey to mauve gradient; frosted cards; pill buttons; sentence case; no lettering or numbering).

## First steps for the design session

1. Answer the open questions above (grill if useful).
2. Screenshot the current app (the `run` skill) for the 8 to 10 core screens as the baseline.
3. Produce the mockup pass in the deck's visual system for the hub screens.
4. Write a handoff with contract tests for the shared component layer (tokens in `tailwind.config.js`, base template, pill/KPI/status components), then implement via the usual Codex flow.
