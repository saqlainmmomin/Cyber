# Session C — Backend Features

> **Runtime:** Codex
> **Parallel with:** Session A (Design & Polish), Session B (Interaction & Feature UI)
> **Coordination file:** `docs/sessions/COORDINATION.md` — READ THIS FIRST

---

## Mission

You are responsible for the **backend** of three new features:

1. **Remediation Tracking** — per gap item: status, owner, target date, notes
2. **Manager Review Workflow** — AI findings reviewed before report release
3. **Assessment Comparison** — delta view between two assessments for same company

You own all Python files: models, migrations, routers, services, schemas. You do NOT touch template files (`.html`) or JavaScript files.

---

## Context

CyberAssess is a compliance gap assessment platform built with FastAPI + SQLAlchemy 2.0 (synchronous, SQLite). Read `CLAUDE.md` in the project root for full architecture details.

Key rules:
- Database is SQLite with `check_same_thread=False`
- No SQLAlchemy `relationship()` declarations — all joins via `.filter()` on FK columns
- JSON stored as TEXT columns (no JSON column type)
- Migrations are DIY in `app/main.py:_run_migrations()`
- Scoring is deterministic and server-side — Claude outputs qualitative strings only
- All PDF text through `S()` sanitizer in `pdf_export.py` (you don't touch this file, but be aware)

Two other sessions run in parallel:
- **Session A** modifies template files (dark mode, visual polish)
- **Session B** creates new template files and JS for the features you build

Your endpoints return HTML partials for HTMX swaps. The template files are created by Session B, but you render them via Jinja2 from your routers. The template filenames and expected context variables are defined in `COORDINATION.md`.

---

## Pre-read Required

```
docs/sessions/COORDINATION.md          — contracts, endpoint specs, column names
CLAUDE.md                              — project architecture, hard rules
app/models/report.py                   — GapReport + GapItem models
app/models/assessment.py               — Assessment + AssessmentDocument models
app/main.py                            — app setup, migrations, router includes
app/routers/reports.py                 — existing report endpoints
app/routers/web.py                     — existing web routes
app/services/scoring.py                — scoring engine
app/schemas/report.py                  — existing report schemas
```

---

## Feature 1: Remediation Tracking

### 1a. Model Changes

In `app/models/report.py`, add these columns to `GapItem`:

```python
from datetime import datetime
from sqlalchemy import DateTime

# Add to GapItem class:
remediation_status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="open")
remediation_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
remediation_target_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
remediation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
remediation_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Column names are mandated by COORDINATION.md Contract 7. Use these exact names.**

### 1b. Migration

In `app/main.py:_run_migrations()`, add migration for the 5 new columns:

```python
# Remediation tracking columns on gap_items
for col_name, col_type in [
    ("remediation_status", "VARCHAR(20) DEFAULT 'open'"),
    ("remediation_owner", "VARCHAR(255)"),
    ("remediation_target_date", "DATETIME"),
    ("remediation_notes", "TEXT"),
    ("remediation_closed_at", "DATETIME"),
]:
    try:
        conn.execute(text(f"ALTER TABLE gap_items ADD COLUMN {col_name} {col_type}"))
    except Exception:
        pass  # column already exists
```

### 1c. Schema

Create `app/schemas/remediation.py`:

```python
from datetime import datetime
from pydantic import BaseModel


class RemediationUpdate(BaseModel):
    remediation_status: str | None = None
    remediation_owner: str | None = None
    remediation_target_date: datetime | None = None
    remediation_notes: str | None = None


class RemediationSummary(BaseModel):
    open: int = 0
    in_progress: int = 0
    closed: int = 0
    accepted_risk: int = 0
    total: int = 0
```

### 1d. Router

Create `app/routers/remediation.py`:

```python
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from app.database import SessionLocal
from app.models.report import GapItem, GapReport
from app.schemas.remediation import RemediationUpdate

router = APIRouter(prefix="/api/assessments", tags=["remediation"])


@router.patch("/{assessment_id}/gap-items/{item_id}/remediation")
def update_remediation(
    assessment_id: str,
    item_id: str,
    update: RemediationUpdate,
    response: Response,
):
    with SessionLocal() as db:
        # Verify item belongs to this assessment's report
        report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        if not report:
            raise HTTPException(404, "Report not found")

        item = db.execute(
            select(GapItem).where(GapItem.id == item_id, GapItem.report_id == report.id)
        ).scalar_one_or_none()
        if not item:
            raise HTTPException(404, "Gap item not found")

        if update.remediation_status is not None:
            item.remediation_status = update.remediation_status
            if update.remediation_status == "closed" and not item.remediation_closed_at:
                item.remediation_closed_at = datetime.now(timezone.utc)
            elif update.remediation_status != "closed":
                item.remediation_closed_at = None
        if update.remediation_owner is not None:
            item.remediation_owner = update.remediation_owner
        if update.remediation_target_date is not None:
            item.remediation_target_date = update.remediation_target_date
        if update.remediation_notes is not None:
            item.remediation_notes = update.remediation_notes

        db.commit()
        db.refresh(item)

        response.headers["X-Toast-Message"] = "Remediation updated"
        response.headers["X-Toast-Type"] = "success"

        # Return the updated remediation panel partial
        from app.main import templates
        return templates.TemplateResponse(
            "partials/remediation_panel.html",
            {"request": None, "item": item, "assessment_id": assessment_id},
        )


@router.get("/{assessment_id}/remediation-summary")
def get_remediation_summary(assessment_id: str):
    with SessionLocal() as db:
        report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        if not report:
            raise HTTPException(404, "Report not found")

        items = db.execute(
            select(GapItem).where(GapItem.report_id == report.id)
        ).scalars().all()

        counts = {"open": 0, "in_progress": 0, "closed": 0, "accepted_risk": 0}
        for item in items:
            status = item.remediation_status or "open"
            if status in counts:
                counts[status] += 1

        counts["total"] = len(items)
        return counts
```

**Important:** The `templates.TemplateResponse` call renders Session B's `remediation_panel.html`. If that file doesn't exist yet when you test, the endpoint will error — that's expected during parallel development. You can return a simple JSON response as a fallback during testing.

### 1e. Register Router

In `app/main.py`, add:
```python
from app.routers import remediation
app.include_router(remediation.router)
```

---

## Feature 2: Manager Review Workflow

### 2a. Model Changes

In `app/models/assessment.py`, add to `Assessment`:

```python
review_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

In `app/models/report.py`, add to `GapItem`:

```python
review_status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="draft")
ai_compliance_status: Mapped[str | None] = mapped_column(Text, nullable=True)
ai_gap_description: Mapped[str | None] = mapped_column(Text, nullable=True)
ai_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Column names are mandated by COORDINATION.md Contract 7.**

### 2b. Migration

In `app/main.py:_run_migrations()`:

```python
# Review workflow columns on assessments
try:
    conn.execute(text("ALTER TABLE assessments ADD COLUMN review_status VARCHAR(20)"))
except Exception:
    pass

# Review workflow columns on gap_items
for col_name, col_type in [
    ("review_status", "VARCHAR(20) DEFAULT 'draft'"),
    ("ai_compliance_status", "TEXT"),
    ("ai_gap_description", "TEXT"),
    ("ai_risk_level", "VARCHAR(20)"),
    ("reviewer_notes", "TEXT"),
    ("reviewed_by", "VARCHAR(255)"),
    ("reviewed_at", "DATETIME"),
]:
    try:
        conn.execute(text(f"ALTER TABLE gap_items ADD COLUMN {col_name} {col_type}"))
    except Exception:
        pass

# Backfill ai_* columns for existing records
try:
    conn.execute(text("""
        UPDATE gap_items
        SET ai_compliance_status = compliance_status,
            ai_gap_description = gap_description,
            ai_risk_level = risk_level
        WHERE ai_compliance_status IS NULL
    """))
except Exception:
    pass
```

### 2c. Preserve AI Output During Analysis

In `app/services/claude_analyzer.py`, where GapItem records are created after gap analysis, ensure the `ai_*` columns are populated at creation time:

```python
# When creating GapItem, also set ai_* columns:
gap_item = GapItem(
    # ... existing fields ...
    ai_compliance_status=assessment_data["compliance_status"],
    ai_gap_description=assessment_data["gap_description"],
    ai_risk_level=assessment_data["risk_level"],
    review_status="draft",
)
```

Find the GapItem creation loop in `claude_analyzer.py` and add these three additional fields. The existing `compliance_status`, `gap_description`, and `risk_level` fields continue to be set as before — the `ai_*` fields are copies that never get overwritten.

### 2d. Schema

Create `app/schemas/review.py`:

```python
from pydantic import BaseModel


class ReviewItemUpdate(BaseModel):
    review_status: str | None = None  # accepted | rejected
    compliance_status: str | None = None  # only if reviewer edits
    gap_description: str | None = None
    risk_level: str | None = None
    reviewer_notes: str | None = None


class ReviewApproval(BaseModel):
    reviewer_name: str


class ReviewRejection(BaseModel):
    reviewer_name: str
    rejection_reason: str | None = None
```

### 2e. Approval Gate Helper

Create a shared helper that gates all client-facing output. Add to `app/routers/reports.py` or a new `app/utils/review_gate.py`:

```python
from fastapi import HTTPException
from sqlalchemy import select

from app.database import SessionLocal
from app.models.assessment import Assessment


def require_review_approval(assessment_id: str) -> None:
    """Raise 403 if assessment is not approved for release."""
    with SessionLocal() as db:
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one_or_none()
        if not assessment:
            raise HTTPException(404, "Assessment not found")
        if assessment.review_status != "approved":
            raise HTTPException(
                403,
                "Report not yet approved for release. Complete the review process first.",
            )
```

### 2f. Gate PDF Download

In `app/routers/reports.py`, find the PDF download endpoint and add the gate:

```python
from app.utils.review_gate import require_review_approval

@router.get("/{assessment_id}/report/pdf")
def download_pdf(assessment_id: str):
    require_review_approval(assessment_id)
    # ... existing PDF generation code ...
```

Also gate any RFI PDF/DOCX download endpoints.

### 2g. Review Router

Create `app/routers/review.py`:

```python
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import select, func

from app.database import SessionLocal
from app.models.assessment import Assessment
from app.models.report import GapItem, GapReport
from app.schemas.review import ReviewApproval, ReviewItemUpdate, ReviewRejection

router = APIRouter(prefix="/api/assessments", tags=["review"])


@router.patch("/{assessment_id}/review/items/{item_id}")
def disposition_item(
    assessment_id: str,
    item_id: str,
    update: ReviewItemUpdate,
    response: Response,
):
    with SessionLocal() as db:
        report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        if not report:
            raise HTTPException(404, "Report not found")

        item = db.execute(
            select(GapItem).where(GapItem.id == item_id, GapItem.report_id == report.id)
        ).scalar_one_or_none()
        if not item:
            raise HTTPException(404, "Gap item not found")

        if update.review_status:
            item.review_status = update.review_status
            item.reviewed_at = datetime.now(timezone.utc)

        # If reviewer edits the assessment (overrides AI)
        if update.compliance_status:
            item.compliance_status = update.compliance_status
        if update.gap_description:
            item.gap_description = update.gap_description
        if update.risk_level:
            item.risk_level = update.risk_level
        if update.reviewer_notes is not None:
            item.reviewer_notes = update.reviewer_notes

        db.commit()
        db.refresh(item)

        # Set assessment to under_review if not already
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one()
        if not assessment.review_status:
            assessment.review_status = "under_review"
            db.commit()

        status_label = (update.review_status or "updated").replace("_", " ").title()
        response.headers["X-Toast-Message"] = f"Finding {status_label}"
        response.headers["X-Toast-Type"] = "success"

        # Return updated finding card partial (Session B creates this template)
        from app.main import templates
        return templates.TemplateResponse(
            "partials/review_finding_card.html",
            {"request": None, "item": item, "assessment": assessment},
        )


@router.post("/{assessment_id}/review/approve")
def approve_assessment(
    assessment_id: str,
    approval: ReviewApproval,
    response: Response,
):
    with SessionLocal() as db:
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one_or_none()
        if not assessment:
            raise HTTPException(404, "Assessment not found")

        report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        if not report:
            raise HTTPException(400, "No report to approve")

        # Check all items are reviewed
        draft_count = db.execute(
            select(func.count()).select_from(GapItem).where(
                GapItem.report_id == report.id,
                GapItem.review_status == "draft",
            )
        ).scalar()
        if draft_count > 0:
            raise HTTPException(
                400,
                f"{draft_count} findings still in draft. Review all findings before approving.",
            )

        assessment.review_status = "approved"

        # Stamp reviewer on all accepted items
        items = db.execute(
            select(GapItem).where(GapItem.report_id == report.id)
        ).scalars().all()
        now = datetime.now(timezone.utc)
        for item in items:
            if not item.reviewed_by:
                item.reviewed_by = approval.reviewer_name
                item.reviewed_at = now

        db.commit()

        response.headers["X-Toast-Message"] = "Assessment approved for release"
        response.headers["X-Toast-Type"] = "success"
        response.headers["HX-Redirect"] = f"/assessments/{assessment_id}?tab=report"
        return {"status": "approved"}


@router.post("/{assessment_id}/review/reject")
def reject_assessment(
    assessment_id: str,
    rejection: ReviewRejection,
    response: Response,
):
    with SessionLocal() as db:
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one_or_none()
        if not assessment:
            raise HTTPException(404, "Assessment not found")

        assessment.review_status = "rejected"
        db.commit()

        response.headers["X-Toast-Message"] = "Assessment rejected — re-analysis may be needed"
        response.headers["X-Toast-Type"] = "error"
        return {"status": "rejected"}
```

### 2h. Web Routes for Review Page

In `app/routers/web.py`, add:

```python
@router.get("/assessments/{assessment_id}/review")
def review_page(request: Request, assessment_id: str):
    with SessionLocal() as db:
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one_or_none()
        if not assessment:
            raise HTTPException(404)

        report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        if not report:
            raise HTTPException(400, "No report — run analysis first")

        gap_items = db.execute(
            select(GapItem).where(GapItem.report_id == report.id)
        ).scalars().all()

        draft_count = sum(1 for i in gap_items if (i.review_status or "draft") == "draft")

        return templates.TemplateResponse(
            "pages/review.html",
            {
                "request": request,
                "assessment": assessment,
                "gap_items": gap_items,
                "draft_count": draft_count,
                "reviewer_name": "",  # TODO: from env or session
            },
        )
```

### 2i. Register Router

In `app/main.py`:
```python
from app.routers import review
app.include_router(review.router)
```

---

## Feature 3: Assessment Comparison

### 3a. Delta Computation

In `app/services/scoring.py`, add:

```python
def compute_delta(
    current_items: list,
    previous_items: list,
) -> dict:
    """Compare two sets of GapItems and return per-requirement deltas."""
    prev_map = {item.requirement_id: item for item in previous_items}
    deltas = []
    improved = regressed = unchanged = 0

    for item in current_items:
        prev = prev_map.get(item.requirement_id)
        if not prev:
            deltas.append({
                "requirement_id": item.requirement_id,
                "requirement_title": item.requirement_title,
                "old_status": None,
                "new_status": item.compliance_status,
                "status_changed": True,
                "is_new": True,
            })
            continue

        status_changed = item.compliance_status != prev.compliance_status

        # Determine direction
        status_order = {
            "non_compliant": 0,
            "partially_compliant": 1,
            "planned": 2,
            "compliant": 3,
            "not_applicable": 3,
        }
        old_rank = status_order.get(prev.compliance_status, 0)
        new_rank = status_order.get(item.compliance_status, 0)

        if new_rank > old_rank:
            improved += 1
        elif new_rank < old_rank:
            regressed += 1
        else:
            unchanged += 1

        deltas.append({
            "requirement_id": item.requirement_id,
            "requirement_title": item.requirement_title,
            "old_status": prev.compliance_status,
            "new_status": item.compliance_status,
            "status_changed": status_changed,
            "is_new": False,
        })

    return {
        "deltas": sorted(deltas, key=lambda d: (not d["status_changed"], d["requirement_id"])),
        "summary": {
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
        },
    }
```

### 3b. Comparison Endpoints

In `app/routers/reports.py`, add:

```python
@router.get("/{assessment_id}/comparable")
def get_comparable_assessments(assessment_id: str):
    """List other completed assessments for the same company."""
    with SessionLocal() as db:
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one_or_none()
        if not assessment:
            raise HTTPException(404)

        others = db.execute(
            select(Assessment).where(
                Assessment.company_name == assessment.company_name,
                Assessment.id != assessment_id,
                Assessment.status == "completed",
            ).order_by(Assessment.created_at.desc())
        ).scalars().all()

        return [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "status": a.status,
            }
            for a in others
        ]


@router.get("/{assessment_id}/compare/{other_id}")
def compare_assessments(assessment_id: str, other_id: str):
    """Compute delta between two assessments."""
    from app.services.scoring import compute_delta

    with SessionLocal() as db:
        current_report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        previous_report = db.execute(
            select(GapReport).where(GapReport.assessment_id == other_id)
        ).scalar_one_or_none()
        if not current_report or not previous_report:
            raise HTTPException(404, "One or both reports not found")

        current_items = db.execute(
            select(GapItem).where(GapItem.report_id == current_report.id)
        ).scalars().all()
        previous_items = db.execute(
            select(GapItem).where(GapItem.report_id == previous_report.id)
        ).scalars().all()

        return compute_delta(current_items, previous_items)
```

### 3c. Web Route for Comparison Page

In `app/routers/web.py`, add:

```python
@router.get("/assessments/{assessment_id}/compare/{other_id}")
def comparison_page(request: Request, assessment_id: str, other_id: str):
    from app.services.scoring import compute_delta

    with SessionLocal() as db:
        assessment = db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        ).scalar_one_or_none()
        if not assessment:
            raise HTTPException(404)

        current_report = db.execute(
            select(GapReport).where(GapReport.assessment_id == assessment_id)
        ).scalar_one_or_none()
        previous_report = db.execute(
            select(GapReport).where(GapReport.assessment_id == other_id)
        ).scalar_one_or_none()
        if not current_report or not previous_report:
            raise HTTPException(404, "Reports not found")

        current_items = db.execute(
            select(GapItem).where(GapItem.report_id == current_report.id)
        ).scalars().all()
        previous_items = db.execute(
            select(GapItem).where(GapItem.report_id == previous_report.id)
        ).scalars().all()

        result = compute_delta(current_items, previous_items)

        return templates.TemplateResponse(
            "pages/comparison.html",
            {
                "request": request,
                "assessment": assessment,
                "current_report": current_report,
                "previous_report": previous_report,
                "current_score": current_report.overall_score,
                "previous_score": previous_report.overall_score,
                "score_delta": current_report.overall_score - previous_report.overall_score,
                "deltas": result["deltas"],
                "delta_summary": result["summary"],
            },
        )
```

---

## Additional Router Context Changes

### Report Page Context Enhancement

In `app/routers/web.py` (or wherever the report summary page is rendered), add these context variables that Session A and Session B templates expect:

```python
# In the report page route handler, add to context:

# Remediation counts
remediation_counts = {
    "open": sum(1 for i in gap_items if (i.remediation_status or "open") == "open"),
    "in_progress": sum(1 for i in gap_items if i.remediation_status == "in_progress"),
    "closed": sum(1 for i in gap_items if i.remediation_status == "closed"),
    "accepted_risk": sum(1 for i in gap_items if i.remediation_status == "accepted_risk"),
    "total": len([i for i in gap_items if i.compliance_status != "not_applicable"]),
}

# Comparable assessments (for "Compare" button)
comparable_assessments = db.execute(
    select(Assessment).where(
        Assessment.company_name == assessment.company_name,
        Assessment.id != assessment_id,
        Assessment.status == "completed",
    ).order_by(Assessment.created_at.desc()).limit(5)
).scalars().all()

# Gap items grouped by chapter (for Session A's grouped findings view)
from collections import defaultdict
gap_items_by_chapter = defaultdict(list)
for item in gap_items:
    gap_items_by_chapter[item.chapter].append(item)
gap_items_by_chapter = dict(gap_items_by_chapter)

# Review status context
review_status = assessment.review_status
reviewed_by = None
reviewed_at = None
if gap_items:
    reviewed_item = next((i for i in gap_items if i.reviewed_by), None)
    if reviewed_item:
        reviewed_by = reviewed_item.reviewed_by
        reviewed_at = reviewed_item.reviewed_at

# Timeline steps
timeline_steps = [
    ("Scope", assessment.scope_answers is not None),
    ("Documents", bool(documents)),
    ("Desk Review", assessment.desk_review_status == "completed"),
    ("Questionnaire", assessment.status in ("questionnaire_done", "analyzing", "completed")),
    ("Analysis", assessment.status == "completed"),
]
```

Add all of these to the template context dict.

---

## X-Toast-Message Headers

Add `X-Toast-Message` and `X-Toast-Type` response headers to ALL mutation endpoints. Session B's JS listens for these.

Pattern:
```python
response.headers["X-Toast-Message"] = "Human-readable message"
response.headers["X-Toast-Type"] = "success"  # or "error" or "info"
```

Also add toast headers to existing endpoints that mutate data:
- Questionnaire save → "Section saved"
- Document upload → "Document uploaded"
- Analysis trigger → "Analysis started"
- RFI generation → "RFI generated"

---

## Pending Changes File

If you need a template change that only Session A or B can make, document it in `docs/sessions/pending-changes-session-c.md`. Example:

```markdown
# Pending Changes from Session C

## For Session A (template owner):
- report_summary.html needs `gap_items_by_chapter` context variable support (I'm now passing it)
- report_summary.html needs `comparable_assessments` context variable support

## For Session B (JS owner):
- Review page needs `timeline_steps` variable from context (I'm now computing and passing it)
```

---

## Register All Routers

Final state of router includes in `app/main.py`:

```python
from app.routers import remediation, review
# ... existing router includes ...
app.include_router(remediation.router)
app.include_router(review.router)
```

---

## Testing

After implementing:

1. Run `uvicorn app.main:app --reload` — verify migrations execute without error
2. Create a test assessment through the web UI or API
3. Run analysis to generate gap items
4. Test remediation PATCH endpoint via curl:
   ```bash
   curl -X PATCH http://localhost:8000/api/assessments/{id}/gap-items/{item_id}/remediation \
     -H "Content-Type: application/json" \
     -d '{"remediation_status": "in_progress", "remediation_owner": "Test User"}'
   ```
5. Test review disposition via curl:
   ```bash
   curl -X PATCH http://localhost:8000/api/assessments/{id}/review/items/{item_id} \
     -H "Content-Type: application/json" \
     -d '{"review_status": "accepted"}'
   ```
6. Test comparison endpoint:
   ```bash
   curl http://localhost:8000/api/assessments/{id}/compare/{other_id}
   ```
7. Verify PDF download is gated (returns 403 when review_status != 'approved')

---

## What NOT to do

- Do NOT create or edit template files (`.html`) — Session A and B own those
- Do NOT edit `app.js` — Session B owns it
- Do NOT edit CSS files — Session A owns those
- Do NOT add a User model or auth — single-user MVP
- Do NOT create an `review_audit_log` table — too much for MVP
- Do NOT add WebSocket or SSE — HTMX polling is sufficient
- Do NOT modify the scoring formula — scoring stays deterministic
- Do NOT touch `app/utils/pdf_export.py` — it has special rules (all text through `S()`)
- Do NOT modify `app/dpdpa/` or `app/frameworks/` — domain knowledge, not your scope
