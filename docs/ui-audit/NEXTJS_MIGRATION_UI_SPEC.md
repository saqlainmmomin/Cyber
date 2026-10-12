# Next.js migration UI specification

This replaces the provisional design decisions in plan sections 4 and 7. It does not authorize an application build. FastAPI remains the API, deterministic scoring stays server-side, and routes cut over individually. The changes below include presentation, backend and content work. A screen port cannot silently treat all three as a restyle.

## Foundation

Use DESIGN_SYSTEM.md tokens and PAGE_ARCHETYPES.md region contracts. Tailwind v4 @theme maps semantic CSS variables to utilities. Disable default colour/type/spacing values in screen composition. Component variants own token classes; routes compose components and do not set padding, colour or size. Inter uses next/font/local with existing woff2 files. Generate web tokens from design/tokens.json during implementation; this audit does not alter that file.

AppShell supplies 224px sidebar and 24px gutters. Page(mode) produces 1168/1008px at 1440/1280 for inventory/task, and 880px document. Split uses minmax(0,1fr) for its work area. Questionnaire rail 196px; queue 280px; gap 20px. No permanent third pane. Sheet opens source details on demand. Use min-width:0 and overflow-wrap:anywhere for filenames and codes; page scroll must not be horizontal. Table rows grow with text.

## Type roles

All decision-bearing audit text is >=14px, body and recommendations 16/26px, requirement/item titles 16/24px at weight600. Guidance and criteria 14/22px. Prose max width 56ch in each role’s own font size, including bold requirements and 14px guidance. Inter’s zero-glyph ch unit held about 95 average letters at the former 72ch setting. Host line measurement must verify at most 80 characters at 1440 and 1280. Only identifiers, timestamps and optional table metadata may be12/18px. Never put gap text or evidence quotes in a metadata role. Page title24/32px, section20/28px. Follow semantic heading order. Avoid all caps and repeated client titles.

## Navigation

One global sidebar. One breadcrumb. One assessment header with task title, period, cut-off and explicit framework focus. One horizontal assessment StageNav: Overview, Scope, Evidence, Questionnaire, Review, Report. Entering assessment replaces engagement navigation. **Navigation choice pending Saqlain:** Option A uses one labelled Section select in the content toolbar for levels two and three. Option B replaces that select with nested assessment section links under Engagements; review-queue-sidebar.html shows Queue, Conclusions, Findings and Workpaper with aria-current on Queue. Recommend B for visible destinations and one-click frequent switching; A saves sidebar space. Both keep the single stage bar. The five original screens keep A for comparison. Choices are flattened, including Requests: Items, Requests: Versions and Requests: Client links; Review: Queue, Conclusions, Findings, Workpaper; Report: Summary, Domains, Versions, Comparison, Narrative, Board inputs; Scope: Boundaries, Applicability.

StageNav uses Next Link with aria-current=page, not tabs roles. SectionSelect uses shadcn Select and updates canonical route or query state. Domain rail is local item navigation. Canonical URLs: /assessments/[id]/questionnaire?domain=organizational&question=...; /review?finding=...&sort=pending; /review/conclusions?domain=...; /report?view=board&framework=iso27001. Preserve selection and scroll on history. Legacy ?tab= routes and standalone /soa redirect to the corresponding stage/section. Do not redirect file downloads. No href=# dummy navigation.

## Status

StatusBadge accepts family and enum member. Use the label and paired foreground/background in DESIGN_SYSTEM.md. Outcome, risk, review progress and source provenance are distinct fields. Never show a dot instead of words. Version/staleness and source absence have explicit wording. Selected row uses border and aria-current, not colour alone. Icons from lucide-react are redundant and aria-hidden when adjacent to label.

## Review hierarchy

This exact ordered field list is the shared FindingDetail read model for Queue, Conclusions, Findings and Workpaper. The coding agent must not create separate evidence blocks by view.

Outcome and risk share the finding title block. Body order is gap statement, risk and impact, Recommendation, Why this recommendation, Where this finding came from. Recommendation is the strongest block after the gap statement, with at least the size and contrast of surrounding prose.

1. Gap title: new Conclusion.gap_title before approval; existing Finding.title after approval. Control code, control title, domain and framework sit directly below it, from registry enriched controls.
2. Gap statement: Conclusion.gaps_identified / approved GapItem.gap_description. If outcome is Compliant, say no gap identified and show the positive conclusion; do not invent a gap to fill the schema.
3. Compliance outcome: Conclusion.outcome / approved row compliance_status. Review approval is a separate progress field.
4. Risk level and impact: Conclusion.risk_level already exists; new impact_statement before approval, existing Finding.business_impact after approval. No impact supplied means explicitly Not recorded, not Low risk.
5. Recommendation: Conclusion.recommended_action / Finding.recommendation, full body weight. Separate new recommendation_reason explains how it addresses the gap. Compliance rationale is not recommendation reasoning.
6. Provenance narrative: existing evidence_summary as raw input, new reviewed provenance_narrative as presentation text. Revision citations_json supplies evidence version IDs and spans. New interview source records supply who, role, date and notes. Reviewer/uploader names do not prove an interview. Cite each unique source once and preserve direct source/span links. Unresolved/superseded citations remain visible warnings.
7. Supporting detail on demand: control criteria, evidence quote, current_state/rationale, client response, contradictions, missing evidence, analysis completeness, prior revision and method trace. These remain available, not deleted.
8. Mechanics specific to the view: Queue sticky ReviewDecision and blockers; Conclusions final approved version, no candidate decisions; Findings ownership/actions/history; Workpaper read-only method and revision trace. Record version, source basis and accepted/released state remain explicit.

Expose this as a typed DTO with existing source fields and optional new fields. Empty fields have an honest missing state. Do not infer impact, interview, recommendation reason or a reviewed title merely by truncating rationale. Do not name pre-approval Conclusion rows as stored Finding records: the user-facing candidate is a finding while model lifecycle stays intact.

## Review queue

Default stable order is pending first, then evidence missing/contradictory among remaining candidates, then control order and record ID. Toolbar lets auditor switch Pending, Evidence issues, All and sort by risk or control. Selecting any of six candidates updates URL and the single reading pane. Queue is a compact divided list, with no bordered card per item. Gap title takes at most two lines, code/name one line, then outcome and risk in words on one line. Decided rows are quieter than pending rows. Toolbar counts are plain text: 3 pending, 3 decided. Queue row contains gap title, code/name, outcome, risk and decision state in words. Use existing ConclusionCard state and RequirementCard blockers; serializer must expose them.

ReviewDecision is sticky at top of selected detail and includes Approve, Edit, Reject; only Approve is primary. No action requires scrolling all detail. Blocked action shows reason and link to missing support. Edits preserve expected_version; 409 shows current versus unsaved values without discarding text. Rejected or locked content cannot be silently reapproved. j/k may supplement native keyboard links and must ignore text inputs.

## Conclusions

Five columns: Domain, Control ID, Gap/conclusion, Risk, Status. Stable sort domain registry order then control ID; risk/outcome filters are optional and reflected in URL. Table markup remains semantic. Gap wraps, identifiers do not squeeze prose. A row disclosure reveals the full shared hierarchy, no approve/edit/reject controls. Show at least25 populated rows across domains in acceptance fixture. Approved compliant controls remain in inventory and say No gap identified. Release/basis gate belongs to page header, not repeated row mechanics.

## Questionnaire

Use registry master domains for single-framework assessments. ISO: Organizational, People, Physical, Technological, with control counts37/8/14/34. Current router treats non-DPDPA as UCC based; fix grouping in app/routers/questionnaire.py. For multi-framework use canonical UCC domains and membership from cluster_engine/mapping/mappings. Centralize labels/order; cover every in-scope requirement exactly once, including singleton fallback, while preserving mappings to all frameworks. Do not change scoring weights or merge framework scores.

QuestionCard order: requirement, why asked, client prompt hint, answer, notes, source provenance. Control.description/test_criteria and existing question/guidance are inputs, but why_asked and client_prompt_hint need authored fields. Work surface uses width; reading text capped at 56ch. No blank persistent evidence pane. Answered state shows answer/source and approved conclusion separately, with explicit change/reopen policy. Show unanswered and answered states without pretending the source assessment is unfinished.

## Draft contract

Existing HTML save accepts answered section responses but marks questionnaire_done; existing JSON response POST deletes prior answers and marks done. Neither satisfies draft autosave. Add PATCH /api/assessments/{id}/questionnaire/drafts with question_id, changed fields (answer nullable, notes, evidence_reference), expected_version and client_mutation_id. Upsert only the supplied fields, including notes before an answer. Omitted fields stay untouched; explicit null clears a field. Add draft storage/nullable-answer model in app/models/questionnaire.py without weakening final completion validation. app/routers/questionnaire.py delegates persistence to one service; web.py legacy save can reuse that service.

Debounce500ms, flush on blur and before domain navigation, serialize writes per question; retain a retryable local copy if failed. Server returns saved version/time and canonical fields. Reject stale version with 409 and diff; no last-writer-wins data loss. Saved/saving/failed indicator uses aria-live=polite. The explicit POST completion action validates all required active questions and scope, then changes completion state. Draft PATCH never runs follow-ups, analysis, scoring or completion. Analysis remains a separate deliberate action; no implicit AI calls on typing. Client demonstrates autosave through mocked network fixtures before integration tests hit a real test DB.

## RFI

Collapsed inventory rows are one line, at most 48px tall: title, required/optional, state (Not requested, In draft RFI, Issued, Received), evidence mapped (2 of 5), and row action. Header buttons sort each column with one default title sort and aria-sort. In this RFI is a separate top group with no add controls; remaining candidates alone form the add list. References stay in the expanded detail; preserve stable request identity. What to send, example and good looks like are collapsed details, not default wall text. Use current document_request_fields and rfi_examples content. No generated content on page load.

Existing request_key/record_request already make active same-key requests idempotent. Cross-source artifact duplication still needs reconciliation: checklist docs, approved insufficient-evidence requirements and added requests must expose a common artifact identity, included_ids, issued state and mapping list in JSON. In the candidate add form exclude already-included IDs. Included items remain inspectable as read-only requested/issued rows or a separate selection count, without the same add checkbox/form. After successful add update state atomically; on failure retain candidate. Versions and client links are choices in the same Section select, not another navigation strip.

## Scope and SoA

Applicability lives in Scope. scope-applicability.html shows the Scope stage active, two illustrative exclusions with reasons, an Add a control that does not apply picker, and the standard justification once. No questionnaire applicability panel or per-applicable-control reason boxes. Default applicable controls use a standard justification with source=standard; ask only for exclusions and explicit reasons. Existing build_soa derives applicability from approved outcome/scope and stores justifications as AuditEvent metadata. Existing justifications POST does not change applicability. Add exclusion API/state that records control, reason, actor, version and time, reconciles scope and reports, and preserves frozen issued snapshots. Defaults describe scope inclusion, never assert tested compliance. No own SoA stage or report subtab. Keep SoA export/download available.

## Report

Document begins with accepted executive prose: engagement, period, material reviewed, domains, gaps, location/criticality and posture. Source approved_report._summary_text is count-based; do not call that prose. Reuse accepted sentences/freshness from app/services/narrative.py and board_report.build_document; expose context and accepted text through report JSON. If accepted prose missing, show Needs narrative review, never auto-generate on GET. Scores derive from approved_report/scoring, separately per framework.

Board summary targets about three screens at 1440: executive summary, posture line, then a weakest-to-strongest domain table with domain, score and gaps by risk. Every domain then shows only high and medium non-compliant gaps, each with impact, risk, recommendation and logic. Low-risk gaps remain in auditor detail. Primary recommendation content stays visible. The board prototype uses task workspace width and two columns of domain gaps, each capped at 56ch. Dense real findings can exceed the height target; host QA must measure and resolve density without hiding this deliverable. No gaps in a domain means show strength and remaining assurance limits, not manufacture non-compliance. Board summary avoids control-level jargon; Auditor detail adds all control findings and source trace. A top-right two-option toggle labelled Board summary and Auditor detail switches views of the same report; they are not Section select entries. Auditor detail contains all 93 controls with filters. Recommendations follow context and domain assessment as the exported board document does. Do not duplicate full findings in both priorities and detail: priorities link to the detailed row. Use frozen report basis for issued views, accepted narrative only when current for that basis.

## States, forms and accessibility

Field combines Label, Input/Textarea/Select, help and errors; unique IDs, aria-describedby and aria-invalid. Inline failed item error appears below that item's heading/field, with a page summary link if needed. Client upload h1 precedes intro. Keep native input keyboard access or a real accessible button; upload progress/result uses aria-live; CyberAssess brand consistent header/footer. No shell Search until it has real retrieval: use scoped inventory search in the meantime.

Loading: region Skeleton, known content retained while refreshing, aria-busy. Empty: explain scope and one next step. Error: preserve input, show retry where safe, retain409 diff. Locked: read-only reason and allowed next step, not faded unreadable content. Overlay: focus trap, Escape, inert background, return focus. Tooltip may explain a nonessential icon; never hold required evidence or decision instructions. Row disclosure button labelled with control/title and aria-expanded. Sorting button announces ascending/descending via aria-sort on header. Staff layouts at 1280/1440; client upload at 390 with 44px targets. Future smoke checks must include keyboard, contrast, reduced motion, Back/Forward and page overflow, alongside state fixtures.

## P0 rules and verification

| P0 issue | Spec rule | Check |
| --- | --- | --- |
| UI-001 | Width modes | At 1440/1280 content is 1168/1008px; question work pane 952/792 before padding; no horizontal overflow. |
| UI-002 | Type roles | DOM computed font size for question/guidance/gap/quote/criteria/recommendation >=14px. |
| UI-003 | Status / Review queue | All six queue rows expose outcome and risk as visible words, no tooltip-only status. |
| UI-008 | Navigation | Stage links have aria-current; reload and Back preserve Section, framework, selected finding and domain query state. |
| UI-009 | Status | Enum family/member map has one label definition; no severity/progress/provenance value accepted as outcome. |
| UI-011 | Client upload | Keyboard Tab reaches native file input or real Choose file button; Enter/Space opens picker; failure linked by aria-describedby. |
| UI-012 | Foundation | All target text/background pairs >=4.5:1 in both themes and eight accents; no literal white component fill under dark theme. |
| UI-013 | Type roles | Long prose max-inline-size 56ch; host Range measurement target 60 to 80 characters per full line; short text exempt. |
| UI-025 | Navigation | Exactly one horizontal route navigation bar inside assessment main; Option A Section select or Option B nested sidebar links replaces both sublevels, including RFI; choice pending Saqlain. |

## Requirement classification

Every row is exactly one of Presentation, Backend, Content. Split rows represent the separate parts of one requirement. JSON UI serialization is backend work even when existing data already exists; it is covered by Delivery and the explicit serializer rows. Presentation does not imply an endpoint already exists. Content rows say whether writing is static or per assessment. Prototype indicators identify dependencies, not implementation completeness.

| ID | Requirement | Classification | Prototype / reason | Spec section | Work and checked source |
| --- | --- | --- | --- | --- | --- |
| D01 | FastAPI remains JSON API; cut over screen by screen | Backend | No static API execution: spec only | Delivery | Extract typed UI view models from app/routers/web.py; keep Python scoring and exports. |
| D02 | Retire gradient canvas and glass | Presentation | All seven | Foundation | Opaque token surfaces. |
| D03 | Keep eight accents for interaction and branding only | Presentation | All seven, graphite shown; other presets in token table | Foundation | Accent never maps status; palette is documented for all presets. |
| D04 | Four status families | Presentation | All seven | Status | Separate severity, outcome, progress, provenance labels. |
| D05 | Control codes allowed beside titles | Presentation | questionnaire.html, review-queue.html, conclusions.html | Review hierarchy | Show requirement_id beside meaningful title. |
| D06a | Single framework uses its own master domains | Backend | questionnaire.html (target ISO focus) | Questionnaire | Use registry Domain keys in app/frameworks/definitions/iso27001.py; expose ordered domain tree via app/routers/questionnaire.py. |
| D06b | Multi-framework covers each requirement once in unified domains | Backend | Not shown: ISO focus prototype; multi-framework is specified | Questionnaire | Centralize existing UnifiedControlCluster.domain_group and DOMAIN_GROUP_ORDER as master domain registry; app/frameworks/mapping.py, cluster_engine.py, mappings/clusters.py, questionnaire_builder.py. Validate each in-scope framework requirement covered exactly once. |
| D07a | Drafts save automatically while typing | Backend | questionnaire.html (static saved state) | Draft contract | Add partial draft PATCH and independent completion; app/models/questionnaire.py QuestionnaireResponse and app/routers/questionnaire.py. |
| D07b | Draft saving feedback and explicit completion act | Presentation | questionnaire.html | Draft contract | Saved, saving, failed and offline feedback; completion button separate. |
| D08 | Pending first, then missing or contradictory evidence; sort and switch anytime | Presentation | review-queue.html | Review queue | Sort existing card state, blockers and evidence conflicts; selectable ordering without changing record. |
| D09 | Laptop 1440 with 1280 support | Presentation | All seven | Foundation | Sidebar 224; gutters 24; minmax(0,1fr) workspace. |
| D10 | Never stack secondary or tertiary navigation bars | Presentation | All seven; review-queue-sidebar.html compares option B | Navigation | Option A flattened Section select; Option B nested assessment links under Engagements. Recommend B; choice pending Saqlain. |
| D11 | Inter stays | Presentation | All seven | Foundation | Vendored relative fonts and local Next font. |
| Q01 | Question area uses available width, no blank side | Presentation | questionnaire.html | Questionnaire | Full-width question surface, 196px domain rail; no persistent context pane. |
| Q02 | Control requirement is primary | Presentation | questionnaire.html | Questionnaire | h2 requirement, followed by contextual prose and hint. |
| Q03 | Explain why asked | Content | questionnaire.html | Content track | Authored once per control in app/frameworks/schema.py QuestionDef; current guidance is not a separate why field. |
| Q04 | Hint on how to put question to client | Content | questionnaire.html | Content track | Authored once per control; separate how-to-ask text slot. |
| Q05 | Persist distinct why and how fields | Backend | questionnaire.html | Questionnaire | Extend QuestionDef and questionnaire serializers; no inference from generic guidance. |
| Q06 | Rework help hierarchy at readable size and measure | Presentation | questionnaire.html | Questionnaire | 14px guidance minimum, 56ch cap, visible labels. |
| Q07 | Show unanswered and answered after assessment | Presentation | questionnaire.html | Questionnaire | Unanswered input plus settled answer and linked conclusion; prototype resets one existing question locally for state demonstration. |
| Q08 | ISO uses four Annex A themes, not privacy headings | Presentation | questionnaire.html | Questionnaire | Organizational, People, Physical, Technological from registry; backend dependency D06a. |
| R01 | Each queue item is a finding before approval | Presentation | review-queue.html | Review hierarchy | Use finding terminology for candidate conclusions; preserve model distinction. |
| R02a | Gap title distinct from control name | Backend | review-queue.html, conclusions.html | Review hierarchy | Add gap_title to Conclusion; propagate to Finding.title in app/services/findings.py. |
| R02b | Write short gap titles | Content | review-queue.html, conclusions.html | Content track | Generated per assessment from grounded gap; reviewed by auditor; compliant title describes positive conclusion. |
| R03 | Gap statement then compliance status | Presentation | review-queue.html, conclusions.html | Review hierarchy | Use gaps_identified then outcome; current_state supplies context. |
| R04a | Risk or impact of non-compliance | Backend | review-queue.html, report.html | Review hierarchy | Add impact_statement to Conclusion; propagate existing Finding.business_impact; risk_level already exists. |
| R04b | Write impact statements | Content | review-queue.html, report.html | Content track | Generated per assessment with no unsupported incident or loss claims. |
| R05 | Recommendation at full weight | Presentation | review-queue.html, report.html | Review hierarchy | Same 16px body role as gap, no tiny inset. |
| R06a | Recommendation reasoning has its own slot | Backend | review-queue.html, report.html | Review hierarchy | Add recommendation_reason to Conclusion and typed reporting view model; existing recommended_action stays. |
| R06b | Write recommendation logic | Content | review-queue.html, report.html | Content track | Generated per assessment, connection from gap to remedy. |
| R07a | What reviewed and who spoken to as provenance | Backend | review-queue.html | Review hierarchy | Store interview records with date, role, consented name, notes, evidence IDs; new interview model/service/router, linked to conclusion. |
| R07b | Concise provenance narrative | Content | review-queue.html, conclusions.html | Content track | Generated per assessment from revision citations and stored interviews. Never invent interviews. |
| R08 | One provenance block; cited file one click away | Presentation | review-queue.html, conclusions.html | Review hierarchy | Deduplicate by evidence version and span; anchors retain exact citation URL. |
| R09 | Queue outcome and risk in words | Presentation | review-queue.html | Review queue | No dot-only queue state. |
| R10 | Approve edit reject attached and visible | Presentation | review-queue.html | Review queue | Sticky decision header on reading pane, no footer-only action. |
| R11 | One Review hierarchy across queue conclusions findings workpaper | Presentation | review-queue.html, conclusions.html | Review hierarchy | Shared FindingDetail field order with domain-specific mechanics. |
| C01 | Conclusions are final gaps without queue mechanics | Presentation | conclusions.html | Conclusions | No approve/edit/reject per row; settled revision only. |
| C02 | Deterministic table domain control ID gap risk status | Presentation | conclusions.html | Conclusions | Five fixed columns, stable domain/control sort; no masonry cards. |
| C03 | Row expands to full finding | Presentation | conclusions.html | Conclusions | Native button/details disclosure with all hierarchy fields. |
| F01 | RFI tight sortable list | Presentation | rfi.html | RFI | 40 real source requests; at least 20 visible compact rows. |
| F02a | Already added item absent from same add form | Backend | rfi.html | RFI | Existing request_key and record_request already idempotent. Add cross-source artifact identity and state serializer in app/routers/web.py rfi_page with app/services/rfi_evidence_requests.py rfi_items and app/services/rfi_requests.py; do not reimplement same-key dedup. |
| F02b | Separate included items from candidates | Presentation | rfi.html | RFI | Included state read-only in list; add form only remaining candidates. |
| F03 | What to send example good looks like on demand | Presentation | rfi.html | RFI | details disclosure, all three source content fields retained. |
| P01 | Written executive context first | Content | report.html | Content track | Generated per assessment from released snapshot; source summary is currently a string of counts. |
| P02 | Summary names engagement reviewed material and scope domains | Content | report.html | Report | Generated per assessment from approved basis and engagement period. |
| P03 | Summary identifies gaps location criticality and overall posture | Content | report.html | Report | Generated per assessment; ratings/metrics from deterministic scoring only. |
| P04 | Gaps by domain, weakest and strongest | Presentation | report.html | Report | All ISO domains with scores; ascending score ranking, tie by registry order. |
| P05 | Each domain gap has non-compliance impact risk for board | Content | report.html | Content track | Generated per assessment; replace raw control wording with audience-specific text, impact backing R04a. |
| P06 | Board summary and auditor/technical detail | Presentation | report.html | Report | Top-right Board summary / Auditor detail toggle preserves released basis; Section select remains separate. |
| P07 | Recommendations and logic follow exported report flow | Presentation | report.html | Report | Context, domains, priorities, recommendations, detail; reuse typed source fields, not regenerate on view. |
| S01a | Ask only non-applicable controls and reasons | Presentation | scope-applicability.html | Scope and SoA | Search exclusion controls; reason field shown only for exclusion. |
| S01b | Everything else applicable with standard justification | Backend | scope-applicability.html | Scope and SoA | app/services/soa.py default source and source marker; preserve frozen issued justification during cutover. |
| S01c | Author standard applicability justification | Content | scope-applicability.html | Content track | Authored once per framework/control, no generated claim of observed effectiveness. |
| S02 | SoA lives under Scope, no own tab | Presentation | scope-applicability.html | Navigation | Scope Section select option Applicability, legacy SoA route redirect. |
| T01 | Content quality is separate, reader-specific track | Content | Not solved by static prototype: examples expose slots only | Content track | Separate writing and prompt work for controls, UCC, RFIs, board reports and auditor workpapers. |
| T02 | Useful consultant AI output and good reports with less effort | Content | Not measured: needs consultant task testing | Content track | Audience-specific acceptance criteria, grounded claims, approved text reuse; do not claim productivity from screenshots. |
| D06c | Unified taxonomy and requirement wording | Content | Not shown: requires content track beyond ISO focus | Content track | Authored once for UCC domain names and cluster prompts; use existing DOMAIN_GROUP_ORDER as starting inventory, not accepted final taxonomy. |
| R07c | Persist independent provenance narrative | Backend | review-queue.html, conclusions.html | Review hierarchy | Store provenance_narrative with conclusion revision and linked method sources; app/models/conclusion.py and app/services/conclusion_review.py. |
| R12 | Expose queue state and evidence conflicts to JSON | Backend | review-queue.html | Delivery | Serialize ConclusionCard and RequirementCard in app/routers/conclusions.py; retain allowed_actions and blocker computation. |
| P08 | Expose accepted narrative and board read model | Backend | report.html | Report | Reuse app/services/narrative.py accepted AuditEvents and app/services/board_report.py build_document; JSON read view must preserve freshness and acceptance gate. |

## Per-screen replacement for plan section7

These31 live page families replace the plan's Tpl/Work columns. Assessment variants and external client states follow. All screens retain current functional gates; no port deletes signed checklists, conflict handling, release blockers or source trace.

| Family / template key | Archetype | Regions | What changes | Classification |
| --- | --- | --- | --- | --- |
| Home (`dashboard`) | Inventory | Attention list, active assessments | Replace generic dashboard cards with sorted next tasks | Presentation |
| Clients (`clients`) | Inventory | Filter, client table, row action | One stable table and create action | Presentation |
| Client (`client_detail`) | Entity | Identity, engagement inventory | Avoid repeating client name; evidence links scoped | Presentation |
| Engagements (`engagements`) | Inventory | Search, stage filter, engagement table | Visible stage and next task | Presentation |
| Portfolio review (`review`) | Queue | Engagement filter, pending decisions list | Persistent outcome and risk labels | Presentation, Backend |
| Issued reports (`reports`) | Inventory | Period filter, issued snapshot table | Show immutable issuance and evidence cut-off | Presentation |
| New engagement (`new_engagement`) | Form | Client, period, validation, submit | Shared Field errors and date labels | Presentation |
| Engagement overview (`engagement_detail`) | Entity | Period, scope, assessments, next task | No assessment stage bar alongside engagement navigation | Presentation |
| New assessment (`new_assessment`) | Form | Framework choices, scope, submit | Conditional framework copy, no aggregate score | Presentation |
| Findings and actions (`remediation_tracker`) | Inventory | Owner/risk/state filter, action table, detail | Reuse FindingDetail and state contract | Presentation, Backend |
| Integrated reports (`integrated_reports`) | Document | Context, separate frameworks, release basis | Keep separate scores, audience sections | Presentation, Backend, Content |
| Client requests (`requests`) | Inventory | Links, expiry, evidence counts, request action | Compact client-link list; remove repeated prose | Presentation |
| AWS evidence (`aws_evidence`) | Form | Connection configuration, policy, run state | CodeBlock and explicit ready/running/error states | Presentation |
| Purge (`engagement_purge`) | Form | Retention, eligibility, destructive confirmation | Typed confirm with affected records count | Presentation |
| Settings (`firm_settings`) | Form | Branding, accent choices, field errors | Neutral surfaces, validated accent pairs | Presentation |
| Evidence inventory (all three scopes) (`evidence_inventory`) | Inventory | Scope, search, status filters, version rows | Wide table, readable audit fields | Presentation, Backend |
| Evidence record and cited span (`evidence_detail`) | Document | Version header, source text, citation location | 56ch text; superseded source labelled | Presentation |
| Evidence reuse (`evidence_reuse`) | Inventory | Prior assessment filter, candidate rows, inclusion | Selection state and preview, no repeated full content | Presentation |
| Desk review (`desk_review`) | Task | Run state, prefill list, provenance inspector | Compact findings, stable async status | Presentation, Backend |
| Assessment workspace (`assessment`) | Task | Breadcrumb, period, stage tabs, selected content | Shared frame and variants below; use task title | Presentation, Backend, Content |
| Review queue (`review_queue`) | Queue | Section select, sort, six candidates, selected FindingDetail | Sticky decisions; gap titles and consolidated provenance | Presentation, Backend, Content |
| Conclusions (`conclusions`) | Inventory | Section select, stable five-column table, expanded finding | No per-row review mechanics; final settled revision | Presentation, Backend, Content |
| Findings (`findings`) | Inventory | Owner/action filters, gap rows, FindingDetail | Existing editable title/impact retained; same hierarchy | Presentation, Backend |
| Workpaper (`workpaper`) | Document | Method, controls, findings, source/history trace | Auditor detail, same field sequence, history disclosed | Presentation, Backend, Content |
| Report versions (`report_snapshots`) | Inventory | Version type selector, issued/draft rows, download | No framework or version tab stack; immutable basis | Presentation |
| Comparison (`comparison`) | Inventory | Two snapshot selectors, domain deltas, expandable changes | Read live comparison, isolate frameworks | Presentation |
| Narrative (`narrative`) | Document | Section select, accepted sentences, citations, freshness | Audience-specific slots, acceptance gate retained | Presentation, Backend, Content |
| Board inputs (`board_inputs`) | Form | Top risks, business impact, priorities, freshness | Structured inputs without shrinking primary deliverable | Presentation, Backend, Content |
| Applicability within Scope (`soa`) | Form | Default rule, exclusion search, exception reasons | Retire standalone tab and 93 justification fields | Presentation, Backend, Content |
| RFI items / versions / links (`rfi`) | Inventory | One Section select, sort, compact requests, disclosure | Flatten navigation, exclude included artifacts from add form | Presentation, Backend |
| Error pages (`error`) | Recovery | Problem, context, safe retry/navigation | Task-specific next step and preserved input | Presentation |

| Variant | Archetype | Regions | What changes | Classification |
| --- | --- | --- | --- | --- |
| Overview | Entity | Next task, stage progress, framework scores separately | Show one next action and separate scores | Presentation |
| Scope | Form | Boundaries, period, framework scope, exception-only SoA | Standard applicability; explicit exclusion reasons | Presentation, Backend, Content |
| Questionnaire | Task | Framework domain rail, requirement, why, hint, response, source | Use full width, partial drafts, separate completion | Presentation, Backend, Content |
| Report / report-summary | Document | Executive summary, all domains, recommendations, detailed findings | Accepted prose first, board/detail switch | Presentation, Backend, Content |
| Evidence scopes: global / engagement / assessment | Inventory | Scope filter, search, source versions, excluded status | One component with scoped reads and breadcrumbs | Presentation, Backend |
| RFI: items / versions / client links | Inventory | Flattened Section selector, request rows or versions/links | No candidate repeated after inclusion; on-demand guidance | Presentation, Backend |
| Client upload / invalid / expired | Form / Recovery | Mobile heading, inline item error, native file control, progress | 44px targets, keyboard file choice, consistent CyberAssess brand | Presentation |

The existing screen-manifest live rows map to these families: home=dashboard; client=client_detail; engagement=engagement_detail; portfolio-review=review; remediation=remediation_tracker; evidence-global/engagement/assessment=evidence_inventory; report/report-summary/report-iso=assessment Report variant; scope/questionnaire=assessment variants; snapshots=report_snapshots; comparison=comparison; soa=Scope Applicability. Supplementary early NIST, expanded/edit/cited and run/error fixtures inherit the same archetype with the indicated state. Comparison fixture404 is not evidence that live comparison is missing.

## Component rulings

The definitive inventory is COMPONENT_INVENTORY.md. Thin typed wrappers are allowed; separate styling and maps are not. shadcn primitives are restyled using token cva variants. There is no universal Card around every region.

### Plan4.2 layout and type

| Plan component | Ruling | Target | Reason |
| --- | --- | --- | --- |
| AppShell | Agree | AppShell | Token variants and state contract apply. |
| Sidebar | Agree | Sidebar | Token variants and state contract apply. |
| TopBar | Change | PageHeader + Breadcrumb | No additional horizontal navigation. |
| Page | Agree | Page | Token variants and state contract apply. |
| PageHeader | Agree | PageHeader | Token variants and state contract apply. |
| Section | Agree | Section | Token variants and state contract apply. |
| Card | Drop | Section | Bounded surface only when a distinct work region needs it. |
| Stack | Agree | Stack | Token variants and state contract apply. |
| Cluster | Agree | Cluster | Token variants and state contract apply. |
| Grid | Agree | Grid | Token variants and state contract apply. |
| Split | Agree | Split | Token variants and state contract apply. |
| Heading | Agree | Heading | Token variants and state contract apply. |
| Text | Agree | Text | Token variants and state contract apply. |
| Prose | Agree | Prose | Token variants and state contract apply. |
| DataTable | Agree | DataTable | Token variants and state contract apply. |
| KeyValue | Agree | KeyValue | Token variants and state contract apply. |
| Toolbar | Agree | Toolbar | Token variants and state contract apply. |

### Plan4.4 base components

| Plan component | Ruling | Target | Reason |
| --- | --- | --- | --- |
| Button | Agree | Button | Token variants and state contract apply. |
| Input | Agree | Field | Token variants and state contract apply. |
| Textarea | Agree | Field | Token variants and state contract apply. |
| Select | Agree | Field / SectionSelect | Token variants and state contract apply. |
| Label | Agree | Field | Token variants and state contract apply. |
| Form | Change | Field | Field-level validation and draft state; no global submit-only wrapper. |
| Checkbox | Agree | Choice | Token variants and state contract apply. |
| RadioGroup | Agree | Choice | Token variants and state contract apply. |
| Switch | Agree | Choice | Token variants and state contract apply. |
| Badge | Agree | StatusBadge | Token variants and state contract apply. |
| Card | Drop | Section | Bounded surface only when a distinct work region needs it. |
| Table | Agree | DataTable | Token variants and state contract apply. |
| Link tab bar | Change | StageNav | Links and aria-current, not ARIA panel tabs. |
| ToggleGroup or link group | Drop | SectionSelect | Never a secondary navigation strip. |
| Dialog | Agree | Dialog | Token variants and state contract apply. |
| AlertDialog | Agree | Dialog destructive | Token variants and state contract apply. |
| Sheet | Agree | Inspector | Token variants and state contract apply. |
| Sonner | Agree | Feedback toast | Token variants and state contract apply. |
| Alert | Agree | Feedback inline | Token variants and state contract apply. |
| Skeleton | Agree | Feedback loading | Token variants and state contract apply. |
| Tooltip | Agree | Menu optional hint | Token variants and state contract apply. |
| DropdownMenu | Agree | Menu | Token variants and state contract apply. |
| Popover | Agree | Menu | Token variants and state contract apply. |
| Breadcrumb | Agree | Breadcrumb | Token variants and state contract apply. |
| Pagination | Agree | Pagination | Token variants and state contract apply. |
| Progress | Agree | Progress | Token variants and state contract apply. |
| Collapsible | Agree | Disclosure | Token variants and state contract apply. |
| Accordion | Agree | Disclosure | Token variants and state contract apply. |
| lucide-react | Agree | Icons inside primitives | Token variants and state contract apply. |

### Plan4.5 domain components

| Plan component | Ruling | Target | Reason |
| --- | --- | --- | --- |
| StatusIndicator | Change | StatusBadge | Typed families, always words. |
| OutcomeBadge | Change | StatusBadge outcome | Thin typed wrapper, no separate colour mapping. |
| SeverityBadge | Change | StatusBadge severity | Thin typed wrapper, no separate colour mapping. |
| EvidenceStatusBadge | Change | StatusBadge provenance/progress | Evidence lifecycle never outcome compliance. |
| ScoreRing | Drop | Text score | Neutral numeric score and distribution; no decoration needed. |
| Distribution | Change | DomainSummary | Labelled counts and outcomes; no colour-only chart. |
| Stepper | Change | Progress | Overview-only next-task/progress summary; no second nav. |
| CitationBlock | Agree | CitationBlock | Token variants and state contract apply. |
| EvidenceViewer | Agree | EvidenceViewer | Token variants and state contract apply. |
| ConclusionCard | Change | FindingDetail + ReviewDecision | Gap-first data hierarchy; one provenance region. |
| RequirementBody | Change | FindingDetail + Inspector | Criteria and history disclosed, not an open parallel evidence block. |
| FindingCard | Change | DataTable + FindingDetail | Gap rows and existing action state machine. |
| WorkpaperEntry | Change | FindingDetail workpaper variant | Same field order, audit trace appended. |
| RequestCard | Change | RequestRow | Compact list with disclosure. |
| QuestionCard | Agree | QuestionCard | Token variants and state contract apply. |
| UploadDropzone | Agree | UploadDropzone | Token variants and state contract apply. |
| RunStatus | Agree | RunStatus | Token variants and state contract apply. |
| CodeBlock | Agree | CodeBlock | Token variants and state contract apply. |

## Delivery

Extract page view models from app/routers/web.py into typed service read models before introducing /api/ui endpoints. Retain current Python models/services for scoring, reports, RFIs and review gates. Serialize ConclusionCard/RequirementCard, board document and RFI state rather than scrape rendered HTML in production. Pydantic response models drive generated TypeScript API types; errors expose detail, field_errors, blockers and conflict. Every screen PR names the archetype and its presentation/backend/content requirements. JSON mutation variants retain expected_version and action-history guards. Remove hx-boost only in migration integration, not in this docs run.

Build foundations, then questionnaire, review queue, conclusions, RFI and report in that order. Existing client magic-link and export HTML may stay in FastAPI/Jinja, but UI-011 and mobile errors still require fixes there. Confirm a screen through a quick smoke check before cutover, with runtime at 1440/1280, light/dark and its error/locked/conflict state; client upload390. Never run analysis just to obtain test data. State fixtures and accepted snapshots are sufficient. Keep old paths until redirects and JSON parity are verified.

## Content track

A separate plan must cover control wording, static why/how hints, canonical UCC taxonomy, concise grounded gap titles, impact wording, recommendation reasoning, RFI client instructions, provenance methods and interview narratives, report executive prose, standard SoA justification and auditor workpaper style. Static content is versioned per control/framework; assessment prose is generated/authored from cited evidence, reviewed, accepted and tied to a snapshot. UI provides named slots with honest missing states. It does not claim the redesign fixes writing quality or consultant productivity. No content plan or prompts are written in this audit.
