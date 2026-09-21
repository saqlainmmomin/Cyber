"""Integration tests for analysis trigger."""

import json
from unittest.mock import patch, MagicMock

from app.models.assessment import Assessment
from app.models.questionnaire import QuestionnaireResponse
from app.models.report import GapItem, GapReport
from app.dpdpa.questionnaire import build_questionnaire
from tests.integration.conftest import create_test_assessment


def _seed_questionnaire(db_session, assessment_id: str):
    """Answer enough questions (80%+) to pass the analysis gate."""
    questions = build_questionnaire()
    core = [q for q in questions if not q["id"].startswith(("IND.", "FU."))]
    needed = int(len(core) * 0.85)
    for q in core[:needed]:
        db_session.add(QuestionnaireResponse(
            assessment_id=assessment_id,
            question_id=q["id"],
            answer="fully_implemented",
        ))
    db_session.commit()


def _mock_gap_analysis_result():
    """Return a minimal valid gap analysis response."""
    return {
        "raw": json.dumps({"executive_summary": "Test summary"}),
        "parsed": {
            "executive_summary": "Test summary",
            "assessments": [
                {
                    "requirement_id": "CH2.CONSENT.1",
                    "compliance_status": "fully_compliant",
                    "current_state": "Implemented",
                    "gap_description": "No gap",
                    "risk_level": "low",
                    "remediation_action": "None needed",
                    "remediation_priority": 1,
                    "remediation_effort": "minimal",
                    "timeline_weeks": 0,
                },
            ],
        },
    }


def test_trigger_analysis(client, db_session):
    assessment_id = create_test_assessment(client)
    _seed_questionnaire(db_session, assessment_id)

    mock_result = _mock_gap_analysis_result()

    with patch("app.routers.analysis.run_gap_analysis", return_value=mock_result), \
         patch("app.database.SessionLocal", return_value=db_session):
        response = client.post(f"/assessments/{assessment_id}/run-analysis")

    assert response.status_code == 200

    report = db_session.query(GapReport).filter(
        GapReport.assessment_id == assessment_id
    ).first()
    assert report is not None
    assert report.executive_summary == "Test summary"

    items = db_session.query(GapItem).filter(GapItem.report_id == report.id).all()
    assert len(items) >= 1
