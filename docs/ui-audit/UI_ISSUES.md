# Prioritised UI issue register

Scope: phases 3 to 12, with the four focused audits integrated below. This is an audit recommendation, not an implementation specification. No application changes or AI actions were made.

Evidence qualification: host captures and 411 measurement rows now exist. This pass inspected the screenshots, including the 390px upload states, and reconciled the original register. Screenshot evidence establishes appearance and geometry; source remains the evidence for unsaved-state, URL and conditional behavior. The host keyboard check confirms UI-011. No browser or server was launched in this pass. Original issue reconciliation: 19 confirmed, 4 corrected, 1 withdrawn. Eleven issues were added, for 35 retained entries, of which 34 remain active.

Severity describes impact; priority describes migration order. P0 is viability, P1 is workflow, P2 is refinement. A high-severity workflow problem can be P1. Each entry identifies the decision obstructed and supporting context that can be disclosed later.

| Priority | Issues | Gate |
|---|---|---|
| P0 | UI-001, UI-002, UI-003, UI-008, UI-009, UI-011, UI-012, UI-013, UI-025 | Reading, usable space, explicit status, navigation and keyboard access |
| P1 | UI-004, UI-005, UI-006, UI-007, UI-010, UI-014, UI-015, UI-016, UI-017, UI-018, UI-019, UI-023, UI-026, UI-027, UI-028, UI-029, UI-030, UI-031, UI-032, UI-033, UI-034, UI-035 | Save work, triage, review, evidence trace and setup |
| P2 | UI-020, UI-021, UI-022 | Consistent presentation and verification discipline |

## UI-001: Questionnaire width is consumed before the question

- **Reconciliation:** Confirmed: questionnaire-open-1440.jpg shows the narrow pane and the long blank area beneath the domain list; measured pane 576px inside a 1040px main region.

- **Screen:** Questionnaire, evidence inventory, review; strongest effect on questionnaire.
- **Severity / priority:** High / P0.
- **Category:** Layout, density, readability.
- **Problem:** `.shell-content` caps every workspace at 1040px with 32px horizontal padding. Questionnaire then subtracts a fixed 288px navigation column, a 16px gap, 24px pane padding on each side and another 24px per question-card side. This constrains the answer/evidence area independently of its content. The captured page is 1040px wide at 1440, with 144px outside unused space. The open question pane is 576px; redundant gutters and the fixed domain column leave a narrow task area.
- **Why it matters:** The auditor must compare question, answer, guidance and quoted evidence. Nested padding spends width on containers while those decision inputs wrap.
- **Evidence:** `screenshots/questionnaire-1440.png` and `screenshots/evidence-assessment-1440.png`; visually inspected in this reconciliation. Live section HTML confirms `.split`, `.split-pane` and `.qcard` structure.
- **Root cause:** `app/static/css/src/shell.css` `.shell-content`; `app/static/css/yozora-patterns.css` `.split`, `.split-pane`, `.qcard`.
- **Recommended fix:** Separate wide task workspaces from prose reading columns, then remove redundant inner gutters. Measure 1280 and 1440 before choosing inspector placement. A persistent third column would subtract more space and needs evidence of benefit.
- **Migration implication / affected component:** Content container and questionnaire workspace must select a task layout rather than inherit one page width.

## UI-002: Critical reading content uses metadata sizes

- **Reconciliation:** Confirmed: measured guidance at 12px, substantive secondary text at 13px. Review has 66 visible text nodes below 14px; report ISO has 343. Counts include metadata, so not every node is a defect.

- **Screen:** Questionnaire, review, evidence inventory, report, RFI, narrative, SoA.
- **Severity / priority:** High / P0.
- **Category:** Readability, hierarchy, accessibility.
- **Problem:** `.help` uses 12px for question guidance and desk-review attention notes. `.sub` and `.t-sub` use 13px for evidence quotations in requirement cards, gap descriptions in report rows, evidence coverage and substantive RFI text. Inputs and narrative textareas also use 13px. These are decision inputs, not merely timestamps.
- **Why it matters:** Important caveats and evidence become harder to read than the title they qualify, creating sustained reading fatigue.
- **Evidence:** `screenshots/questionnaire-1440.png`, `screenshots/review-queue-1440.png`, `screenshots/report-1440.png`; visually inspected in this reconciliation.
- **Root cause:** `app/static/css/yozora-components.css` `.help`, `.sub`, `.t-sub`, `.field textarea`; `app/templates/partials/section_questions.html`; `app/templates/components/requirement_card_body.html`; `app/templates/partials/report_summary.html`.
- **Recommended fix:** Assign audit prose, quotes, editable conclusions and guidance a minimum 14px content role; retain smaller sizes only for optional identifiers and timestamps.
- **Migration implication / affected component:** Content typography must be separate from metadata typography across question, evidence and report primitives. The open questionnaire has 159 visible text nodes below 14px. Guidance is measured at 12px and up to 101 characters per line.

## UI-003: Review queue communicates outcomes with a dot

- **Reconciliation:** Confirmed: visible queue rows carry colored dots without persistent outcome or risk wording; the selected card does carry both labels.

- **Screen:** Review queue.
- **Severity / priority:** High / P0.
- **Category:** Scannability, status, accessibility.
- **Problem:** Each queue link contains a title, framework/reference and a coloured outcome dot with a `title` attribute. Outcome wording is absent from the visible queue. Risk and flags exist as data attributes on the detail item but have no queue labels or filters.
- **Why it matters:** The reviewer cannot triage non-compliant, unsupported or high-risk proposals from the list without opening them. The tooltip requires pointer hover and does not provide persistent wording.
- **Evidence:** `screenshots/review-queue-1440.png`; visually inspected in this reconciliation. Source selector `[data-queue-select] .dot` and `[data-queue-item][data-risk][data-flags]`.
- **Root cause:** `app/templates/pages/review_queue.html`; `.item b` also truncates titles to one line in `app/static/css/yozora-components.css`.
- **Recommended fix:** Show a concise outcome label, decision state and exception indicator alongside the control reference. Add risk, pending and missing-evidence filters; retain the dot as redundant reinforcement.
- **Migration implication / affected component:** Queue rows need explicit semantic fields and accessible names, not colour plus hidden data.

## UI-004: Questionnaire save requires the whole section

- **Reconciliation:** Confirmed: captured form offers Save section with no draft state. The full-section validation and replacement risk are code-backed, not demonstrated by mutating the app.

- **Screen:** Questionnaire, especially early/partly answered NIST state.
- **Severity / priority:** High / P1.
- **Category:** Auditor workflow, progressive disclosure, recovery.
- **Problem:** `validateSection()` prevents submission whenever any active question is unanswered. The only submit action is “Save section”. A section switch replaces `#section-content`; no dirty-work guard is present in the inspected questionnaire/shared scripts.
- **Why it matters:** Auditors frequently pause to seek evidence. They need to preserve confirmed answers and notes without inventing answers to finish a section. Section completion and draft persistence are different decisions.
- **Evidence:** `screenshots/questionnaire-1440.png`; visually inspected in this reconciliation. Behaviour is code-backed, not interactively exercised.
- **Root cause:** `app/templates/partials/section_questions.html` `[data-questionnaire-form]`, `validateSection`; `app/templates/partials/questionnaire_sections.html` `hx-swap="innerHTML"`.
- **Recommended fix:** Provide draft persistence separately from completion validation, a visible saved/unsaved state and recovery on section navigation.
- **Migration implication / affected component:** Questionnaire form state needs a draft contract and route-change handling; copying this submit gate preserves the workflow defect.

## UI-005: Request guidance dominates the item list

- **Reconciliation:** Confirmed: rfi-items-1440.jpg is 20,005px tall, with guidance open on each item and 1,746 visible text nodes below 14px.

- **Screen:** RFI items; engagement Requests is the summary entry point, not the source of the repeated prose.
- **Severity / priority:** High / P1.
- **Category:** Density, component choice, cognitive load.
- **Problem:** Every RFI item expands summary, artifact lists and nested specifics, example, “Good looks like”, sample/period placeholders, mapping and received files. Only “Why we ask” is disclosed. This repeats guidance before the auditor can scan inclusion decisions.
- **Why it matters:** Selecting what to request and identifying what has arrived should be possible without reading full teaching material for each item.
- **Evidence:** `screenshots/rfi-items-1440.jpg`, `screenshots/requests-1440.png`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/pages/rfi.html` `[data-rfi-item]`, `[data-rfi-request-text]`, `[data-rfi-why]`.
- **Recommended fix:** Default to title, required/recommended, compact control mapping, received count and inclusion state. Expand “What to send”, example and criteria guidance on demand. Keep full client-facing request wording in a preview.
- **Migration implication / affected component:** Request list item should separate selection summary from request guidance, with a stable inspector/disclosure state.

## UI-006: Review detail has many simultaneous reading layers

- **Reconciliation:** Confirmed: review-selected-1440.png shows successive conclusion, action, Evidence, Evidence on this control and AI proposal blocks. The lower decision region is not visible in the initial screen.

- **Screen:** Review queue, expanded conclusions.
- **Severity / priority:** High / P1.
- **Category:** Hierarchy, progressive disclosure, cognitive load.
- **Problem:** Conclusion cards render rationale, gaps, action, citations, linked files, AI proposal, criteria, client/evidence comparison, quality, missing evidence and divergence as successive open blocks. The auditor decision remains at the end. The code already distinguishes these concepts, but gives nearly all the same block treatment.
- **Why it matters:** A reviewer must decide whether the proposed conclusion is justified; reading every provenance layer before reaching the decision adds context switching and scrolling.
- **Evidence:** `screenshots/review-queue-1440.png`, `screenshots/conclusions-1440.jpg`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/components/conclusion_card.html` `.block`, `.cc-decide`; `app/templates/components/requirement_card_body.html`.
- **Recommended fix:** Keep outcome, auditor decision, blockers and evidence sufficiency visible. Start with rationale and supporting evidence, then reveal detailed criteria, linked-file catalog and proposal history. Preserve real warnings and conflict comparison.
- **Migration implication / affected component:** Review detail needs information layers and a decision region that remains associated with the selected conclusion, not a card clone.

## UI-007: Report detail repeats rows without local triage

- **Reconciliation:** Confirmed: report-iso-1440.jpg is 15,854px tall and repeats Fix first findings within Detailed findings. Existing executive-summary and domain sections are retained strengths.

- **Screen:** Report and report-summary.
- **Severity / priority:** High / P1.
- **Category:** Reporting, density, scannability.
- **Problem:** The report already has a score, outcome distribution, executive summary, domain summary and “Fix first”. Do not rediscover these as missing. Its detail then renders every selected finding as a flat table, with gap prose in `.t-sub`, and repeats critical items in both “Fix first” and “Detailed findings”. There is no local search, severity/outcome filter or expandable detail.
- **Why it matters:** Once the executive conclusion is understood, an auditor needs to inspect relevant exceptions and trace evidence, not rescan the complete row set.
- **Evidence:** `screenshots/report-1440.png`, `screenshots/report-summary-iso-1440.jpg`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/partials/report_summary.html` `findings_table`, `findings_sections`, `[data-domain-findings]`.
- **Recommended fix:** Keep existing domain and risk summaries; let them filter/jump to exception groups. Collapse lengthy gap rationale into row detail and distinguish “Fix first” as a subset, avoiding duplicate full rows.
- **Migration implication / affected component:** Report findings view should share explicit filters and expandable rows with audit lists while retaining document hierarchy.

## UI-008: Navigation uses incompatible state/history contracts

- **Reconciliation:** Confirmed: captures show route stage tabs, segmented subnavigation and local selections. Inconsistent URL/history semantics are source-backed; Back/Forward was not exercised in this pass.

- **Screen:** Assessment, RFI, report versions, questionnaire, review and workpaper.
- **Severity / priority:** High / P0.
- **Category:** Navigation, consistency, accessibility.
- **Problem:** Shared tabs are links with `aria-selected` but no tab roles; segmented navigation is a button calling `window.location.href`. Report-version type tabs use `href="#"` and hide panels without updating URL. Questionnaire sections swap fragments without a URL section state. Review links suppress their hash navigation. These patterns differ in reopen, copy-link and Back behaviour.
- **Why it matters:** Auditors need to return to the same assessment, control and report type after checking evidence. A location that does not encode the selected work item loses that context.
- **Evidence:** `screenshots/snapshots-1440.png`, `screenshots/questionnaire-1440.png`, `screenshots/review-queue-1440.png`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/components/layout.html` `tabs`, `seg`; `app/templates/pages/report_snapshots.html` `[data-tab]`; questionnaire and queue selection scripts.
- **Recommended fix:** Use links and `aria-current` for route navigation; use full tab semantics for actual in-page panels. Encode assessment/framework/section/selected control in URLs, preserve position and test Back/Forward.
- **Migration implication / affected component:** Define one navigation and selected-item contract before migrating individual page tabs.

## UI-009: Status mappings are repeated and sometimes semantically wrong

- **Reconciliation:** Confirmed: outcome, risk, AI proposal and decision badges coexist in the review detail while queue rows lose those distinctions. Source inventory records semantic label and tone collisions.

- **Screen:** Conclusions, review, findings, evidence, RFI, report versions, narrative.
- **Severity / priority:** High / P0.
- **Category:** Status, hierarchy, consistency.
- **Problem:** Outcome labels/tones are separately declared in several templates. Card metadata uses `.ai` for both “AI proposed” and “Edited by consultant”. Evidence status fallback differs between record and inventory; active/Available uses ok tone there but accent tone in `app/templates/components/workpaper_entry.html`. Resolved findings are labelled “Verified” in the findings list while the service status wording is “Resolved”. Domain report rows display only the first qualifying risk/outcome state, hiding simultaneous categories. Release, issuance, acceptance and approval are distinct transitions that reuse broad accent/neutral treatments.
- **Why it matters:** Readers must distinguish provenance, evidence availability, compliance, risk and sign-off. Similar appearance must not imply equivalent authority.
- **Evidence:** `screenshots/review-queue-1440.png`, `screenshots/evidence-record-1440.png`, `screenshots/report-1440.png`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/components/conclusion_card.html` `.ai`; `app/templates/pages/evidence_detail.html` `evidence_dot`; `app/templates/partials/document_list.html`; report domain priority branch.
- **Recommended fix:** Separate status families and centralize wording/tone mappings. Pair icons/text with restrained semantic colour; distinguish machine provenance from auditor decisions. Show multiple domain counts when they affect triage.
- **Migration implication / affected component:** Status badge and provenance indicator need typed semantics rather than a caller-supplied arbitrary colour.

## UI-010: Shell Search promises a capability without a handler

- **Reconciliation:** Confirmed: home-1440.png shows the shell Search field. The missing retrieval handler remains established by source, not by a screenshot alone.

- **Screen:** All internal screens.
- **Severity / priority:** Medium / P1.
- **Category:** Navigation, interaction, auditor workflow.
- **Problem:** The sidebar presents a Search input, without form action, name, data hook or result target. Shared JavaScript supports dashboard filtering via a different `[data-filter-input]` selector, not this input.
- **Why it matters:** An auditor trying to locate a control, client or evidence file can type into a prominent field with no result. Its scope is unspecified.
- **Evidence:** `screenshots/home-1440.png`; visually inspected in this reconciliation. Functional absence is from markup/handler inspection; no search interaction was executed.
- **Root cause:** `app/templates/base.html` `.side-in > .field input`; `app/static/js/app.js` Dashboard Search/Filter.
- **Recommended fix:** Specify searchable entities and scope, then connect the shell field to results; remove the affordance until there is a functional search contract.
- **Migration implication / affected component:** App-shell search needs real retrieval/navigation, not a decorative input preserved from the template.

## UI-011: Client upload removes the keyboard path to choosing a file

- **Reconciliation:** Confirmed: mobile capture shows a Choose file label. Host keyboard evidence confirms eight Tab presses never reach the input; tabindex=-1 and the label anatomy establish the cause.

- **Screen:** Client upload, the 390px mobile-first screen.
- **Severity / priority:** High / P0.
- **Category:** Accessibility, client workflow.
- **Problem:** The file input has `tabindex="-1"`; the visible “Choose file” control is a label, not a keyboard-focusable button. With JavaScript enabled `.client-upload-submit` is hidden and upload starts on input change. `magic-client.js` adds no keyboard activation for the label.
- **Why it matters:** The client cannot reach the file picker through normal keyboard navigation. Touch-friendly styling does not address keyboard access.
- **Evidence:** `screenshots/b6-magic_upload-default-390.png` captured in the host pass; visually inspected in this reconciliation. Source proves the focusability contract; The host runtime check reports that eight Tab presses never reach a file control.
- **Root cause:** `app/templates/magic/upload.html` `[data-upload-input]`; `app/static/css/yozora-patterns.css` `.client-upload-submit`; `app/static/js/magic-client.js`.
- **Recommended fix:** Keep an accessible native file input in the tab order or provide a real button with keyboard activation and clear upload result/error feedback.
- **Migration implication / affected component:** Client file-picker and upload progress need a complete keyboard and screen-reader interaction contract.

## UI-012: Dark theme inherits unsafe accent pairs and white surfaces

- **Reconciliation:** Confirmed: questionnaire-dark-1440.png and evidence-assessment-dark-1440.png show inherited theme surfaces. Seven non-graphite accent-text pairs fail modeled AA; not all preset associations are shown by these graphite captures.

- **Screen:** Evidence, questionnaire, review; common chips and row icons.
- **Severity / priority:** Medium / P0.
- **Category:** Contrast, theme consistency, readability.
- **Problem:** `.chip` uses `rgba(255,255,255,.7)` and `.rows .ico` uses `rgba(255,255,255,.75)` while their foregrounds come from theme text tokens. They are not theme surface tokens. In dark mode these mixes can produce a light component with a light foreground. Source-based contrast computation also finds seven non-graphite presets retaining light accent-text colours over dark solid surfaces: minimum ratios range from 1.622 (midnight) to 3.187 (azure), below 4.5 for small text. Dark captures confirm the dark surface treatment; the seven accent-text failures are source-computed theme-specific pair failures, not a claim that the default graphite capture shows all presets.
- **Why it matters:** Control mappings and reference chips carry audit context. Their visibility must survive the theme switch.
- **Evidence:** `screenshots/evidence-assessment-1440.png`, `screenshots/questionnaire-1440.png`; visually inspected in this reconciliation; dark equivalents are retained in the screenshot set. Use `MEASUREMENTS.md` for computed failures and limits.
- **Root cause:** `app/static/css/yozora-components.css` `.chip`, `.rows .ico`, `.rec b`; `app/static/css/yozora-tokens.css` accent/theme overrides; `app/static/css/yozora-patterns.css` accent link styles.
- **Recommended fix:** Bind foreground and background as validated pairs in each theme, including compositing over the gradient extremes. Do not infer a global muted-text failure from this specific mismatch.
- **Migration implication / affected component:** Chips, icon containers and theme surfaces need paired semantic tokens and contrast checks.

## UI-013: Long prose has no consistent reading-width role

- **Reconciliation:** Confirmed: report ISO longest prose reaches 138 characters per rendered line at 14px. Review reaches 85 at 16px; evidence record reaches 88 at 13px. A universal prose role is missing.

- **Screen:** Evidence record, executive summary, conclusions and narrative.
- **Severity / priority:** High / P0.
- **Category:** Readability, layout.
- **Problem:** Document text, conclusion prose and executive summary inherit container widths rather than a common prose measure. Some RFI text uses local `70ch` limits, while extracted text and report paragraphs have none. Conversely review prose may be squeezed by a split pane. Measured maximum prose line lengths are 138 characters in the ISO report, 85 in review and 88 in the evidence record.
- **Why it matters:** Evidence and conclusions need a comfortable reading measure while tables need width; neither follows from a global page cap.
- **Evidence:** `screenshots/evidence-record-1440.png`, `screenshots/report-1440.png`, `screenshots/conclusions-1440.jpg`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/pages/evidence_detail.html` `[data-extracted-text]`; `app/static/css/yozora-components.css` `.concl`; `app/static/css/yozora-patterns.css` `.rp-summary`, `.cite-text`.
- **Recommended fix:** Introduce a prose role with measured line length, paragraph rhythm and readable quote styling. Allow spreadsheet tables and full-width inspectors to opt out.
- **Migration implication / affected component:** Reading typography and task layout must be independent primitives; validate 400-word examples before acceptance.

## UI-014: Evidence inventory hides the full mapping summary

- **Reconciliation:** Confirmed: global and assessment inventory captures show compressed mapping and assessment summaries. Exact hidden associations still require the record view.

- **Screen:** Evidence inventory in all three scopes.
- **Severity / priority:** Medium / P1.
- **Category:** Scannability, progressive disclosure, evidence workflow.
- **Problem:** “Supports” shows only the first two mappings plus `+N`. “Both assessments” or `N assessments` replaces assessment names. There is no disclosure attached to those summary counts; the reader must open the file record to discover the exact context.
- **Why it matters:** The decision “does this file support my current control/assessment?” cannot reliably be made from the inventory row.
- **Evidence:** `screenshots/evidence-global-1440.png`, `screenshots/evidence-assessment-1440.png`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/partials/document_list.html` `row.supports[:2]`, `row.used_by|length`.
- **Recommended fix:** Keep compact summaries, but make the mapping count expandable or open a context inspector. Show the current assessment association first and keep source/status visible.
- **Migration implication / affected component:** Evidence rows should expose mapping detail without forcing a full-page context switch.

## UI-015: Record summaries explicitly admit filename ambiguity

- **Reconciliation:** Corrected: the captured evidence record has no visible filename ambiguity warning. Keep this as a conditional source-backed identity risk, not an observed defect in this seeded record.

- **Screen:** Evidence record.
- **Severity / priority:** High / P1.
- **Category:** Auditor workflow, trust, information hierarchy.
- **Problem:** When more than one desk-review catalog entry matches a filename, the UI says some entries may describe another file, then displays the entries as Summary cards and control coverage. These inferred summaries precede the underlying document text.
- **Why it matters:** An auditor deciding whether a file supports a control could rely on a prominently displayed summary whose identity is uncertain. This is a conditional code path; captured record does not show this conditional warning.
- **Evidence:** `screenshots/evidence-record-1440.png`; visually inspected in this reconciliation. Conditional finding, not a claim that this demo contains ambiguous records.
- **Root cause:** `app/templates/pages/evidence_detail.html` `[data-ai-summary]`, `catalog_entries|length > 1`.
- **Recommended fix:** Treat ambiguous matches as unresolved context and withhold authoritative coverage until bound to an evidence version. Make version identity and matched source explicit.
- **Migration implication / affected component:** Evidence summary needs identity and provenance data, not just layout changes. Escalate the matching contract as a migration dependency.

## UI-016: Draft counts treat pre-selected suggestions like answers

- **Reconciliation:** Confirmed: questionnaire-open-1440.jpg shows pre-filled selection and saved-progress messaging. The mismatch between persisted server counts and checked-radio client counts is source-backed; no save was invoked.

- **Screen:** Questionnaire.
- **Severity / priority:** Medium / P1.
- **Category:** Status, auditor workflow.
- **Problem:** Server section progress counts saved answers; client `updateProgress()` counts every checked radio including a pre-fill suggestion before save. The pre-fill copy separately says it only counts once saved. “Answered” therefore changes meaning after hydration.
- **Why it matters:** Auditors need to distinguish selected, confirmed and persisted answers before deciding whether analysis is ready.
- **Evidence:** `screenshots/questionnaire-1440.png`; visually inspected in this reconciliation. Conditional pre-filled-state behaviour is source-backed.
- **Root cause:** `app/templates/partials/section_questions.html` `progress.answered`, `prefill_answer`, `updateProgress`; `app/templates/partials/questionnaire_sections.html` section counters.
- **Recommended fix:** Track proposed, edited/selected and confirmed/saved separately. Keep the completion count tied to persisted confirmation and show pending save changes locally.
- **Migration implication / affected component:** Questionnaire progress needs explicit state semantics rather than DOM checkbox counts.

## UI-017: Review progress uses one tick per conclusion

- **Reconciliation:** Corrected: the captured six-item queue does not overflow at either desktop width. Keep the 93-item tick arithmetic as a scaling risk, not a measured overflow on the captured interim assessment.

- **Screen:** Review queue, particularly full control sets.
- **Severity / priority:** Medium / P1.
- **Category:** Density, layout, scannability.
- **Problem:** The queue renders `range(total)` ticks. Each is 12px with a 3px gap in a nonwrapping flex row, so 93 conclusions imply 1392px of tick width before progress wording. The interim queue has six entries and will not reveal this scale problem by itself.
- **Why it matters:** Portfolio-scale control review needs a compact aggregate progress cue, not a marker per database row.
- **Evidence:** `screenshots/review-queue-1440.png`; visually inspected in this reconciliation; full-set overflow is a CSS arithmetic risk, not a measured screenshot defect.
- **Root cause:** `app/templates/pages/review_queue.html` `.ticks`; `app/static/css/yozora-components.css` `.ticks`, `.ticks i`.
- **Recommended fix:** Use decided/total wording and a bounded progress bar. Show per-item state in the queue where it helps navigation.
- **Migration implication / affected component:** Progress primitive must handle large counts without proportional width.

## UI-018: New engagement hides the completion action

- **Reconciliation:** Confirmed: new-engagement-1440.png shows no completion action before framework selection. Field-error relationships are a source-backed accessibility defect; no submission was made.

- **Screen:** New engagement and setup forms.
- **Severity / priority:** Medium / P1.
- **Category:** Form interaction, workflow, accessibility.
- **Problem:** “Create engagement” is hidden until a framework is checked. The form provides no adjacent persistent explanation for the missing action. Field errors use visual `.invalid` and `.err` without `aria-invalid`/`aria-describedby` links on the affected input.
- **Why it matters:** Users cannot see the final step or receive the field-level relationship reliably through assistive technology.
- **Evidence:** `screenshots/new-engagement-1440.png`; visually inspected in this reconciliation.
- **Root cause:** `app/templates/pages/new_engagement.html` `#create-engagement`, `update`, `.field.invalid`; settings has a similar field-error linkage gap.
- **Recommended fix:** Keep the final action visible with a stated prerequisite, validate on submission and associate each error/help message with its input. Preserve existing explicit labels and error summary.
- **Migration implication / affected component:** Shared form fields and submission states need help/error ids and deterministic validation messaging.

## UI-019: Narrative editing offers acceptance but no draft save

- **Reconciliation:** Confirmed: narrative-1440.png shows section acceptance controls and no independent save-draft action. Replacement and dirty-state behavior remain code-backed; generation was not run.

- **Screen:** Narrative.
- **Severity / priority:** Medium / P1.
- **Category:** Auditor workflow, decision hierarchy.
- **Problem:** The editable textarea has “Save and accept” and “Discard”, but no separate save-draft control or displayed dirty state. Generation and regeneration forms can replace section text; copy explains historical retention but there is no inspected unsaved-edit guard.
- **Why it matters:** Editing a board narrative and approving it for export are separate decisions. A reviewer needs to pause without committing acceptance or losing unsaved work.
- **Evidence:** `screenshots/narrative-1440.png`; visually inspected in this reconciliation. No generate, accept or discard action was invoked.
- **Root cause:** `app/templates/pages/narrative.html` `[data-narrative-accept-form]`, `.narrative-regenerate`.
- **Recommended fix:** Separate draft persistence from acceptance, show unsaved/saved/accepted/stale states and warn before replacement of unsaved edits.
- **Migration implication / affected component:** Narrative editor needs persistence and approval lifecycle support, beyond moving the textarea into React.

## UI-020: Spacing and surface rules are screen-local

- **Reconciliation:** Confirmed: requests, workpaper and RFI captures show different header and disclosure spacing for similar anatomy, matching screen-local source rules.

- **Screen:** Requests, evidence, RFI, setup, workpaper and reporting.
- **Severity / priority:** Medium / P2.
- **Category:** Consistency, visual rhythm.
- **Problem:** Repeated headers, navigation margins, form stacks and row details use inline styles alongside `.cc-*`, `.dr-*`, `.rp-*`, `.nv-*` and `.s8-*` variants. Heading rules repeat in component CSS and shell CSS. This makes equivalent structures depend on which build slice produced the screen.
- **Why it matters:** Consistency reduces the effort of learning where actions, statuses and details appear. Local overrides make later fixes difficult to apply uniformly.
- **Evidence:** `screenshots/requests-1440.png`, `screenshots/workpaper-1440.png`, `screenshots/rfi-items-1440.jpg`; visually inspected in this reconciliation.
- **Root cause:** `app/static/css/yozora-patterns.css`; `app/static/css/src/shell.css`; inline spacing in the cited page templates.
- **Recommended fix:** Consolidate repeated layout recipes and token-backed spacing at migration boundaries; keep legitimate task differences. Do not turn every row into a generic card.
- **Migration implication / affected component:** Shared page header, section, toolbar and disclosure recipes need a small intentional variant set.

## UI-021: Retained live-screen visual acceptance coverage is incomplete

- **Reconciliation:** Corrected: host captures now provide populated live-route audit coverage, including dark and mobile states. The remaining defect is lack of retained automated migration acceptance for this representative content, not lack of any screenshots.

- **Screen:** Entire application and fixture states.
- **Severity / priority:** Medium / P2.
- **Category:** Consistency, verification.
- **Problem:** The 20 retained baselines cover shell/home and component gallery. S7/S8/S9 screen gates also exist, so prior screen QA is not absent. A comprehensive retained baseline set for populated live questionnaire, review, request and report workspaces is still missing. A visually consistent primitive can fail inside nested screen layouts.
- **Why it matters:** Migration must demonstrate large content sets, dark states, conflict and long text, not merely a clean gallery.
- **Evidence:** `screenshots/questionnaire-1440.png`; visually inspected in this reconciliation; source evidence `design/baselines/` file inventory and `design/harness/screenshot.py`.
- **Root cause:** Incomplete retained populated live-screen coverage; see `design/harness/gate_s7.py`, `gate_s8.py`, `gate_s9.py` for existing page-state gates. Host audit captures now cover the populated live routes. They are an audit set, not automatically maintained migration acceptance baselines.
- **Recommended fix:** After first design decisions are accepted, validate five populated workflow screens at both desktop widths, five dark screens and client upload at 390px, including keyboard and text measurements.
- **Migration implication / affected component:** Screen acceptance needs fixtures and capture criteria alongside primitive tests. The second-run prototypes and migration acceptance criteria are specified separately.

## UI-022: Glass and gradient obscure the surface contract

- **Reconciliation:** Confirmed: home and report captures visibly use gradient canvas and translucent reading planes. Fatigue is not measured. Saqlain has decided to retire both.

- **Screen:** All internal pages and the client request container.
- **Severity / priority:** Low / P2.
- **Category:** Visual language, hierarchy, contrast.
- **Problem:** `.glass` and `.solid` both use translucent surfaces, backdrop blur, rounded corners and shadows. The “solid” name does not imply an opaque reading surface. Text contrast depends on composition against the canvas and parent surfaces rather than a single background token.
- **Why it matters:** Long audit sessions benefit from quiet predictable reading planes. Decorative surface variation should not compete with warnings or require screen-position-dependent contrast assumptions.
- **Evidence:** `screenshots/home-1440.png`, `screenshots/report-1440.png`; visually inspected in this reconciliation. This is a design recommendation, not proof of fatigue or measured contrast failure.
- **Root cause:** `app/static/css/yozora-components.css` `.glass`, `.solid`; `app/static/css/yozora-tokens.css` canvas/surface values.
- **Recommended fix:** Use the fixed decision of opaque neutral task surfaces and restrained borders; reserve elevation for genuinely overlapping UI. Saqlain has accepted this direction.
- **Migration implication / affected component:** Surface/elevation tokens should express containment and overlays; do not copy decorative glass into every card.

## UI-023: ISO questionnaire navigation uses privacy-oriented sections

- **Reconciliation:** Corrected: privacy headings are visible in the ISO questionnaire. Saqlain removes the earlier product-intent uncertainty: individual frameworks need their own master domains, multi-framework work needs unified domains.

- **Screen:** Current ISO assessment questionnaire.
- **Severity / priority:** High / P1, confirmed by Saqlain.
- **Category:** Information architecture, framework context, auditor workflow.
- **Problem:** Live GET `/assessments/d491ee73-0925-43bd-8cb2-3b5fff2cc8ac/questionnaire/sections` reports 38 answered questions and includes sections named “Children & Vulnerable Individuals” and “Incident Response & Breach Notification”. The brief identifies this assessment as ISO 27001 with 93 controls, but live HTML also contains six legacy DPDPA conclusions and both framework tabs. Saqlain confirms that privacy headings are wrong for a single ISO assessment. The navigation must follow its own domains; the cross-framework case needs unified domains. The questionnaire section labels are not recognizable ISO domains/control-set coverage. This does not prove the answers or deterministic scoring are incorrect.
- **Why it matters:** Auditors need to understand how questions map to the chosen framework and what coverage remains before moving to control review.
- **Evidence:** `screenshots/questionnaire-1440.png`; visually inspected in this reconciliation; live HTML section names and `[data-section]` navigation.
- **Root cause:** `app/templates/partials/questionnaire_sections.html` renders supplied section titles without showing framework/control coverage per section. Backend question-set selection and seed provenance require separate investigation before asserting a data defect.
- **Recommended fix:** Expose framework and control coverage in questionnaire navigation; use the fixed single-framework and unified-framework domain decision. Use source framework terminology where the grouping is framework-specific.
- **Migration implication / affected component:** Questionnaire navigation must accept coverage/context data. Use master framework domains and validate the underlying mapping, rather than merely changing labels.

## UI-024: Upload fixture audit blocker resolved

- **Reconciliation:** Withdrawn: the host temporarily seeded three fixture links, captured all four upload states at 390, then removed them. This resolves audit coverage, not the self-contained-fixture code dependency.
- **Screen:** Design-only client upload fixture.
- **Severity / priority:** Medium / P2, withdrawn.
- **Category:** Verification, client workflow coverage.
- **Problem:** First-run GETs returned 500 because required fixture links were absent. Captures now establish all advertised states.
- **Why it matters:** Mobile upload was inaccessible to the original audit. It is now reviewed, including a confirmed keyboard defect and error-layout findings.
- **Evidence:** `screenshots/b6-magic_upload-default-390.png`, `screenshots/b6-magic_upload-uploading-390.png`, `screenshots/b6-magic_upload-done-390.png`, `screenshots/b6-magic_upload-error-390.png`.
- **Root cause:** Temporary fixture/demo seed mismatch, resolved for capture by the host.
- **Recommended fix:** Keep deterministic upload fixtures in migration acceptance. Do not reseed this audit database.
- **Migration implication / affected component:** Client upload state fixtures and acceptance coverage.

## Focused workflow conclusions

**Questionnaire (Phase 7):** The auditor is confirming answers against evidence, then saving work. Its existing domain navigation and two-pane pattern are useful starting points, but nested gutters, undersized guidance, hidden draft semantics and framework ambiguity require resolution. A third inspector pane is conditional: at 1280px it may be better as a drawer or replaceable context pane. Keep the question and confirmed answer visible; disclose repetitive criteria/context and retain persistent unsaved status. UI-001, UI-002, UI-004, UI-008, UI-016, UI-023.

**Evidence requests (Phase 8):** Distinguish the engagement Requests dashboard, assessment RFI item selection, immutable RFI versions and client links. The choice is what to request next; title, requirement, receipt and inclusion state belong in the summary. Full request wording and examples belong in a disclosure/preview. UI-005, UI-008, UI-009, UI-011.

**Review (Phase 9):** The decision is whether evidence justifies the conclusion and whether the auditor will approve, amend or reject it. Current source includes citation links, contradiction alerts, conflict comparison, locked state, separate client/evidence comparison and shared-evidence grouping. Preserve those strengths. Expose queue triage wording, promote auditor decision authority and keep supporting provenance layers available without making every layer mandatory reading. UI-002, UI-003, UI-006, UI-008, UI-009, UI-017.

**Reporting (Phase 10):** Existing executive summary, domain distribution and “Fix first” are valuable. Improve their connection to exception detail, search/filtering and authoritative release/version state; avoid duplicating long detail rows. Narrative editing needs a draft state distinct from acceptance. UI-007, UI-008, UI-009, UI-013, UI-019.

## Coverage and remaining validation

The register groups systemic issues across screens rather than creating one issue for every page. `SCREEN_INVENTORY.md` carries the route-by-route coverage, density and task assessment, including home, clients, engagement management, AWS evidence, purge, settings, evidence reuse, desk review, scope, comparison, board inputs, SoA and fixtures. No new issue is asserted merely because a screen is empty.

All categories A to M are covered: hierarchy (002, 006, 009), readability (001, 002, 012, 013), layout (001, 013, 017), density (005, 007, 017), scannability (003, 007, 014), status (009, 016), component choice (005, 006, 007), disclosure (005, 006, 014), navigation (008, 010), workflow (004, 015, 018, 019, 023), cognitive load (005, 006), consistency (008, 009, 020), accessibility (003, 008, 011, 012, 018).

The host captures establish visual geometry and the upload keyboard defect. Remaining interaction acceptance includes Back/Forward recovery, partial-save recovery, a 93-item queue, dark preset usage and screen-reader error linkage. This docs-only pass does not claim those interactions were exercised. The comparison fixture has two 404 captures; the populated live comparison is reviewed through `screenshots/comparison-1440.jpg` and `screenshots/comparison-1280.jpg`.

## UI-025: Stacked navigation obscures the current work area

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Assessment RFI, Review and Report.
- **Severity / priority:** High / P0.
- **Category:** Navigation, hierarchy.
- **Problem:** RFI places assessment stage tabs, report segmented navigation and RFI Items/Versions/Client links in successive horizontal bars above an empty Consultant name field.
- **Why it matters:** The auditor must decode three changing levels before reaching the evidence request task.
- **Evidence:** `screenshots/rfi-items-1440.jpg`.
- **Root cause:** RC-12 and RC-13; layout.html, seg_rows.html and pages/rfi.html.
- **Recommended fix:** Keep one stage tab bar. Use a titled workspace sidebar for all sub-sections, with grouped links for third-level destinations.
- **Migration implication / affected component:** Assessment navigation and workspace sidebar.

## UI-026: Client name replaces the assessment page purpose

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Questionnaire, Overview, Report.
- **Severity / priority:** Medium / P1.
- **Category:** Hierarchy, context.
- **Problem:** The client name repeats in breadcrumb, h1 and subtitle while the current work area depends on the selected tab.
- **Why it matters:** Readers must find the tab to identify the page; repeated identity displaces the task title.
- **Evidence:** `screenshots/questionnaire-open-1440.jpg`.
- **Root cause:** RC-13; assessment header and breadcrumb view model.
- **Recommended fix:** Name the task in h1 and keep client, engagement and framework in context metadata.
- **Migration implication / affected component:** Page header and breadcrumbs.

## UI-027: Review repeats the same file in two evidence blocks

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Review queue, expanded conclusion.
- **Severity / priority:** High / P1.
- **Category:** Provenance, density.
- **Problem:** Access rights shows Veldhara_Access_Review_Q2_FY26.docx under both Evidence and Evidence on this control.
- **Why it matters:** Duplicate blocks consume decision space without adding a second source of assurance.
- **Evidence:** `screenshots/review-selected-1440.png`.
- **Root cause:** RC-14; conclusion_card.html and requirement_card_body.html.
- **Recommended fix:** One concise provenance narrative with linked file and citation disclosure; retain conflicts and missing evidence.
- **Migration implication / affected component:** Finding detail and provenance.

## UI-028: Recommendation is demoted below its deliverable weight

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Review queue, conclusions.
- **Severity / priority:** High / P1.
- **Category:** Hierarchy, deliverables.
- **Problem:** Recommended action uses a small tinted inset and smaller body type than the conclusion. No recommendation reasoning is visible.
- **Why it matters:** The recommendation is a primary client deliverable; its logic must be reviewed alongside the gap.
- **Evidence:** `screenshots/review-selected-1440.png`.
- **Root cause:** RC-14 and RC-16; conclusion_card.html .cc-remediation.
- **Recommended fix:** Give recommendation a 14px or larger full-weight section and a reasoning slot.
- **Migration implication / affected component:** Finding recommendation and content track.

## UI-029: Finding titles name controls rather than actual gaps

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Review queue, conclusions and findings.
- **Severity / priority:** High / P1.
- **Category:** Scannability, content.
- **Problem:** The selected finding is titled Access rights while its actual gap is incomplete access reviews and outstanding removals.
- **Why it matters:** The auditor must read each detail to understand the action item.
- **Evidence:** `screenshots/review-selected-1440.png`.
- **Root cause:** RC-14 and RC-16; finding/conclusion view model and conclusion_card.html.
- **Recommended fix:** Use a distinct gap title, retaining A.5.18 and Access rights as secondary context.
- **Migration implication / affected component:** Finding summary and data contract.

## UI-030: SoA asks for a justification on every control

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Statement of applicability.
- **Severity / priority:** High / P1.
- **Category:** Workflow, density.
- **Problem:** The SoA page is 17,481px tall at 1440 and shows a justification textarea beside every control, plus its own report subview.
- **Why it matters:** Repeated normal-applicability work distracts from the exceptions that need an auditor decision.
- **Evidence:** `screenshots/soa-1440.jpg`.
- **Root cause:** RC-15; pages/soa.html and applicability persistence.
- **Recommended fix:** Default controls to applicable with a standard justification. Collect only not-applicable exceptions and reasons inside Scope.
- **Migration implication / affected component:** Scope applicability exceptions.

## UI-031: Upload error is detached from the failed item

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Client upload at 390.
- **Severity / priority:** High / P1.
- **Category:** Recovery, accessibility.
- **Problem:** The error alert sits immediately above the h1 without a gap and does not identify which evidence item failed.
- **Why it matters:** The client cannot tell where to retry, especially after selecting among several requested items.
- **Evidence:** `screenshots/b6-magic_upload-error-390.png`.
- **Root cause:** RC-05; magic/upload.html and magic-client.js.
- **Recommended fix:** Put an associated error and retry beside the failed item; reserve an error summary for navigation to that item.
- **Migration implication / affected component:** Client upload item error.

## UI-032: Upload introduction precedes the task title

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Client upload at 390.
- **Severity / priority:** Medium / P1.
- **Category:** Hierarchy, client context.
- **Problem:** The introductory sentence appears above Upload your evidence.
- **Why it matters:** The page delays the main task and separates its h1 from the brand header.
- **Evidence:** `screenshots/b6-magic_upload-default-390.png`.
- **Root cause:** RC-13; magic/upload.html.
- **Recommended fix:** Place h1 first, then purpose and instructions in a readable paragraph.
- **Migration implication / affected component:** Client page header.

## UI-033: Upload combines undersized instructions with mixed branding

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Client upload at 390.
- **Severity / priority:** Medium / P1.
- **Category:** Readability, consistency.
- **Problem:** Most upload guidance is 13px. Header says CyberAssess; footer says Powered by Yozora. Default state has 9 visible text nodes below 14px, error state 13.
- **Why it matters:** Clients need readable evidence instructions and an unambiguous service identity.
- **Evidence:** `screenshots/b6-magic_upload-default-390.png`.
- **Root cause:** RC-02 and RC-13; magic/upload.html typography and footer.
- **Recommended fix:** Set substantive guidance to 14px minimum and use one CyberAssess identity. Keep only optional expiry metadata below 14px.
- **Migration implication / affected component:** Client typography and branding.

## UI-034: Already requested evidence remains in the selection form

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** RFI items.
- **Severity / priority:** High / P1.
- **Category:** Workflow, density.
- **Problem:** Rows marked Already requested remain alongside unissued candidates with the same expanded request guidance.
- **Why it matters:** The auditor must repeatedly distinguish items that are no longer request candidates.
- **Evidence:** `screenshots/rfi-items-1440.jpg`.
- **Root cause:** RC-15; pages/rfi.html and request membership projection.
- **Recommended fix:** Exclude current RFI members from candidate selection. Show requested items in a compact issued group or version view.
- **Migration implication / affected component:** RFI candidate membership and list.

## UI-035: Report prose does not yet serve board decisions

- **Reconciliation:** Added: confirmed from the cited capture and Saqlain's notes.
- **Screen:** Report.
- **Severity / priority:** High / P1.
- **Category:** Content, audience.
- **Problem:** The executive summary exists but leads with numerical posture and framework distributions. It does not provide the requested engagement narrative, per-gap impact and recommendation logic for a board.
- **Why it matters:** A board needs context, business consequences and priorities; counts alone do not establish those decisions.
- **Evidence:** `screenshots/report-iso-1440.jpg`.
- **Root cause:** RC-16; report_summary.html, narrative generation and report view model.
- **Recommended fix:** Keep board and detailed views with content slots for engagement context, domain gaps, business impact and reasoned recommendations. Address writing in a separate content track.
- **Migration implication / affected component:** Report document and content contract.
