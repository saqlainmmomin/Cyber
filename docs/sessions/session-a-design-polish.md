# Session A — Design System & Visual Polish

> **Runtime:** Sonnet 4.6
> **Parallel with:** Session B (Interaction & Feature UI), Session C (Backend Features)
> **Coordination file:** `docs/sessions/COORDINATION.md` — READ THIS FIRST

---

## Mission

You are responsible for the **visual layer** of CyberAssess. Your job is to:

1. Migrate from Tailwind CDN to a local Tailwind CLI build (prerequisite for dark mode)
2. Implement a complete dark mode system across every existing template
3. Improve visual hierarchy, cleanliness, and premium feel of every page
4. Add structural hooks (data attributes, include directives) for Session B's interaction layer

You own ALL existing template files, CSS, and Tailwind config. You do NOT touch Python files or `app.js`.

---

## Context

CyberAssess is a compliance gap assessment platform. Tech stack: FastAPI + Jinja2 + HTMX + Tailwind CSS (currently CDN). The design system is documented at `docs/design.md`. Read it — it defines every color, component, and spacing rule.

Key design principles (do not violate):
- **One signal per element** — color communicates meaning, not decoration
- **Flat confidence** — no drop shadows on content cards (only nav bar and login card)
- **Navy owns primary** — `#1e1e50` is the single primary. No indigo. No competing primaries.
- **Inter font** — `text-sm` (14px) minimum for body text. `text-xs` only for metadata/badges.

---

## Pre-read Required

Before starting any work, read these files to understand current state:

```
docs/sessions/COORDINATION.md          — contracts, file ownership, data attributes
docs/design.md                         — full design system
app/templates/base.html                — nav, structure
app/templates/pages/dashboard.html     — assessment list
app/templates/pages/login.html         — brand reference
app/templates/partials/section_questions.html    — most complex UI (questionnaire cards)
app/templates/partials/report_summary.html       — gap report view (~475 lines)
app/templates/partials/questionnaire_sections.html — section sidebar + content
app/templates/partials/questionnaire_tab.html    — context + screening + questionnaire container
app/templates/partials/scope_form.html
app/templates/partials/scope_complete.html
app/templates/partials/documents_tab.html
app/templates/partials/desk_review_running.html
app/templates/partials/screening_form.html
app/static/css/style.css
```

---

## Task 1: Tailwind CLI Migration

Replace the CDN play script with a local build. This is the foundation everything else depends on.

### Steps:

1. Create `package.json`:
```json
{
  "name": "cyberassess",
  "private": true,
  "scripts": {
    "css:build": "npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css --minify",
    "css:watch": "npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/tailwind.css --watch"
  },
  "devDependencies": {
    "tailwindcss": "^3.4"
  }
}
```

2. Create `tailwind.config.js`:
```js
module.exports = {
  darkMode: 'class',
  content: ['./app/templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f1f8', 100: '#d9dbed', 200: '#b3b7db', 300: '#8d93c9',
          400: '#676fb7', 500: '#4a5296', 600: '#3a4178', 700: '#2b315a',
          800: '#1e1e50', 900: '#1a1a40', 950: '#111130',
        },
        brand: { DEFAULT: '#1e1e50', light: '#2b315a', dark: '#141438' },
      },
    },
  },
  plugins: [],
}
```

3. Create `app/static/css/input.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

4. Run `npm install && npm run css:build`

5. In `base.html`:
   - Remove the `<script src="https://cdn.tailwindcss.com"></script>` tag
   - Remove the inline `<script>tailwind.config = { ... }</script>` block
   - Add `<link rel="stylesheet" href="/static/css/tailwind.css">` (before the existing style.css link)

6. Add to `.gitignore`: `node_modules/` and `app/static/css/tailwind.css` (generated file)

7. Verify the app still looks identical by running `npm run css:build` and loading the page.

---

## Task 2: Dark Mode Toggle

Add a toggle button in the nav bar of `base.html`.

### Implementation:

In the nav's right-side `<div class="flex items-center gap-4">`, add before the "Compliance Platform" span:

```html
<button onclick="toggleTheme()" class="p-1.5 rounded-lg hover:bg-white/10 transition-colors" aria-label="Toggle dark mode">
  <svg class="h-5 w-5 text-navy-200 dark:hidden" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"/>
  </svg>
  <svg class="h-5 w-5 text-navy-200 hidden dark:block" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"/>
  </svg>
</button>
```

Add this inline script in `base.html` inside `<head>` (before any render to prevent FOUC):
```html
<script>
  if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
</script>
```

Add this before closing `</body>`:
```html
<script>
  function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
  }
</script>
```

Update `<body>` tag:
```html
<body class="h-full bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100" hx-boost="true">
```

---

## Task 3: Dark Mode — All Templates

Apply `dark:` variants to every existing template file. Use these mappings consistently:

### Token Mapping (memorize this — apply everywhere)

| Surface | Light | Dark |
|---|---|---|
| Page bg | `bg-gray-50` | `dark:bg-gray-950` |
| Card | `bg-white border-gray-200` | `dark:bg-gray-900 dark:border-gray-800` |
| Card inset / table header | `bg-gray-50` | `dark:bg-gray-800/50` |
| Nav bar | `bg-brand` | `dark:bg-gray-950 dark:border-b dark:border-gray-800` |
| Nav logo bg | `bg-white/15` | `dark:bg-white/10` |
| Nav subtitle | `text-navy-200` | `dark:text-gray-400` |
| Primary btn | `bg-brand hover:bg-brand-light` | `dark:bg-navy-600 dark:hover:bg-navy-500` |
| Secondary btn | `border-gray-300 text-gray-600 hover:bg-gray-50` | `dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800` |
| Destructive btn | `text-red-400 hover:text-red-600` | `dark:text-red-500 dark:hover:text-red-400` |
| Input | `bg-white border-gray-300` | `dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100` |
| Focus ring | `focus:border-navy-500 focus:ring-navy-100` | `dark:focus:border-navy-400 dark:focus:ring-navy-900` |
| Drop zone | `border-gray-300 hover:border-navy-400` | `dark:border-gray-700 dark:hover:border-navy-500` |
| Running banner | `bg-navy-50 border-navy-200` | `dark:bg-navy-900/40 dark:border-navy-800` |
| Error alert | `bg-red-50 border-red-200` | `dark:bg-red-950 dark:border-red-800` |
| Tab active | `border-brand text-brand` | `dark:border-navy-400 dark:text-navy-300` |
| Tab inactive | `text-gray-500` | `dark:text-gray-400` |
| Text primary | `text-gray-900` | `dark:text-gray-100` |
| Text body | `text-gray-700` | `dark:text-gray-300` |
| Text supporting | `text-gray-500` | `dark:text-gray-400` |
| Text metadata | `text-gray-400` | `dark:text-gray-500` |
| Interactive text | `text-brand` | `dark:text-navy-300` |
| Divider | `divide-gray-200` | `dark:divide-gray-800` |
| Border subtle | `border-gray-100` | `dark:border-gray-800` |
| Hover row | `hover:bg-gray-50` | `dark:hover:bg-gray-800/50` |
| Progress bar track | `bg-gray-200` | `dark:bg-gray-800` |
| Progress bar fill | `bg-brand` | `dark:bg-navy-500` |

### Status badge mapping:

Every status badge follows this pattern:
- Light: `bg-{color}-100 text-{color}-700`
- Dark: `dark:bg-{color}-900/40 dark:text-{color}-400`

Apply to green (compliant), yellow (partial), red (non-compliant), blue (planned), orange (high risk), purple (screening/inferred), gray (neutral).

### Login page exception:

The login page uses `bg-brand-dark` full bleed — this is already dark. Only add dark mode to the white card: `dark:bg-gray-900 dark:border dark:border-gray-800`. The surrounding dark navy background stays the same.

### Template-by-template notes:

- **dashboard.html** — replace the `<table>` with a card list (see Task 4). Remove `shadow-sm` from the current table container.
- **section_questions.html** — this is the biggest template (~438 lines). Be methodical. Every `bg-white`, `border-gray-*`, `text-gray-*`, `bg-{color}-50` needs a dark pair.
- **report_summary.html** — ~475 lines. The SVG gauge uses inline `fill` and `stroke` attributes that can't use Tailwind dark: classes. Leave the SVGs as-is — they use computed hex colors that work on both backgrounds because the card background changes.
- **screening_form.html** — uses purple accent (`bg-purple-100`, `text-purple-700`). Dark equivalent: `dark:bg-purple-900/40 dark:text-purple-400`.

---

## Task 4: Dashboard Card List Redesign

Replace the HTML `<table>` in `dashboard.html` with a card list. The table reads as "admin panel."

Replace the `{% if assessments %}` block's table with:

```html
<div class="space-y-3">
  {% for a in assessments %}
  <a href="/assessments/{{ a.id }}"
     class="block bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:border-navy-300 dark:hover:border-navy-600 transition-colors group"
     data-assessment-card>
    <div class="flex items-center justify-between">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-3">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 group-hover:text-brand dark:group-hover:text-navy-300 truncate">{{ a.company_name }}</h3>
          {% include "components/status_badge.html" %}
        </div>
        <div class="flex items-center gap-3 mt-1.5">
          <span class="text-xs text-gray-500 dark:text-gray-400">{{ a.industry | replace("_", " ") | title }}</span>
          <span class="text-xs text-gray-400 dark:text-gray-500">{{ a.created_at.strftime('%d %b %Y') }}</span>
          {% if a.description %}
          <span class="text-xs text-gray-400 dark:text-gray-500 truncate max-w-xs">{{ a.description }}</span>
          {% endif %}
        </div>
      </div>
      <svg class="h-4 w-4 text-gray-300 dark:text-gray-600 flex-shrink-0 ml-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5"/>
      </svg>
    </div>
  </a>
  {% endfor %}
</div>
```

Note: `data-assessment-card` attribute is required — Session B's JS uses it for search/filter (see Contract 4 in COORDINATION.md).

Remove the delete button from dashboard rows. It's visual clutter for a rare destructive action.

---

## Task 5: Questionnaire Visual Improvements

In `section_questions.html`:

### 5a. Badge simplification

Current question cards show up to 4 badges (source, confidence, criticality, tier). Reduce to max 2 in the header row:
- Always show: **criticality** badge
- Show ONE source badge: tier (deep/light) OR source (document/inferred) — not both
- Move confidence badge into the evidence panel where it belongs

### 5b. Evidence panel unification

Replace the three inconsistent evidence styles with one:
```html
<div class="mt-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
```

Source quotes use a left accent:
```html
<div class="pl-3 border-l-2 border-navy-200 dark:border-navy-700">
```

### 5c. GRC radio sizing

On standard/deep tier cards, increase radio options from `px-3 py-1.5 text-xs` to `px-3.5 py-2 text-sm`. Keep `text-xs` on light-tier compact cards only.

### 5d. Sticky section header

Make the section title + progress counter sticky:
```html
<div class="sticky top-0 z-10 bg-white dark:bg-gray-900 -mx-1 px-1 pb-3 mb-4 border-b border-gray-100 dark:border-gray-800" data-section-header>
```

Add `data-section-header` attribute (Contract 4 — Session B may enhance this).

---

## Task 6: Report Summary Improvements

In `report_summary.html`:

### 6a. Score gauge enlargement

Change the overall score gauge from `w-24 h-24` to `w-28 h-28`. Make the score card `col-span-2` on the 4-column hero grid (`grid-cols-2 md:grid-cols-4` → keep grid, but let score card span 2 on mobile).

### 6b. Grouped findings

Replace the flat `<table>` in the detailed findings section (section G) with collapsible chapter groups:

```html
<div class="space-y-3">
  {% for chapter_key, chapter_items in gap_items_by_chapter.items() %}
  <details class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl overflow-hidden" open>
    <summary class="px-5 py-3 bg-gray-50 dark:bg-gray-800/50 flex items-center justify-between cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
      <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ chapter_key | replace("_", " ") | title }}</span>
      <div class="flex items-center gap-3">
        <!-- status count chips -->
        <svg class="h-4 w-4 text-gray-400 details-chevron transition-transform" ...></svg>
      </div>
    </summary>
    <div class="divide-y divide-gray-100 dark:divide-gray-800">
      {% for item in chapter_items %}
      <div class="px-5 py-4">
        <!-- finding row: requirement title, status badge, risk, gap description -->
        <div id="remediation-{{ item.id }}">
          {% include "partials/remediation_panel.html" ignore missing %}
        </div>
      </div>
      {% endfor %}
    </div>
  </details>
  {% endfor %}
</div>
```

**IMPORTANT:** This requires the router (`app/routers/reports.py`) to group gap_items by chapter and pass `gap_items_by_chapter` as a dict to the template context. Since you don't own the router (Session C does), document this requirement in `docs/sessions/pending-changes-session-a.md`:

```
PENDING: reports.py must pass `gap_items_by_chapter` dict to report_summary.html context.
Structure: { "chapter_name": [gap_item_1, gap_item_2, ...], ... }
Currently passes flat `gap_items` list.
```

Until Session C makes this change, keep the flat list rendering as a fallback:
```html
{% if gap_items_by_chapter is defined %}
  <!-- grouped view -->
{% else %}
  <!-- existing flat table view (with dark mode applied) -->
{% endif %}
```

### 6c. Include hooks for Session B

Add after the hero metrics grid:
```html
<div id="remediation-summary-area">
  {% include "partials/remediation_summary.html" ignore missing %}
</div>
```

Add a "Compare" button (shown conditionally) in the report header:
```html
{% if comparable_assessments %}
<a href="/assessments/{{ assessment_id }}/compare/{{ comparable_assessments[0].id }}"
   class="text-xs text-brand dark:text-navy-300 hover:text-brand-light font-medium">
  Compare with previous
</a>
{% endif %}
```

Add a review banner area at the top:
```html
<div id="review-banner">
  {% if review_status == 'approved' %}
  <div class="mb-4 px-4 py-3 rounded-lg bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 flex items-center gap-2">
    <svg class="h-4 w-4 text-green-600 dark:text-green-400" ...><!-- check icon --></svg>
    <span class="text-sm text-green-700 dark:text-green-400 font-medium">Manager Reviewed</span>
    {% if reviewed_by %}<span class="text-xs text-green-600 dark:text-green-500">by {{ reviewed_by }} · {{ reviewed_at.strftime('%d %b %Y') }}</span>{% endif %}
  </div>
  {% elif review_status == 'under_review' %}
  <div class="mb-4 px-4 py-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-800 flex items-center justify-between">
    <span class="text-sm text-yellow-700 dark:text-yellow-400 font-medium">Under Review — exports disabled until approved</span>
    <a href="/assessments/{{ assessment_id }}/review" class="text-xs text-brand dark:text-navy-300 font-medium">Open Review Queue →</a>
  </div>
  {% endif %}
</div>
```

### 6d. Copy button on executive summary

Add `data-copy-target="executive-summary"` to the executive summary text div:
```html
<div class="flex items-center justify-between mb-3">
  <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Executive Summary</h3>
  <button class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          data-copy-trigger="executive-summary" aria-label="Copy executive summary">
    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184"/>
    </svg>
  </button>
</div>
<div class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line" data-copy-target="executive-summary">
  {{ report.executive_summary }}
</div>
```

---

## Task 7: Empty States

Standardize all empty states to the same pattern. Apply dark mode.

```html
<div class="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
  <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600 mb-4" ...><!-- contextual icon --></svg>
  <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ heading }}</h3>
  <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ description }}</p>
  {% if cta %}
  <a href="{{ cta_href }}" class="mt-4 inline-flex items-center gap-2 bg-brand dark:bg-navy-600 hover:bg-brand-light dark:hover:bg-navy-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
    {{ cta_text }}
  </a>
  {% endif %}
</div>
```

Apply to: dashboard (no assessments), documents tab (no documents uploaded), questionnaire (not started), analysis (not yet run). Icons: shield-document, cloud-upload, clipboard, chart-bar respectively.

---

## Task 8: Breadcrumb Navigation

Add to assessment detail pages (all partials that render inside an assessment). In `base.html` or the assessment detail container (whichever template renders the assessment tabs), add above the tab bar:

```html
{% if assessment is defined %}
<nav class="text-xs text-gray-400 dark:text-gray-500 mb-2">
  <a href="/" class="hover:text-brand dark:hover:text-navy-300 transition-colors">Assessments</a>
  <span class="mx-1.5">/</span>
  <span class="text-gray-600 dark:text-gray-300">{{ assessment.company_name }}</span>
</nav>
{% endif %}
```

---

## Task 9: CSS Updates

In `app/static/css/style.css`, add:

```css
/* Spinner delay — prevents flash on fast loads */
.htmx-indicator {
  opacity: 0;
  transition: opacity 150ms ease-in 200ms;
}
.htmx-request .htmx-indicator,
.htmx-request.htmx-indicator {
  opacity: 1;
}

/* Details chevron rotation */
details[open] > summary .details-chevron {
  transform: rotate(180deg);
}

/* Dark mode scrollbar */
.dark ::-webkit-scrollbar { width: 8px; }
.dark ::-webkit-scrollbar-track { background: #1a1a2e; }
.dark ::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }

/* Drag-over state for dark mode */
.dark .drag-over {
  border-color: #676fb7 !important;
  background-color: rgba(103, 111, 183, 0.08) !important;
}
```

---

## Task 10: Data Attributes (Contract 4)

Add these `data-*` attributes throughout templates per the coordination file:

- `data-assessment-card` on each assessment card in dashboard
- `data-save-indicator` on a `<span>` below the questionnaire save button
- `data-section-header` on the sticky section title div
- `data-copy-target="executive-summary"` on the exec summary text
- `data-copy-target="requirement-id"` on requirement ID `<span>` elements in report
- `data-shortcut-scope="questionnaire"` on the questionnaire form container
- `data-shortcut-scope="dashboard"` on the dashboard content container
- `data-question-index="{{ loop.index }}"` on each question card in section_questions.html
- `data-collapsible-section` on each section in questionnaire_sections.html

---

## Task 11: Design System Documentation

Update `docs/design.md` to add:

1. A new section "## 10. Dark Mode" with the full token mapping table
2. A note under each existing color section about dark equivalents
3. Update component examples to show `dark:` variants

---

## Verification

After completing all tasks:
1. Run `npm run css:build`
2. Start the app: `uvicorn app.main:app --reload`
3. Check every page in both light and dark mode
4. Verify no text is invisible against its background in dark mode
5. Verify all status badge colors remain distinguishable
6. Verify login page renders correctly
7. Take a screenshot of each major page in dark mode for Session B reference

---

## What NOT to do

- Do NOT edit `app.js` (Session B owns it)
- Do NOT edit any Python file (Session C owns them)
- Do NOT create new template files (Session B creates new partials)
- Do NOT add JavaScript behavior beyond the dark mode toggle — Session B handles all interaction
- Do NOT add shadows to content cards
- Do NOT introduce new colors without semantic justification
- Do NOT use CSS custom properties — pure Tailwind utilities only
