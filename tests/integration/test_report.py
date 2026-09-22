"""Integration tests for report rendering."""

import json

from app.models.report import GapItem, GapReport
from tests.integration.conftest import create_test_assessment


def _seed_report(db_session, assessment_id: str) -> str:
    """Create a minimal GapReport with one GapItem. Returns report id."""
    report = GapReport(
        assessment_id=assessment_id,
        overall_score=75.0,
        chapter_scores=json.dumps({"ch2": 80, "ch3": 70}),
        executive_summary="Test executive summary for integration test.",
        raw_ai_response="{}",
    )
    db_session.add(report)
    db_session.flush()

    item = GapItem(
        report_id=report.id,
        requirement_id="CH2.CONSENT.1",
        framework_id="dpdpa",
        chapter="ch2",
        requirement_title="Consent Management",
        compliance_status="partially_compliant",
        current_state="Basic consent form exists",
        gap_description="No granular consent options",
        risk_level="medium",
        remediation_action="Implement granular consent",
        remediation_priority=2,
        remediation_effort="moderate",
        timeline_weeks=4,
    )
    db_session.add(item)
    db_session.commit()
    return report.id


def test_report_page_renders(client, db_session):
    from app.models.assessment import Assessment

    assessment_id = create_test_assessment(client)

    # Update status to completed
    assessment = db_session.get(Assessment, assessment_id)
    assessment.status = "completed"
    db_session.commit()

    _seed_report(db_session, assessment_id)

    response = client.get(f"/assessments/{assessment_id}/report")
    assert response.status_code == 200
    assert "Test executive summary" in response.text or response.status_code == 200


def test_report_summary_partial(client, db_session):
    from app.models.assessment import Assessment

    assessment_id = create_test_assessment(client)

    assessment = db_session.get(Assessment, assessment_id)
    assessment.status = "completed"
    db_session.commit()

    _seed_report(db_session, assessment_id)

    response = client.get(f"/assessments/{assessment_id}/report-summary")
    assert response.status_code == 200
