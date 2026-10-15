# CyberAssess UI audit

The interface needs a shared reading and decision system before its Next.js cutover. Most defects come from design decisions, shortcuts and missing specifications. Replacing Jinja and HTMX alone will preserve them. The target is opaque neutral surfaces, readable audit text, compact inventories and a consistent finding hierarchy.

## The ten biggest problems

| Issue | Problem | Target |
| --- | --- | --- |
| UI-001 | Question pane is576px inside a1040px page at 1440. | Wide task workspace with a196px domain rail and no permanent third pane. |
| UI-002 / UI-013 | Guidance is12px, substantive text13px, report prose reaches138 characters per line. | Audit text >=14px; primary reading16px; prose56ch target. |
| UI-025 / UI-008 | Stage tabs stack above changing subnavigation; RFI adds a third level. | One stage bar; Option A flattened Section selector or Option B nested sidebar links, pending Saqlain; stable URL state. |
| UI-003 / UI-009 / UI-012 | Queue dots hide outcomes; status meanings collide; seven dark accent-text pairs fail modeled contrast. | Four labelled status families and validated theme pairs. |
| UI-004 | Section validation prevents draft saving and navigation can discard work. | Partial autosave and separate explicit completion. |
| UI-027 / UI-028 / UI-029 | Control-name titles, duplicate evidence and demoted recommendation obscure the finding. | Gap title, outcome, impact, recommendation/logic and one provenance narrative. |
| UI-005 / UI-034 | RFI is20,005px tall and repeats selection content. | Compact sorted requests, inclusion state, guidance on demand. |
| UI-007 / UI-035 | Report repeats detail and needs reader-specific context rather than counts. | Accepted executive prose, all domains, board/detail views. |
| UI-030 | SoA is17,481px and asks for every control justification. | Scope exception panel with standard applicable justification. |
| UI-011 / UI-031 / UI-032 / UI-033 | Mobile upload file picker is unreachable by Tab; error/heading/type/branding need repair. | Keyboard file choice, item-linked errors, h1 first and consistent CyberAssess branding. |

## Which problems are systemic

ROOT_CAUSES.md records16 causes:1 Stack,3 Design decision,7 Shortcut,5 Never designed. Fifteen of 16 are not inherent to Jinja/HTMX. Width, small text roles, status semantics, repeated navigation, copied card markup and missing provenance/content contracts affect many screens. The stack cause is fragment-local state and focus/history coordination; explicit React contracts can help, but do not automatically fix it.

## What must not carry into Next.js

Retire gradient canvas, glass surfaces, stacked segmented navigation, universal narrow page width, metadata-sized audit content, control-title-only findings, duplicate evidence regions, footer-only decisions, per-control SoA justification forms and full RFI teaching text on every row. Do not copy HTML fragments into React with the same structure. Keep deterministic Python scoring, separate framework scores, evidence/version trace, conflict guards, locked/released gates and conditional framework copy.

## Core principles

Information follows the auditor's decision. A table is for scanning, a workspace for comparing, and a document for reading. All audit content is at least14px. Prose targets60 to 80 characters per full line. Status has words and a semantic family. Surface, spacing and typography come from shared tokens. Greyscale preserves title, gap and next action. One stage navigation bar is enough; Option A uses a labelled Section selector; Option B exposes nested sidebar links. Choice pending Saqlain; B is recommended for frequent switching. Good writing remains a separate track.

## P0 migration gates

UI-001, UI-002, UI-003, UI-008, UI-009, UI-011, UI-012, UI-013 and UI-025 must pass the measured checks in the spec's P0 table before the migrated UI is viable. These cover usable width, reading size/measure, explicit status, navigation/history, theme contrast and keyboard file access. Source/math checks in this run do not replace runtime geometry and keyboard tests of a future implementation.

## Prototype screens and components

Build Questionnaire, Review queue, Conclusions, RFI and Report first. Scope applicability and a second queue navigation option bring the total to seven files. Their [static prototypes](prototypes/README.md) test distinct work patterns with real Veldhara GET content. The first primitives are AppShell, Page width modes, Header/StageNav/SectionSelect, Text/Prose roles, Field, StatusBadge and DataTable. Then compose QuestionCard, FindingDetail/ReviewDecision, RequestRow and DomainSummary. The component inventory rules on every provisional plan component; no generic Card or decorative score ring is required.

## Requirements coverage

Each of Saqlain's decisions and per-screen requirements is linked below. Split rows distinguish data, writing and display dependencies. Presentation 32, Backend 14, Content 14;60 rows total. Requirements that are not demonstrated name the reason instead of implying a static screen verifies them. Requirements JSON and the spec use identical IDs.

| ID | Decision / requirement | Prototype or reason | Spec section | Classification |
| --- | --- | --- | --- | --- |
| D01 | FastAPI remains JSON API; cut over screen by screen | No static API execution: spec only | Delivery | Backend |
| D02 | Retire gradient canvas and glass | All seven | Foundation | Presentation |
| D03 | Keep eight accents for interaction and branding only | All seven, graphite shown; other presets in token table | Foundation | Presentation |
| D04 | Four status families | All seven | Status | Presentation |
| D05 | Control codes allowed beside titles | questionnaire.html, review-queue.html, gaps.html | Review hierarchy | Presentation |
| D06a | Single framework uses its own master domains | questionnaire.html (target ISO focus) | Questionnaire | Backend |
| D06b | Multi-framework covers each requirement once in unified domains | Not shown: ISO focus prototype; multi-framework is specified | Questionnaire | Backend |
| D07a | Drafts save automatically while typing | questionnaire.html (static saved state) | Draft contract | Backend |
| D07b | Draft saving feedback and explicit completion act | questionnaire.html | Draft contract | Presentation |
| D08 | Pending first, then missing or contradictory evidence; sort and switch anytime | review-queue.html | Review queue | Presentation |
| D09 | Laptop 1440 with 1280 support | All seven | Foundation | Presentation |
| D10 | Never stack secondary or tertiary navigation bars | All seven; review-queue-sidebar.html compares option B | Navigation | Presentation |
| D11 | Inter stays | All seven | Foundation | Presentation |
| Q01 | Question area uses available width, no blank side | questionnaire.html | Questionnaire | Presentation |
| Q02 | Control requirement is primary | questionnaire.html | Questionnaire | Presentation |
| Q03 | Explain why asked | questionnaire.html | Content track | Content |
| Q04 | Hint on how to put question to client | questionnaire.html | Content track | Content |
| Q05 | Persist distinct why and how fields | questionnaire.html | Questionnaire | Backend |
| Q06 | Rework help hierarchy at readable size and measure | questionnaire.html | Questionnaire | Presentation |
| Q07 | Show unanswered and answered after assessment | questionnaire.html | Questionnaire | Presentation |
| Q08 | ISO uses four Annex A themes, not privacy headings | questionnaire.html | Questionnaire | Presentation |
| R01 | Each queue item is a finding before approval | review-queue.html | Review hierarchy | Presentation |
| R02a | Gap title distinct from control name | review-queue.html, gaps.html | Review hierarchy | Backend |
| R02b | Write short gap titles | review-queue.html, gaps.html | Content track | Content |
| R03 | Gap statement then compliance status | review-queue.html, gaps.html | Review hierarchy | Presentation |
| R04a | Risk or impact of non-compliance | review-queue.html, report.html | Review hierarchy | Backend |
| R04b | Write impact statements | review-queue.html, report.html | Content track | Content |
| R05 | Recommendation at full weight | review-queue.html, report.html | Review hierarchy | Presentation |
| R06a | Recommendation reasoning has its own slot | review-queue.html, report.html | Review hierarchy | Backend |
| R06b | Write recommendation logic | review-queue.html, report.html | Content track | Content |
| R07a | What reviewed and who spoken to as provenance | review-queue.html | Review hierarchy | Backend |
| R07b | Concise provenance narrative | review-queue.html, gaps.html | Content track | Content |
| R08 | One provenance block; cited file one click away | review-queue.html, gaps.html | Review hierarchy | Presentation |
| R09 | Queue outcome and risk in words | review-queue.html | Review queue | Presentation |
| R10 | Approve edit reject attached and visible | review-queue.html | Review queue | Presentation |
| R11 | One gap detail across the Review queue and the gap register | review-queue.html, gaps.html | Review hierarchy | Presentation |
| C01 | Gaps are decided conclusions without queue mechanics | gaps.html | Gaps | Presentation |
| C02 | Deterministic table domain control ID gap risk status owner | gaps.html | Gaps | Presentation |
| C03 | Row expands to the gap workpaper and remediation | gaps.html | Gaps | Presentation |
| F01 | RFI tight sortable list | rfi.html | RFI | Presentation |
| F02a | Already added item absent from same add form | rfi.html | RFI | Backend |
| F02b | Separate included items from candidates | rfi.html | RFI | Presentation |
| F03 | What to send and good looks like on demand | rfi.html | RFI | Presentation |
| P01 | Written executive context first | report.html | Content track | Content |
| P02 | Summary names engagement reviewed material and scope domains | report.html | Report | Content |
| P03 | Summary identifies gaps location criticality and overall posture | report.html | Report | Content |
| P04 | Gaps by domain, weakest and strongest | report.html | Report | Presentation |
| P05 | Each domain gap has non-compliance impact risk for board | report.html | Content track | Content |
| P06 | Board summary and auditor/technical detail | report.html | Report | Presentation |
| P07 | Recommendations and logic follow exported report flow | report.html | Report | Presentation |
| S01a | Ask only non-applicable controls and reasons | scope-applicability.html | Scope and SoA | Presentation |
| S01b | Everything else applicable with standard justification | scope-applicability.html | Scope and SoA | Backend |
| S01c | Author standard applicability justification | scope-applicability.html | Content track | Content |
| S02 | SoA lives under Scope, no own tab | scope-applicability.html | Navigation | Presentation |
| T01 | Content quality is separate, reader-specific track | Not solved by static prototype: examples expose slots only | Content track | Content |
| T02 | Useful consultant AI output and good reports with less effort | Not measured: needs consultant task testing | Content track | Content |
| D06c | Unified taxonomy and requirement wording | Not shown: requires content track beyond ISO focus | Content track | Content |
| R07c | Persist independent provenance narrative | review-queue.html, gaps.html | Review hierarchy | Backend |
| R12 | Expose queue state and evidence conflicts to JSON | review-queue.html | Delivery | Backend |
| P08 | Expose accepted narrative and board read model | report.html | Report | Backend |

## Deliverables

The nine requested audit documents are:

| Document | Purpose |
| --- | --- |
| [README.md](README.md) | Executive findings and requirements coverage |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Current source architecture |
| [SCREEN_INVENTORY.md](SCREEN_INVENTORY.md) | Live route and state coverage |
| [UI_ISSUES.md](UI_ISSUES.md) | Reconciled35-issue register |
| [ROOT_CAUSES.md](ROOT_CAUSES.md) | 16 causes and design rulings |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Target tokens, contrast, type, widths and navigation |
| [PAGE_ARCHETYPES.md](PAGE_ARCHETYPES.md) | Reusable archetypes and T1 to T7 rulings |
| [NEXTJS_MIGRATION_UI_SPEC.md](NEXTJS_MIGRATION_UI_SPEC.md) | Coding-agent contract and 60 classified requirements |
| [COMPONENT_INVENTORY.md](COMPONENT_INVENTORY.md) | 40 shared primitive/domain contracts |

Supporting evidence: [Measurements](MEASUREMENTS.md), [Status inventory](STATUS_INVENTORY.md), [Contrast appendix](CONTRAST_APPENDIX.md), [Saqlain decisions](SAQLAIN_FEEDBACK.md), [Host rendered summary](rendered-measurements-summary.json), [Target contrast](target-contrast.json), [Prototypes and illustrative dependencies](prototypes/README.md). Capture requests remain a historical plan with completion status, not a list of missing screenshots.

## What changed after the first half

Host captures now substantiate appearance and geometry:411 measured rows,109 committed live/dark/mobile captures plus local fixture captures. The original24 issues reconcile to 19 confirmed,4 corrected and 1 withdrawn. UI-015's conditional wording and UI-017's six-item scale claim were narrowed; UI-021 acknowledges host coverage; UI-023 is now a product requirement with confirmed wrong framework headings. UI-024's audit fixture blocker is withdrawn because the upload fixtures were temporarily seeded, captured and removed. Eleven new entries UI-025 toUI-035 capture stacked navigation, repeated client headings, duplicate provenance, small recommendation treatment, finding titles, SoA workload, upload error/heading/type/brand problems, RFI repetition and audience-specific report content. There are 35 register entries,34 active.

The comparison fixture still returns404 in two captures. The populated live comparison is captured at both widths and is not unreviewed. Most below14px counts include metadata, so counts alone are not accessibility defect counts. Runtime host keyboard evidence establishes the upload file-control failure. Autosave, conflict and history behavior remain code-backed findings unless exercised by the host.

## Verification and limits

Run `python docs/ui-audit/tools/verify_audit.py`. It checks all nine documents,35 structured issues and existing cited screenshots, all P0 rules,60 coverage rows, classification values and code paths, seven prototype files/shared CSS/fonts, illustrative IDs and manifests, realistic source row counts, target contrast and write scope. Prototype source is GET-only, with no AI spend. No browser/server/commit was used in this run.

The pre-fix prototypes have supplied host captures at both laptop widths. This fix pass inspected them and made static changes without launching a browser. Fresh rendering remains unverified, as instructed. Host screenshot review must prove layout at 1440/1280, actual line lengths, focus order and sticky decisions. Autosave and other backend contracts are specified, not implemented. The seven screens render from disk; citation destinations require the existing app. The current source assessment contains DPDPA plus ISO; questionnaire/report prototypes explicitly demonstrate ISO focus, and the target single-framework grouping is disclosed. Content quality and productivity need their own writing and consultant testing work. Sub-section navigation is pending Saqlain between the select and nested sidebar options; neither prevents this prototype pass. Board height may exceed the three-screen target while all 25 primary findings remain visible.
