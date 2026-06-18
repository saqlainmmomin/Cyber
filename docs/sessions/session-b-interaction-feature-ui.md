# Session B — Interaction Layer & Feature UI

> **Runtime:** Sonnet 4.6
> **Parallel with:** Session A (Design & Polish), Session C (Backend Features)
> **Coordination file:** `docs/sessions/COORDINATION.md` — READ THIS FIRST

---

## Mission

You are responsible for the **interaction layer** and **new feature templates**. Your job is to:

1. Build quality-of-life JS features (toast, keyboard shortcuts, copy, search, save indicator, collapsible sections)
2. Create NEW template files for the backend features Session C is building (remediation, review, comparison)
3. Wire everything together via HTMX and vanilla JS

You own `app/static/js/app.js` and all NEW template files. You do NOT touch existing templates (Session A owns them) or Python files (Session C owns them).

---

## Context

CyberAssess is a compliance gap assessment platform. Tech stack: FastAPI + Jinja2 + HTMX + Tailwind CSS. Read the full design system at `docs/design.md`.

Session A is applying dark mode to all existing templates. Your new templates MUST follow the dark mode patterns documented in `COORDINATION.md` Contract 1. Session C is building backend endpoints whose contracts are in `COORDINATION.md` Contract 3.

---

## Pre-read Required

```
docs/sessions/COORDINATION.md          — contracts, file ownership, endpoint specs
docs/design.md                         — design system
app/static/js/app.js                   — current JS (your primary file)
app/templates/base.html                — structure (read only — Session A owns)
app/templates/partials/report_summary.html — where your partials render (read only)
app/templates/partials/section_questions.html — questionnaire cards (read only)
```

---

## Dark Mode Classes Reference

Every new template you create MUST use these patterns (from COORDINATION.md Contract 1):

```
Card:           bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 rounded-xl
Card inset:     bg-gray-50 dark:bg-gray-800/50
Text primary:   text-gray-900 dark:text-gray-100
Text body:      text-gray-700 dark:text-gray-300
Text support:   text-gray-500 dark:text-gray-400
Text metadata:  text-gray-400 dark:text-gray-500
Interactive:    text-brand dark:text-navy-300
Primary btn:    bg-brand dark:bg-navy-600 hover:bg-brand-light dark:hover:bg-navy-500 text-white
Secondary btn:  border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300
Input:          bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100
Focus:          focus:border-navy-500 dark:focus:border-navy-400 focus:ring-navy-100 dark:focus:ring-navy-900
Divider:        divide-gray-200 dark:divide-gray-800
Status badge:   bg-{color}-100 dark:bg-{color}-900/40 text-{color}-700 dark:text-{color}-400
```

---

## Task 1: Toast Notification System

Build a lightweight toast system in `app.js`. No external library. No template changes needed — the container is created dynamically via JS.

```js
// Toast notification system
const CyberToast = {
  container: null,
  
  init() {
    this.container = document.createElement('div');
    this.container.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(this.container);
  },

  show(message, type = 'success') {
    if (!this.container) this.init();
    const colors = {
      success: 'bg-green-800 text-green-100 border-green-700',
      error: 'bg-red-900 text-red-100 border-red-800',
      info: 'bg-gray-800 text-gray-100 border-gray-700',
    };
    const icons = {
      success: '✓',
      error: '✕',
      info: 'ℹ',
    };
    const toast = document.createElement('div');
    toast.className = `${colors[type] || colors.info} pointer-events-auto px-4 py-3 rounded-lg text-sm border shadow-lg flex items-center gap-2 transform translate-y-2 opacity-0 transition-all duration-200 max-w-sm`;
    toast.innerHTML = `<span class="font-medium">${icons[type] || ''}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    });
    setTimeout(() => {
      toast.classList.add('translate-y-2', 'opacity-0');
      setTimeout(() => toast.remove(), 200);
    }, 3000);
  }
};

// Listen for X-Toast-Message header from HTMX responses
document.body.addEventListener('htmx:afterSwap', (event) => {
  const msg = event.detail.xhr?.getResponseHeader('X-Toast-Message');
  if (msg) {
    const type = event.detail.xhr.getResponseHeader('X-Toast-Type') || 'success';
    CyberToast.show(decodeURIComponent(msg), type);
  }
});

// Also listen for htmx:responseError for automatic error toasts
document.body.addEventListener('htmx:responseError', (event) => {
  CyberToast.show('Something went wrong. Please try again.', 'error');
});
```

This hooks into the `X-Toast-Message` / `X-Toast-Type` headers that Session C adds to backend responses (Contract 5).

---

## Task 2: Copy-to-Clipboard Utility

Add to `app.js`. Hooks onto `data-copy-trigger` attributes that Session A places in templates.

```js
// Copy-to-clipboard
document.addEventListener('click', (e) => {
  const trigger = e.target.closest('[data-copy-trigger]');
  if (!trigger) return;
  
  const targetId = trigger.dataset.copyTrigger;
  const target = document.querySelector(`[data-copy-target="${targetId}"]`);
  if (!target) return;
  
  const text = target.textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    CyberToast.show('Copied to clipboard', 'info');
  }).catch(() => {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    CyberToast.show('Copied to clipboard', 'info');
  });
});
```

---

## Task 3: Progress Save Indicator

Show "Saved at HH:MM" after questionnaire section saves.

```js
// Save indicator
document.body.addEventListener('htmx:afterSwap', (event) => {
  const indicator = document.querySelector('[data-save-indicator]');
  if (!indicator) return;
  
  // Check if the swap was a questionnaire save
  const target = event.detail.target;
  if (target && (target.id === 'section-content' || target.closest('[data-questionnaire-form]'))) {
    const now = new Date();
    indicator.textContent = `Saved ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    indicator.classList.remove('hidden');
    indicator.classList.add('text-green-600', 'dark:text-green-400');
    setTimeout(() => {
      indicator.classList.remove('text-green-600', 'dark:text-green-400');
      indicator.classList.add('text-gray-400', 'dark:text-gray-500');
    }, 2000);
  }
});
```

---

## Task 4: Dashboard Search/Filter

Client-side text filter for assessment cards. Session A adds `data-assessment-card` to each card.

```js
// Dashboard search filter
document.addEventListener('input', (e) => {
  if (!e.target.matches('[data-filter-input]')) return;
  const query = e.target.value.toLowerCase();
  document.querySelectorAll('[data-assessment-card]').forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(query) ? '' : 'none';
  });
});
```

Session A adds the filter input above the assessment list. If Session A hasn't added it, you may add the input HTML inside a small `<div>` that you inject via JS on page load:

```js
// Inject search input if dashboard has assessment cards
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('[data-assessment-card]');
  if (cards.length > 3) {
    const container = cards[0]?.parentElement;
    if (container) {
      const searchDiv = document.createElement('div');
      searchDiv.className = 'mb-4';
      searchDiv.innerHTML = `<input type="text" data-filter-input placeholder="Filter assessments..." 
        class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 focus:ring-2 focus:ring-navy-100 dark:focus:ring-navy-900 outline-none transition placeholder-gray-400 dark:placeholder-gray-500">`;
      container.parentElement.insertBefore(searchDiv, container);
    }
  }
});
```

---

## Task 5: Keyboard Shortcuts

Implement a lightweight keyboard shortcut system.

```js
// Keyboard shortcuts
const Shortcuts = {
  enabled: true,
  
  init() {
    document.addEventListener('keydown', (e) => {
      if (!this.enabled) return;
      // Don't trigger when typing in inputs
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
      if (e.target.isContentEditable) return;
      
      const key = e.key.toLowerCase();
      const scope = document.querySelector('[data-shortcut-scope]')?.dataset.shortcutScope;
      
      // Global shortcuts
      if (key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        this.showHelp();
        return;
      }
      
      // Dashboard shortcuts
      if (scope === 'dashboard') {
        if (key === 'n') {
          e.preventDefault();
          window.location.href = '/assessments/new';
        }
      }
      
      // Questionnaire shortcuts
      if (scope === 'questionnaire') {
        if (key === 'j' || key === 'k') {
          e.preventDefault();
          this.navigateQuestions(key === 'j' ? 1 : -1);
        }
        if (['1', '2', '3', '4', '5'].includes(key)) {
          e.preventDefault();
          this.selectOption(parseInt(key));
        }
        if (key === 's' && !e.ctrlKey && !e.metaKey) {
          e.preventDefault();
          const form = document.querySelector('[data-questionnaire-form]');
          if (form) htmx.trigger(form, 'submit');
        }
      }
    });
  },
  
  currentQuestionIndex: -1,
  
  navigateQuestions(direction) {
    const cards = Array.from(document.querySelectorAll('[data-question-index]'));
    if (!cards.length) return;
    
    this.currentQuestionIndex = Math.max(0, Math.min(cards.length - 1, this.currentQuestionIndex + direction));
    const target = cards[this.currentQuestionIndex];
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // Visual focus indicator
    cards.forEach(c => c.classList.remove('ring-2', 'ring-navy-300', 'dark:ring-navy-600'));
    target.classList.add('ring-2', 'ring-navy-300', 'dark:ring-navy-600');
  },
  
  selectOption(num) {
    const cards = document.querySelectorAll('[data-question-index]');
    if (this.currentQuestionIndex < 0 || this.currentQuestionIndex >= cards.length) return;
    const card = cards[this.currentQuestionIndex];
    const radios = card.querySelectorAll('input[type="radio"]');
    if (radios[num - 1]) {
      radios[num - 1].checked = true;
      radios[num - 1].dispatchEvent(new Event('change', { bubbles: true }));
    }
  },
  
  showHelp() {
    const existing = document.getElementById('shortcut-help-modal');
    if (existing) { existing.remove(); return; }
    
    const modal = document.createElement('div');
    modal.id = 'shortcut-help-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
      <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 max-w-sm w-full mx-4 shadow-xl">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">Keyboard Shortcuts</h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Show this help</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">?</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">New assessment</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">n</kbd></div>
          <hr class="border-gray-100 dark:border-gray-800">
          <p class="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wide">Questionnaire</p>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Next question</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">j</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Previous question</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">k</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Select option 1–5</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">1-5</kbd></div>
          <div class="flex justify-between"><span class="text-gray-500 dark:text-gray-400">Save section</span><kbd class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono text-gray-700 dark:text-gray-300">s</kbd></div>
        </div>
        <button onclick="this.closest('#shortcut-help-modal').remove()" class="mt-4 w-full text-center text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">Press ? or click to close</button>
      </div>`;
    document.body.appendChild(modal);
  }
};

Shortcuts.init();
```

---

## Task 6: Collapsible Sections with localStorage

Persist questionnaire section collapsed state.

```js
// Collapsible sections with persistence
document.addEventListener('click', (e) => {
  const section = e.target.closest('[data-collapsible-section]');
  if (!section) return;
  
  const sectionId = section.dataset.collapsibleSection;
  const assessmentId = section.closest('[data-assessment-id]')?.dataset.assessmentId;
  if (!assessmentId || !sectionId) return;
  
  const key = `collapsed_${assessmentId}`;
  const collapsed = JSON.parse(localStorage.getItem(key) || '[]');
  
  if (collapsed.includes(sectionId)) {
    collapsed.splice(collapsed.indexOf(sectionId), 1);
  } else {
    collapsed.push(sectionId);
  }
  localStorage.setItem(key, JSON.stringify(collapsed));
});

// Restore collapsed state on HTMX swap
document.body.addEventListener('htmx:afterSettle', () => {
  const container = document.querySelector('[data-assessment-id]');
  if (!container) return;
  const key = `collapsed_${container.dataset.assessmentId}`;
  const collapsed = JSON.parse(localStorage.getItem(key) || '[]');
  collapsed.forEach(id => {
    const section = document.querySelector(`[data-collapsible-section="${id}"]`);
    if (section) {
      const details = section.querySelector('details');
      if (details) details.removeAttribute('open');
    }
  });
});
```

---

## Task 7: Status Timeline Component

Create `app/templates/partials/status_timeline.html`:

```html
{# Assessment status timeline — rendered via {% include %} from assessment detail #}
{# Expects: timeline_steps list of (label, completed) tuples #}
{% if timeline_steps is defined %}
<div class="flex items-center gap-1 text-xs mb-4">
  {% for label, done in timeline_steps %}
  <div class="flex items-center gap-1.5">
    {% if done %}
    <span class="w-2 h-2 rounded-full bg-green-500 flex-shrink-0"></span>
    <span class="text-gray-700 dark:text-gray-300 font-medium">{{ label }}</span>
    {% else %}
    <span class="w-2 h-2 rounded-full bg-gray-300 dark:bg-gray-600 flex-shrink-0"></span>
    <span class="text-gray-400 dark:text-gray-500">{{ label }}</span>
    {% endif %}
  </div>
  {% if not loop.last %}
  <span class="w-5 h-px bg-gray-300 dark:bg-gray-700 flex-shrink-0"></span>
  {% endif %}
  {% endfor %}
</div>
{% endif %}
```

**Note:** The `timeline_steps` variable must be computed by the router and passed to the template context. Document this for Session C in `docs/sessions/pending-changes-session-b.md`:

```
PENDING: web.py assessment detail route must pass `timeline_steps` to context.
Compute as:
timeline_steps = [
    ('Scope', assessment.scope_answers is not None),
    ('Documents', bool(documents)),
    ('Desk Review', assessment.desk_review_status == 'completed'),
    ('Questionnaire', assessment.status in ('questionnaire_done', 'analyzing', 'completed')),
    ('Analysis', assessment.status == 'completed'),
]
```

---

## Task 8: Remediation Panel

Create `app/templates/partials/remediation_panel.html`:

This renders inside each finding card in report_summary.html. Session A adds the include hook.

```html
{# Remediation tracking panel for a single gap item #}
{# Expects: item (GapItem with remediation fields), assessment_id #}
{% if item is defined and item.remediation_status is defined %}
<details class="mt-3 border-t border-gray-100 dark:border-gray-800 pt-3">
  <summary class="flex items-center justify-between cursor-pointer select-none text-xs">
    <div class="flex items-center gap-2">
      <span class="font-medium text-gray-600 dark:text-gray-400">Remediation</span>
      {% set rem_colors = {
        'open': 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400',
        'in_progress': 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400',
        'closed': 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400',
        'accepted_risk': 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
      } %}
      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {{ rem_colors.get(item.remediation_status, rem_colors.open) }}">
        {{ item.remediation_status | replace('_', ' ') | title }}
      </span>
    </div>
    {% if item.remediation_owner %}
    <span class="text-gray-400 dark:text-gray-500">{{ item.remediation_owner }}</span>
    {% endif %}
  </summary>
  
  <form class="mt-3 space-y-3"
        hx-patch="/api/assessments/{{ assessment_id }}/gap-items/{{ item.id }}/remediation"
        hx-target="closest details"
        hx-swap="outerHTML">
    
    <div class="grid grid-cols-3 gap-3">
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Status</label>
        <select name="remediation_status"
                class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 focus:ring-1 focus:ring-navy-100 dark:focus:ring-navy-900 outline-none">
          {% for val, label in [('open', 'Open'), ('in_progress', 'In Progress'), ('closed', 'Closed'), ('accepted_risk', 'Accepted Risk')] %}
          <option value="{{ val }}" {% if item.remediation_status == val %}selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
      </div>
      
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Owner</label>
        <input type="text" name="remediation_owner" value="{{ item.remediation_owner or '' }}"
               placeholder="Assign owner..."
               class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 focus:ring-1 focus:ring-navy-100 dark:focus:ring-navy-900 outline-none">
      </div>
      
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Target Date</label>
        <input type="date" name="remediation_target_date"
               value="{{ item.remediation_target_date.strftime('%Y-%m-%d') if item.remediation_target_date else '' }}"
               class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 focus:ring-1 focus:ring-navy-100 dark:focus:ring-navy-900 outline-none">
      </div>
    </div>
    
    <div>
      <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Notes</label>
      <textarea name="remediation_notes" rows="2" placeholder="Progress notes, blockers, decisions..."
                class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 focus:ring-1 focus:ring-navy-100 dark:focus:ring-navy-900 outline-none resize-none">{{ item.remediation_notes or '' }}</textarea>
    </div>
    
    <div class="flex justify-end">
      <button type="submit"
              class="bg-brand dark:bg-navy-600 hover:bg-brand-light dark:hover:bg-navy-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors inline-flex items-center gap-1.5">
        Save
        <span class="htmx-indicator">
          <svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
        </span>
      </button>
    </div>
  </form>
</details>
{% endif %}
```

Also create `app/templates/partials/remediation_summary.html`:

```html
{# Remediation progress summary — rendered at top of report page #}
{# Expects: remediation_counts dict with open, in_progress, closed, accepted_risk, total #}
{% if remediation_counts is defined and remediation_counts.total > 0 %}
<div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 mb-6">
  <div class="flex items-center justify-between mb-3">
    <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Remediation Progress</h3>
    <span class="text-xs text-gray-400 dark:text-gray-500">{{ remediation_counts.closed }} of {{ remediation_counts.total }} closed</span>
  </div>
  
  {# Stacked progress bar #}
  {% set total = remediation_counts.total %}
  {% set closed_pct = ((remediation_counts.closed / total) * 100) | round(1) %}
  {% set progress_pct = ((remediation_counts.in_progress / total) * 100) | round(1) %}
  {% set risk_pct = ((remediation_counts.accepted_risk / total) * 100) | round(1) %}
  {% set open_pct = ((remediation_counts.open / total) * 100) | round(1) %}
  <div class="flex h-3 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800 mb-3">
    {% if closed_pct > 0 %}<div class="bg-green-500 transition-all" style="width: {{ closed_pct }}%"></div>{% endif %}
    {% if progress_pct > 0 %}<div class="bg-yellow-400 transition-all" style="width: {{ progress_pct }}%"></div>{% endif %}
    {% if risk_pct > 0 %}<div class="bg-gray-400 transition-all" style="width: {{ risk_pct }}%"></div>{% endif %}
    {% if open_pct > 0 %}<div class="bg-red-400 transition-all" style="width: {{ open_pct }}%"></div>{% endif %}
  </div>
  
  <div class="flex items-center gap-4 text-xs">
    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-green-500"></span><span class="text-gray-600 dark:text-gray-400">Closed ({{ remediation_counts.closed }})</span></span>
    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-yellow-400"></span><span class="text-gray-600 dark:text-gray-400">In Progress ({{ remediation_counts.in_progress }})</span></span>
    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-gray-400"></span><span class="text-gray-600 dark:text-gray-400">Accepted Risk ({{ remediation_counts.accepted_risk }})</span></span>
    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-red-400"></span><span class="text-gray-600 dark:text-gray-400">Open ({{ remediation_counts.open }})</span></span>
  </div>
</div>
{% endif %}
```

---

## Task 9: Review Queue Page

Create `app/templates/pages/review.html`:

```html
{% extends "base.html" %}
{% block title %}Review — {{ assessment.company_name }}{% endblock %}

{% block content %}
<nav class="text-xs text-gray-400 dark:text-gray-500 mb-2">
  <a href="/" class="hover:text-brand dark:hover:text-navy-300 transition-colors">Assessments</a>
  <span class="mx-1.5">/</span>
  <a href="/assessments/{{ assessment.id }}" class="hover:text-brand dark:hover:text-navy-300 transition-colors">{{ assessment.company_name }}</a>
  <span class="mx-1.5">/</span>
  <span class="text-gray-600 dark:text-gray-300">Review</span>
</nav>

<div class="flex items-center justify-between mb-6">
  <div>
    <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Review Queue</h1>
    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ assessment.company_name }} — review AI findings before report release</p>
  </div>
  <div class="flex items-center gap-3">
    {% if draft_count == 0 and assessment.review_status != 'approved' %}
    <form hx-post="/api/assessments/{{ assessment.id }}/review/approve" hx-swap="none">
      <input type="hidden" name="reviewer_name" value="{{ reviewer_name or '' }}">
      <button type="submit"
              class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors inline-flex items-center gap-2">
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        Approve for Release
      </button>
    </form>
    {% elif assessment.review_status == 'approved' %}
    <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 text-sm font-medium">
      ✓ Approved
    </span>
    {% endif %}
  </div>
</div>

{# Filter bar #}
{% include "partials/review_filter_bar.html" %}

{# Finding cards #}
<div class="space-y-4" id="review-findings-list">
  {% for item in gap_items %}
  {% include "partials/review_finding_card.html" %}
  {% endfor %}
</div>

{% if not gap_items %}
<div class="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
  <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
  </svg>
  <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">No findings to review</h3>
  <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Run the gap analysis first to generate findings.</p>
</div>
{% endif %}
{% endblock %}
```

Create `app/templates/partials/review_filter_bar.html`:

```html
{# Review queue filter bar #}
<div class="flex items-center gap-2 mb-4 text-xs">
  <button class="px-3 py-1.5 rounded-lg font-medium transition-colors bg-navy-50 dark:bg-navy-900/40 text-brand dark:text-navy-300 border border-navy-200 dark:border-navy-700"
          data-review-filter="all">
    All ({{ gap_items | length }})
  </button>
  <button class="px-3 py-1.5 rounded-lg font-medium transition-colors text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent"
          data-review-filter="draft">
    Draft ({{ draft_count }})
  </button>
  <button class="px-3 py-1.5 rounded-lg font-medium transition-colors text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent"
          data-review-filter="high">
    High Severity
  </button>
  <button class="px-3 py-1.5 rounded-lg font-medium transition-colors text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent"
          data-review-filter="rejected">
    Rejected
  </button>
</div>
```

Create `app/templates/partials/review_finding_card.html`:

```html
{# Individual finding review card #}
{# Expects: item (GapItem with review + ai_* fields), assessment (Assessment) #}
<div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
     data-review-card
     data-review-status="{{ item.review_status or 'draft' }}"
     data-risk-level="{{ item.risk_level }}"
     id="review-card-{{ item.id }}">
  
  <div class="px-5 py-4">
    {# Header: requirement + badges #}
    <div class="flex items-start justify-between mb-3">
      <div>
        <div class="flex items-center gap-2 mb-1">
          {% if item.framework_id %}
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">{{ item.framework_id | upper }}</span>
          {% endif %}
          <span class="font-mono text-xs text-gray-400 dark:text-gray-500">{{ item.requirement_id }}</span>
        </div>
        <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ item.requirement_title }}</h4>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0 ml-4">
        {# Review status badge #}
        {% set review_badge = {
          'draft': 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
          'accepted': 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400',
          'rejected': 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400',
        } %}
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ review_badge.get(item.review_status or 'draft', review_badge.draft) }}">
          {{ (item.review_status or 'draft') | title }}
        </span>
      </div>
    </div>
    
    {# AI assessment (read-only) #}
    <div class="grid grid-cols-3 gap-4 mb-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
      <div>
        <p class="text-xs text-gray-400 dark:text-gray-500 mb-0.5">AI Status</p>
        {% set status_colors = {'compliant': 'text-green-600', 'partially_compliant': 'text-yellow-600', 'non_compliant': 'text-red-600'} %}
        <p class="text-sm font-medium {{ status_colors.get(item.ai_compliance_status or item.compliance_status, 'text-gray-600') }}">
          {{ (item.ai_compliance_status or item.compliance_status) | replace('_', ' ') | title }}
        </p>
      </div>
      <div>
        <p class="text-xs text-gray-400 dark:text-gray-500 mb-0.5">AI Risk Level</p>
        <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ (item.ai_risk_level or item.risk_level) | title }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-400 dark:text-gray-500 mb-0.5">Evidence</p>
        <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ (item.evidence_confidence or 'weak') | title }}</p>
      </div>
    </div>
    
    {# Gap description #}
    <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3">{{ item.ai_gap_description or item.gap_description }}</p>
    
    {% if item.evidence_quote %}
    <div class="mb-3 pl-3 border-l-2 border-navy-200 dark:border-navy-700">
      <p class="text-xs text-gray-500 dark:text-gray-400 italic">"{{ item.evidence_quote[:300] }}{% if item.evidence_quote | length > 300 %}...{% endif %}"</p>
    </div>
    {% endif %}
    
    {# Reviewer actions #}
    <div class="flex items-center gap-2 pt-3 border-t border-gray-100 dark:border-gray-800">
      <button hx-patch="/api/assessments/{{ assessment.id }}/review/items/{{ item.id }}"
              hx-vals='{"review_status": "accepted"}'
              hx-target="#review-card-{{ item.id }}"
              hx-swap="outerHTML"
              class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                     {% if item.review_status == 'accepted' %}bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800
                     {% else %}text-gray-600 dark:text-gray-400 hover:bg-green-50 dark:hover:bg-green-900/20 border border-gray-200 dark:border-gray-700{% endif %}">
        ✓ Accept
      </button>
      <button hx-patch="/api/assessments/{{ assessment.id }}/review/items/{{ item.id }}"
              hx-vals='{"review_status": "rejected"}'
              hx-target="#review-card-{{ item.id }}"
              hx-swap="outerHTML"
              class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                     {% if item.review_status == 'rejected' %}bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800
                     {% else %}text-gray-600 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/20 border border-gray-200 dark:border-gray-700{% endif %}">
        ✕ Reject
      </button>
      <div class="flex-1"></div>
      <details class="relative">
        <summary class="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700 cursor-pointer transition-colors">
          Add Notes
        </summary>
        <div class="absolute right-0 mt-1 w-80 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 shadow-lg p-3 z-10">
          <form hx-patch="/api/assessments/{{ assessment.id }}/review/items/{{ item.id }}"
                hx-target="#review-card-{{ item.id }}"
                hx-swap="outerHTML">
            <textarea name="reviewer_notes" rows="3" placeholder="Reviewer notes..."
                      class="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-gray-100 focus:border-navy-500 dark:focus:border-navy-400 outline-none resize-none mb-2">{{ item.reviewer_notes or '' }}</textarea>
            <button type="submit" class="bg-brand dark:bg-navy-600 hover:bg-brand-light dark:hover:bg-navy-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors">Save Notes</button>
          </form>
        </div>
      </details>
    </div>
  </div>
</div>
```

---

## Task 10: Review Filter JS

Add to `app.js`:

```js
// Review queue filtering
document.addEventListener('click', (e) => {
  const filter = e.target.closest('[data-review-filter]');
  if (!filter) return;
  
  const type = filter.dataset.reviewFilter;
  
  // Update active filter button
  filter.closest('.flex').querySelectorAll('[data-review-filter]').forEach(btn => {
    btn.classList.remove('bg-navy-50', 'dark:bg-navy-900/40', 'text-brand', 'dark:text-navy-300', 'border-navy-200', 'dark:border-navy-700');
    btn.classList.add('text-gray-500', 'dark:text-gray-400', 'border-transparent');
  });
  filter.classList.add('bg-navy-50', 'dark:bg-navy-900/40', 'text-brand', 'dark:text-navy-300', 'border-navy-200', 'dark:border-navy-700');
  filter.classList.remove('text-gray-500', 'dark:text-gray-400', 'border-transparent');
  
  // Filter cards
  document.querySelectorAll('[data-review-card]').forEach(card => {
    const status = card.dataset.reviewStatus;
    const risk = card.dataset.riskLevel;
    let show = true;
    
    if (type === 'draft') show = status === 'draft';
    else if (type === 'high') show = ['critical', 'high'].includes(risk);
    else if (type === 'rejected') show = status === 'rejected';
    // 'all' shows everything
    
    card.style.display = show ? '' : 'none';
  });
});
```

---

## Task 11: Comparison Page

Create `app/templates/pages/comparison.html`:

```html
{% extends "base.html" %}
{% block title %}Compare — {{ assessment.company_name }}{% endblock %}

{% block content %}
<nav class="text-xs text-gray-400 dark:text-gray-500 mb-2">
  <a href="/" class="hover:text-brand dark:hover:text-navy-300 transition-colors">Assessments</a>
  <span class="mx-1.5">/</span>
  <a href="/assessments/{{ assessment.id }}" class="hover:text-brand dark:hover:text-navy-300 transition-colors">{{ assessment.company_name }}</a>
  <span class="mx-1.5">/</span>
  <span class="text-gray-600 dark:text-gray-300">Compare</span>
</nav>

<div class="mb-6">
  <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">Assessment Comparison</h1>
  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
    {{ current_report.generated_at.strftime('%d %b %Y') }} vs {{ previous_report.generated_at.strftime('%d %b %Y') }}
  </p>
</div>

{# Summary cards #}
<div class="grid grid-cols-3 gap-4 mb-6">
  <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 text-center">
    <p class="text-3xl font-bold text-green-600">{{ delta_summary.improved }}</p>
    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Improved</p>
  </div>
  <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 text-center">
    <p class="text-3xl font-bold text-red-600">{{ delta_summary.regressed }}</p>
    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Regressed</p>
  </div>
  <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 text-center">
    <p class="text-3xl font-bold text-gray-400 dark:text-gray-500">{{ delta_summary.unchanged }}</p>
    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Unchanged</p>
  </div>
</div>

{# Score delta #}
<div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 mb-6">
  <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Overall Score</h3>
  <div class="flex items-baseline gap-3">
    <span class="text-2xl font-bold {% if score_delta > 0 %}text-green-600{% elif score_delta < 0 %}text-red-600{% else %}text-gray-500{% endif %}">
      {% if score_delta > 0 %}+{% endif %}{{ score_delta | round(1) }}%
    </span>
    <span class="text-sm text-gray-500 dark:text-gray-400">{{ previous_score | round(0) | int }}% → {{ current_score | round(0) | int }}%</span>
  </div>
</div>

{# Detailed changes #}
<div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
  <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800">
    <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Requirement Changes</h3>
  </div>
  <div class="divide-y divide-gray-100 dark:divide-gray-800">
    {% for delta in deltas %}
    {% if delta.status_changed %}
    <div class="px-5 py-3 flex items-center justify-between">
      <div>
        <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ delta.requirement_title }}</p>
        <span class="font-mono text-xs text-gray-400 dark:text-gray-500">{{ delta.requirement_id }}</span>
      </div>
      <div class="flex items-center gap-2 text-xs">
        {% set old_color = {'compliant': 'text-green-600', 'partially_compliant': 'text-yellow-600', 'non_compliant': 'text-red-600'} %}
        {% set new_color = {'compliant': 'text-green-600', 'partially_compliant': 'text-yellow-600', 'non_compliant': 'text-red-600'} %}
        <span class="{{ old_color.get(delta.old_status, 'text-gray-500') }} font-medium">{{ delta.old_status | replace('_', ' ') | title }}</span>
        <svg class="h-4 w-4 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"/>
        </svg>
        <span class="{{ new_color.get(delta.new_status, 'text-gray-500') }} font-medium">{{ delta.new_status | replace('_', ' ') | title }}</span>
      </div>
    </div>
    {% endif %}
    {% endfor %}
  </div>
</div>
{% endblock %}
```

---

## Final: app.js Structure

Restructure `app.js` to include all systems. Keep the existing code (HTMX config, drop zone, upload progress) and add the new modules. Final file structure:

```
// ── HTMX Configuration ─────────────────────────
// (existing code: configRequest, responseError, beforeSwap handlers)

// ── Toast Notifications ─────────────────────────
// (Task 1)

// ── Copy to Clipboard ───────────────────────────
// (Task 2)

// ── Save Indicator ──────────────────────────────
// (Task 3)

// ── Dashboard Search/Filter ─────────────────────
// (Task 4)

// ── Keyboard Shortcuts ──────────────────────────
// (Task 5)

// ── Collapsible Sections ────────────────────────
// (Task 6)

// ── Review Queue Filtering ──────────────────────
// (Task 10)

// ── Upload Handling ─────────────────────────────
// (existing code: initDropZone, upload progress)
```

---

## What NOT to do

- Do NOT edit existing template files (Session A owns them)
- Do NOT edit Python files (Session C owns them)
- Do NOT introduce any JS library or framework — vanilla JS only
- Do NOT create CSS files (Session A owns CSS)
- Do NOT use indigo anywhere — navy only
- Do NOT add shadows to cards in your new templates
