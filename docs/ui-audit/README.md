# CyberAssess UI audit: Phase 12 stop point

The source/HTTP audit identifies 24 grouped issues, with 8 P0, 12 P1 and 4 P2 priorities. The largest migration risks are constrained task layouts, undersized audit prose, hidden queue outcomes, inconsistent navigation/state and blurred status semantics. Most are avoidable within the existing stack. This is the authorised A2 fallback result: no screenshots or browser measurements were obtained, so visual approval remains pending.

Port 8011 was reachable. Chromium launch failed with a sandbox macOS MachPort permission error. All 38 required live route variants returned HTTP 200 after redirects. Read-only inspection covered 213 routes/fragments/states, including every questionnaire section returned for the current and NIST assessments. Five fixture responses failed: four upload states returned 500 and the comparison fixture returned 404. No server was started, no seed changed and no AI action ran.

## The ten biggest problems

These are source/HTTP findings with expected workflow impacts, not measured scanning-time or fatigue results. See the issue register for severity, evidence and specific recommendations.

| Issue | Problem | Migration priority |
|---|---|---|
| UI-001 | Fixed navigation and nested gutters consume the questionnaire work area before the reading task is considered. | P0 |
| UI-002 | Guidance, caveats, evidence and gap descriptions use 12/13px metadata roles. | P0 |
| UI-003 | The review list represents outcome with a dot and tooltip; risk and exception flags remain in hidden data. | P0 |
| UI-004 | Questionnaire saves require a complete section, with no inspected draft/dirty-navigation contract. | P1 |
| UI-005 | RFI selection exposes repeated guidance before compact receipt and inclusion decisions. | P1 |
| UI-006 | Review exposes many provenance layers at once and places decisions after long supporting detail. | P1 |
| UI-007 | Report detail lacks local triage and repeats critical rows despite useful existing summaries. | P1 |
| UI-008 | Route tabs, in-page tabs, questionnaire selection and review selection have different URL/history contracts. | P0 |
| UI-009 | Status mappings duplicate wording and confuse provenance, lifecycle, outcome and authority. | P0 |
| UI-010 | The prominent shell Search input has no inspected search handler or result contract. | P1 |

The client upload keyboard path (UI-011), dark theme foreground/background pairs (UI-012) and consistent reading measure (UI-013) are also P0. High severity does not automatically mean P0: a workflow improvement may be P1 while an accessibility foundation must precede viability.

## Which problems are systemic?

Width, type roles, surface pairs, status mapping, form anatomy, navigation state and retained screen verification span multiple routes. [ROOT_CAUSES.md](ROOT_CAUSES.md) classifies 12 causes exactly once:

| Stack | Design decision | Shortcut | Never designed |
|---:|---:|---:|---:|
| 1 | 3 | 7 | 1 |

Eleven of twelve causes concern design decisions, bypasses or unspecified rules; React does not solve them automatically. The stack-related cause is coordination of selection, fragments, local scripts, errors and URL state. Jinja already supports shared macros and the app already has tokens, readable conclusion type, explicit warnings and useful component primitives.

Starting assumptions were corrected rather than repeated. There are 623 parsed inline style attributes, 426 outside board-print layout. Only the gallery actually calls the shared `ui.field` macro. Local prose caps and review-width exceptions already exist. The retained shell/gallery baselines are incomplete, but S7/S8/S9 page comparison gates refute the claim that no screen was ever checked.

## What should not carry into Next.js?

Do not preserve the single default workspace width, nested card gutters, metadata styling for audit prose, arbitrary surface combinations, repeated status dictionaries, undurable selected-item state, decorative Search or completion-only persistence. Do not translate each inline layout choice into a one-off Tailwind class composition.

Preserve deterministic framework-specific scoring, period/cutoff and immutable release semantics, citation/version identity, contradiction and conflict warnings, shared evidence, readable conclusion styling, current executive/domain summaries and existing keyboard/modal behavior. The current report already has summaries; the recommendation is to connect them to exception detail.

## Core design principles proposed for the new UI

Separate content typography from metadata. Optimize layouts for the decision and allow dense inventory, reading and task-workspace modes. Show outcome, severity, lifecycle and provenance as distinct text-backed dimensions. Keep blockers and auditor authority explicit. Reveal repetitive guidance and provenance detail after a concise summary. Make selected section/control and framework context durable in the URL, with safe draft persistence and predictable focus. Validate both desktop widths and the one mobile-first client flow using real content.

The Yozora recommendation keeps P1/P3/P4/P6/P8/P9/P10, changes P2/P5/P7, retires the canvas gradient and glass reading surfaces, keeps eight branding presets subject to pair validation, and changes the status color contract. [ROOT_CAUSES.md](ROOT_CAUSES.md) gives the exact principle wording, rationale and limits. These are recommendations for Saqlain, not adopted design decisions.

Source contrast calculations do not support a global muted-text failure: base body, secondary and muted tokens pass AA on modeled canvas/glass/solid. Seven non-graphite accent-text presets in dark theme require targeted attention, and literal white chips need rendered pairing checks. The complete 5,198-row contrast matrix is a conservative source superset; it is not an accessibility certification of the running UI.

## P0 fixes and acceptance direction

The eight P0 issues are UI-001, UI-002, UI-003, UI-008, UI-009, UI-011, UI-012 and UI-013. Resolve task width, reading type/measure, queue outcome wording, navigation state, status vocabulary, upload keyboard access and validated theme pairs before considering migration UI viable. Acceptance must include actual rendered width/type/line-length measurements and keyboard/history checks, which remain deferred here.

Candidate archetypes for the second dispatch are inventory/list, review workspace, form/configuration, report/document and work queue. Keep prose width independent of table/task width. Questionnaire may use navigation plus reading with contextual evidence in a drawer or replaceable inspector at 1280; a permanent third column must be justified by actual content measurements. This run does not create PAGE_ARCHETYPES.md or an implementation specification.

## Five screens to redesign first

1. Evidence requests: include RFI item selection, engagement Requests and client upload, since they are distinct tasks.
2. Evidence inventory: test all three scopes and exact mapping/version discovery.
3. Questionnaire: test populated and partly answered sections, evidence disclosure and draft persistence.
4. Review: test pending selection, expanded evidence, edit, conflict, locked and blocked states.
5. Report: use the ISO 93-control content, preserve domain/risk summaries and improve exception drill-down.

## Common components to establish first

At the recommendation level, start with shell/context navigation and task-width containers; typography/content roles; status/provenance indicators; labelled form controls with errors and draft state; structured table/list rows with filter and disclosure anatomy; and a reading/decision workspace with citation context. Dialog, alert, loading and upload primitives must retain focus and recovery contracts. The formal component inventory and exact variants belong to the second run.

## Deliverables and coverage

| Artifact | What it establishes |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Verified stack, source organization, reusable primitives and corrected starting assumptions |
| [SCREEN_INVENTORY.md](SCREEN_INVENTORY.md) | 206 route/state/interaction entries, including 38 required live variants and all 44 fixture names |
| [UI_ISSUES.md](UI_ISSUES.md) | 24 grouped findings with P0/P1/P2 and focused questionnaire/request/review/report assessments |
| [ROOT_CAUSES.md](ROOT_CAUSES.md) | 12 classified causes and full Yozora ruling |
| [MEASUREMENTS.md](MEASUREMENTS.md) | Per-screen pending browser fields, contrast method and source type risks |
| [CONTRAST_APPENDIX.md](CONTRAST_APPENDIX.md) | All source-computed contrast candidate pairs and extrema |
| [STATUS_INVENTORY.md](STATUS_INVENTORY.md) | Status wording, tone, location and semantic collisions |
| [CAPTURE_REQUESTS.md](CAPTURE_REQUESTS.md) | 421 exact requests: 412 light desktop, five dark desktop and four mobile upload |
| [http-observations.json](http-observations.json) | 213 curl GET responses, effective URLs, markup/text and fragment targets |
| [tools](tools/) | Reproducible manifest, HTTP inspection, contrast, deferred capture/measurement and documentation verification tools |

Phases 1, 3, 4 and 7 to 12 are delivered through source/HTTP inspection. Phase 2 is delivered through A2's deferred-capture inventory. Phase 5 DESIGN_SYSTEM.md and Phase 6 PAGE_ARCHETYPES.md are explicitly second-run deliverables under A6, with only recommendations/candidate archetypes here. Phases 13 to 15 were not executed.

Document verification passed: complete request coverage, issue structure and references, valid local links, contrast extrema, live HTTP status, no new long dashes and allowed change scope. The contrast calculation smoke checks passed. No production test run was needed for documentation-only changes.

## What remains unverified

Zero screenshots exist. Width, unused width, actual line length, rendered text-node counts, visible overflow, scroll/action placement, keyboard runtime behavior and visual hierarchy remain pending. Each issue cites a requested capture and an inspected source; the existing-screenshot requirement cannot be met in this sandbox, so A2's fallback takes precedence. The 421 requests are comprehensive state coverage, not 421 claims of distinct visual defects.

The upload fixture needs its expected `s8-client-active` data; the comparison fixture needs a valid previous assessment. These failures are fixture limitations, not proof that production upload or live comparison is broken. No changes to either were authorised in this docs-only run. [CAPTURE_REQUESTS.md](CAPTURE_REQUESTS.md) includes the handoff for an unrestricted capture host and records the remaining manual interaction checks.

## Questions for Saqlain at this stop point

- Accept opaque neutral reading surfaces and retirement of the gradient canvas, or retain a restrained brand treatment outside content?
- Should shared questionnaire grouping stay cross-framework with explicit control coverage, or should navigation present framework-native domains? The demo includes legacy DPDPA alongside ISO.
- Should questionnaire and narrative drafts save explicitly or automatically, with completion/acceptance kept separate?
- Which queue triage dimension should lead: pending decision, high risk or missing/contradictory evidence?

These decisions are for the second dispatch. No redesign, production implementation, push or PR was performed.
