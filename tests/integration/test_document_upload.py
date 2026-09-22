"""Integration tests for document upload."""

import io
from unittest.mock import patch

from app.models.assessment import AssessmentDocument
from tests.integration.conftest import create_test_assessment


def test_upload_document(client, db_session):
    assessment_id = create_test_assessment(client)
    pdf_content = b"%PDF-1.4 test content"

    with patch("app.routers.web.save_upload", return_value="/tmp/fake/test-policy.pdf"), \
         patch("app.routers.web.extract_text", return_value="Extracted policy text for testing."):
        response = client.post(
            f"/assessments/{assessment_id}/upload",
            data={"category": "policy"},
            files={"file": ("test-policy.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )

    assert response.status_code == 200

    docs = db_session.query(AssessmentDocument).filter(
        AssessmentDocument.assessment_id == assessment_id
    ).all()
    assert len(docs) == 1
    assert docs[0].filename == "test-policy.pdf"
    assert docs[0].document_category == "policy"


def test_upload_unsupported_file_type(client, db_session):
    assessment_id = create_test_assessment(client)
    response = client.post(
        f"/assessments/{assessment_id}/upload",
        data={"category": "policy"},
        files={"file": ("test.xyz", io.BytesIO(b"content"), "application/octet-stream")},
    )
    assert response.status_code == 200  # returns error partial, not HTTP error
    assert "Unsupported" in response.text
