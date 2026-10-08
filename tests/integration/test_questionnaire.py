"""Integration tests for questionnaire save."""

from unittest.mock import patch

from app.models.questionnaire import QuestionnaireResponse
from app.services.question_engine import questionnaire_progress
from tests.integration.conftest import create_test_assessment


def test_save_questionnaire_responses(client, db_session):
    assessment_id = create_test_assessment(client)

    # Mock the adaptive questionnaire builder to return a known section with questions
    mock_result = {
        "sections": [
            {
                "section_id": "test_section",
                "section_title": "Test section",
                "chapter_title": "Test chapter",
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


def test_followup_save_updates_without_affecting_questionnaire_inputs(client, db_session):
    assessment_id = create_test_assessment(client)
    mock_result = {
        "sections": [
            {
                "section_id": "test_section",
                "section_title": "Test section",
                "chapter_title": "Test chapter",
                "questions": [
                    {"id": "PARENT", "status": "active", "tier": "standard"},
                ],
            }
        ],
        "stats": {"tier_counts": {"standard": 1}},
    }

    with patch("app.routers.web.build_adaptive_questionnaire", return_value=mock_result):
        before = client.get(f"/assessments/{assessment_id}/questionnaire/section/test_section")
        first = client.post(
            f"/assessments/{assessment_id}/questionnaire/save",
            data={
                "section_id": "test_section",
                "answer_PARENT": "partially_implemented",
                "followup_FU.PARENT.1": "We review access quarterly.",
                "followup_question_FU.PARENT.1": "How often do you review access?",
            },
        )
        progress_after_first = questionnaire_progress(mock_result, assessment_id, db_session)
        second = client.post(
            f"/assessments/{assessment_id}/questionnaire/save",
            data={
                "section_id": "test_section",
                "answer_PARENT": "partially_implemented",
                "followup_FU.PARENT.1": "We review access monthly.",
                "followup_question_FU.PARENT.1": "How often do you review access?",
            },
        )
        progress_after_second = questionnaire_progress(mock_result, assessment_id, db_session)
        after = client.get(f"/assessments/{assessment_id}/questionnaire/section/test_section")

    assert first.status_code == 200
    assert second.status_code == 200
    assert before.status_code == 200
    assert after.status_code == 200

    rows = db_session.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.assessment_id == assessment_id
    ).all()
    assert len(rows) == 2
    followup = next(row for row in rows if row.question_id == "FU.PARENT.1")
    assert followup.answer == "not_applicable"
    assert "How often do you review access?" in followup.notes
    assert "We review access monthly." in followup.notes
    # The saved question is rendered once as the label and once in the hidden
    # field needed to preserve it on the next save.
    assert after.text.count("How often do you review access?") == 2
    assert "We review access monthly." in after.text

    non_followup_ids = sorted(row.question_id for row in rows if not row.question_id.startswith("FU."))
    assert non_followup_ids == ["PARENT"]
    assert progress_after_first == progress_after_second
    assert progress_after_second["answered_questions"] == 1

    multi_id = create_test_assessment(
        client,
        company_name="MultiFramework Corp",
        selected_frameworks=["dpdpa", "iso27001"],
    )
    multi_result = {
        "sections": [
            {
                "section_id": "multi_section",
                "section_title": "Multi section",
                "chapter_title": "Multi chapter",
                "questions": [
                    {"id": "CLUSTER_002", "cluster_id": "CLUSTER_002", "status": "active", "tier": "standard"},
                ],
            }
        ],
        "stats": {"tier_counts": {"standard": 1}},
    }
    with patch("app.routers.web.build_adaptive_questionnaire", return_value=multi_result):
        response = client.post(
            f"/assessments/{multi_id}/questionnaire/save",
            data={
                "section_id": "multi_section",
                "answer_CLUSTER_002": "planned",
                "followup_FU.CLUSTER_002.1": "The review is documented in the access register.",
                "followup_question_FU.CLUSTER_002.1": "Where is the review documented?",
            },
        )

    assert response.status_code == 200
    multi_followup = db_session.query(QuestionnaireResponse).filter_by(
        assessment_id=multi_id,
        question_id="FU.CLUSTER_002.1",
    ).one()
    assert multi_followup.cluster_id == "CLUSTER_002"
    assert multi_followup.answer == "not_applicable"


def test_followup_question_text_reaches_the_framework_prompt():
    from app.frameworks.mappings.clusters import CONTROL_CLUSTERS
    from app.frameworks.prompts import build_framework_user_prompt
    from app.services.followup_responses import encode_notes

    cluster = next(c for c in CONTROL_CLUSTERS if any(m["framework"] == "iso27001" for m in c["controls"]))
    fu_id = f"FU.{cluster['cluster_id']}.1"
    response = {
        "question_id": fu_id,
        "answer": "not_applicable",
        "notes": encode_notes(fu_id, "Where is the review documented?", "In the access register."),
    }
    prompt = build_framework_user_prompt("iso27001", "Acme", "Technology", "medium", None, [response], [])

    assert "**Where is the review documented?**" in prompt
    assert "In the access register." in prompt
