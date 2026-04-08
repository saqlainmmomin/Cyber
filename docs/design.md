# CyberAssess — Design System

> Design principles for the CyberAssess web portal (FastAPI + Jinja2 + HTMX + Tailwind CSS).
> Inspired by Revolut's visual language, adapted for a B2B compliance and audit context.

---

## 1. Philosophy

CyberAssess is used by auditors and CISOs — people who equate visual clarity with analytical rigour. The design must communicate *"your data is in capable hands"* without fintech flair.

**Three principles:**

1. **One signal per element.** Every color, border, and weight change communicates something specific. Never use a color for decoration — only for meaning.
2. **Flat confidence.** No drop shadows. Depth comes from the white-card-on-gray-background contrast. Shadows signal uncertainty; flat surfaces signal control.
3. **Navy owns primary.** A single primary color eliminates ambiguity about what is actionable. Every button, link, active state, and progress indicator uses the same navy. No competing primaries.

---

## 2. Color Palette

### Brand
| Token | Hex | Role |
|---|---|---|
| `brand` / `navy-800` | `#1e1e50` | Primary actions, active states, links |
| `brand-light` / `navy-700` | `#2b315a` | Button hover, secondary emphasis |
| `brand-dark` / `navy-900` | `#141438` | Page backgrounds (login, dark surfaces) |

### Navy Scale (for tints and surfaces)
| Token | Hex | Use |
|---|---|---|
| `navy-50` | `#f0f1f8` | Active selection background (sidebar, radio) |
| `navy-100` | `#d9dbed` | Badge backgrounds, chip surfaces |
| `navy-200` | `#b3b7db` | Subtle borders on navy-tinted elements |
| `navy-400` | `#676fb7` | Hover borders on inputs/dropzones |
| `navy-500` | `#4a5296` | Focus ring border |

### Semantic Status Colors
Used exclusively for compliance status, severity, and risk level — never for decoration.

| Meaning | Background | Text | Border |
|---|---|---|---|
| Compliant / Success | `bg-green-100` | `text-green-700` | `border-green-200` |
| Partial / Warning | `bg-yellow-100` | `text-yellow-700` | `border-yellow-200` |
| Planned | `bg-blue-100` | `text-blue-700` | `border-blue-200` |
| Non-compliant / Error | `bg-red-100` | `text-red-700` | `border-red-200` |
| High risk / Alert | `bg-orange-100` | `text-orange-700` | `border-orange-200` |
| Neutral / N/A | `bg-gray-100` | `text-gray-600` | `border-gray-200` |

### Page Surfaces
| Surface | Class | Use |
|---|---|---|
| Page background | `bg-gray-50` | Main content area |
| Card | `bg-white` | All content containers |
| Table header | `bg-gray-50` | `<thead>` rows |
| Muted section | `bg-gray-50` | Section dividers in lists |

### Do's and Don'ts
- **Do** use `text-brand` / `text-brand-light` for all interactive text links
- **Do** use semantic colors only for compliance states — not for UI decoration
- **Don't** use indigo. It was purged. Indigo = indistinguishable from navy at a glance, and creates two competing primaries
- **Don't** introduce new color families without a semantic justification

---

## 3. Typography

**Font:** Inter (system sans-serif). No display font — this is a professional tool, not a marketing page.

### Scale
| Role | Class | Size | Weight | Notes |
|---|---|---|---|---|
| Page title | `text-2xl font-bold` | 24px / 700 | — | Dashboard, assessment company name |
| Section heading | `text-lg font-semibold` | 18px / 600 | — | Card headers, tab section titles |
| Sub-heading | `text-base font-semibold` | 16px / 600 | — | Questionnaire section titles |
| Body | `text-sm` | 14px / 400 | — | All primary content, form labels, table cells |
| Supporting | `text-sm text-gray-500` | 14px / 400 | Gray | Descriptions, subtitles under headings |
| Metadata | `text-xs text-gray-400` | 12px / 400 | — | Timestamps, IDs, secondary counts |
| Badge / label | `text-xs font-medium` | 12px / 500 | — | All status badges and chips |
| Table header | `text-xs font-medium text-gray-500 uppercase tracking-wider` | 12px | — | `<th>` elements |
| Monospace code | `font-mono text-xs` | 12px | — | Requirement IDs (e.g., `CH2.CONSENT.1`) |

### Rules
- **Minimum body text is `text-sm` (14px).** `text-xs` is reserved for metadata, badges, table headers, and code references — never for primary content.
- **Semibold (600) for headings, not bold (700).** Bold is reserved for page-level titles only. Authority comes from size and color, not weight.
- **Gray hierarchy:** `text-gray-900` → `text-gray-700` → `text-gray-500` → `text-gray-400`. Never skip levels.

---

## 4. Components

### Buttons

Three variants only. No others.

**Primary** — Navy fill
```
bg-brand hover:bg-brand-light text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
```

**Secondary** — Outlined
```
border border-gray-300 text-gray-600 hover:bg-gray-50 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
```

**Destructive** — Red text only (no fill, used inline)
```
text-red-400 hover:text-red-600 text-sm transition-colors
```

**Rules:**
- All buttons: `rounded-lg` (8px radius). Never `rounded-full` or `rounded-xl`.
- Primary padding: `py-2.5 px-4` for standard, `py-3 px-6` for large CTAs (e.g., section-end call-to-action).
- Never use size variants inline — if you need a smaller button, reconsider whether it should be a text link instead.
- Icon buttons: `gap-2` between icon and label, icon always `h-4 w-4`.

### Cards

Single card style throughout.
```
bg-white rounded-xl border border-gray-200 p-6
```

- Padding: always `p-6`. Use `p-5` only for dense data panels (report metric cards).
- Radius: always `rounded-xl` (12px) for cards, `rounded-lg` (8px) for inset elements within cards.
- No shadows. The `border border-gray-200` on white against `bg-gray-50` is sufficient depth.
- Card headers with a bottom border: `px-6 py-4 border-b border-gray-200`.

### Badges and Status Chips

One shape, semantic colors.
```
inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {color}
```

For non-pill (flat) chips (criticality, category labels):
```
inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {color}
```

**Color mapping:**

| Semantic meaning | Classes |
|---|---|
| Compliant | `bg-green-100 text-green-700` |
| Partially compliant | `bg-yellow-100 text-yellow-700` |
| Non-compliant | `bg-red-100 text-red-700` |
| Analyzing / In progress | `bg-purple-100 text-purple-700` |
| Documents uploaded / Context gathered | `bg-blue-100 text-blue-700` |
| Questionnaire done | `bg-yellow-100 text-yellow-700` |
| Completed | `bg-green-100 text-green-700` |
| Error | `bg-red-100 text-red-700` |
| New / Created | `bg-gray-100 text-gray-700` |
| Navy branded chip (category, industry, code ref) | `bg-navy-100 text-brand` |
| Critical severity | `bg-red-100 text-red-700` |
| High severity | `bg-orange-100 text-orange-700` |
| Medium severity | `bg-yellow-100 text-yellow-700` |
| Low / Info | `bg-gray-100 text-gray-600` |

**Rule:** Always use `-100` backgrounds. Never `-50`. The `-50` tint was inconsistently used — standardised to `-100` for visible contrast.

### Form Inputs

All inputs share the same base style:
```
rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-navy-500 focus:ring-2 focus:ring-navy-100 outline-none transition bg-white
```

- Focus ring: `focus:border-navy-500 focus:ring-2 focus:ring-navy-100` — navy always, never indigo
- Textarea: same, add `resize-none` where height should be fixed
- Select: always include `bg-white` to prevent OS-default gray on some browsers
- Compact inputs (inside questionnaire cards): `px-3 py-2 text-xs focus:ring-1`

### Radio / Checkbox Selections (Card Style)

Used in context wizard, scope form, GRC scale.
```
inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 
hover:border-navy-300 cursor-pointer transition-colors 
has-[:checked]:border-brand has-[:checked]:bg-navy-50
```

- Use `has-[:checked]` CSS to drive selected state — no JavaScript class toggling where avoidable
- Where JS is needed (HTMX-loaded partials): toggle `border-brand` and `bg-navy-50`

### Tabs

```
py-3 px-1 text-sm font-medium border-b-2 transition-colors
Active:   border-brand text-brand
Inactive: border-transparent text-gray-500 hover:text-gray-700
```

Tab counter badges:
- Count (neutral): `bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs`
- Done (success): `bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs`
- Score: `bg-navy-100 text-brand px-2 py-0.5 rounded-full text-xs`

### Loading Spinners

All spinners use `text-brand`. No exceptions.

```html
<svg class="animate-spin h-5 w-5 text-brand" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
</svg>
```

Sizes: `h-5 w-5` standard, `h-6 w-6` for full-panel loading banners, `h-4 w-4` for inline button loading.

### Running State Banners

Used for analysis and desk review in-progress states.
```
flex items-center gap-4 p-4 rounded-lg bg-navy-50 border border-navy-200
```

Body text inside banners: `text-sm font-medium text-gray-900` for title, `text-xs text-gray-500` for subtitle. Never use colored text inside a colored banner — it compounds and reads as alarm.

### Navigation

```
bg-brand shadow-lg
```

- Logo icon: `bg-white/15 rounded-lg` — translucent white against navy
- Brand name: `text-white font-semibold text-lg`
- Subtitle: `text-navy-200 text-sm`

### Alerts and Validation Errors

```
p-4 rounded-lg bg-red-50 border border-red-200
```

- Error title: `text-sm font-medium text-red-900`
- Error body: `text-xs text-red-700`
- Inline validation summary: `rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700`

### Drop Zone (Document Upload)

```
border-2 border-dashed border-gray-300 rounded-lg p-8 text-center
cursor-pointer hover:border-navy-400 transition-colors
```

Drag active (via `style.css`): `border-color: #1e1e50; background-color: rgba(30, 30, 80, 0.04)`

### Progress Bars

```
w-full bg-gray-200 rounded-full h-2
  → fill: bg-brand h-2 rounded-full transition-all
```

Step progress bars (multi-step wizard): `h-1.5 rounded-full bg-brand` (active), `bg-gray-200` (inactive).

---

## 5. Spacing & Layout

### Scale
Stick to the 8px grid.

| Token | Value | Common use |
|---|---|---|
| `gap-2` | 8px | Tight icon+label gaps, badge groups |
| `gap-3` | 12px | Form option groups |
| `gap-4` | 16px | Standard flex/grid gaps |
| `gap-6` | 24px | Section spacing within a card |
| `space-y-4` | 16px | Question stacks |
| `space-y-5` | 20px | Form field stacks |
| `space-y-6` | 24px | Major section stacks within a form |
| `mb-6` | 24px | Card-to-card vertical spacing |
| `py-8` | 32px | Empty state padding |
| `py-16` | 64px | Full empty state (dashboard) |

### Container
- Max width: `max-w-7xl` for main content, `max-w-2xl` for centered forms (new assessment, login)
- Horizontal padding: `px-4 sm:px-6 lg:px-8`

### Card Padding
- Standard card body: `p-6`
- Dense data card: `p-5`
- Card header (with border): `px-6 py-4`
- Table cells: `px-4 py-3` (data), `px-6 py-3` (wider tables)

---

## 6. Elevation & Depth

**No shadows on cards.** The exception is the nav bar (`shadow-lg`) and the login card (`shadow-2xl`) — both intentional and isolated.

Depth hierarchy:
1. `bg-gray-50` page background
2. `bg-white border border-gray-200` cards
3. `bg-gray-50` inset sections within cards (table headers, section dividers)
4. `bg-navy-50` active/selected states

Never add `shadow-sm` or `shadow-md` to content cards — it makes the tool look like a consumer product.

---

## 7. HTMX Interaction Patterns

### Swap transitions (style.css)
```css
.htmx-swapping { opacity: 0; transition: opacity 200ms ease-out; }
.htmx-settling { opacity: 1; transition: opacity 200ms ease-in; }
```

### Loading indicators
- Use `hx-indicator="#spinner-id"` to target a specific `htmx-indicator` element
- Inline button spinners: wrap in `<span class="htmx-indicator">` inside the button
- Panel loading: full `htmx-indicator` div with centered spinner + optional text

### Polling
- Status polling: `hx-trigger="every 3s"` with `hx-swap="outerHTML"` — the partial replaces itself when complete
- Always include a terminal state (complete/error) that removes the polling trigger

---

## 8. Do's and Don'ts

### Do
- Use `text-brand` for all interactive links and active states
- Use `bg-navy-50` for all selected/active backgrounds
- Use `focus:border-navy-500 focus:ring-2 focus:ring-navy-100` on every input
- Use semantic `-100` badge backgrounds exclusively
- Use `rounded-xl` for cards, `rounded-lg` for buttons and inputs
- Keep `text-xs` to metadata, badges, and table headers only

### Don't
- Don't use indigo (`#6366f1`). It was the previous competing primary. It's gone.
- Don't add shadows to content cards — flat is intentional
- Don't use bold (700) for section headings — semibold (600) is the ceiling below page titles
- Don't use semantic colors (green/red/orange) for non-compliance-state UI elements
- Don't introduce a new color without a documented semantic reason
- Don't use `bg-{color}-50` for badges — always `-100` for visibility

---

## 9. Inspiration & Rationale

This system is adapted from Revolut's design language with deliberate modifications for B2B audit context:

| Revolut principle | CyberAssess adaptation |
|---|---|
| Near-black + white binary | Navy `#1e1e50` + white — same principle, warmer authority |
| Universal pill buttons (9999px) | `rounded-lg` — pill reads as consumer/banking; lg reads as professional tool |
| 136px display headings | `text-2xl` / `text-xl` — dashboard, not billboard |
| Zero shadows | Kept exactly — flat = confident |
| Rich semantic color system | Kept exactly — compliance has natural green/yellow/red semantics |
| Single primary action color | Kept exactly — navy only, no indigo contamination |
| Positive body letter-spacing | Deferred — Tailwind defaults are close enough |

The login page is the reference implementation. It uses `bg-brand-dark` as the full-bleed background with the white card centered — confident, dark, professional. All other pages should feel like they belong to the same tool as that login screen.
