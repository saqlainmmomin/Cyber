# Parallel Session Coordination

> **Three sessions run in parallel. This file is the single source of truth for contracts between them.**
> Each session MUST read this file before starting. Update your section when you complete a deliverable.

---

## Session Map

| Session | Type | Scope | File Ownership |
|---|---|---|---|
| **A — Design & Polish** | Sonnet 4.6 | Dark mode, visual redesigns, template aesthetics | All existing `app/templates/**/*.html`, `app/static/css/`, `tailwind.config.js`, `input.css`, `package.json`, `docs/design.md` |
| **B — Interaction & Feature UI** | Sonnet 4.6 | JS behavior, QoL features, NEW template files for features | `app/static/js/app.js`, all NEW files in `app/templates/` (listed below) |
| **C — Backend Features** | Codex | Models, migrations, routers, services, schemas | All `app/*.py`, `app/models/`, `app/routers/`, `app/services/`, `app/schemas/`, `app/main.py` |

---

## File Ownership — Hard Rules

**NO SESSION may edit a file owned by another session.**

### Session A owns (READ-WRITE):
```
app/templates/base.html
app/templates/pages/dashboard.html
app/templates/pages/login.html
app/templates/partials/scope_form.html
app/templates/partials/scope_complete.html
app/templates/partials/documents_tab.html
app/templates/partials/document_list.html
app/templates/partials/desk_review_running.html
app/templates/partials/questionnaire_tab.html
app/templates/partials/questionnaire_sections.html
app/templates/partials/section_questions.html
app/templates/partials/screening_form.html
app/templates/partials/report_summary.html
app/templates/partials/analysis_complete.html
app/templates/partials/analysis_running.html
app/templates/partials/analysis_error.html
app/templates/partials/rfi_generated.html
app/templates/components/status_badge.html
app/static/css/style.css
app/static/css/input.css              (NEW — Tailwind input)
app/static/css/tailwind.css           (NEW — Tailwind output, gitignored)
tailwind.config.js                     (NEW)
package.json                           (NEW)
docs/design.md
```

### Session B owns (READ-WRITE):
```
app/static/js/app.js
app/templates/partials/remediation_panel.html       (NEW)
app/templates/partials/review_finding_card.html     (NEW)
app/templates/partials/review_filter_bar.html       (NEW)
app/templates/partials/report_comparison.html       (NEW)
app/templates/partials/status_timeline.html         (NEW)
app/templates/partials/toast_container.html          (NEW — optional, may be pure JS)
app/templates/pages/review.html                     (NEW)
app/templates/pages/comparison.html                 (NEW)
```

### Session C owns (READ-WRITE):
```
app/models/report.py
app/models/assessment.py
app/models/questionnaire.py
app/main.py
app/routers/remediation.py            (NEW)
app/routers/review.py                 (NEW)
app/routers/reports.py
app/routers/web.py
app/routers/analysis.py
app/services/scoring.py
app/schemas/report.py
app/schemas/review.py                 (NEW)
app/schemas/remediation.py            (NEW)
```

### ALL sessions may READ (but not write):
```
docs/sessions/COORDINATION.md         (read for contracts)
app/dpdpa/                            (read for domain knowledge)
app/frameworks/                       (read for framework data)
CLAUDE.md                             (read for project rules)
```

---

## Interface Contracts

### Contract 1: Dark Mode Class Pattern (Session A → Session B)

Session B's new templates MUST use these dark mode patterns established by Session A:

```
Page background:     bg-gray-50 dark:bg-gray-950
Card:                bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800
Card inset:          bg-gray-50 dark:bg-gray-800/50
Text primary:        text-gray-900 dark:text-gray-100
Text body:           text-gray-700 dark:text-gray-300
Text supporting:     text-gray-500 dark:text-gray-400
Text metadata:       text-gray-400 dark:text-gray-500
Interactive text:    text-brand dark:text-navy-300
Primary button:      bg-brand dark:bg-navy-600 hover:bg-brand-light dark:hover:bg-navy-500 text-white
Secondary button:    border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300
Form input:          bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100
Focus ring:          focus:border-navy-500 dark:focus:border-navy-400 focus:ring-navy-100 dark:focus:ring-navy-900

Status badge pattern (all statuses):
  Light: bg-{color}-100 text-{color}-700
  Dark:  dark:bg-{color}-900/40 dark:text-{color}-400
```

### Contract 2: Include Hooks (Session A → Session B)

Session A will add these `{% include %}` directives in existing templates. Session B creates the corresponding files.

| Existing template (Session A) | Include directive added | New partial (Session B) | Location in template |
|---|---|---|---|
| `report_summary.html` — inside each finding in detailed findings | `{% include "partials/remediation_panel.html" ignore missing %}` | `remediation_panel.html` | After gap_description in each finding row, inside a `<div id="remediation-{{ item.id }}">` wrapper |
| `report_summary.html` — top of page, after hero metrics | `{% include "partials/remediation_summary.html" ignore missing %}` | `remediation_summary.html` (NEW — add to Session B file list) | After the hero metrics grid, before executive summary |
| `base.html` or assessment detail area | `{% include "partials/status_timeline.html" ignore missing %}` | `status_timeline.html` | In assessment detail page header area, after company name |

Session A will wrap each include hook with a container `<div>` that has the appropriate `id` for HTMX targeting.

### Contract 3: HTMX Endpoint Contracts (Session C → Session B)

Session C builds these endpoints. Session B's templates target them via HTMX.

#### Remediation

```
PATCH /api/assessments/{assessment_id}/gap-items/{item_id}/remediation
  Body: {
    "remediation_status": "open" | "in_progress" | "closed" | "accepted_risk",
    "remediation_owner": "string | null",
    "remediation_target_date": "ISO date string | null",
    "remediation_notes": "string | null"
  }
  Response: 200 with updated remediation partial HTML (hx-swap target)
  Headers: X-Toast-Message on success
```

```
GET /api/assessments/{assessment_id}/remediation-summary
  Response: HTML partial with remediation counts (open/in_progress/closed)
```

#### Manager Review

```
GET /assessments/{assessment_id}/review
  Response: Full review page (Session B's review.html template)
```

```
PATCH /api/assessments/{assessment_id}/review/items/{item_id}
  Body: {
    "review_status": "accepted" | "rejected",
    "compliance_status": "string | null (only if editing)",
    "gap_description": "string | null (only if editing)",
    "risk_level": "string | null (only if editing)",
    "reviewer_notes": "string | null"
  }
  Response: Updated finding card HTML partial
  Headers: X-Toast-Message
```

```
POST /api/assessments/{assessment_id}/review/approve
  Body: { "reviewer_name": "string" }
  Response: 200 + redirect to report page
  Headers: X-Toast-Message
```

```
POST /api/assessments/{assessment_id}/review/reject
  Body: { "reviewer_name": "string", "rejection_reason": "string" }
  Response: 200
  Headers: X-Toast-Message
```

#### Assessment Comparison

```
GET /api/assessments/{assessment_id}/compare/{other_assessment_id}
  Response: JSON { deltas: [{requirement_id, old_status, new_status, score_delta}], summary: {improved, regressed, unchanged} }
```

```
GET /assessments/{assessment_id}/compare/{other_assessment_id}
  Response: Full comparison page (Session B's comparison.html template)
```

```
GET /api/assessments/{assessment_id}/comparable
  Response: JSON list of other completed assessments for same company_name
  Used by: Session A to conditionally show "Compare" button in report_summary.html
```

### Contract 4: Data Attributes (Session A → Session B)

Session A adds `data-*` attributes to existing templates. Session B's JS hooks onto them.

| Attribute | Where (Session A adds) | Purpose (Session B reads) |
|---|---|---|
| `data-assessment-card` | Each assessment card on dashboard | JS search/filter targeting |
| `data-save-indicator` | Span below questionnaire save button | JS updates "Saved at HH:MM" |
| `data-section-header` | Section title div in section_questions.html | JS sticky behavior enhancement |
| `data-copy-target="executive-summary"` | Executive summary text div | Copy-to-clipboard targeting |
| `data-copy-target="requirement-id"` | Requirement ID spans | Copy-to-clipboard targeting |
| `data-shortcut-scope="questionnaire"` | Questionnaire form container | Keyboard shortcut scoping |
| `data-shortcut-scope="dashboard"` | Dashboard content container | Keyboard shortcut scoping |
| `data-question-index` | Each question card | j/k navigation indexing |
| `data-collapsible-section` | Questionnaire section containers | Collapse persistence |

### Contract 5: Toast System (Session B → Session C)

Session C adds this response header to trigger toasts:

```python
from fastapi import Response

response.headers["X-Toast-Message"] = "Section saved successfully"
response.headers["X-Toast-Type"] = "success"  # success | error | info
```

Session B's JS listens for this header on `htmx:afterSwap` events and shows the toast. No template cooperation needed.

### Contract 6: Review Gate (Session C internal, affects Session A)

Session C adds a `review_status` column to `Assessment` model. Session A should be aware that report_summary.html may eventually show a draft watermark, but Session A does NOT implement this — Session C adds the gating logic and Session A's template already has the `{% if %}` blocks that Session C will use.

**Practical impact on Session A:** When redesigning report_summary.html, leave room for a banner/watermark area at the top (an empty div with id="review-banner"). Session C's router will populate it via context.

### Contract 7: Model Column Names (Session C → Session B)

Session B's templates reference these model fields. Session C MUST use these exact names:

**GapItem new columns:**
```
remediation_status      VARCHAR(20)  default 'open'
remediation_owner       VARCHAR(255) nullable
remediation_target_date DATETIME     nullable
remediation_notes       TEXT         nullable
remediation_closed_at   DATETIME     nullable
review_status           VARCHAR(20)  default 'draft'
ai_compliance_status    TEXT         nullable
ai_gap_description      TEXT         nullable
ai_risk_level           VARCHAR(20)  nullable
reviewer_notes          TEXT         nullable
reviewed_by             VARCHAR(255) nullable
reviewed_at             DATETIME     nullable
```

**Assessment new columns:**
```
review_status           VARCHAR(20)  nullable  (null | under_review | approved | rejected)
```

---

## Status Tracking

Each session updates its section here when completing a deliverable. Check before starting work that depends on another session.

### Session A — Design & Polish
```
[x] Tailwind CLI setup (package.json, tailwind.config.js, input.css)
[x] Dark mode toggle in base.html
[x] base.html dark mode classes + breadcrumb nav
[x] dashboard.html — dark mode + card redesign + empty state
[x] login.html — dark mode
[x] scope_form.html — dark mode
[x] scope_complete.html — dark mode
[x] documents_tab.html — dark mode + empty state
[x] desk_review_running.html — dark mode
[x] questionnaire_tab.html — dark mode
[x] questionnaire_sections.html — dark mode
[x] section_questions.html — dark mode + badge simplification + evidence panel unification + GRC radio sizing + sticky header
[x] screening_form.html — dark mode
[x] report_summary.html — dark mode + findings grouping (with flat fallback) + score gauge enlarged + include hooks + copy button + review banner
[x] analysis_complete.html — dark mode
[x] analysis_running.html — dark mode
[x] analysis_error.html — dark mode
[x] components/status_badge.html — dark mode
[x] style.css — spinner delay, details chevron, dark scrollbar, drag-over dark
[x] Data attributes added (Contract 4): data-assessment-card, data-save-indicator, data-section-header, data-copy-target, data-shortcut-scope, data-question-index, data-collapsible-section
[x] Include hooks added (Contract 2): remediation_summary.html, remediation_panel.html, status_timeline.html
[x] Breadcrumb navigation added (base.html)
[ ] docs/design.md updated with dark mode tokens (deferred — not blocking Sessions B or C)

PENDING changes for Session C: see docs/sessions/pending-changes-session-a.md
```

### Session B — Interaction & Feature UI
```
[ ] Toast notification system (app.js)
[ ] Assessment status timeline (status_timeline.html + JS)
[ ] Progress save indicator (JS)
[ ] Copy-to-clipboard utility (JS)
[ ] Keyboard shortcuts system (JS + help modal)
[ ] Dashboard search/filter (JS)
[ ] Collapsible sections with localStorage (JS)
[ ] remediation_panel.html created
[ ] remediation_summary.html created
[ ] review.html page created
[ ] review_finding_card.html created
[ ] review_filter_bar.html created
[ ] report_comparison.html created
[ ] comparison.html page created
```

### Session C — Backend Features
```
[ ] GapItem model — remediation columns added
[ ] GapItem model — review columns added (review_status, ai_*, reviewer_*)
[ ] Assessment model — review_status column added
[ ] Migrations written in app/main.py
[ ] app/routers/remediation.py — PATCH endpoint
[ ] app/routers/remediation.py — GET summary endpoint
[ ] app/routers/review.py — item disposition endpoint
[ ] app/routers/review.py — approve/reject endpoints
[ ] app/routers/review.py — GET review page route
[ ] Approval gate helper (shared)
[ ] app/routers/reports.py — PDF gated via approval helper
[ ] app/services/scoring.py — compute_delta() function
[ ] app/routers/reports.py — comparison endpoint
[ ] app/routers/reports.py — comparable assessments endpoint
[ ] app/routers/web.py — review page route
[ ] app/routers/web.py — comparison page route
[ ] X-Toast-Message headers on all mutation responses
```

---

## Conflict Resolution

If a session discovers it MUST edit a file owned by another session:
1. Do NOT edit the file
2. Document the needed change in a `docs/sessions/pending-changes-session-{X}.md` file
3. The owning session picks up pending changes when it reads the coordination file

---

## Merge Order

When all three sessions are complete, merge in this order:
1. **Session C** first (backend — no template/CSS conflicts possible)
2. **Session A** second (templates — builds on models from C)
3. **Session B** last (JS + new templates — hooks onto A's data attributes and C's endpoints)

Test after each merge.
