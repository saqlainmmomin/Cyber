"""Yozora backend item 3: add an assessment to an existing engagement.

Handoff: tasks/handoffs/2026-10-03-yozora-backend-features.md.
"""

from __future__ import annotations

import json
import sqlite3

import pytest
from alembic import command

from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.routers import web
from app.services.engagement_factory import add_assessment_to_engagement
from app.services import retention
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    alembic_config,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)


def _post(http, engagement_id, **data):
    return http.post(f"/engagements/{engagement_id}/assessments", data=data, follow_redirects=False)


def test_form_lists_only_enabled_frameworks(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    page = http.get(f"/engagements/{engagement.id}/assessments/new")
    assert page.status_code == 200
    for framework_id in web.ENABLED_ASSESSMENT_FRAMEWORKS:
        assert f'value="{framework_id}"' in page.text
    for framework_id in web.ROADMAP_FRAMEWORKS:
        assert f'value="{framework_id}"' not in page.text
    assert 'name="name"' in page.text and 'name="description"' in page.text
    assert http.get("/engagements/missing/assessments/new").status_code == 404


def test_engagement_page_has_the_add_assessment_button(db, http):
    client, engagement, _assessment = seed_engagement(db)
    add_assessment_to_engagement(
        db,
        engagement=engagement,
        client=client,
        name="Operations",
        description="Operations scope",
        framework_ids=["dpdpa"],
    )
    page = http.get(f"/engagements/{engagement.id}").text
    assert "data-add-assessment-link" in page
    assert f'href="/engagements/{engagement.id}/assessments/new"' in page


def test_single_assessment_engagement_redirects_to_assessment_overview(db, http):
    _client, engagement, assessment = seed_engagement(db)
    response = http.get(f"/engagements/{engagement.id}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/assessments/{assessment.id}?tab=overview"


def test_create_inherits_the_client_and_redirects_to_the_assessment(db, http):
    client, engagement, first = seed_engagement(db, frameworks=("dpdpa",))
    response = http.post(
        f"/engagements/{engagement.id}/assessments",
        data={
            "name": "  Head office  ",
            "description": "Mumbai head office and the HR system",
            "selected_frameworks": ["iso27001", "nist_csf", "iso27001"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    created = (
        db.query(Assessment)
        .filter(Assessment.engagement_id == engagement.id, Assessment.id != first.id)
        .one()
    )
    assert response.headers["location"] == f"/assessments/{created.id}"
    assert created.name == "Head office" and created.display_name == "Head office"
    assert created.description == "Mumbai head office and the HR system"
    assert (created.company_name, created.industry, created.company_size) == (client.name, client.industry, client.size)
    assert json.loads(created.selected_frameworks) == ["iso27001", "nist_csf"]
    packs = {pack.framework_id for pack in db.query(AssessmentPack).filter(AssessmentPack.assessment_id == created.id)}
    assert packs == {"iso27001", "nist_csf"}
    page = http.get(f"/engagements/{engagement.id}").text
    assert "Head office" in page and "Mumbai head office and the HR system" in page
    assert http.get(f"/assessments/{created.id}").status_code == 200


def test_name_is_optional_and_falls_back_to_the_company_name(db, http):
    client, engagement, _first = seed_engagement(db, client_name="Kestrel Health")
    response = _post(http, engagement.id, name="", selected_frameworks="dpdpa")
    assert response.status_code == 303
    created = db.get(Assessment, response.headers["location"].rsplit("/", 1)[-1])
    assert created.name is None
    assert created.display_name == "Kestrel Health" == client.name
    # Legacy rows have no name either; the display falls back the same way.
    unnamed = Assessment(company_name="Brightfold Learning", industry="education", company_size="small")
    assert unnamed.display_name == "Brightfold Learning"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"name": "Branch"}, web.ADD_ASSESSMENT_NO_FRAMEWORK),
        ({"name": "Branch", "selected_frameworks": "gdpr"}, web.ADD_ASSESSMENT_UNKNOWN_FRAMEWORK),
        ({"name": "Branch", "selected_frameworks": "made_up"}, web.ADD_ASSESSMENT_UNKNOWN_FRAMEWORK),
        ({"name": "x" * 256, "selected_frameworks": "dpdpa"}, web.ADD_ASSESSMENT_NAME_TOO_LONG),
    ],
    ids=["no-framework", "roadmap-framework", "unknown-framework", "long-name"],
)
def test_validation_refuses_and_creates_nothing(db, http, data, message):
    _client, engagement, _first = seed_engagement(db)
    response = _post(http, engagement.id, **data)
    assert response.status_code == 400
    assert message in response.text
    assert response.headers["X-Toast-Type"] == "error"
    assert 'value="Branch"' in response.text or "x" * 256 in response.text  # the form keeps what was typed
    assert db.query(Assessment).filter(Assessment.engagement_id == engagement.id).count() == 1


def test_archived_engagement_is_refused(db, http):
    _client, engagement, _first = seed_engagement(db)
    assert http.post(f"/api/engagements/{engagement.id}/archive", data={"reviewer_name": "Priya"}).status_code == 200
    page = http.get(f"/engagements/{engagement.id}/assessments/new")
    assert page.status_code == 400 and page.json()["detail"] == retention.ARCHIVED_READ_ONLY
    # The shared archive write guard refuses the POST before the handler runs (409, as for every write).
    response = _post(http, engagement.id, name="Late", selected_frameworks="dpdpa")
    assert response.status_code == 409 and response.json()["detail"] == retention.ARCHIVED_READ_ONLY
    assert db.query(Assessment).filter(Assessment.engagement_id == engagement.id).count() == 1
    assert "data-add-assessment-link" not in http.get(f"/engagements/{engagement.id}").text


def test_unknown_engagement_is_404(http):
    assert _post(http, "missing", selected_frameworks="dpdpa").status_code == 404


def test_name_column_migration_and_guarded_downgrade(tmp_path):
    path = tmp_path / "name.sqlite3"
    config = alembic_config(path)
    command.upgrade(config, "head")
    with sqlite3.connect(path) as connection:
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(assessments)")}
        assert "name" in columns and columns["name"][3] == 0  # nullable
        connection.execute(
            "INSERT INTO assessments (id, company_name, industry, company_size, status, created_at, updated_at, version, name) "
            "VALUES ('a1', 'Acme', 'Technology', 'small', 'created', '2026-10-03', '2026-10-03', 1, 'Head office')"
        )
    with pytest.raises(RuntimeError, match="assessments.name=1"):
        command.downgrade(config, "-1")
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE assessments SET name = NULL")
    command.downgrade(config, "-1")
    with sqlite3.connect(path) as connection:
        assert "name" not in {row[1] for row in connection.execute("PRAGMA table_info(assessments)")}
        assert connection.execute("SELECT company_name FROM assessments WHERE id='a1'").fetchone() == ("Acme",)


def test_duplicate_assessment_name_is_refused_case_insensitively(db, http):
    _client, engagement, first = seed_engagement(db)
    for name in (first.display_name, first.display_name.upper()):
        response = _post(http, engagement.id, name=name, selected_frameworks="dpdpa")
        assert response.status_code == 400 and web.ADD_ASSESSMENT_DUPLICATE_NAME in response.text, name
    assert _post(http, engagement.id, name="Head office", selected_frameworks="dpdpa").status_code == 303
    again = _post(http, engagement.id, name="head OFFICE", selected_frameworks="dpdpa")
    assert again.status_code == 400
