# Handoff: UI audit second run (design system, archetypes, migration spec, components, five prototypes)

For Codex. Docs only. Assume no memory of the first run.

## Goal

The first half of the UI audit (phases 1 to 12: what is wrong and why) is done and Saqlain has answered every open decision. This run produces the second half: the target design system, page archetypes, the Next.js migration UI spec, the component inventory, a final README, and five static prototype screens that prove the system on real content.

**Done means** these exist under `docs/ui-audit/`:

1. `DESIGN_SYSTEM.md` (Part B phase 5)
2. `PAGE_ARCHETYPES.md` (phase 6)
3. `NEXTJS_MIGRATION_UI_SPEC.md` (phase 13)
4. `COMPONENT_INVENTORY.md` (phase 14)
5. `prototypes/` with five HTML screens and one shared stylesheet (phase 15)
6. `README.md` rewritten as the final executive summary, answering the 7 questions in Part B "FINAL OUTPUT"
7. The first-half documents reconciled with the captures (see "Reconcile" below)

Then append a `## Results` section to this file and stop. Do not commit (the git index is outside your sandbox; Claude commits). Do not try to launch a browser (Chromium cannot start in your sandbox; Claude screenshots the prototypes on the host).

## Read first

| Path | Why |
|---|---|
| `tasks/handoffs/2026-10-12-ui-audit.md` | The original brief. Part B phases 5, 6, 13, 14, 15, "IMPORTANT DESIGN PRINCIPLE", "DO NOT" and "FINAL OUTPUT" are your instructions for this run, as amended below. Part A1 rules still apply. The "Host capture pass" section at the end has measured numbers. |
| `docs/ui-audit/SAQLAIN_FEEDBACK.md` | Saqlain's decisions and per-screen requirements. Part 2 is verbatim and wins over any summary, including this file. |
| `docs/ui-audit/UI_ISSUES.md`, `ROOT_CAUSES.md`, `STATUS_INVENTORY.md`, `MEASUREMENTS.md`, `README.md` | First-half output. Written before any screenshot existed. |
| `docs/ui-audit/rendered-measurements-summary.json` | Per-capture content width, font-size counts, text nodes below 14px, page height. 411 rows. The raw file `rendered-measurements.json` (git-ignored, present on disk) also has longest-prose-block line lengths and foreground/background pairs. |
| `docs/ui-audit/screenshots/` | 109 committed captures at 1440 and 1280, plus the client upload page at 390. Fixture captures are also on disk (git-ignored). You can read images; look at them. |
| `docs/plans/2026-10-12-001-nextjs-frontend-migration-plan.md` | The migration plan. Sections 4 (design system, templates T1 to T7, components) and 7 (every screen) are provisional and you rule on them. |
| `docs/product/yozora-design-system.md` | The current rules P1 to P10 that the decisions below change. |

The demo app is running at `http://127.0.0.1:8011` (`curl` works; do not start another server, do not re-seed). Assessment ids are in the original brief, section A2. Use `curl` to pull real Veldhara content for the prototypes.

## Fixed inputs. Decided by Saqlain. Do not reopen, do not offer alternatives.

- FastAPI stays as the JSON API. No Python port. Screens cut over one by one.
- Retire the gradient canvas and the glass surfaces. Opaque surfaces on a neutral background.
- Keep the 8 accents, for interaction and branding only. They never carry status.
- Status colours are rebuilt as four families: severity, outcome, progress, provenance.
- Control codes (for example A.5.18) are allowed beside titles in lists.
- Questionnaire navigation: a single-framework assessment uses that framework's own domains. A multi-framework assessment uses domains from the unified control framework, each requirement covered once. One master set of domains per framework.
- Drafts save automatically as the auditor types. Completion stays a separate, explicit act.
- Review queue order: pending decisions first, then missing or contradictory evidence. The auditor can sort and switch at any time.
- Design for a laptop, about 1440 wide. 1280 must still work.
- Never two navigation bars stacked under each other. Sub-sections inside a tab need another pattern. Today the assessment has page tabs, then a segmented control, and RFI has a third level under that. Your spec must name the one pattern that replaces levels two and three, and every prototype must use it.
- Inter stays as the typeface.

## Saqlain's per-screen requirements. The prototypes must show every one.

**Questionnaire**
- The question area uses the available width. No narrow column with a blank side (measured today: a 576px question column inside a 1040px page at 1440).
- Per question, in this order of weight: what the control requires; why it is asked; a hint on how to put it to the client.
- Help text and text hierarchy reworked (today guidance is 12px muted at about 100 characters a line).
- The answered state after assessment is redesigned too. Show both an unanswered and an answered question.
- Section navigation uses the framework's own domains (the demo is ISO 27001: use its four Annex A themes or clause groups, not privacy headings).

**Review queue**
- Each item is a finding. The title is the gap itself ("Access reviews do not cover all systems"), not the control name. The control code and name sit beside or under it.
- Show, in this order: gap statement; compliance status; risk or impact of the non-compliance; recommendation at full weight with its reasoning; where the finding came from (what was reviewed, who was spoken to) as a short narrative, not an evidence extract.
- Remove the duplicate "Evidence" and "Evidence on this control" blocks. One provenance block, with the cited file one click away.
- The queue list shows outcome and risk in words, not a dot.
- The decision (approve, edit, reject) stays attached to the selected finding and visible without scrolling through all supporting detail.
- One data hierarchy for every screen under Review. Write it down once in the spec and use it in queue, conclusions, findings and workpaper.

**Conclusions**
- Same content as the queue with the review mechanics removed: the final gap.
- A table like a standard assessment sheet: domain, control ID, gap, risk, status. Deterministic layout. A row can expand to the full finding.

**RFI (evidence requests)**
- Much simpler: a tight list with good sorting (think of a Vercel deployments list). Today the page is 20,005px tall at 1440.
- An item already added to an RFI is not shown again in the same form.
- Full "what to send", example and "good looks like" text is on demand, not open on every row.

**Report**
- Opens with a written executive summary that sets the context: what the engagement was, what was reviewed, the domains in scope, the gaps, where they lie, how critical they are, the overall posture. Well written prose, not a string of counts.
- Then gaps by domain, weakest and strongest, each with the non-compliance, the impact if unresolved and the risk, readable by a board.
- A summary view for the board and a detailed view for auditors and technical teams.
- Recommendations with their logic, following the flow of the exported report.

**Statement of applicability**
- Ask only which controls are not applicable and why. Everything else is applicable with a standard justification.
- It does not get its own tab. Decide where it lives (Scope is the likely home) and show the pattern inside one of the five prototypes or as a clearly marked panel.

**Content quality is a separate track.** Saqlain flagged that the content itself is not shaped for its reader (report writing, control wording, unified-framework structure, how AI output reads to a consultant; workpapers for the auditor, reports for boards). The spec must leave room for that work and must not claim the redesign solves it.

## What to produce

### A. Reconcile the first half with the captures

The first-half documents still say "0 captures", "pending, not visually verified" and "requested" throughout. That is no longer true.

- For each of the 24 issues: look at the cited captures and the measurements, then mark it confirmed, corrected (say what changed) or withdrawn. Replace "pending, not visually verified" with what the capture shows. Every issue must cite a screenshot file that exists on disk; check the name and extension (tall pages are `.jpg`).
- Add the issues the captures and Saqlain's notes surfaced that are not in the register. At least: (1) stacked navigation, up to three levels on RFI above an empty "Consultant name" field; (2) the assessment page title is the client name, repeated in the breadcrumb, title and subtitle; (3) the duplicate "Evidence" and "Evidence on this control" blocks in review; (4) the recommendation sits in a small box although it is a primary deliverable; (5) findings are titled by control name, not by the gap; (6) SoA is a 17,481px page asking for a justification on every control.
- Client upload page, now captured at 390 (`screenshots/b6-magic_upload-*-390.png`). Claude's host findings to fold in: UI-011 is confirmed at runtime (eight Tab presses never reach a file control; the file input has `tabindex=-1` and the visible control is a label); the error alert renders above the page title with no gap and is not tied to the item that failed; the intro sentence sits above the h1; most text is 13px; the footer says "Powered by Yozora" while the header says CyberAssess. UI-024 (fixture data missing) is resolved for the audit: Claude seeded the three fixture links temporarily to capture, then removed them.
- The comparison fixture still returns 404 (2 captures). The live comparison page is captured (`comparison-1440.jpg`), so nothing is unreviewed.
- Update `MEASUREMENTS.md` so the per-screen rows carry the measured values instead of "pending".
- Keep the stack-or-oversight classification. Recount it if you add root causes.

### B. `DESIGN_SYSTEM.md`

Follow phase 5 of the brief, with these additions:

- Concrete token values, light and dark: neutral background and surface steps, borders, text steps, the 8 accents (keep today's hues from `design/tokens.json`; fix the seven dark accent-text pairs that fail contrast), and the four status families. Give each status family its members, wording, icon, foreground and background, and the WCAG ratio of each pair. Reuse `tools/contrast.py` to compute them.
- A type scale with roles, not only sizes. Audit content (questions, conclusions, gap statements, evidence quotes, criteria, recommendations, guidance) is 14px minimum. State which roles may go below 14px (identifiers, timestamps, table meta) and nothing else.
- Width modes with pixel values at 1440 and 1280: inventory, task workspace, document. Prose measure 60 to 80 characters.
- The navigation model: sidebar, assessment stage tabs, and the single pattern for sub-sections that replaces the stacked segmented controls.
- A ruling on each of P1 to P10, restated as the new rule.
- A greyscale test: say how hierarchy survives without colour.

### C. `PAGE_ARCHETYPES.md`

Follow phase 6. For each archetype: purpose, regions, width mode, which of the 31 screens use it, and its states. Then a table for the plan's templates T1 to T7 (plan section 4.3): **agree, change or drop**, with the archetype that replaces each one where they differ.

### D. `NEXTJS_MIGRATION_UI_SPEC.md`

Follow phase 13. It must be usable directly by a coding agent. Additions:

- **A rule for every P0 issue.** A table: P0 issue id, the spec rule that fixes it, how to verify it (a measurement or a check, not an opinion).
- **A requirement classification table.** Every decision and every per-screen requirement above, one row each, marked exactly one of:
  - **Presentation**: the data exists today in the shape needed; only layout and components change.
  - **Backend**: needs a new field, a changed data shape, a new endpoint or new stored state. Say what, and name the code that would change (model, service or router) after checking it. For example: is there a gap title distinct from the control name today? Is there a risk or impact statement per conclusion? Is there a stored record of who was interviewed? Does a master domain list exist per framework and for the unified framework (`app/frameworks/`, the UCC cluster mappings)? Does autosave have an endpoint that accepts a partial section? Check the code; do not guess.
  - **Content**: needs writing or prompt work (executive summary prose, question "why we ask" and "how to ask" text, recommendation reasoning, standard SoA justification). Say whether the text would be authored once (static, per control) or generated per assessment.
  A requirement may need more than one; then list each part on its own row.
- **Per-screen spec** for all 31 screens: archetype, regions, what changes from today, and the classification above. This replaces the "Tpl" and "Work" columns in plan section 7.
- **The Review data hierarchy**, once, as an ordered field list with the source of each field.
- **A ruling on the plan's component lists** (plan sections 4.2, 4.4, 4.5): agree, change or drop per component, reconciled with `COMPONENT_INVENTORY.md`.
- Tailwind v4 and shadcn/ui recommendations at the level of "which primitive, which variant". No hundreds of one-off components.
- A short "Content track" section: what the content plan must cover, and the slots the UI leaves for it. Do not write the content plan.

### E. `COMPONENT_INVENTORY.md`

Follow phase 14: purpose, variants, states, where used. The minimum useful set. Mark which are shadcn primitives restyled and which are domain components.

### F. Five prototypes in `docs/ui-audit/prototypes/`

Screens: `questionnaire.html`, `review-queue.html`, `conclusions.html`, `rfi.html`, `report.html`. (Phase 15 lists evidence inventory; Saqlain's notes are about conclusions instead, so conclusions takes its place. Cover the inventory in the archetypes document.)

Rules:

- Static HTML that opens from disk (`file://`). One shared `prototype.css` holding the design tokens as CSS variables and the component classes, so the five screens visibly share one system. Tailwind's browser build from a CDN is allowed for utilities, but every colour, size and spacing value must come from the shared tokens, not from arbitrary values. Load Inter from `../../../app/static/fonts/` by relative path.
- shadcn-style markup and naming, so the mapping to real components is obvious.
- Real Veldhara content pulled from the running app with `curl` (assessment `d491ee73-0925-43bd-8cb2-3b5fff2cc8ac` for the populated ISO state, `506d1f04-9c19-44e4-9fdd-fa286f2b4eb6` for the review queue with 3 pending). Never open `validation/companies/*/answer_key.json`.
- Where a requirement needs text that does not exist in the data today (gap titles, risk or impact statements, provenance narrative, "why we ask", executive summary prose), write plausible text from the real conclusion and evidence, and give that element the attribute `data-illustrative="true"`. List every such element in `prototypes/README.md` with the classification it implies (backend or content). This list is how Saqlain sees what the redesign depends on.
- Each screen shows the full app frame (sidebar, breadcrumb, assessment header, stage tabs) so navigation depth is judged honestly. No stacked navigation bars anywhere.
- Light theme. Laid out for 1440, working at 1280 without horizontal scroll.
- Audit content at 14px or more. Prose lines 60 to 80 characters. Hierarchy must read in greyscale.
- Minimal JavaScript, only for showing a state (expand a row, switch board and detailed view, sort). No frameworks.
- Realistic density: the conclusions table shows at least 25 rows across domains; the RFI list at least 20 items; the review queue the six real items; the report all the domains.
- `report.html` includes the board view and the detailed view. One of the screens includes the SoA "not applicable" pattern.
- `prototypes/README.md`: one paragraph per screen saying which requirement each region answers, then the illustrative-content list.

### G. Final `README.md`

Rewrite as the final executive summary answering the 7 questions. Add:

- A **requirements coverage table**: every decision and per-screen requirement of Saqlain's, the prototype that shows it, the spec section that specifies it, or the reason it is not covered.
- A deliverables table listing all nine audit documents.
- What changed between the first-half findings and the reconciled ones.

## Rules

- Docs only: write under `docs/ui-audit/` and the Results section of this file. Nothing under `app/`, `design/`, `tests/`, `scripts/`. No Next.js scaffold.
- No AI spend. Do not call or trigger analysis, desk review, follow-ups, narrative generation or action drafts. GET requests only against port 8011.
- Never read `validation/companies/*/answer_key.json`.
- No em dashes anywhere you write. No attribution lines.
- Plain language. Short sentences. A reader who has not seen the code should follow the README and the spec.
- Do not optimise for pretty. See "IMPORTANT DESIGN PRINCIPLE" and "DO NOT" in the brief.
- Do not reopen Saqlain's decisions. If one is impossible to honour, say so in Results with the reason and build the nearest thing.

## Verification before you report

- `python docs/ui-audit/tools/verify_audit.py` passes. It was written for the first run (it asserts the second-run documents do not exist, exactly 24 issues, and it reads every file as text), so update it for this run. It must also check: all nine documents exist; every screenshot cited in `UI_ISSUES.md` exists on disk; the five prototype files exist; no em dashes in any file you wrote.
- No remaining "pending, not visually verified" or "0 captures" text in the audit documents.
- Every P0 issue id appears in the spec's P0 rule table.
- Every row of the requirements coverage table names a prototype or a reason.
- In `prototype.css` no content text role is below 14px.
- `git status` shows changes only under `docs/ui-audit/` and this file.

## Report back

Append `## Results` to this file:

- what was produced, with file names;
- the reconciliation count (confirmed, corrected, withdrawn, added);
- the T1 to T7 ruling in one table;
- the count of requirements by classification (presentation, backend, content) and the three largest backend items;
- every `data-illustrative` dependency in one list;
- anything you could not do or could not verify, and why;
- questions for Saqlain, only if a decision is truly blocking.

## Results

Completed sections A to G in order. All changes are under docs/ui-audit/ and this Results section. No commit, browser launch, server launch, application mutation, AI action or answer-key read occurred. Runtime content was retrieved with GET curl requests on port 8011. The populated source actually contains DPDPA and ISO; prototypes disclose ISO focus and target single-framework domain grouping.

### Produced

- DESIGN_SYSTEM.md: opaque light/dark tokens, eight retained accent hues with corrected dark text, four status families, type roles, measured width targets, navigation and P1 to P10 rulings.
- PAGE_ARCHETYPES.md: seven archetypes, all 31 live page families and explicit assessment/evidence/RFI variants, T1 to T7 rulings.
- NEXTJS_MIGRATION_UI_SPEC.md: nine P0 acceptance checks, 60 classified requirement parts, Review hierarchy, draft API contract, per-screen regions/states and rulings on every provisional component.
- COMPONENT_INVENTORY.md: 40 shared component contracts, variants, states, uses and shadcn/domain mapping.
- prototypes/questionnaire.html, review-queue.html, conclusions.html, rfi.html, report.html and shared prototype.css. Six real interim queue candidates, 32 final conclusions across four domains, 40 source RFI requests and all 93 ISO control records in auditor report detail.
- prototypes/README.md, source-data.json and illustrative-content.json document all content/state dependencies. Requirements and contrast have requirements.json and target-contrast.json supporting records.
- README.md is the final seven-question executive summary, with all requirements covered by a prototype or an explicit reason and all nine core deliverables listed.
- Reconciled ARCHITECTURE.md, SCREEN_INVENTORY.md, UI_ISSUES.md, ROOT_CAUSES.md, STATUS_INVENTORY.md, MEASUREMENTS.md and CAPTURE_REQUESTS.md. The legacy contrast appendix remains source evidence; the new system has separate opaque target calculations.
- Updated tools/verify_audit.py for this run. The host capture_prototypes.py helper present under tools was not executed.

### Reconciliation

19 confirmed, 4 corrected, 1 withdrawn from the original 24; 11 added, UI-025 to UI-035. The register contains 35 entries, 34 active. Corrected entries: UI-015, UI-017, UI-021, UI-023. UI-024 is withdrawn as an audit fixture blocker: the host temporarily seeded upload fixtures, captured them, then removed the records. Live comparison is captured even though two comparison fixture captures show 404. Measurements now contain all 411 host rows. Causes: Stack 1, Design decision 3, Shortcut 7, Never designed 5, total 16.

### T1 to T7

| Template | Ruling | Replacement | Reason |
| --- | --- | --- | --- |
| T1 List | Agree | Inventory | Tables and compact lists share filter and row semantics. |
| T2 Detail | Change | Entity / Inventory / Form | Client and engagement use Entity; versions/comparison use Inventory; AWS/purge use Form, not generic cards. |
| T3 Workspace | Change | Task plus shared assessment frame | One stage bar; no overview stepper duplicated on every stage. |
| T4 Two-pane review | Change | Queue; Conclusions uses Inventory | Only queue needs permanent selection pane. Conclusions is a deterministic assessment sheet. |
| T5 Form | Change | Form | SoA becomes Scope exception panel. Settings and board inputs remain forms. |
| T6 Wizard / run | Change | Task and Form | Questionnaire is a workspace, not a forced sequential wizard. RunStatus is a region. |
| T7 Document | Agree | Document | Add board/auditor report variants; source viewer and workpaper keep document measure. |

### Classification and largest backend items

60 requirement parts: Presentation 32, Backend 14, Content 14. Split rows distinguish the data contract from writing and display work, rather than assigning multiple classes to one row.

1. Questionnaire draft persistence and domain routing: partial field upsert, notes before an answer, version/conflict handling, no completion side effect, explicit completion; canonical single-framework and unified-domain coverage. Current save routes couple persistence to completion.
2. Pre-approval finding read model: gap title, impact, recommendation reasoning, reviewed provenance and interview source records. Reuse existing Finding.title/business_impact after approval rather than inventing replacement fields.
3. Cross-source RFI identity and JSON membership: existing same-key idempotency stays; reconcile checklist artifacts, conclusion requests and added requests so included/issued items cannot repeat in the add form. Expose true requested/issued/received state separately from evidence mapping.

Accepted report narrative and the board read model also need JSON exposure, reusing existing narrative AuditEvents and freshness gates rather than adding another prose store.

### Every illustrative dependency

The list below names every exact data-illustrative element, its primary classification and paired dependency. Content is not accepted report text; Backend is not implemented state. See the prototype README for the same manifest and descriptions. The first two RFI included states are explicitly illustrative; the source has no issued RFI version. No interviewee has been invented.

- `questionnaire.html#q1-why`: Content. Static per-control why_asked field.
- `questionnaire.html#q1-hint`: Content. Static per-control client_prompt_hint field.
- `questionnaire.html#q2-why`: Content. Static per-control why_asked field.
- `questionnaire.html#q2-hint`: Content. Static per-control client_prompt_hint field.
- `questionnaire.html#soa-standard`: Content. Authored standard justification plus Backend default applicability source marker.
- `review-queue.html#queue-title-0`: Backend. Reviewed Conclusion.gap_title field; text is illustrative Content per assessment.
- `review-queue.html#finding-title-0`: Backend. Conclusion.gap_title with reviewed per-assessment Content.
- `review-queue.html#finding-impact-0`: Backend. Conclusion.impact_statement; generated per assessment Content.
- `review-queue.html#finding-reason-0`: Content. Generated recommendation reasoning; Backend recommendation_reason slot.
- `review-queue.html#finding-provenance-0`: Content. Reviewed provenance narrative with Backend method/interview source records.
- `review-queue.html#queue-title-1`: Backend. Reviewed Conclusion.gap_title field; text is illustrative Content per assessment.
- `review-queue.html#finding-title-1`: Backend. Conclusion.gap_title with reviewed per-assessment Content.
- `review-queue.html#finding-impact-1`: Backend. Conclusion.impact_statement; generated per assessment Content.
- `review-queue.html#finding-reason-1`: Content. Generated recommendation reasoning; Backend recommendation_reason slot.
- `review-queue.html#finding-provenance-1`: Content. Reviewed provenance narrative with Backend method/interview source records.
- `review-queue.html#queue-title-2`: Backend. Reviewed Conclusion.gap_title field; text is illustrative Content per assessment.
- `review-queue.html#finding-title-2`: Backend. Conclusion.gap_title with reviewed per-assessment Content.
- `review-queue.html#finding-impact-2`: Backend. Conclusion.impact_statement; generated per assessment Content.
- `review-queue.html#finding-reason-2`: Content. Generated recommendation reasoning; Backend recommendation_reason slot.
- `review-queue.html#finding-provenance-2`: Content. Reviewed provenance narrative with Backend method/interview source records.
- `review-queue.html#queue-title-3`: Backend. Reviewed Conclusion.gap_title field; text is illustrative Content per assessment.
- `review-queue.html#finding-title-3`: Backend. Conclusion.gap_title with reviewed per-assessment Content.
- `review-queue.html#finding-impact-3`: Backend. Conclusion.impact_statement; generated per assessment Content.
- `review-queue.html#finding-reason-3`: Content. Generated recommendation reasoning; Backend recommendation_reason slot.
- `review-queue.html#finding-provenance-3`: Content. Reviewed provenance narrative with Backend method/interview source records.
- `review-queue.html#queue-title-4`: Backend. Reviewed Conclusion.gap_title field; text is illustrative Content per assessment.
- `review-queue.html#finding-title-4`: Backend. Conclusion.gap_title with reviewed per-assessment Content.
- `review-queue.html#finding-impact-4`: Backend. Conclusion.impact_statement; generated per assessment Content.
- `review-queue.html#finding-reason-4`: Content. Generated recommendation reasoning; Backend recommendation_reason slot.
- `review-queue.html#finding-provenance-4`: Content. Reviewed provenance narrative with Backend method/interview source records.
- `review-queue.html#queue-title-5`: Backend. Reviewed Conclusion.gap_title field; text is illustrative Content per assessment.
- `review-queue.html#finding-title-5`: Backend. Conclusion.gap_title with reviewed per-assessment Content.
- `review-queue.html#finding-impact-5`: Backend. Conclusion.impact_statement; generated per assessment Content.
- `review-queue.html#finding-reason-5`: Content. Generated recommendation reasoning; Backend recommendation_reason slot.
- `review-queue.html#finding-provenance-5`: Content. Reviewed provenance narrative with Backend method/interview source records.
- `conclusions.html#conclusion-title-0`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-1`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-2`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-3`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-4`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-5`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-6`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-7`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-8`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-9`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-10`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-11`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-12`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-13`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-14`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-15`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-16`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-17`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-18`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-19`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-20`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-21`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-22`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-23`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-24`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-25`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-26`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-27`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-28`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-29`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-30`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `conclusions.html#conclusion-title-31`: Backend. Reviewed gap_title; title uses real gap text but field is absent.
- `rfi.html#rfi-included-0`: Backend. Illustrative inclusion state; stable cross-source request identity/state contract, not live receipt or issuance.
- `rfi.html#rfi-included-1`: Backend. Illustrative inclusion state; stable cross-source request identity/state contract, not live receipt or issuance.
- `report.html#report-executive`: Content. Accepted per-assessment executive narrative, exposed by existing narrative/board read model.
- `report.html#report-organizational-impact-0`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-0`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-1`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-1`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-2`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-2`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-3`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-3`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-4`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-4`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-5`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-5`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-6`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-6`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-7`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-7`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-8`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-8`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-9`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-9`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-10`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-10`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-11`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-11`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-12`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-12`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-13`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-13`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-14`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-14`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-15`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-15`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-16`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-16`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-17`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-17`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-18`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-18`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-19`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-19`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-organizational-impact-20`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-organizational-reason-20`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-people-impact-0`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-people-reason-0`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-people-impact-1`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-people-reason-1`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-people-impact-2`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-people-reason-2`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-technological-impact-0`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-technological-reason-0`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-technological-impact-1`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-technological-reason-1`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-technological-impact-2`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-technological-reason-2`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-technological-impact-3`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-technological-reason-3`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-technological-impact-4`: Content. Board impact text; Backend per-conclusion impact slot.
- `report.html#report-technological-reason-4`: Content. Recommendation reasoning generated per assessment; Backend explicit reason slot.
- `report.html#report-physical-strength`: Content. Board domain narrative generated per assessment.
- `conclusions.html#conclusion-impact-0`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-0`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-0`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-1`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-2`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-3`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-4`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-4`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-4`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-5`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-5`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-5`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-6`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-7`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-8`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-9`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-10`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-10`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-10`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-11`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-11`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-11`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-12`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-12`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-12`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-13`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-14`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-15`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-16`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-16`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-16`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-17`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-17`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-17`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-18`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-18`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-18`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-19`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-20`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-21`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-22`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-23`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-24`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-25`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-26`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-26`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-26`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-impact-27`: Content. Assessment-specific impact narrative; Backend impact_statement slot.
- `conclusions.html#conclusion-reason-27`: Content. Recommendation logic from source action; Backend recommendation_reason slot.
- `conclusions.html#conclusion-provenance-27`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-28`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-29`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-30`: Content. Reviewed provenance narrative with method/interview source records.
- `conclusions.html#conclusion-provenance-31`: Content. Reviewed provenance narrative with method/interview source records.

### Verification and limits

`python docs/ui-audit/tools/verify_audit.py` passed: nine documents, 35 structured issues with existing screenshot citations, nine P0 rules, 60 aligned requirements, 31 page families, five prototypes, 32 conclusions, 40 RFI rows, six queue items, 183 illustrative IDs, 144 AA pairs: 64 light/dark text/status, 64 accent-text/surface and 16 button pairs, local fonts and allowed scope. `node --check` passed for each of the five extracted inline scripts. `git diff --check` passed. No stale capture-unverified wording or zero-capture claims remain in audit documents. Only the optional metadata type role is below 14px in prototype CSS.

No prototype browser rendering was performed, as instructed. Host review must still measure overflow at 1440/1280, actual line lengths, sticky decision visibility, keyboard focus and greyscale hierarchy. Target geometry is CSS arithmetic, not a new browser measurement. Draft APIs, stored impact/reason/interview records, RFI identity reconciliation and Next.js implementation remain future work. Local sorting, row expansion, board/detail switching and decision previews are illustrative interaction states, not production mutations. Static screenshots cannot establish content quality or consultant productivity.

No blocking questions for Saqlain.
