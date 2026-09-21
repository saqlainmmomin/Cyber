"""Integration tests for desk review trigger."""

from datetime import datetime, timezone
from unittest.mock import patch

from app.models.assessment import AssessmentDocument
from app.models.desk_review import DeskReviewSummary
from tests.integration.conftest import create_test_assessment


def _seed_document(db_session, assessment_id: str):
    """Add a minimal document so desk review doesn't reject the assessment."""
    doc = AssessmentDocument(
        assessment_id=assessment_id,
        filename="policy.pdf",
        file_path="/tmp/fake/policy.pdf",
        file_type="pdf",
        document_category="policy",
        extracted_text="This is a privacy policy document with sufficient text for analysis.",
    )
    db_session.add(doc)
    db_session.commit()


def test_trigger_desk_review(client, db_session):
    assessment_id = create_test_assessment(client)
    _seed_document(db_session, assessment_id)

    def mock_run_desk_review(aid, db):
        summary = db.query(DeskReviewSummary).filter(
            DeskReviewSummary.assessment_id == aid
        ).first()
        if summary:
            summary.status = "completed"
            summary.completed_at = datetime.now(timezone.utc)
        db.commit()
        return summary

    with patch("app.services.desk_review.run_desk_review", mock_run_desk_review):
        response = client.post(f"/assessments/{assessment_id}/run-desk-review")

    assert response.status_code == 200

    summary = db_session.query(DeskReviewSummary).filter(
        DeskReviewSummary.assessment_id == assessment_id
    ).first()
    assert summary is not None
    assert summary.status in ("analyzing", "completed")
