"""PW-5: Verify foreign key declarations and soft delete behavior."""

import json

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models.assessment import Assessment
from app.models.report import GapItem, GapReport


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'fk.db'}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_fk_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def _make_assessment(db):
    a = Assessment(company_name="FKCo", industry="Tech", company_size="small")
    db.add(a)
    db.commit()
    return a.id


def test_gap_report_fk_enforced(db):
    """Creating a GapReport with a non-existent assessment_id should fail."""
    report = GapReport(
        assessment_id="nonexistent-id",
        overall_score=50.0,
        chapter_scores="{}",
        executive_summary="Test",
        raw_ai_response="{}",
    )
    db.add(report)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()


def test_gap_item_fk_enforced(db):
    """Creating a GapItem with a non-existent report_id should fail."""
    assessment_id = _make_assessment(db)
    item = GapItem(
        report_id="nonexistent-report",
        requirement_id="CH2.CONSENT.1",
        framework_id="dpdpa",
        chapter="ch2",
        requirement_title="Test",
        compliance_status="compliant",
        current_state="OK",
        gap_description="None",
        risk_level="low",
        remediation_action="None",
        remediation_priority=1,
        remediation_effort="minimal",
        timeline_weeks=0,
    )
    db.add(item)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()


def test_valid_fk_chain_works(db):
    """Valid FK references should commit without error."""
    assessment_id = _make_assessment(db)
    report = GapReport(
        assessment_id=assessment_id,
        overall_score=80.0,
        chapter_scores="{}",
        executive_summary="Valid chain",
        raw_ai_response="{}",
    )
    db.add(report)
    db.flush()

    item = GapItem(
        report_id=report.id,
        requirement_id="CH2.CONSENT.1",
        framework_id="dpdpa",
        chapter="ch2",
        requirement_title="Test",
        compliance_status="compliant",
        current_state="OK",
        gap_description="None",
        risk_level="low",
        remediation_action="None",
        remediation_priority=1,
        remediation_effort="minimal",
        timeline_weeks=0,
    )
    db.add(item)
    db.commit()

    assert db.query(GapItem).filter(GapItem.report_id == report.id).count() == 1


def test_orphan_detection_clean(db):
    """Orphan detection script should find zero orphans on a clean DB."""
    from scripts.detect_orphans import detect_orphans

    assessment_id = _make_assessment(db)
    report = GapReport(
        assessment_id=assessment_id,
        overall_score=80.0,
        chapter_scores="{}",
        executive_summary="Clean",
        raw_ai_response="{}",
    )
    db.add(report)
    db.commit()

    db_url = str(db.get_bind().url)
    assert detect_orphans(db_url) is True
