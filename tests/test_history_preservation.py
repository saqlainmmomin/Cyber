"""PW-2: Verify legacy_history is populated before destructive re-runs."""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.assessment import Assessment
from app.models.report import GapItem, GapReport
from app.models.desk_review import DeskReviewFinding, DeskReviewSummary


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'history.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def _make_assessment(db):
    a = Assessment(company_name="HistoryCo", industry="Tech", company_size="small")
    db.add(a)
    db.commit()
    return a.id


def _make_report_with_items(db, assessment_id):
    report = GapReport(
        assessment_id=assessment_id,
        overall_score=65.0,
        chapter_scores=json.dumps({"ch2": 70}),
        executive_summary="Original summary",
        raw_ai_response="{}",
    )
    db.add(report)
    db.flush()

    item = GapItem(
        report_id=report.id,
        requirement_id="CH2.CONSENT.1",
        framework_id="dpdpa",
        chapter="ch2",
        requirement_title="Consent",
        compliance_status="partially_compliant",
        current_state="Partial",
        gap_description="Missing granular consent",
        risk_level="medium",
        remediation_action="Add consent",
        remediation_priority=1,
        remediation_effort="moderate",
        timeline_weeks=4,
    )
    db.add(item)
    db.commit()
    return report.id


def test_gap_report_history_preserved_on_rerun(db):
    """Simulates the serialization logic from analysis.py trigger_analysis."""
    from datetime import datetime

    assessment_id = _make_assessment(db)
    report_id = _make_report_with_items(db, assessment_id)

    existing = db.query(GapReport).filter(GapReport.assessment_id == assessment_id).first()
    old_items = db.query(GapItem).filter(GapItem.report_id == existing.id).all()

    snapshot = {
        "preserved_at": datetime.now().isoformat(),
        "label": "gap_analysis_rerun",
        "report": {c.name: getattr(existing, c.name) for c in existing.__table__.columns},
        "items": [
            {c.name: getattr(item, c.name) for c in item.__table__.columns}
            for item in old_items
        ],
    }
    history = [snapshot]
    carried = json.dumps(history, default=str)

    db.query(GapItem).filter(GapItem.report_id == existing.id).delete()
    db.delete(existing)
    db.flush()

    new_report = GapReport(
        assessment_id=assessment_id,
        overall_score=80.0,
        chapter_scores=json.dumps({"ch2": 85}),
        executive_summary="New summary",
        raw_ai_response="{}",
        legacy_history=carried,
    )
    db.add(new_report)
    db.commit()

    loaded = json.loads(new_report.legacy_history)
    assert isinstance(loaded, list)
    assert len(loaded) == 1
    assert loaded[0]["report"]["executive_summary"] == "Original summary"
    assert len(loaded[0]["items"]) == 1
    assert loaded[0]["items"][0]["requirement_id"] == "CH2.CONSENT.1"


def test_gap_report_history_accumulates(db):
    """Second re-run should append to history, not replace."""
    from datetime import datetime

    assessment_id = _make_assessment(db)

    # First run
    first = GapReport(
        assessment_id=assessment_id,
        overall_score=60.0,
        chapter_scores="{}",
        executive_summary="First",
        raw_ai_response="{}",
        legacy_history=json.dumps([{
            "preserved_at": datetime.now().isoformat(),
            "label": "gap_analysis_rerun",
            "report": {"executive_summary": "Zeroth"},
            "items": [],
        }]),
    )
    db.add(first)
    db.commit()

    # Simulate second re-run serialization
    history = json.loads(first.legacy_history)
    history.append({
        "preserved_at": datetime.now().isoformat(),
        "label": "gap_analysis_rerun",
        "report": {"executive_summary": "First"},
        "items": [],
    })
    carried = json.dumps(history, default=str)

    db.delete(first)
    db.flush()
    second = GapReport(
        assessment_id=assessment_id,
        overall_score=80.0,
        chapter_scores="{}",
        executive_summary="Second",
        raw_ai_response="{}",
        legacy_history=carried,
    )
    db.add(second)
    db.commit()

    loaded = json.loads(second.legacy_history)
    assert len(loaded) == 2
    assert loaded[0]["report"]["executive_summary"] == "Zeroth"
    assert loaded[1]["report"]["executive_summary"] == "First"


def test_desk_review_history_preserved(db):
    """Verify desk review findings are serialized before deletion."""
    from datetime import datetime, timezone

    assessment_id = _make_assessment(db)

    summary = DeskReviewSummary(
        assessment_id=assessment_id,
        status="completed",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(summary)
    db.flush()

    finding = DeskReviewFinding(
        assessment_id=assessment_id,
        finding_type="evidence",
        requirement_id="CH2.CONSENT.1",
        content="Found consent form in policy doc",
        severity="medium",
    )
    db.add(finding)
    db.commit()

    # Simulate the serialization from web.py run_desk_review_web
    old_findings = db.query(DeskReviewFinding).filter(
        DeskReviewFinding.assessment_id == assessment_id
    ).all()
    snapshot = {
        "preserved_at": datetime.now(timezone.utc).isoformat(),
        "label": "desk_review_rerun",
        "findings": [
            {c.name: getattr(f, c.name) for c in f.__table__.columns}
            for f in old_findings
        ],
    }
    summary.legacy_history = json.dumps([snapshot], default=str)
    db.query(DeskReviewFinding).filter(
        DeskReviewFinding.assessment_id == assessment_id
    ).delete()
    db.commit()

    loaded = json.loads(summary.legacy_history)
    assert len(loaded) == 1
    assert loaded[0]["findings"][0]["requirement_id"] == "CH2.CONSENT.1"
    assert loaded[0]["findings"][0]["content"] == "Found consent form in policy doc"
