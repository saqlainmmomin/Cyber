# Pending Changes — Session B → Session C

> Items Session B cannot implement (Session C owns those files). Session C must pick these up.

---

## 1. `timeline_steps` context variable in assessment detail route

**File:** `app/routers/web.py` — assessment detail route handler

The `status_timeline.html` partial expects a `timeline_steps` variable in the template context. Add it when rendering the assessment detail page:

```python
timeline_steps = [
    ('Scope', assessment.scope_answers is not None),
    ('Documents', bool(documents)),
    ('Desk Review', assessment.desk_review_status == 'completed'),
    ('Questionnaire', assessment.status in ('questionnaire_done', 'analyzing', 'completed')),
    ('Analysis', assessment.status == 'completed'),
]
```

Pass as `timeline_steps=timeline_steps` in the `TemplateResponse` context dict.

---

## 2. `remediation_counts` context variable in report route

**File:** `app/routers/web.py` — report/assessment detail route handler

The `remediation_summary.html` partial expects `remediation_counts` in context:

```python
# Query counts from gap_items for this report
remediation_counts = {
    'open': <count of items where remediation_status='open'>,
    'in_progress': <count where remediation_status='in_progress'>,
    'closed': <count where remediation_status='closed'>,
    'accepted_risk': <count where remediation_status='accepted_risk'>,
    'total': <total gap items count>,
}
```

---

## 3. Review page route context

**File:** `app/routers/web.py` — review page route (`/assessments/{id}/review`)

The `review.html` template expects:
- `assessment` — Assessment ORM object (with `review_status` column — see Contract 7)
- `gap_items` — list of GapItem ORM objects (with `review_status`, `ai_*`, `reviewer_notes` columns — see Contract 7)
- `draft_count` — integer count of items where `review_status == 'draft'`
- `reviewer_name` — optional string from session or query param

---

## 4. Comparison page route context

**File:** `app/routers/web.py` — comparison page route (`/assessments/{id}/compare/{other_id}`)

The `comparison.html` template expects:
- `assessment` — current Assessment
- `current_report` — GapReport with `.generated_at` datetime
- `previous_report` — GapReport with `.generated_at` datetime
- `current_score` — float
- `previous_score` — float
- `score_delta` — float (current - previous)
- `delta_summary` — dict with `improved`, `regressed`, `unchanged` integer counts
- `deltas` — list of dicts: `{requirement_id, requirement_title, old_status, new_status, status_changed: bool}`
