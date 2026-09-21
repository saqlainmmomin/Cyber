# Pre-Work Sprint: Fix Bugs + Build Test Infrastructure

**Date:** 2026-09-21
**Repo:** `saqlainmmomin/Cyber`, local `~/dpdpa-gap-tool/`
**Context:** Adversarial review (`tasks/2026-09-21-adversarial-review.md`) found two live bugs and missing infrastructure that block the revised 4-phase implementation plan (`docs/plans/2026-09-21-002-revised-implementation-plan.md`). This sprint fixes them before any schema work begins.
**Branch:** Create `pre-work-sprint` from `main`.

Five independent tasks. Each should be its own commit. They share no code dependencies and can be built in any order, but PW-4 (test harness) is the most valuable — it becomes the regression baseline for all future phases.

---

## Task 1 — PW-1: Fix questionnaire column rebuild

**Bug:** `app/main.py:83-117` (`_ensure_questionnaire_answer_constraint`) drops and recreates `questionnaire_responses` with a hardcoded 8-column CREATE TABLE. The model in `app/models/questionnaire.py` defines 11 columns — `cluster_id` and `answer_source` are added by `_run_migrations()` but lost when the rebuild fires on an incrementally-upgraded database.

**Files to change:**

| File | What |
|---|---|
| `app/main.py:86-100` | Add `cluster_id TEXT` and `answer_source VARCHAR(20) DEFAULT 'human'` to the CREATE TABLE statement. Add them to the INSERT...SELECT on lines 103-113. |

**The fix is mechanical:**

1. In the CREATE TABLE (line 86-100), add after `submitted_at`:
   ```sql
   cluster_id TEXT,
   answer_source VARCHAR(20) DEFAULT 'human',
   ```

2. In the INSERT...SELECT (lines 103-113), add `cluster_id, answer_source` to both the column list and the SELECT list.

**Test to add:** `tests/test_questionnaire_rebuild.py`
- Create a questionnaire_responses row with `cluster_id='UCC.01'` and `answer_source='document'`
- Remove the check constraint from the table (to trigger the rebuild path)
- Call `_ensure_questionnaire_answer_constraint(conn)`
- Assert the row still has `cluster_id='UCC.01'` and `answer_source='document'`

**Verification:** `uv run pytest -q` — full suite must still pass (128+ tests, 0 failures).

---

## Task 2 — PW-2: Stop destructive re-runs

**Bug:** `app/routers/analysis.py:257-259` deletes all GapItems and the GapReport before re-running analysis. `app/routers/web.py:1754-1756` deletes all DeskReviewFindings before re-running desk review. This destroys history that the Phase 1 migration script needs to backfill into the Conclusion model.

**Files to change:**

| File | What |
|---|---|
| `app/models/report.py` | Add `legacy_history: Mapped[str \| None] = mapped_column(Text, nullable=True)` to `GapReport`. |
| `app/models/desk_review.py` | Add `legacy_history: Mapped[str \| None] = mapped_column(Text, nullable=True)` to `DeskReviewSummary`. |
| `app/main.py` | Add `("legacy_history", "TEXT")` to the migrations dict for `gap_reports` and `desk_review_summaries`. |
| `app/routers/analysis.py:~250-260` | Before deleting GapItems/GapReport, serialize them to JSON and store in `gap_report.legacy_history`. |
| `app/routers/web.py:~1750-1760` | Before deleting DeskReviewFindings, serialize them to JSON and store in `desk_review_summary.legacy_history`. |

**Serialization approach:**
```python
import json
from datetime import datetime

def _serialize_for_history(rows, label: str) -> str:
    """Serialize SQLAlchemy rows to JSON for legacy_history preservation."""
    snapshot = {
        "preserved_at": datetime.now().isoformat(),
        "label": label,
        "rows": [
            {c.name: getattr(row, c.name) for c in row.__table__.columns}
            for row in rows
        ],
    }
    # Append to existing history if present (multiple re-runs)
    return json.dumps(snapshot, default=str)
```

For GapReport, the history should accumulate — if `legacy_history` already has content, parse it as a list and append the new snapshot. Same for DeskReviewSummary.

**Important:** Do NOT change the re-run behavior itself. Analysis and desk review should still produce fresh results. The only change is that the about-to-be-deleted data is preserved in the `legacy_history` column before deletion.

**Test to add:** `tests/test_history_preservation.py`
- Create an assessment with a GapReport and GapItems
- Trigger analysis re-run (or call the serialization function directly)
- Assert `gap_report.legacy_history` contains the original GapItems data
- Trigger a second re-run
- Assert `legacy_history` now contains both snapshots

**Verification:** `uv run pytest -q` — full suite passes. Manual: run analysis on a test assessment, re-run, check that `legacy_history` is populated via a quick DB query.

---

## Task 3 — PW-3: Fix branding import-order bug

**Bug:** `app/main.py:21-25` sets `web.templates.env.globals["branding"]` as a module-level side effect. Tests that import templates through `web.py` without importing `main.py` first get an undefined `branding` variable, causing 5 template tests to fail when run in isolation.

**Files to change:**

| File | What |
|---|---|
| New `app/templates/config.py` | Extract template configuration into a standalone function. |
| `app/main.py:21-25` | Replace inline branding setup with a call to the new function. |
| `app/routers/web.py` | Import and call the configuration function when creating the templates instance. |
| `tests/conftest.py` | Call the configuration function in test fixtures that render templates. |

**Design:**

```python
# app/templates/config.py
from app.config import settings

def configure_templates(templates):
    """Set template globals. Safe to call multiple times (idempotent)."""
    templates.env.globals["branding"] = {
        "firm_name": settings.firm_name,
        "firm_primary_hex": settings.firm_primary_hex,
        "has_custom_nav_color": settings.firm_primary_hex != "#2563eb",
    }
```

In `app/routers/web.py`, after creating the `Jinja2Templates` instance, call `configure_templates(templates)`. In `app/main.py`, remove the 5 lines that set branding directly — the import of `web` now handles it.

**Test:** Run the 5 previously-failing tests in isolation:
```bash
uv run pytest tests/test_content_integrity.py -q
```
They must pass without importing `main.py`.

**Verification:** `uv run pytest -q` — full suite passes. The isolated template test run also passes.

---

## Task 4 — PW-4: Build HTTP integration test harness

**Gap:** 128 existing tests pass, but only 2 use `TestClient` for HTTP-level testing. There are zero route-level integration tests for the core assessment workflow. All future phases need this harness for regression safety.

**Files to create:**

| File | What |
|---|---|
| `tests/integration/__init__.py` | Empty. |
| `tests/integration/conftest.py` | Shared fixtures for integration tests. |
| `tests/integration/test_assessment_crud.py` | Create, read, list, archive assessment. |
| `tests/integration/test_document_upload.py` | Upload a document, verify AssessmentDocument created. |
| `tests/integration/test_questionnaire.py` | Save questionnaire responses, verify persistence. |
| `tests/integration/test_desk_review.py` | Trigger desk review (mocked LLM), verify DeskReviewSummary created. |
| `tests/integration/test_analysis.py` | Trigger analysis (mocked LLM), verify GapReport + GapItems created. |
| `tests/integration/test_report.py` | Render report page for an assessed assessment, verify 200 response. |

**Fixture design (`tests/integration/conftest.py`):**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

@pytest.fixture
def db_session():
    """Fresh in-memory SQLite database per test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    """TestClient with dependency-overridden database."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

For LLM-dependent routes (desk review, analysis), mock `app.services.llm_client` to return canned responses. Use the existing pattern from `tests/support/analyzer_mock.py` if it fits, or a simpler `unittest.mock.patch` approach.

**Minimum coverage per test file:**

- `test_assessment_crud.py`: POST /assessments/new → 302 redirect, GET /assessments/{id} → 200, DELETE /assessments/{id} → verify removed
- `test_document_upload.py`: POST /assessments/{id}/upload with a test file → 200, verify document in DB
- `test_questionnaire.py`: POST /assessments/{id}/questionnaire/save → 200, verify QuestionnaireResponse rows
- `test_desk_review.py`: POST /assessments/{id}/run-desk-review (mocked) → 200, verify DeskReviewSummary
- `test_analysis.py`: POST /assessments/{id}/run-analysis (mocked) → 200, verify GapReport + GapItems
- `test_report.py`: GET /assessments/{id}/report → 200 with valid HTML

**Verification:** `uv run pytest tests/integration/ -q` — at least 6 tests passing. `uv run pytest -q` — full suite (128 + new) passes.

---

## Task 5 — PW-5: Add foreign keys to existing tables

**Gap:** Zero `ForeignKey` declarations exist anywhere in `app/models/`. All cross-table references are bare string columns. `db.delete(assessment)` leaves orphaned GapReports, DeskReviewFindings, AssessmentDocuments, and QuestionnaireResponses.

**This is the most delicate task.** Read the approach carefully.

**Step 1: Orphan detection script**

Create `scripts/detect_orphans.py`:
```python
"""Find rows in child tables whose assessment_id/report_id doesn't exist in the parent table."""
```
- Check every child table's reference against its parent
- Print orphaned row counts and IDs
- This is diagnostic only — does not modify data

Run it against the production database (if any rows exist). If orphans are found, log them for manual review.

**Step 2: Add ForeignKey declarations to models**

| File | Column | FK Target |
|---|---|---|
| `app/models/assessment.py` (AssessmentDocument) | `assessment_id` | `assessments.id` |
| `app/models/questionnaire.py` | `assessment_id` | `assessments.id` |
| `app/models/desk_review.py` (DeskReviewSummary) | `assessment_id` | `assessments.id` |
| `app/models/desk_review.py` (DeskReviewFinding) | `assessment_id` | `assessments.id` |
| `app/models/report.py` (GapReport) | `assessment_id` | `assessments.id` |
| `app/models/report.py` (GapItem) | `report_id` | `gap_reports.id` |
| `app/models/initiative.py` | `report_id` | `gap_reports.id` |
| `app/models/rfi.py` | `assessment_id` | `assessments.id` |

Add `ForeignKey("assessments.id")` (or `"gap_reports.id"`) to each `mapped_column` declaration. Do NOT add `relationship()` declarations yet — that's a Phase 1 concern.

**Step 3: Replace hard delete with soft delete**

In `app/routers/web.py:351-367` (`delete_assessment_web`) and `app/routers/assessments.py` (if there's a delete endpoint):
- Instead of `db.delete(assessment)`, set `assessment.status = "archived"` and `db.commit()`
- Filter archived assessments out of the dashboard query
- Add an "Archived" filter to the dashboard (optional, nice-to-have)

**Step 4: Add migration for FK enforcement**

Since SQLite doesn't enforce FKs on ALTER TABLE and `create_all` won't retroactively add them to existing tables, the enforcement comes from:
1. The model declarations (SQLAlchemy validates on insert/update)
2. `PRAGMA foreign_keys = ON` in the engine connect args
3. New tables created by Alembic in Phase 1 will have proper FK constraints

Add to `app/database.py`:
```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**Test to add:** `tests/test_foreign_keys.py`
- Create an assessment, then a GapReport referencing it
- Attempt to delete the assessment via the web route → verify it's archived, not deleted
- Attempt to create a GapReport with a non-existent assessment_id → verify the insert fails (FK violation, or at least SQLAlchemy relationship validation)
- Run orphan detection script on the test DB → verify zero orphans

**Verification:** `uv run pytest -q` — full suite passes. Orphan detection script runs clean on production DB.

---

## Constraints

- Do NOT modify the schema beyond what each task describes. No new domain tables.
- Do NOT change the assessment workflow behavior (create, scope, questionnaire, analysis, report). Only preserve history and add integrity.
- Do NOT touch framework definitions, UCC mappings, scoring logic, or PDF export.
- Keep each task in its own commit with a clear message.
- Run `uv run pytest -q` after each task and report the result.

## Definition of Done

All five tasks committed. Full test suite passes (128 existing + new tests). No regressions. The codebase is ready for Phase 1 (Alembic adoption + target schema).

## Suggested order

PW-3 (branding fix, 30 min) → PW-1 (questionnaire fix, 30 min) → PW-4 (test harness, 2-3 hours) → PW-2 (history preservation, 1 hour) → PW-5 (foreign keys, 1-2 hours).

PW-3 first because it unblocks PW-4's test fixtures. PW-1 is a quick win. PW-4 is the long pole and everything else benefits from having it. PW-2 and PW-5 are independent.

## Execution: Claude, not Codex

Use **Claude** (interactive session) for all 5 pre-work tasks. Reasoning:

- **PW-1 through PW-3** are surgical 1-2 file edits. Claude handles these in minutes. No parallelism advantage from Codex.
- **PW-4 (test harness)** needs to understand existing test patterns (`tests/support/analyzer_mock.py`), route signatures, DB fixtures, and LLM mocking. If the first fixture doesn't work, you iterate in-session. Codex runs blind and you'd debug its output anyway.
- **PW-5 (FK retrofit)** touches every model file and the delete routes. Needs judgment calls on orphan handling and SQLite FK pragma edge cases. Interactive beats fire-and-forget.

Run PW-3 → PW-1 → PW-4 → PW-2 → PW-5 in one Claude session (or split after PW-4 if context gets long). Should take an afternoon.

**Save Codex for Phase 1** — the Alembic adoption, target schema migration, and backfill script are more mechanical, well-specified, and benefit from Codex's longer unattended runs.
