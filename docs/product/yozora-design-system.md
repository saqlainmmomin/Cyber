# Yozora design system

Status: **approved by Saqlain, 3 Oct 2026**, to match the 61 screens in `docs/product/2026-10-01-app-design-mockups/screens/`. Values are not retyped here: `design/tokens.json` is the source and `design/tokens_tool.py` generates the checked application copy at `app/static/css/yozora-tokens.css`; `design/yozora-components.css` and `design/yozora-patterns.css` hold every component and page pattern. If this document and those files disagree, the files win and this document is wrong. The component gallery is `docs/product/2026-10-01-app-design-mockups/screens/gallery.html`. Direction: `v3-polish.html`. Where things live: `screens/IA-SPEC.md` and `flow-map.html`.

## Principles (each one is checkable)

| # | Rule | How to check |
|---|---|---|
| P1 | Sentence case everywhere. No all-caps text, no eyebrow labels. | `grep -rniE "uppercase\|text-transform" app/templates design app/static/css/src` finds nothing |
| P2 | No serial lettering or numbering of sections, steps or nav; no ref codes in list views (ids only in detail views). | Template lint for `Step \d`, `[A-Z]\.` heading prefixes, `^\d+\.` headings |
| P3 | No subtext unless it earns its place. Each `.sub`/`.t-sub` must answer a question the title cannot. | Design review |
| P4 | Hierarchy from size, weight and spacing only, not caps, rules or colour. | Design review |
| P5 | At most one primary action (`.btn.primary`) per screen state, and none in a state with no real action (never a disabled primary). | Screenshot test counts visible `.btn.primary` per page, max 1 |
| P6 | No glow blobs, gradient text, sparkle icons or rainbow borders. Gradient only on the canvas and the primary button highlight. | Lint for `background-clip:text`, `blur-3xl`, extra gradients |
| P7 | Severity and outcome colours are fixed, never themed: critical `#9B1C1C`, high `#D9481E`, medium `#F0A030`, low `#3C9D6B`; compliant `#2F9466`, partially compliant `#F0A030`, non-compliant `#C0392B`, insufficient evidence `#9AA3B5`. | Tokens test: values equal in light, dark and every accent |
| P8 | Scores are never combined across frameworks. Period and evidence cut-off are always visible on assessment pages. No numeric priority shown to clients. Framework-specific copy is conditional. | Contract tests per slice |
| P9 | No hex or arbitrary Tailwind values in templates; colour comes from tokens. | Lint: `#[0-9a-fA-F]{3,8}` and `\[[^\]]*(px\|#)` in `app/templates` |
| P10 | Colour is never the only carrier of meaning: every severity or outcome has a text label. | Review |

Decision recorded here: the score ring stays neutral (accent colour), never green or red. Outcome is carried by the distribution list and pills beside it.

## Information architecture

Binding spec: `screens/IA-SPEC.md`; picture: `flow-map.html`. Summary:

- **Side menu** (every staff screen, Settings at the bottom): Home, Clients, Engagements, Review (count badge), Evidence, Reports. `aria-current="page"` marks the section; anything inside an engagement or assessment marks Engagements, except the cross-engagement views (Review, Evidence with `?state=all`, Reports).
- **Engagement tabs** (`<nav class="tabs" aria-label="Engagement">`): Overview, Evidence, Findings and actions, Reports.
- **Assessment tabs** (`<nav class="tabs" aria-label="Assessment">`): Overview, Scope, Questionnaire, Review, Report.
- **Stepper**: one five-stage stepper (Scope, Evidence, Questionnaire, Review, Report), on the assessment Overview only. The engagement Overview has none; its assessments table shows Stage and Next step columns.
- **Sub-views** use one `.seg` row under the tab row, never a second `.tabs` row: Evidence (Inventory, Requests), Review (Queue, Conclusions, Findings, Workpaper), Report (Report, Versions, Applicability, ISO 27001 only). A request page shows only its own seg (Items, Versions, Client links).
- **Detail pages** keep the parent tab row with that tab selected and add the page name as the last crumb.
- **Breadcrumbs are complete**: client / engagement / assessment / page. The last crumb is `<b>`.
- **Single assessment**: an engagement with one assessment opens straight on that assessment's Overview.
- **Framework tabs** inside Report, the statement of applicability and Compare keep their `.tabs` row (they switch content, not pages).

## Tokens

Canvas gradient (top, mid at 52%, bottom) light and dark; surfaces (`--glass`, `--glass-strong`, `--solid`, `--glass-edge`); lines and states (`--line`, `--hover`, `--press`, `--track`); text (`--text`, `--text-2`, `--muted`); elevation (`--e-1` card, `--e-2` raised, `--e-3` popover/drawer); fixed semantic colours; radius (`--r-xs` 5, `--r-sm` 8, `--r-md` 10, `--r-lg` 16, `--r-full`); spacing 4/8/12/16/20/24/32/40/48/64; type 12/13/14/16/20/28 (40 reserved for framework scores, not yet in the file: add `--t-score` before use); accent set. Inter 400/500/600, tabular figures for numbers, vendored under `/static/fonts`, no CDN. Motion 140 ms colour and shadow, 80 ms press, none under `prefers-reduced-motion` (enforced in the stylesheet).

Deviation from the kickoff table: the mockup uses radius 5 and 8 where the kickoff said 4 and 6. The file is canonical, so 5 and 8 stand.

Firm accent: the firm theme sets only `--accent`, `--accent-text`, `--on-accent` (and the dark pair). An uploaded accent must pass at upload time: `--on-accent` on `--accent` at least 4.5:1, and `--accent-text` on the light panel (and dark `--accent-text` on the dark canvas) at least 4.5:1; otherwise it is rejected with the failing ratio shown.

## Components

Defined in `yozora-components.css`; each is shown in every state in the gallery.

| Component | Variants and states | Notes |
|---|---|---|
| Button | primary, secondary, ghost, danger (text), destructive (filled, confirm dialogs only); sm; icon; lead icon; rest, hover, active, focus (2px gap + 4px accent ring), disabled (45%) | Pill, 34px (28 sm). Keycap hint `kbd` only on review actions. |
| Segmented control | pressed/not | Two to four options max. Also the one sub-view row under a tab row (Review has four). |
| Field | default, hover, focus, invalid, disabled; input, select, textarea | 32px; label above, help or error below. Error text is `--danger-text`. |
| Checkbox, radio, switch | unchecked, checked, focus, disabled | Switch for immediate settings only. |
| Pill | severity, outcome, accent, neutral | Tinted fill, dot, normal-colour text. |
| Chip | framework tag | 22px, 5px radius. |
| Status | open, in progress, plus dot variants | Never colour-only. |
| Surfaces | `.glass` (decorative, frosted), `.solid` (tables, detail, menus) | Solid wherever text is dense. |
| Table | header, row, hover with chevron, numeric columns | Rows are `cursor:pointer` only when the whole row navigates. |
| Rows list | icon, text, action | Home attention list. |
| Nav, brand, user menu, breadcrumb, page header | active via `aria-current` | Drawer under 860px. |
| Stepper | done, current, next | Five stages, no numbers. Assessment Overview only. |
| Ring and distribution | neutral ring | Score never coloured. |
| Review: list item, detail, citation, recommendation, check list, progress ticks | selected, decided | Left bar marks selection. |
| Tabs | selected via `aria-selected` | Engagement and assessment tab rows; framework tabs in Report, statement of applicability and Compare. |
| Alert | medium, noncompliant, accent colour via `--c` | Inline, not toast. |
| Empty state | icon, title, one sentence, one action | See copy rules. |
| Skeleton | line | Loading for HTMX swaps over 300 ms. |
| Toast | success, error, information, with action (Undo), stacked | `.toasts` container, bottom-right, full width above the safe area under 860px. Success and information dismiss after 4 s; errors stay until closed. Never the only record of an action. |
| Progress bar | track and fill | `.progress-bar`; used in request cards and upload rows. `.progress` with `.ticks` is the review progress count. |
| Key-value grid | label, value | `.kv`; detail pages. |
| Stat | number and label | `.stat`, `.big-n`; summary rows (`.top-sum` is the four-up version). |
| Code block | head with copy action, body | `.code`; AWS policy text. |
| Disclosure | closed, open | `details.disclose`; one line, chevron turns. |
| Select | chevron, light and dark | `.field select` carries its own chevron image. |
| Date input | tabular figures | `.field input[type=date]`. A calendar panel is not built; the browser control is used. |
| Touch size | 44px field and button | `.touch` on `.field` and `.btn`; client-facing pages only. |
| File input and dropzone | idle | `.field input[type=file]` button styling; `.drop` is the bordered row with tile, text and action (logo, upload). Drag-over and uploading states come from the page, not the CSS. |
| Loading button | busy | `.btn.loading`: label hidden, spinner, no pointer events. Used while an HTMX request is in flight. |
| Tooltip | hover, focus | `data-tip`; icon-only buttons still keep `aria-label`. |
| Screen-reader text | | `.sr-only`. |
| Responsive helpers | | `.hide-md` (under 1100px), `.hide-sm` and `.show-sm` (under 860px). |
| Menu and popover | closed, open | `.anchor` wraps trigger and `.menu`; `.menu.open` shows it. Row actions, share, account. |
| Static table | no row hover | `.static` on a table whose rows do not navigate. |
| Filter toolbar | search, selects | `.tools` (search plus selects); `.tools.keep-row` keeps the selects on one line on phones. `.filter-bar` is the older single-row form. |
| Pager | previous, next, count | `.pager`, at the foot of a table. |
| Line list | text left, action right | `.line-list`; unmigrated assessments, archived engagements, purge history. |
| Swatches | radio group of accents | `.swatches`; firm accent picker. |
| Request card | header with count and expiry, progress, item checklist, footer | `.req`, `.req-head`, `.req-meta`, `.req-prog`, `.req-items`, `.req-foot`. Staff client-links list and client upload page. |
| Request marker | received, waiting | `.mk` and `.mk.on`: round tick marker beside a requested item. Always paired with text ("Received", "Waiting"). |
| Request picker | ticked, unticked | `.req-pick` inside `.req-picks`: tick boxes for requested items when creating a link. |
| Login shell | | `.login` with `.box`; centred card, no side menu. |
| Loading blocks | line, stack | `.skel` and `.skel-stack`. |
| Modal | title, body, cancel, destructive | Destructive confirm: names the object, states what is lost, button label repeats the verb ("Delete engagement"). Delete confirms by typing the name; the destructive button stays disabled until it matches. |

Still missing: **breadcrumb overflow.** At 390px the client and engagement crumbs are hidden with `hide-sm` on deep pages, so only the last crumbs show; a collapse into an ellipsis menu is not built. If the build needs it, add it to the CSS and gallery first. Calendar panel for dates is also not built (browser control stays).

## Patterns

Page header: h1 (28/500), optional single meta line (period and evidence cut-off on assessment pages), actions right, the one primary last. Tables: solid surface, 40px header, 14px cell padding, sort only if the data is ordered, empty state in place of an empty table. Forms: one column, labels above, validate on blur and submit, error summary only for forms with more than five fields. Empty states: say what is missing and the one next step. Destructive actions: modal with the object named; delete confirms by typing the name. Retention period is a firm setting (Settings, data housekeeping); an engagement keeps only Archive. Evidence reuse is between assessments of the same engagement: tick boxes plus one confirm button. The statement of applicability saves in one action. There is no combined cross-framework report view. One Generate button follows the selected report tab. HTMX swaps: swap target keeps its id; show `.skel` when a swap takes more than 300 ms; a failed swap shows an `.alert` in the target, never a blank. Focus order follows visual order; focus returns to the trigger after a modal closes.

## Copy rules

Sentence case. Plain verbs ("Approve", "Send link", "Delete engagement"). Say what happened and what to do, not who is to blame ("The file is over the 25 MB limit. Upload a smaller copy."). Empty state: "No evidence yet. Upload documents or send the client a link." Errors never say "Oops". No exclamation marks. Numbers carry units. Framework names appear only where the framework is in scope (P8). Dates "15 Oct 2026".

Fixed vocabularies (shown as written, never colour-only):

- **Evidence status:** Scanning (quarantined), Available (active), Rejected, Out of date (invalidated). Archived evidence is not listed.
- **Evidence source:** Upload, AWS, Client link, Reused.
- **Priority, as words:** Do first, Next, Planned, Backlog. Never a number, never shown to clients as a number.
- **Questionnaire answer scale:** Fully implemented, Partially implemented, Planned, Not implemented, Not applicable.
- **Control and requirement codes** (A.5.18, s.8) appear in small muted text in lists, never as the row title; detail pages may show them in the meta line.
- **Screening** is DPDPA only, so screening copy appears only when DPDPA is in scope.
- **Error page** shows a short reference code the user can quote.
- **Reviewer name:** designs assume a signed-in user and show no name field. The build keeps a temporary name field on routes that need one until Track 4 auth.

## Accessibility

Contrast measured 2026-10-01 against the nearest solid surface (light panel approximated as `#F0F1F6`): text 15.4, text-2 8.7, muted 5.9 (4.7 on the darkest canvas stop), Midnight accent text 9.8, white on Midnight 11.1, danger text 5.8; dark: text 14.0, text-2 8.8, muted 6.4, accent text 8.8, white on dark accent fill 7.9, danger 6.0. All at least 4.5:1. Status pill text uses the normal text colour because amber and orange fail as text. Severity labels are always text. Focus is always visible (2px gap and 4px accent ring at 38%). Targets at least 28px, controls 34px; touch pages (client upload) use 44px controls (`.touch`). Reduced motion removes transitions and animation. Every icon-only button has `aria-label`.

Measured 3 Oct 2026 for the request-card components (`.req`, `.mk`): item text and links reuse measured pairs (muted 5.9, accent text 9.8 on Midnight, on-accent on accent 11.1). The `.mk.on` marker is on-accent on accent, so it is covered by the per-accent upload rule. Accent text on the light panel for the preset accents: graphite 13.9, azure 5.0, cobalt 6.0, midnight 9.8, teal 5.2, violet 5.8, plum 7.0, slate 7.3 (all at least 4.5). Dark muted on the dark panel `#141824` is 6.8.

Known gap, for Saqlain: the outline of unticked `.mk`, `.choice` checkboxes and radios and `.drop` uses `--line-strong`, about 1.3:1 on the light panel (1.5:1 dark), and field outlines use the lighter `--line`. WCAG 1.4.11 asks 3:1 for the boundary of a control. State is also carried by text beside the marker and by fill when ticked, but the empty control is hard to see. Not changed here; see Results.

## Wordmark and favicon

Typographic wordmark: "Yozora" in Inter 600, letter-spacing -0.01em, preceded by the existing 24px rounded accent tile with the open-circle mark (`#i-mark`). The favicon is that tile on the Midnight accent. A custom symbol is not proposed. Trademark search in India (classes 9, 42, 45) and registrar check are still open and gate Track 4, not this work.

## Deliberately not in the system

Charts and chart libraries (SVG/CSS only, fed by the board-deck presenter later); illustrations; avatars beyond initials; per-severity row colouring; icon sets beyond the Lucide-style outline symbols already in the mockup; any theming other than the firm accent; print templates (board report, standalone workpaper), which share colour tokens only.
