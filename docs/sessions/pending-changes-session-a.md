# Pending Changes — Session A → Session C

## PENDING: gap_items_by_chapter in report_summary.html

`app/routers/reports.py` must pass `gap_items_by_chapter` dict to the `report_summary.html` template context.

**Structure:**
```python
{ "chapter_name": [gap_item_1, gap_item_2, ...], ... }
```

**Currently:** router passes a flat `gap_items` list.

**Why:** `report_summary.html` now has a collapsible grouped-by-chapter view that is significantly cleaner than the flat table. It falls back to the flat table if `gap_items_by_chapter` is not defined, so this is non-breaking.

**Where to group:** In `app/routers/reports.py` (or wherever `report_summary.html` context is built), group `gap_items` by the chapter portion of `item.requirement_id` (e.g., `"CH2.CONSENT.1"` → chapter key `"CH2"`), or use the chapter title from the DPDPA framework dict.

---

## PENDING: comparable_assessments in report_summary.html

`app/routers/reports.py` (or `app/routers/web.py`) should pass `comparable_assessments` — a list of other **completed** assessments for the same `company_name` — to the report context.

**Used by:** The "Compare with previous" link in the executive summary header (Session A added it, conditional on `{% if comparable_assessments %}`).

**Contract 3** in `COORDINATION.md` defines the `/api/assessments/{id}/comparable` endpoint (Session C work).

---

## PENDING: review_status, reviewed_by, reviewed_at in report context

`report_summary.html` now has a `#review-banner` div that conditionally renders approval / under-review banners.

Pass these from the router when the Assessment model has a `review_status` column (Session C P3 work):
- `review_status` — one of `"approved"`, `"under_review"`, or `None`
- `reviewed_by` — reviewer name string or `None`
- `reviewed_at` — datetime or `None`
