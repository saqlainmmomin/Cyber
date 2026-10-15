# Page archetypes

An archetype specifies regions and states, not a template copied from today's markup. The 31 count refers to live page families, including error; login is a design-only fixture. The assessment template contains Overview, Scope, Questionnaire and Report; evidence has three scopes and RFI has three views. Every route variant in SCREEN_INVENTORY.md remains covered below and in the migration spec.

## Archetypes

| Archetype | Purpose | Regions | Width mode | States | Page families |
| --- | --- | --- | --- | --- | --- |
| Inventory | Scan many records and choose one | PageHeader, Toolbar, DataTable/list, optional row disclosure | Inventory | loading, empty, filtered-empty, populated, error, locked | Home, Clients, Engagements, Issued reports, Findings and actions, Client requests, Evidence inventory (all three scopes), Evidence reuse, Conclusions, Findings, Report versions, Comparison, RFI items / versions / links |
| Queue | Make a decision on a selected candidate | Toolbar, QueueList, FindingDetail, sticky ReviewDecision | Task workspace | pending, decided, no pending, blocker, edit, conflict, locked | Portfolio review, Review queue |
| Task | Complete control work without losing context | Header, domain/item rail, work surface, optional Sheet inspector | Task workspace | unanswered, draft, saving, saved, failed, complete, running, blocked | Desk review, Assessment workspace |
| Form | Configure or record explicit exceptions | Header, labelled Field groups, validation, action | Task workspace; field groups <=56ch | pristine, dirty, invalid, saving, saved, conflict, disabled | New engagement, New assessment, AWS evidence, Purge, Settings, Board inputs, Applicability within Scope |
| Document | Read a report or source with stable provenance | Context header, document sections, domain navigation/select, citations | Document | board, auditor detail, draft, accepted, issued, stale, unavailable | Integrated reports, Evidence record and cited span, Workpaper, Narrative |
| Entity | Understand an entity and enter its work | Identity/period, next task, related inventory | Inventory | empty, active, closed, error | Client, Engagement overview |
| Recovery | Recover a missing page or failed task | Problem, preserved context, next step | Document | 404, 500, expired, unavailable | Error pages |

All regions inherit loading, empty, error and keyboard focus states. Empty filtered lists offer Clear filters; an empty source inventory offers upload. Async regions do not clear known results while refreshing. Queue selection does not navigate away from the task. Wide tables use wrapped cells, not tiny text. A right inspector is on demand only.

## All 31 page families

| Family | Archetype | Primary regions | Target changes |
| --- | --- | --- | --- |
| Home | Inventory | Attention list, active assessments | Replace generic dashboard cards with sorted next tasks |
| Clients | Inventory | Filter, client table, row action | One stable table and create action |
| Client | Entity | Identity, engagement inventory | Avoid repeating client name; evidence links scoped |
| Engagements | Inventory | Search, stage filter, engagement table | Visible stage and next task |
| Portfolio review | Queue | Engagement filter, pending decisions list | Persistent outcome and risk labels |
| Issued reports | Inventory | Period filter, issued snapshot table | Show immutable issuance and evidence cut-off |
| New engagement | Form | Client, period, validation, submit | Shared Field errors and date labels |
| Engagement overview | Entity | Period, scope, assessments, next task | No assessment stage bar alongside engagement navigation |
| New assessment | Form | Framework choices, scope, submit | Conditional framework copy, no aggregate score |
| Findings and actions | Inventory | Owner/risk/state filter, action table, detail | Reuse FindingDetail and state contract |
| Integrated reports | Document | Context, separate frameworks, release basis | Keep separate scores, audience sections |
| Client requests | Inventory | Links, expiry, evidence counts, request action | Compact client-link list; remove repeated prose |
| AWS evidence | Form | Connection configuration, policy, run state | CodeBlock and explicit ready/running/error states |
| Purge | Form | Retention, eligibility, destructive confirmation | Typed confirm with affected records count |
| Settings | Form | Branding, accent choices, field errors | Neutral surfaces, validated accent pairs |
| Evidence inventory (all three scopes) | Inventory | Scope, search, status filters, version rows | Wide table, readable audit fields |
| Evidence record and cited span | Document | Version header, source text, citation location | 56ch text; superseded source labelled |
| Evidence reuse | Inventory | Prior assessment filter, candidate rows, inclusion | Selection state and preview, no repeated full content |
| Desk review | Task | Run state, prefill list, provenance inspector | Compact findings, stable async status |
| Assessment workspace | Task | Breadcrumb, period, stage tabs, selected content | Shared frame and variants below; use task title |
| Review queue | Queue | Section select, sort, six candidates, selected FindingDetail | Sticky decisions; gap titles and consolidated provenance |
| Conclusions | Inventory | Section select, stable five-column table, expanded finding | No per-row review mechanics; final settled revision |
| Findings | Inventory | Owner/action filters, gap rows, FindingDetail | Existing editable title/impact retained; same hierarchy |
| Workpaper | Document | Method, controls, findings, source/history trace | Auditor detail, same field sequence, history disclosed |
| Report versions | Inventory | Version type selector, issued/draft rows, download | No framework or version tab stack; immutable basis |
| Comparison | Inventory | Two snapshot selectors, domain deltas, expandable changes | Read live comparison, isolate frameworks |
| Narrative | Document | Section select, accepted sentences, citations, freshness | Audience-specific slots, acceptance gate retained |
| Board inputs | Form | Top risks, business impact, priorities, freshness | Structured inputs without shrinking primary deliverable |
| Applicability within Scope | Form | Default rule, exclusion search, exception reasons | Retire standalone tab and 93 justification fields |
| RFI items / versions / links | Inventory | One Section select, sort, compact requests, disclosure | Flatten navigation, exclude included artifacts from add form |
| Error pages | Recovery | Problem, context, safe retry/navigation | Task-specific next step and preserved input |

Assessment variants: Overview uses Entity inside the assessment frame; Scope uses Form with an Applicability exception panel; Questionnaire uses Task with a framework-domain rail; Report uses Document with board/detail choices. Report-summary is the same report content without a second presentation system. Evidence global/engagement/assessment use one Inventory with distinct scope. Client upload and invalid/expired magic links use a mobile Form/Recovery without staff shell, outside the 31 staff template count. Existing FastAPI client routes may retain Jinja while adopting the same token and accessibility contract.

## T1 to T7 ruling

| Plan template | Ruling | Replacement | Reason |
| --- | --- | --- | --- |
| T1 List | Agree | Inventory | Tables and compact lists share filter and row semantics. |
| T2 Detail | Change | Entity / Inventory / Form | Client and engagement use Entity; versions/comparison use Inventory; AWS/purge use Form, not generic cards. |
| T3 Workspace | Change | Task plus shared assessment frame | One stage bar; no overview stepper duplicated on every stage. |
| T4 Two-pane review | Change | Queue; Conclusions uses Inventory | Only queue needs permanent selection pane. Conclusions is a deterministic assessment sheet. |
| T5 Form | Change | Form | SoA becomes Scope exception panel. Settings and board inputs remain forms. |
| T6 Wizard / run | Change | Task and Form | Questionnaire is a workspace, not a forced sequential wizard. RunStatus is a region. |
| T7 Document | Agree | Document | Add board/auditor report variants; source viewer and workpaper keep document measure. |

No generic Card wrapper is an archetype. A surface is justified only by a distinct decision region. RFI, conclusions, evidence and versions should scan as rows. Questionnaire and queue get work surfaces. Narrative and reports get readable documents.
