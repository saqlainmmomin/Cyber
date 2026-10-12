# Frontend architecture audit

Audit date: 12 Oct 2026. This document records verified source structure, not a visual verdict. Chromium could not launch in the sandbox; page geometry, focus behavior and appearance remain pending the capture requests.

## Generation and ownership

FastAPI routes construct view models and render Jinja2 pages. `app/templates/base.html` supplies the staff shell, vendored HTMX 2.0.4 and `<body hx-boost="true">`. HTMX fetches and swaps server-rendered partials; JavaScript supplies interaction behavior. There is no loaded Tailwind stylesheet, React runtime or frontend build step. The comment in `app/static/css/style.css` claiming Tailwind does most work is stale.

| Source | Verified extent | Responsibility |
|---|---|---|
| `app/routers/web.py` | 3,916 lines, 59 `@router` HTTP decorators | Portfolio and assessment pages and fragment endpoints; route count is not screen count |
| `app/templates/` | 92 HTML files | 35 pages, 42 partials, 10 components, 2 magic, 2 report templates and base |
| `app/templates/pages/` | 35 files | 31 non-design page templates and 4 design templates; assessment tabs and inventory scopes create additional meaningful screens |
| `app/templates/components/ui.html` | Shared Jinja macros | Buttons, fields, pills, alerts, toasts, modal, disclosure and client request cards |
| `app/templates/components/layout.html` | Shared Jinja macros | Headers, breadcrumbs, tabs, engagement/assessment navigation, table, review and citation anatomy |
| `app/templates/components/seg_rows.html` | Shared subnavigation | Queue/conclusions/findings/workpaper and report/version/applicability/narrative/board inputs |
| `app/templates/components/conclusion_card.html` | Reusable stateful card | Proposal, decision, evidence, editing and revision state |
| `app/static/js/app.js` | 905 lines | Toast headers, skeletons, errors, confirms, focus management, menus, copy, row navigation, shortcuts and upload progress |
| Design routers | `PREVIEW_PAGES` registries | No-spend fixture states; they supplement seeded live pages |

The 31 page-template count includes error and login templates, while the brief's live-screen table separates tabs and scopes. Use the screen inventory for capture coverage rather than treating the template count as a complete route inventory.

## CSS cascade and tokens

The staff base loads these files in this exact order:

1. `app/static/css/src/fonts.css`: vendored Inter.
2. `app/static/css/yozora-tokens.css`: generated from `design/tokens.json` by `design/tokens_tool.py`.
3. `app/static/css/yozora-components.css`: 384 lines of shared components, shell, type and interaction states.
4. `app/static/css/yozora-patterns.css`: 667 lines of utilities and page patterns, including S5 through S9 additions.
5. `app/static/css/style.css`: 53 lines of HTMX, drag-over, tabs and scrollbar rules.
6. `app/static/css/src/shell.css`: final shell, headings and overflow rules.

The token scale includes type 12/13/14/16/20/28px, spacing 4/8/12/16/20/24/32/40/48/64px and radii 5/8/10/16px/full. Body text is 14px at 1.5. Light text tokens are `#141A26`, `#3B4456`, `#525D71`. There is a fixed three-stop gradient canvas and alpha-composited surfaces. Even `.solid` is translucent: light white at 90%, dark `rgba(18,21,31,.88)`, both with backdrop filtering. See the independent calculations in `MEASUREMENTS.md`; nominal CSS values alone do not prove rendered contrast.

`.page` and `.shell-content` both cap their border boxes at 1040px with 32px desktop horizontal padding. Review overrides reach 1120px. Sidebar width is 256px. Questionnaire `.split` allocates 288px to navigation and a 16px gap, then `.split-pane` takes 24px padding on both sides. `[data-section-questionnaire]` adds an 820px cap. These are source constraints, not browser-measured widths.

## Navigation and state

The global sidebar groups Home, Clients, Engagements, Review, Evidence and Reports. Engagement tabs and assessment tabs describe distinct scopes. Assessment tabs lead to six stages; segmented buttons lead to review/report subviews. Deep pages reuse breadcrumbs and parent navigation. Several stages have both a canonical path and a `?tab=` entry, so the migration must preserve route identity and avoid resetting framework context.

Questionnaire section navigation swaps `#section-content` without pushing a section URL. It changes selection immediately in inline `onclick`; a failed request can therefore leave the selected section name ahead of the displayed content. This is a code-level state-order risk. Reload/back behavior needs a browser check.

`app.js` has explicit HTMX lifecycle handlers, modal focus trapping/restoration, menu arrow keys and request error alerts. Do not attribute all keyboard behavior to missing architecture. Eighteen templates contain inline script blocks; swapped partial scripts and centralized event handlers coexist. React migration needs an inventory of these behaviors, not a literal translation of the markup.

## Duplication and bypasses

The source contains 633 textual `style=` occurrences. Parsing HTML start tags identifies 623 style attributes, of which 197 are in the board-print template; 426 remain outside that template. This reconciles the brief's approximate 424 with a current count and avoids treating print layout as staff-screen drift. The count is source markup, not expanded runtime DOM.

The shared `ui.field` macro is actually invoked only by the component gallery, seven times. `new_assessment.html` imports it without calling it. `workpaper_entry.html` defines a different local macro also named `field`; its calls are display fields, not uses of the shared form primitive. Most live forms hand-write `.field` markup.

`yozora-patterns.css` retains batch boundaries and prefixes `.cc-*`, `.dr-*`, `.f-*`, `.an-*`, `.nv-*`, `.rp-*`, `.s8-*`. The same selector sometimes gets later definitions, such as `.cc-requirement` changing from flex to block and `.cc-remediation` doing the same. The cascade is functioning as a patch sequence rather than a small set of composable patterns.

Global h1/h2 rules are repeated in components and shell CSS. Literal radii include the 7px brand tile, 12px review detail and 3px selection edge. There are literal overlay z-index values, but no overlay token scale. `.cc-evidence` uses undefined `--surface-2`, so its background declaration is invalid unless a future ancestor supplies the variable.

The 7 Oct hierarchy rules specify question guidance as a reason in secondary text with a 14px/70ch target. `section_questions.html` still uses `.help`, which resolves to 12px muted text. Shared citation quotations inherit 14px body text and `.concl` is 16px; the entire app is not uniformly tiny or uniformly low contrast.

Twenty persistent PNG baselines cover home/shell/mobile menus and the gallery. S7/S8/S9 harness gates also compare page candidates against generated baselines. It is incorrect to conclude that no page was ever checked. Persistent live-route coverage is still narrower than this audit requires.

## Migration implications

Jinja2 supports reusable macros, templates, tokens and deliberate layouts today. Most confirmed drift comes from bypassing those tools or incomplete task-specific rules. The stack-specific risk is fragmented browser state across swaps, scripts and navigation; Next.js can reduce that risk only if selection, URL, errors and focus are specified together. The root register classifies each causal finding separately and keeps recommendations at the audit stage.
