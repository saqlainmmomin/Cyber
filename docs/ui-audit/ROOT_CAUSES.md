# Systemic root causes and Yozora ruling

Source causes are now reconciled against host captures and rendered measurements. Questionnaire pane width, 12px guidance, long report prose, repeated evidence and three-level RFI navigation are visible findings. Interaction limits are called out in UI_ISSUES.md. Saqlain's decisions are fixed inputs; DESIGN_SYSTEM.md supplies the target rules, superseding first-run proposals.

## Classification

Each row has exactly one classification. Stack means a causal limitation of the Jinja/HTMX state model; Design decision means an existing token or principle; Shortcut means the current system permitted a better implementation; Never designed means a missing specification. Counts describe causes, not issue prevalence or percentage of screens.

| Class | Causes |
|---|---:|
| Stack | 1 |
| Design decision | 3 |
| Shortcut | 7 |
| Never designed | 5 |
| Total | 16 |

Fifteen of sixteen causes require design or implementation discipline independent of framework choice; React components alone cannot resolve them.

## Cause register

| ID | Problem and evidence | Classification | Affected screens | Source or selector | Recommended migration direction |
|---|---|---|---|---|---|
| RC-01 | A generic content cap combines with fixed navigation and padding. Measured 1040px page, 576px question pane and 144px outside unused space at 1440; fixed questionnaire navigation and nested gutters constrain the reading workspace. Review gets a separate 1120px exception. | Design decision | Questionnaire, evidence inventory, report, comparison, review | `yozora-components.css` `.page`, `.review-page`; `src/shell.css` `.shell-content`; `yozora-patterns.css` `.split`, `.split-pane` | Use explicit inventory, task-workspace and document width modes. Determine questionnaire evidence inspector behavior from measured content at both desktop widths; do not prescribe three fixed columns. |
| RC-02 | Question guidance, skip reason and desk-review note reuse `.help`, which is 12px and muted. The 7 Oct hierarchy amendment reserves `.help` for field hints and defines reasons as secondary text. | Shortcut | Questionnaire, early/context states | `partials/section_questions.html`; `yozora-components.css` `.help`; `docs/product/2026-10-07-hierarchy-rules.md` section 7 | Introduce a readable reason role with a 14px minimum, separate from metadata and field hints. Preserve quote and conclusion roles. |
| RC-03 | Source carries 623 parsed inline style attributes, 426 outside the board-print template; layout and spacing choices travel with each element. Tokens exist, but reuse is not enforced. | Shortcut | Evidence record, requests, remediation, engagement detail, workpaper | `pages/evidence_detail.html`, `partials/magic_links.html`, `pages/remediation_tracker.html`, `components/workpaper_entry.html` | Move repeated anatomy into shared variants. Keep explicit dynamic values where data genuinely determines presentation. Avoid hundreds of one-off utilities. |
| RC-04 | CSS groups S5/S7/S8 implementation slices and revisits selectors later. `.cc-requirement` and `.cc-remediation` change from flex to block farther down the same file. | Shortcut | Conclusions, findings, report, narrative, versions | `yozora-patterns.css` lines 295-601, `.cc-*`, `.f-*`, `.rp-*`, `.nv-*`, `.s8-*` | Organize styles around stable component roles and page archetypes, with documented variants and local ownership. |
| RC-05 | Shared form primitive exists but real forms bypass it. `ui.field` calls occur only in `pages/design.html`; `new_assessment` imports it unused. The similarly named workpaper macro is unrelated. | Shortcut | Setup, settings, scope, questionnaire, filters | `components/ui.html` field macro; handwritten `.field` in live templates | Give form controls one label/help/error/disabled contract. Reuse this contract in creation, settings and workflow forms. |
| RC-06 | Token contracts contain concrete drift: undefined `--surface-2` on `.cc-evidence`, literal 7/12px radii and duplicated global headings. | Shortcut | Evidence in conclusions, review detail, shell | `yozora-patterns.css:303`; `yozora-components.css` `.mark`, `.rq-detail`, h1/h2; `src/shell.css` h1/h2 | Define every semantic surface, one typography source and intentional radius variants. Add token-reference validation during migration. |
| RC-07 | Translucency and blur remain on even the surface called `.solid`; the background depends on canvas position and nested alpha. This adds variation beneath long reading areas. It is a complexity finding, not proof of contrast failure. | Design decision | Most staff pages, menus, review, report | `yozora-tokens.css` canvas/glass/solid/blur; `yozora-components.css` `.glass`, `.solid` | Use opaque neutral reading surfaces and a restrained canvas. Retire translucency throughout the staff surfaces. |
| RC-08 | A finite palette represents independent dimensions with overlapping tones: `.c-neutral` and `.c-insuf` share insufficient gray, medium/partial share amber, accent denotes required, active, issued and AI proposal. Text still distinguishes them. | Design decision | Requests, review, inventory, report | `yozora-components.css` `.c-*`; `components/ui.html` pill tone mapping; RFI and conclusion templates | Keep a restrained palette but separate severity, outcome, progress and provenance through labels, icons and placement. Never infer decision authority from accent color. |
| RC-09 | Dense live-route regression coverage is not retained as a comprehensive baseline set. Existing 20 persistent files cover shell/home/gallery; S7/S8/S9 page comparison gates do exist. | Shortcut | All populated live workflows | `design/baselines/`; `design/harness/gate_s7.py`, `gate_s8.py`, `gate_s9.py` | Retain representative populated reading, inventory and interaction states at both desktop widths plus required themes and mobile upload. Do not claim there was zero prior QA. |
| RC-10 | Section identity is split across local class changes, an HTMX partial, inline scripts and the URL. Section clicks update selection before the request and do not push a URL. Shared global events and 18 inline-script templates increase state coordination burden. | Stack | Questionnaire, conclusions/review swaps, browser back/reload | `partials/questionnaire_sections.html` inline onclick/hx-target; `app.js` lifecycle handlers; inline partial scripts | Model selected item, request result, error, dirty edit and focus as one state contract. Use routable section/control identity where useful. Verify equivalent history behavior. |
| RC-11 | Z-index roles are not specified centrally. Drawer80/scrim70/modal90/toasts100/menu20/tooltip50 are literal local choices; no token scale describes interaction precedence. | Never designed | Menus, confirms, mobile shell, tooltip, toast | `yozora-components.css` overlays; `yozora-patterns.css` `.anchor .menu`, `.toasts`; tokens have no z-index | Specify overlay layering and focus ownership together before choosing shadcn/Radix components. Overlay overlap and focus acceptance remain required in implementation. |
| RC-12 | Navigation spec and rendering differ. The segmented primitive is specified for two to four choices, but report subnavigation can have five; section navigation lacks durable identity. | Shortcut | Report, versions, applicability, narrative, board inputs | `docs/product/yozora-design-system.md` Segmented control; `components/seg_rows.html` report_seg; `components/layout.html` seg | Define primary stage, subview and item navigation with enough room and stable links. Preserve conditional ISO applicability. Validate at 1280 rather than relying on wrap alone. |
| RC-13 | Page-purpose and navigation depth lack one shared contract. RFI stacks three bars; assessment headers repeat the client identity; upload places instructions before the h1 and mixes service names. | Never designed | Assessment, RFI, client upload | `screenshots/rfi-items-1440.jpg`, `questionnaire-open-1440.jpg`, `b6-magic_upload-default-390.png`; assessment header, RFI and upload templates | One stage bar, one labelled Section select for all sub-sections, task h1 and contextual identity. |
| RC-14 | Finding content has no shared deliverable hierarchy. Titles name controls, two evidence blocks repeat a file, and the recommended action is a secondary inset. | Never designed | Queue, conclusions, findings, workpaper | `screenshots/review-selected-1440.png`; conclusion/requirement card macros | Gap, outcome, impact, recommendation with reasoning, provenance; decision mechanics only in review states. |
| RC-15 | Exception work and completed membership are not designed as separate states. SoA asks for every justification; RFI keeps already-requested evidence in candidate form. | Never designed | Scope/SoA and RFI | `screenshots/soa-1440.jpg`, `screenshots/rfi-items-1440.jpg`; SoA and RFI view models | Default applicability with explicit exclusions; distinct RFI candidates and issued membership. |
| RC-16 | Content is not specified for each audience. Existing report summary does not supply engagement narrative, per-gap impact and recommendation reasoning; question guidance also lacks distinct why/how roles. | Never designed | Questionnaire, Review, Report, client instructions | `screenshots/report-iso-1440.jpg`, `screenshots/review-selected-1440.png`; report/narrative and question content | A separate authored/generated content track with stable UI slots and validation. Layout cannot manufacture missing assessment facts. |

## Verification of the six starting hypotheses

| Brief hypothesis | Ruling | Evidence and qualification |
|---|---|---|
| 424 inline styles | Confirmed in substance, corrected count | 633 textual occurrences; HTML start-tag parser finds 623 attributes including 197 board-print attributes, leaving 426. Source counts do not equal runtime nodes. |
| CSS by slice rather than component | Confirmed | Batch comments and `.cc/.dr/.f/.s8/.rp/.an/.nv` families remain, alongside valid shared primitives. |
| Field macro called in two files | Corrected | Only gallery calls shared `ui.field`; new assessment imports it unused; workpaper defines a different local field macro. |
| Token gaps | Mostly confirmed, prose claim narrowed | Undefined surface, literal radii, duplicate headings and absent overlay scale exist. Prose caps already exist locally at 36/44/68/70ch and the hierarchy doc specifies a 70ch target. A universal reason role is unfinished; there is not a complete absence of line-length design. |
| One global content width | Partially confirmed | Generic 1040px shell is real, but 1120px review and 560/640/720px form/reading exceptions exist. Missing coherent task modes is the cause. |
| No screen ever checked for drift | Refuted | Persistent baselines are shell/gallery-focused, but page-state comparisons occur in S7/S8/S9 gates. The remaining gap is comprehensive retained live-route coverage. |

## Yozora principles: reconciled rulings

The canonical principles are `docs/product/yozora-design-system.md`. Existing hierarchy amendments also apply. Keep means retain the rule, not that every screen currently obeys it.

| Principle | Ruling | Evidence and fixed interpretation |
|---|---|---|
| P1 Sentence case | Keep | Staff primitives generally use sentence-case labels. Uppercase remains in standalone print styles; scope lint to staff/client UI and document print exceptions explicitly. |
| P2 No serial numbering or reference codes in lists | Change | The same source document later allows small muted control codes in lists. Auditors need stable ISO/control references for cross-checking. Permit references beside human titles, never as the only title; keep decorative numbering out. |
| P3 Subtext must earn its place | Change | Distinguish useful reason from metadata. `section_questions.html` guidance is necessary task content and must receive the reason role rather than hint styling. |
| P4 Hierarchy through size, weight and spacing | Change | Shared h1/h2/h3 and conclusion styles support this. Preserve non-color differentiation of proposal, evidence and decision; rules/borders may separate structural regions without becoming the sole hierarchy. The target system requires a greyscale acceptance test; source screenshots alone do not certify it. |
| P5 One primary action per state | Keep | Preserve one dominant workflow action in the active task region, but define screen versus independent dialog/queue state. Multiple repeated card actions need a scoped audit rather than a pagewide CSS count alone. See conclusion cards and `assessment_header` conditional primary action. |
| P6 Restrained decoration | Change | Retire the gradient canvas and glass surfaces. Retain functional loading animation, and keep accents for branding and interaction only. |
| P7 Fixed severity/outcome colors | Change | Use four fixed semantic families: severity, outcome, progress and provenance. Foreground/background pairs vary by theme for contrast, never by firm accent. DESIGN_SYSTEM.md defines the complete token pairs. |
| P8 Framework integrity and period/cutoff | Keep | `assessment_header` has identity and conditional period/cutoff; `report_seg` gates applicability to ISO. Preserve framework-specific scoring and provenance. Presence of metadata on every route still needs live-route review. |
| P9 Tokenized colors | Keep | The generated token file provides a strong source of truth. Enforce no unknown token references and document print/template data-driven exceptions. Tailwind should consume semantic roles rather than create arbitrary colors. |
| P10 Never color-only meaning | Keep | Outcome pills carry labels and conclusion decisions use words/icons. Keep text on every status; small isolated dots require accessible names and context, verified during the capture pass. |

## Canvas, glass, accents and statuses

| Element | Ruling | Evidence and decision |
|---|---|---|
| Three-stop canvas | Retire | `html` paints a fixed viewport gradient and surfaces composite over it. A neutral canvas removes a location-dependent background from sustained audit reading. Saqlain fixed this decision; visual fatigue was not measured. |
| Glass reading surfaces | Retire | `.solid` and `.glass` both blur and composite. Use opaque reading/table surfaces; retain elevation only for spatial context such as menus. |
| Eight firm accent presets | Keep | Graphite, azure, cobalt, midnight, teal, violet, plum and slate are tokenized light/dark presets. Restrict accents to interactive/selected/brand roles and validate each pairing in `MEASUREMENTS.md`. They must not theme severity or outcome. |
| Status colors | Change | Stable severity/outcome families are useful. Separate progress, severity, outcome and provenance labels, retain restrained fill/markers, and use accessible foreground tokens. The code inventory and contrast appendix support exact pair decisions; every status does not need a unique hue. |

Concrete token values, component specifications and prototypes are in the second-run deliverables. Content quality remains a separate track.
