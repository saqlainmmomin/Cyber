# Component inventory

This is the minimum shared set for the named workflows. Domain components compose the restyled shadcn primitives; they do not each introduce a new spacing or colour system. There are 40 contracts, including small layout/type primitives, not40 independent screen designs. Thin family-specific badge helpers have no separate style map.

| Component | Base / kind | Purpose | Variants | States | Where used |
| --- | --- | --- | --- | --- | --- |
| AppShell | Domain | Staff frame, sidebar, breadcrumb and identity | staff / client frame | loading, selected route, collapsed | Every staff page |
| Sidebar | Domain | Global routes and working identity | expanded / drawer | active, focus, unavailable | AppShell |
| Page | Domain | Width/gutter contract | inventory / task / document | normal, stacked | All pages |
| PageHeader | Domain | Task title and contextual metadata | entity / assessment / document | draft, released, stale | All pages |
| AssessmentHeader | Domain | Assessment period and framework context | single / multi framework focus | active, released | Assessment frame |
| StageNav | Domain | Only horizontal stage navigation | engagement / assessment, never both | aria-current, keyboard focus | Assessment frame |
| SectionSelect | shadcn Select | Flattened sub-sections, route state | review / evidence / report / scope | selected, disabled, focus | Assessment views |
| Section | Domain | Semantic section rhythm | plain / bounded surface | normal, loading | All pages |
| Stack | Domain | Vertical gaps | token gap variants | normal | Composed regions |
| Cluster | Domain | Wrapping inline groups | start / between | wrapped | Headers and toolbars |
| Grid | Domain | Responsive grid regions | one / two column | stacked | Forms and entity detail |
| Split | Domain | One rail and work region | questionnaire / queue | stacked, selected | Task and Queue |
| Heading | Domain | Semantic heading role | page / section / item | normal | All pages |
| Text | Domain | Content versus restricted metadata | body / guidance / table / metadata | normal, emphasis | All pages |
| Prose | Domain | 72ch readable paragraphs | body / quote / criteria | normal | Documents and detail |
| Toolbar | Domain | Sort search filters and section selector | inventory / queue | filtered, refreshing | Lists and queue |
| DataTable | shadcn Table | Stable columns and row disclosure | inventory / conclusions / comparison | loading, empty, sorted, expanded | Inventory |
| KeyValue | Domain | Compact labelled metadata | inline / stacked | missing | Entity and source headers |
| Button | shadcn Button | Explicit action | default / secondary / ghost / destructive / small | focus, disabled, loading | All actions |
| Field | shadcn Label Input Textarea Select | Accessible labelled input | text / textarea / select / date / file | invalid, dirty, saving, disabled | Forms and Questionnaire |
| Choice | shadcn Checkbox RadioGroup Switch | Answer and selection | single / multiple / boolean | checked, focus, disabled | Questionnaire and Scope |
| StatusBadge | shadcn Badge | Typed family and member | severity / outcome / progress / provenance | normal, explanatory text | Lists and detail |
| Dialog | shadcn Dialog AlertDialog | Confirm or resolve conflict | normal / destructive / conflict | open, invalid, submitting | Purge and edits |
| Inspector | shadcn Sheet | On-demand source detail | source / criteria | open, loading, unavailable | Questionnaire, finding detail |
| Feedback | shadcn Alert Skeleton Sonner | Errors, task loading and notifications | inline / global / toast | empty, loading, error, saved | All pages |
| Menu | shadcn DropdownMenu Popover Tooltip | Secondary actions and optional hints | menu / popover / tooltip | open, focus | Rows and headers |
| Breadcrumb | shadcn Breadcrumb | Single context trail | staff / assessment | current | AppShell |
| Pagination | shadcn Pagination | Large inventories | pages / load more | first, last, loading | Evidence and conclusions |
| Progress | shadcn Progress | Task completion count | determinate / indeterminate | ready, running, complete | Overview and RunStatus |
| Disclosure | shadcn Collapsible Accordion | Details on demand | row / section | open, closed | RFI and finding details |
| FindingDetail | Domain | One Review field hierarchy | candidate / final / action / workpaper | missing source, locked, conflict | Queue, conclusions, findings, workpaper |
| ReviewDecision | Domain | Attached decision actions and blocker | view / edit / conflict | allowed, blocked, submitting, stale | Queue only |
| QuestionCard | Domain | Requirement why hint and response | unanswered / draft / answered | saving, failed, complete | Questionnaire |
| RequestRow | Domain | Tight artifact summary with included state | candidate / included / issued | expanded, received, missing | RFI and request inventory |
| EvidenceViewer | Domain | Versioned document and cited span | text / workbook / binary download | current, superseded, unresolved | Source document and Inspector |
| CitationBlock | Domain | Narrative sources with direct file links | document / interview | verified, unresolved, superseded | FindingDetail and report detail |
| RunStatus | Domain | Async operation feedback | desk review / analysis | ready, running, done, failed, blocked | Task workspaces |
| UploadDropzone | Domain | Accessible file choice and progress | staff / mobile client | ready, uploading, failed, done | Evidence and client upload |
| CodeBlock | Domain | Policy/source code and copy | plain / copy | copied, error | AWS configuration |
| DomainSummary | Domain | Report domain context and gaps | board / auditor | strongest, weakest, no gaps | Report |

Use cva variants for Button and typed StatusBadge. Field wraps input semantics once. Table supplies HTML semantics; DataTable adds search/sort/disclosure behavior only as needed. RequestRow is not a Card. FindingDetail is one read model and field order with small mechanics slots. ReviewDecision never appears on final Conclusions rows. SectionSelect replaces all nested segmented/link navigation groups.

No generic Card, decorative ScoreRing or secondary ToggleGroup navigation. Progress is overview/run feedback, never another stage bar. DomainSummary uses text and counts that survive greyscale. Tooltip is optional help only. Empty and Error views are Feedback variants, not separate page-specific components.

Acceptance gallery must exercise light/dark and all listed states using real fixtures: unanswered question with notes, autosave failure, stale409, locked conclusion, unsupported citation, already-issued RFI, empty filter, all four domains and client picker keyboard access. Runtime screenshots are host work after this docs-only run. Component-level visual assertions do not replace JSON mutation or domain invariant tests.
