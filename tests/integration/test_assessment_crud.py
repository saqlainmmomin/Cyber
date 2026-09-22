"""Integration tests for assessment CRUD operations."""

from app.models.assessment import Assessment
from tests.integration.conftest import create_test_assessment


def test_create_assessment(client, db_session):
    assessment_id = create_test_assessment(client)
    assessment = db_session.get(Assessment, assessment_id)
    assert assessment is not None
    assert assessment.company_name == "TestCorp"
    assert assessment.industry == "Technology"
    assert assessment.status == "created"


def test_get_assessment_detail(client, db_session):
    assessment_id = create_test_assessment(client)
    response = client.get(f"/assessments/{assessment_id}")
    assert response.status_code == 200
    assert "TestCorp" in response.text


def test_dashboard_lists_assessment(client, db_session):
    create_test_assessment(client, company_name="DashboardCo")
    response = client.get("/")
    assert response.status_code == 200
    assert "DashboardCo" in response.text


def test_delete_assessment_archives(client, db_session):
    assessment_id = create_test_assessment(client)
    response = client.delete(f"/assessments/{assessment_id}")
    assert response.status_code == 200
    db_session.expire_all()
    assessment = db_session.get(Assessment, assessment_id)
    assert assessment is not None
    assert assessment.status == "archived"

    # Archived assessment should not appear on dashboard
    dashboard = client.get("/")
    assert assessment_id not in dashboard.text


def test_get_nonexistent_assessment_returns_404(client):
    response = client.get("/assessments/nonexistent-id")
    assert response.status_code == 404
