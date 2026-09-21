"""Shared fixtures for HTTP integration tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — register all ORM tables
from app.database import Base, get_db
from app.main import app
from app.template_config import configure_templates
from app.routers.web import templates


@pytest.fixture()
def db_session(tmp_path):
    """Fresh SQLite database per test."""
    db_path = tmp_path / "integration.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """TestClient with dependency-overridden database."""
    configure_templates(templates)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def create_test_assessment(client, **overrides):
    """Helper: create an assessment via the web route and return its id."""
    data = {
        "company_name": overrides.get("company_name", "TestCorp"),
        "industry": overrides.get("industry", "Technology"),
        "company_size": overrides.get("company_size", "medium"),
        "description": overrides.get("description", "Integration test assessment"),
        "selected_frameworks": overrides.get("selected_frameworks", "dpdpa"),
    }
    response = client.post("/assessments/new", data=data, follow_redirects=False)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}: {response.text[:300]}"
    location = response.headers["location"]
    assessment_id = location.split("/assessments/")[1].split("?")[0].split("/")[0]
    return assessment_id
