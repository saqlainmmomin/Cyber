"""Integration tests for questionnaire save."""

from unittest.mock import patch

from app.models.questionnaire import QuestionnaireResponse
from tests.integration.conftest import create_test_assessment


def test_save_questionnaire_responses(client, db_session):
    assessment_id = create_test_assessment(client)

    # Mock the adaptive questionnaire builder to return a known section with questions
    mock_result = {
        "sections": [
            {
                "section_id": "test_section",
                "questions": [
                    {"id": "Q1", "status": "active"},
                    {"id": "Q2", "status": "active"},
                ],
            }
        ],
        "total_questions": 2,
    }

    with patch("app.routers.web.build_adaptive_questionnaire", return_value=mock_result):
        response = client.post(
            f"/assessments/{assessment_id}/questionnaire/save",
            data={
                "section_id": "test_section",
                "answer_Q1": "fully_implemented",
                "notes_Q1": "All controls in place",
                "evidence_Q1": "ISO cert",
                "answer_Q2": "not_implemented",
            },
        )

    assert response.status_code == 200

    rows = db_session.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id
    ).all()
    assert len(rows) == 2

    by_qid = {r.question_id: r for r in rows}
    assert by_qid["Q1"].answer == "fully_implemented"
    assert by_qid["Q1"].notes == "All controls in place"
    assert by_qid["Q2"].answer == "not_implemented"
