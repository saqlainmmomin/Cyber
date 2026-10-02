# Yozora design system

Status: **draft for Saqlain's sign-off** (2026-10-01). Values are not retyped here: `design/yozora-tokens.css` is the source until the generator lands, `design/tokens.json` is its checked copy (`python design/tokens_tool.py check`), `design/yozora-components.css` holds every component. If this document and those files disagree, the files win and this document is wrong. The component gallery is `docs/product/2026-10-01-app-design-mockups/screens/gallery.html`. Direction: `v3-polish.html`.

## 1. Principles (each one is checkable)

| # | Rule | How to check |
|---|---|---|
| P1 | Sentence case everywhere. No all-caps text, no eyebrow labels. | `grep -rniE "uppercase\|text-transform" app/templates design app/static/css/src` finds nothing |
| P2 | No serial lettering or numbering of sections, steps or nav; no ref codes in list views (ids only in detail views). | Template lint for `Step \d`, `[A-Z]\.` heading prefixes, `^\d+\.` headings |
| P3 | No subtext unless it earns its place. Each `.sub`/`.t-sub` must answer a question the title cannot. | Design review |
| P4 | Hierarchy from size, weight and spacing only, not caps, rules or colour. | Design review |
| P5 | One primary action (`.btn.primary`) per screen. | Gallery/screenshot test counts `.btn.primary` per page, max 1 |
| P6 | No glow blobs, gradient text, sparkle icons or rainbow borders. Gradient only on the canvas and the primary button highlight. | Lint for `background-clip:text`, `blur-3xl`, extra gradients |
| P7 | Severity and outcome colours are fixed, never themed: critical `#9B1C1C`, high `#D9481E`, medium `#F0A030`, low `#3C9D6B`; compliant `#2F9466`, partially compliant `#F0A030`, non-compliant `#C0392B`, insufficient evidence `#9AA3B5`. | Tokens test: values equal in light, dark and every accent |
| P8 | Scores are never combined across frameworks. Period and evidence cut-off are always visible on assessment pages. No numeric priority shown to clients. Framework-specific copy is conditional. | Contract tests per slice |
| P9 | No hex or arbitrary Tailwind values in templates; colour comes from tokens. | Lint: `#[0-9a-fA-F]{3,8}` and `\[[^\]]*(px\|#)` in `app/templates` |
| P10 | Colour is never the only carrier of meaning: every severity or outcome has a text label. | Review |

Decision recorded here: the score ring stays neutral (accent colour), never green or red. Outcome is carried by the distribution list and pills beside it.

## 2. Tokens

Canvas gradient (top, mid at 52%, bottom) light and dark; surfaces (`--glass`, `--glass-strong`, `--solid`, `--glass-edge`); lines and states (`--line`, `--hover`, `--press`, `--track`); text (`--text`, `--text-2`, `--muted`); elevation (`--e-1` card, `--e-2` raised, `--e-3` popover/drawer); fixed semantic colours; radius (`--r-xs` 5, `--r-sm` 8, `--r-md` 10, `--r-lg` 16, `--r-full`); spacing 4/8/12/16/20/24/32/40/48/64; type 12/13/14/16/20/28 (40 reserved for framework scores, not yet in the file: add `--t-score` before use); accent set. Inter 400/500/600, tabular figures for numbers, vendored under `/static/fonts`, no CDN. Motion 140 ms colour and shadow, 80 ms press, none under `prefers-reduced-motion` (enforced in the stylesheet).

Deviation from the kickoff table: the mockup uses radius 5 and 8 where the kickoff said 4 and 6. The file is canonical, so 5 and 8 stand.

Firm accent: the firm theme sets only `--accent`, `--accent-text`, `--on-accent` (and the dark pair). An uploaded accent must pass at upload time: `--on-accent` on `--accent` at least 4.5:1, and `--accent-text` on the light panel (and dark `--accent-text` on the dark canvas) at least 4.5:1; otherwise it is rejected with the failing ratio shown.

## 3. Components

Defined in `yozora-components.css`; each is shown in every state in the gallery.

| Component | Variants and states | Notes |
|---|---|---|
| Button | primary, secondary, ghost, danger (text), destructive (filled, confirm dialogs only); sm; icon; lead icon; rest, hover, active, focus (2px gap + 4px accent ring), disabled (45%) | Pill, 34px (28 sm). Keycap hint `kbd` only on review actions. |
| Segmented control | pressed/not | Two to four options max. |
| Field | default, hover, focus, invalid, disabled; input, select, textarea | 32px; label above, help or error below. Error text is `--danger-text`. |
| Checkbox, radio, switch | unchecked, checked, focus, disabled | Switch for immediate settings only. |
| Pill | severity, outcome, accent, neutral | Tinted fill, dot, normal-colour text. |
| Chip | framework tag | 22px, 5px radius. |
| Status | open, in progress, plus dot variants | Never colour-only. |
| Surfaces | `.glass` (decorative, frosted), `.solid` (tables, detail, menus) | Solid wherever text is dense. |
| Table | header, row, hover with chevron, numeric columns | Rows are `cursor:pointer` only when the whole row navigates. |
| Rows list | icon, text, action | Home attention list. |
| Nav, brand, user menu, breadcrumb, page header | active via `aria-current` | Drawer under 860px. |
| Stepper | done, current, next | Five stages, no numbers. |
| Ring and distribution | neutral ring | Score never coloured. |
| Review: list item, detail, citation, recommendation, check list, progress ticks | selected, decided | Left bar marks selection. |
| Tabs | selected via `aria-selected` | Framework tabs on the hub. |
| Alert | medium, noncompliant, accent colour via `--c` | Inline, not toast. |
| Empty state | icon, title, one sentence, one action | See copy rules. |
| Skeleton | line | Loading for HTMX swaps over 300 ms. |
| Toast | success | Bottom-right, auto-dismiss 4 s, never carries the only record of an action. |
| Modal | title, body, cancel, destructive | Destructive confirm: names the object, states what is lost, button label repeats the verb ("Delete engagement"). |

Missing from the file and required by the batches before build: date picker input styling, file dropzone, popover, pagination, breadcrumb overflow. Each is added to the CSS and gallery first, in the batch that needs it.

## 4. Patterns

Page header: h1 (28/500), optional single meta line (period and evidence cut-off on assessment pages), actions right, the one primary last. Tables: solid surface, 40px header, 14px cell padding, sort only if the data is ordered, empty state in place of an empty table. Forms: one column, labels above, validate on blur and submit, error summary only for forms with more than five fields. Empty states: say what is missing and the one next step. Destructive actions: modal with the object named. HTMX swaps: swap target keeps its id; show `.skel` when a swap takes more than 300 ms; a failed swap shows an `.alert` in the target, never a blank. Focus order follows visual order; focus returns to the trigger after a modal closes.

## 5. Copy rules

Sentence case. Plain verbs ("Approve", "Send link", "Delete engagement"). Say what happened and what to do, not who is to blame ("The file is over the 25 MB limit. Upload a smaller copy."). Empty state: "No evidence yet. Upload documents or send the client a link." Errors never say "Oops". No exclamation marks. Numbers carry units. Framework names appear only where the framework is in scope (P8). Dates "15 Oct 2026".

## 6. Accessibility

Contrast measured 2026-10-01 against the nearest solid surface (light panel approximated as `#F0F1F6`): text 15.4, text-2 8.7, muted 5.9 (4.7 on the darkest canvas stop), Midnight accent text 9.8, white on Midnight 11.1, danger text 5.8; dark: text 14.0, text-2 8.8, muted 6.4, accent text 8.8, white on dark accent fill 7.9, danger 6.0. All at least 4.5:1. Status pill text uses the normal text colour because amber and orange fail as text. Severity labels are always text. Focus is always visible (2px gap and 4px accent ring at 38%). Targets at least 28px, controls 34px; touch pages (client upload) use 44px controls. Reduced motion removes transitions and animation. Every icon-only button has `aria-label`.

## 7. Wordmark and favicon

Typographic wordmark: "Yozora" in Inter 600, letter-spacing -0.01em, preceded by the existing 24px rounded accent tile with the open-circle mark (`#i-mark`). The favicon is that tile on the Midnight accent. A custom symbol is not proposed. Trademark search in India (classes 9, 42, 45) and registrar check are still open and gate Track 4, not this work.

## 8. Deliberately not in the system

Charts and chart libraries (SVG/CSS only, fed by the board-deck presenter later); illustrations; avatars beyond initials; per-severity row colouring; icon sets beyond the Lucide-style outline symbols already in the mockup; any theming other than the firm accent; print templates (board report, standalone workpaper), which share colour tokens only.
