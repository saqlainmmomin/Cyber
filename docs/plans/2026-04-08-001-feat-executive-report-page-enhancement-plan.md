---
title: "feat: Executive Report Page Enhancement — Business Impact, Visualizations, Signal Reduction"
type: feat
status: active
date: 2026-04-08
---

# feat: Executive Report Page Enhancement

## Overview

The current report page shows chapter scores (CSS bars), executive summary text, and a flat 41-row gap table. This gives auditors what they need but leaves executives without an answer to the most important question: *"What does this actually mean for us?"*

This plan adds four high-signal sections to `report_summary.html` and the backing endpoint in `web.py`:

1. **Radial score gauge** — visual replacement for the plain score number
2. **Business Impact panel** — regulatory exposure, risk themes, operational reach
3. **Per-chapter compliance distribution** — stacked bar chart (compliant / partial / non-compliant / N/A) computed from gap items
4. **Critical Findings + Quick Wins** — the two questions every executive asks first
5. **Root cause distribution** — why the org is in this state (5-category breakdown)

All visualizations are server-side rendered: SVG via Jinja2 math, stacked CSS flex bars, no JavaScript chart library.

---

## Problem Statement

**Current report is auditor-grade, not board-grade.** Specific gaps:

- Overall score is a raw number — conveys nothing about severity or threshold standing
- Chapter scores show *how* compliant each chapter is, but not *where the gaps are concentrated*
- Executive summary is Claude prose — valuable but buried under nothing before it
- No section translates compliance gaps into business language (fines, operational disruption, affected data)
- Full 41-row table is the first thing after the summary — overwhelming before context is set
- Quick wins (low-effort, high-priority fixes) are invisible — require scanning all 41 rows

---

## Proposed Solution

### Section Layout After Enhancement

```
┌─────────────────────────────────────────────────────────┐
│  [Gauge: Score] [Total Reqs] [Critical] [High]          │  ← Metric Row (enhanced)
├─────────────────────────────────────────────────────────┤
│  BUSINESS IMPACT                                        │  ← NEW
│  Regulatory Exposure | Risk Themes | Data Affected      │
├─────────────────────────────────────────────────────────┤
│  EXECUTIVE SUMMARY                                      │  ← Existing (moved after impact)
├─────────────────────────────────────────────────────────┤
│  COMPLIANCE DISTRIBUTION BY CHAPTER                     │  ← NEW (replaces simple bars)
│  [Stacked bar per chapter: ■ ■ ■ □ counts + score]     │
├─────────────────────────────────────────────────────────┤
│  CRITICAL FINDINGS        │  QUICK WINS                 │  ← NEW (2-col)
│  Top N critical/high gaps │  Priority 1 + low effort   │
├─────────────────────────────────────────────────────────┤
│  ROOT CAUSE BREAKDOWN                                   │  ← NEW
│  Policy ██ 8  Process ████ 12  Technology ██ 5 ...     │
├─────────────────────────────────────────────────────────┤
│  DETAILED FINDINGS (gap table — existing)               │  ← Existing (below fold)
├─────────────────────────────────────────────────────────┤
│  RFI SECTION (existing)                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Technical Approach

### No new JavaScript dependencies

All visualizations use one of three patterns already established in the codebase:

| Visualization | Technique | Precedent |
|---|---|---|
| Radial score gauge | Server-rendered SVG (Jinja2 math) | Loading spinner SVGs |
| Chapter stacked bars | CSS flex with `style="width: X%"` | Chapter score bars today |
| Root cause bars | CSS flex bars | Chapter score bars today |
| Critical/quick-win cards | Tailwind card grid | Dashboard cards |

**HTMX note:** `report_summary.html` is loaded via `hx-swap="innerHTML"` from `report_tab.html`. No `<script>` tags will be placed inside the partial — all rendering is pure HTML/SVG/CSS. This is safe.

### SVG Gauge Math (server-side)

```
r = 40, center = (50, 50)
circumference = 2 × π × 40 = 251.33

stroke-dasharray  = 251.33          (full circle)
stroke-dashoffset = 251.33 × (1 − score/100)
transform         = rotate(-90 50 50)   (start from top)
```

Jinja2 expression:
```jinja2
{{ (251.327 * (1 - report.overall_score / 100)) | round(2) }}
```

Gauge arc color matches existing threshold tiers:
- ≥ 80 → `#22c55e` (green-500)
- ≥ 60 → `#eab308` (yellow-500)
- ≥ 40 → `#f97316` (orange-500)
- < 40 → `#ef4444` (red-500)

### Business Impact — Deterministic Computation

No additional Claude calls. Derived purely from `gap_items` using a penalty map and domain mapping:

**DPDPA penalty reference (Schedule to the Act):**
| Violation category | Max penalty |
|---|---|
| Security safeguards / breach not notified | ₹250 Cr |
| Children's data protections | ₹200 Cr |
| Consent, notice, rights violations | ₹50 Cr |
| Significant Data Fiduciary obligations | ₹50 Cr |
| Repeated violations | ₹500 Cr |

Three impact metrics to display:

1. **Regulatory Exposure** — penalty tier of the highest-severity non-compliant requirement
2. **Risk Domains Affected** — set of domains (e.g., "Data Security", "Consent Management", "Data Subject Rights") derived from requirement_id prefixes
3. **Critical Process Count** — count of `critical` + `high` risk non-compliant gap items

**Prefix → domain mapping (for web.py helper):**
```python
DOMAIN_MAP = {
    "CH2.CONSENT":  "Consent Management",
    "CM.":          "Consent Management",
    "CH2.NOTICE":   "Notice & Transparency",
    "CH2.PURPOSE":  "Purpose Limitation",
    "CH2.MINIMIZE": "Data Minimization",
    "CH2.SECURITY": "Data Security",
    "BN.NOTIFY":    "Breach Response",
    "CH3.":         "Data Subject Rights",
    "CH4.SDF":      "Governance & Oversight",
    "CH4.CHILD":    "Children's Data",
    "CB.TRANSFER":  "Cross-Border Transfers",
}

PENALTY_MAP = {
    "CH2.SECURITY": 250,
    "BN.NOTIFY":    250,
    "CH4.CHILD":    200,
    "CH4.SDF":       50,
    "CH2.CONSENT":   50,
    "CM.":           50,
    "CH2.NOTICE":    50,
    "CH3.":          50,
    "CB.TRANSFER":   50,
}
```

### Per-Chapter Status Distribution — Stacked Bars

Computed in web.py, passed as `chapter_status_counts` dict to template.

Shape:
```python
{
  "chapter_2": {
    "compliant": 5, "partially_compliant": 5, "non_compliant": 6,
    "not_applicable": 0, "not_assessed": 0, "total": 16
  },
  ...
}
```

Jinja2 renders each chapter as a stacked flex row:
```html
<div class="flex h-4 rounded-full overflow-hidden">
  <div class="bg-green-500" style="width: {{ (counts.compliant / counts.total * 100) | round(1) }}%"></div>
  <div class="bg-yellow-500" style="width: {{ (counts.partially_compliant / counts.total * 100) | round(1) }}%"></div>
  <div class="bg-red-500"    style="width: {{ (counts.non_compliant / counts.total * 100) | round(1) }}%"></div>
  <div class="bg-gray-300"   style="width: {{ ((counts.not_applicable + counts.not_assessed) / counts.total * 100) | round(1) }}%"></div>
</div>
```

Each chapter row also shows the score (`chapter_scores[chapter_key].score`) so the bar and the number reinforce each other.

### Quick Wins — Filtering in Template (or web.py)

Definition: `compliance_status in (non_compliant, partially_compliant)` AND `remediation_priority <= 2` AND `remediation_effort == "low"`.

Limit to 4 items. If none qualify, show message "No quick wins identified — all gaps require medium or high effort."

### Critical Findings — Top Risks

Non-compliant or partially-compliant items where `risk_level in (critical, high)`, sorted by `remediation_priority` ASC, limit 5.

Show: title, risk badge, chapter, one-line gap_description (truncated at 100 chars).

### Root Cause Distribution

Computed in web.py from gap items where `compliance_status in (non_compliant, partially_compliant)`.

```python
root_cause_counts = Counter(
    item.root_cause_category
    for item in gap_items
    if item.compliance_status in ("non_compliant", "partially_compliant")
    and item.root_cause_category
)
```

Display as horizontal CSS bars (same pattern as chapter scores). Label with category title from `ROOT_CAUSE_CLUSTERS` dict in `framework.py`.

---

## Implementation Plan

### Phase 1 — Backend: New Computed Data (`app/routers/web.py`)

**1a. Add private helper functions (before `report_summary` function):**

- `_compute_chapter_status_counts(gap_items) → dict` — per-chapter breakdown
- `_compute_business_impact(gap_items) → dict` — exposure tier, domains, counts
- `_compute_root_cause_counts(gap_items) → dict` — root_cause_category counts

**1b. Update `report_summary` endpoint (lines 815–855):**

Add to context passed to template:
```python
return templates.TemplateResponse("partials/report_summary.html", {
    "request": request,
    "assessment_id": assessment_id,
    "report": report,
    "gap_items": gap_items,
    "chapter_scores": chapter_scores,
    "status_counts": status_counts,
    "chapter_status_counts": _compute_chapter_status_counts(gap_items),
    "business_impact": _compute_business_impact(gap_items),
    "root_cause_counts": _compute_root_cause_counts(gap_items),
    "rfi": rfi,
})
```

**Files to touch:** `app/routers/web.py`

---

### Phase 2 — Template: `app/templates/partials/report_summary.html`

Restructure the file into clearly labeled sections:

**Section A — Metric Row (enhanced score card)**
- Replace plain `text-3xl` score with SVG radial gauge (40px radius, stroke-dashoffset)
- Keep requirements count card and critical/high gap count cards
- Add overall rating text below gauge

**Section B — Business Impact Card** (new)
- 3-column sub-grid: Regulatory Exposure | Risk Domains | Critical Processes
- Regulatory exposure: formatted as "Up to ₹Xcr" with penalty context line
- Risk domains: flex chip list (navy-100 badges)
- Critical processes: count badge

**Section C — Executive Summary** (existing, unchanged position shifted down)

**Section D — Compliance Distribution by Chapter** (replaces existing chapter bars)
- Section title: "Compliance by Chapter"
- Per-chapter row: chapter title + score (right-aligned) + stacked bar + count chips (4 counts inline)
- Legend row below: ■ Compliant ■ Partial ■ Non-Compliant □ N/A

**Section E — Critical Findings + Quick Wins** (new, 2-col grid)
- Left: "Critical Findings" — top 5 critical/high gap cards (title, risk badge, gap snippet)
- Right: "Quick Wins" — top 4 low-effort/high-priority items

**Section F — Root Cause Breakdown** (new)
- Section title: "Why These Gaps Exist"
- Horizontal bars per root cause category, labeled with category name + count
- Brief explainer line per category (from ROOT_CAUSE_CLUSTERS description)

**Section G — Detailed Findings** (existing table, relabeled)
- Add collapsible toggle: `<details><summary>Detailed Findings (N items)</summary>...</details>` — reduces visual weight

**Section H — RFI** (existing, unchanged)

---

## Acceptance Criteria

- [ ] Radial SVG gauge renders correctly at score 0, 50, 100 and intermediate values without JS
- [ ] Business impact section shows correct penalty tier for any combination of non-compliant chapters
- [ ] Business impact shows empty state gracefully when all requirements are compliant
- [ ] Stacked bars per chapter: widths sum to exactly 100% (handles rounding via flex overflow)
- [ ] Stacked bars: not-applicable chapters render as fully gray (N/A) with no colored segments
- [ ] Chapter N/A flag: chapters with `applicable: False` in `chapter_scores` are visually distinguished (grayed title, N/A label instead of score)
- [ ] Quick wins empty state: renders message if no low-effort/priority-1-2 gaps exist
- [ ] Critical findings: correctly ranks by remediation_priority, not just risk_level alphabetically
- [ ] Root cause breakdown: not rendered if all gaps have `null` root_cause_category (handles legacy data)
- [ ] Full table is collapsible by default (via `<details>`) — default open for now, closeable
- [ ] All new sections respect the existing Tailwind design system (navy brand, no shadows, `rounded-xl border border-gray-200`)
- [ ] No `<script>` tags introduced inside `report_summary.html` partial
- [ ] HTMX `hx-swap="innerHTML"` load of the partial continues to work correctly
- [ ] Template renders correctly when `gap_items` is empty (assessment with no gaps found)
- [ ] Gauge SVG is accessible: `aria-label` set to "Overall compliance score: X%"

---

## System-Wide Impact

**Interaction graph:**
`GET /assessments/{id}/report-summary` → `web.py:report_summary` → 3 new helper functions → `report_summary.html` partial. No new DB queries — all computation is done over the already-fetched `gap_items` list. Zero performance impact.

**Backward compatibility:**
`chapter_scores` dict now has `"applicable"` key (added by scoring.py fix). Template must access `data.score` not `data["score"]` — Jinja2's attribute-or-key resolution handles both. No API schema change (Pydantic `ChapterScore` drops the extra key silently in API responses, intentional).

**State lifecycle:** No DB writes. Read-only rendering endpoint. No risk.

**API surface:** `GET /api/assessments/{id}/report` (JSON API) is unaffected — it uses `ReportOut` schema via `reports.py`, not the web router.

---

## Dependencies & Risks

| Risk | Mitigation |
|---|---|
| SVG gauge looks off at boundary scores (0%, 100%) | Test explicitly; at 0% the offset = circumference = no arc drawn; at 100% offset = 0 = full arc |
| Stacked bar width rounding causes bars to exceed 100% | Use `overflow-hidden` on the container; browser clips overflow naturally |
| `root_cause_category` is null on pre-Phase-3 gap items | Guard: only render section if `root_cause_counts` is non-empty |
| Business impact penalty map needs updates when DPDPA rules are notified | Keep `PENALTY_MAP` as a named constant in `web.py` with a comment linking to the Act schedule |
| `<details>` tag default-open state may confuse users expecting it closed | Start as `open` attribute on `<details>` for now — can toggle default later |

---

## Key Files

| File | Change |
|---|---|
| `app/routers/web.py` | Add 3 helper functions; extend `report_summary` context |
| `app/templates/partials/report_summary.html` | Major restructure — add 5 new sections, relabel existing |

No new files needed. No DB migrations. No schema changes.

---

## Sources & References

### Internal References
- Design system: `docs/design.md` — card patterns, color palette, SVG spinner precedents
- Existing visualization pattern: `app/templates/partials/report_summary.html:38–59` (chapter score bars)
- Coverage chip grid: `app/templates/partials/desk_review_findings.html:100–125`
- HTMX swap pattern: `app/templates/partials/report_tab.html:1–15`
- Report endpoint: `app/routers/web.py:815–855` (`report_summary`)
- Scoring constants: `app/services/scoring.py` (`RATING_THRESHOLDS`, `STATUS_SCORES`)
- Root cause labels: `app/dpdpa/framework.py:ROOT_CAUSE_CLUSTERS`

### DPDPA Penalty Reference
- DPDPA 2023 Schedule: Sections 33–40 (penalty provisions)
- Penalty tiers: ₹50Cr (consent/notice/rights), ₹200Cr (children's data), ₹250Cr (security/breach notification), ₹500Cr (repeat)
