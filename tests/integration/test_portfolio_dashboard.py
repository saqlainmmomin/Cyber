"""Integration coverage for the Client -> Engagement portfolio surface."""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.client import Client
from app.models.engagement import Engagement
from app.services.portfolio import (
    build_client_card,
    build_engagement_card,
    derive_last_activity,
    derive_progress_pct,
    derive_status,
)


def _client(db, name="Acme", industry="it_services", size="sme"):
    row = Client(name=name, industry=industry, size=size)
    db.add(row)
    db.flush()
    return row


def _engagement(db, client, name="Privacy review", status="active"):
    row = Engagement(client_id=client.id, name=name, type="gap_assessment", status=status)
    db.add(row)
    db.flush()
    return row


def _assessment(
    db,
    engagement=None,
    company_name="Acme",
    status="created",
    frameworks=("dpdpa",),
    description=None,
):
    row = Assessment(
        company_name=company_name,
        industry="it_services",
        company_size="sme",
        description=description,
        status=status,
        selected_frameworks=json.dumps(list(frameworks)),
        engagement_id=engagement.id if engagement else None,
    )
    db.add(row)
    db.flush()
    return row


def _post_data(**overrides):
    data = {
        "client_mode": "new",
        "company_name": "Fresh Client",
        "industry": "fintech",
        "company_size": "startup",
        "engagement_name": "Readiness review",
        "engagement_type": "gap_assessment",
        "description": "A new portfolio engagement",
        "selected_frameworks": ["dpdpa"],
    }
    data.update(overrides)
    return data


def test_dashboard_renders_clients_engagements_and_no_linked_assessment_cards(client, db_session):
    client_a = _client(db_session, "Alpha", "it_services", "sme")
    client_b = _client(db_session, "Beta", "healthcare", "large")
    alpha_one = _engagement(db_session, client_a, "Alpha gap")
    alpha_two = _engagement(db_session, client_a, "Alpha audit")
    beta_one = _engagement(db_session, client_b, "Beta readiness")
    assessment_ids = [
        _assessment(db_session, alpha_one, "Alpha", frameworks=("dpdpa", "iso27001")).id,
        _assessment(db_session, alpha_one, "Alpha", frameworks=("iso27001",)).id,
        _assessment(db_session, alpha_two, "Alpha").id,
        _assessment(db_session, beta_one, "Beta").id,
    ]
    db_session.commit()

    response = client.get("/")

    assert response.status_code == 200
    for name in ("Alpha", "Beta", "Alpha gap", "Alpha audit", "Beta readiness"):
        assert name in response.text
    assert f"/clients/{client_a.id}" in response.text
    assert f"/clients/{client_b.id}" in response.text
    for engagement in (alpha_one, alpha_two, beta_one):
        assert f"/engagements/{engagement.id}" in response.text
    for assessment_id in assessment_ids:
        assert f"/assessments/{assessment_id}" not in response.text


def test_derived_status_uses_least_advanced_wins_and_rendered_badges(client, db_session):
    assert derive_status([SimpleNamespace(status="completed"), SimpleNamespace(status="context_gathered")]) == "context_gathered"
    assert derive_status([SimpleNamespace(status="completed"), SimpleNamespace(status="error")]) == "error"
    assert derive_status([SimpleNamespace(status="completed"), SimpleNamespace(status="completed")]) == "completed"
    assert derive_status([SimpleNamespace(status="analyzing"), SimpleNamespace(status="created")]) == "analyzing"

    company = _client(db_session, "Status Co")
    context_engagement = _engagement(db_session, company, "Context work")
    error_engagement = _engagement(db_session, company, "Failed work")
    analyzing_engagement = _engagement(db_session, company, "Running work")
    _assessment(db_session, context_engagement, status="completed")
    _assessment(db_session, context_engagement, status="context_gathered")
    _assessment(db_session, error_engagement, status="completed")
    _assessment(db_session, error_engagement, status="error")
    _assessment(db_session, analyzing_engagement, status="analyzing")
    _assessment(db_session, analyzing_engagement, status="created")
    db_session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert "Context Gathered" in response.text
    assert "Error" in response.text
    assert "Analyzing" in response.text


def test_derived_progress_excludes_archived_assessments():
    assert derive_progress_pct([SimpleNamespace(status="created"), SimpleNamespace(status="completed")]) == 50
    assert derive_progress_pct([SimpleNamespace(status="questionnaire_done")]) == 67
    assert derive_progress_pct([]) == 0
    assert derive_status([]) == "empty"
    assert derive_progress_pct([SimpleNamespace(status="completed")]) == 100
    assert derive_progress_pct([SimpleNamespace(status="created")]) == 0

    engagement = SimpleNamespace(id="engagement", name="Engagement", type="gap_assessment", status="active", updated_at=datetime.now())
    active = SimpleNamespace(status="completed", frameworks=["dpdpa"], updated_at=datetime.now())
    archived = SimpleNamespace(status="archived", frameworks=["iso27001"], updated_at=datetime.now())
    card = build_engagement_card(engagement, [active, archived])
    assert card["assessment_count"] == 1
    assert card["progress_pct"] == 100
    assert card["framework_ids"] == ["dpdpa"]


def test_last_activity_uses_assessments_then_engagements_for_client(db_session):
    fallback = datetime(2026, 1, 1, tzinfo=timezone.utc)
    later = fallback + timedelta(days=2)
    latest = fallback + timedelta(days=4)
    assert derive_last_activity([], fallback) == fallback
    assert derive_last_activity(
        [SimpleNamespace(updated_at=later), SimpleNamespace(updated_at=latest)], fallback
    ) == latest

    company = _client(db_session, "Activity Co")
    first = _engagement(db_session, company, "First")
    second = _engagement(db_session, company, "Second")
    first.updated_at = fallback
    second.updated_at = later
    first_assessment = _assessment(db_session, first)
    first_assessment.updated_at = latest
    db_session.commit()

    first_card = build_engagement_card(first, [first_assessment])
    second_card = build_engagement_card(second, [])
    client_card = build_client_card(company, [first_card, second_card])

    assert first_card["last_activity"] == first_assessment.updated_at
    assert second_card["last_activity"] == second.updated_at
    assert client_card["last_activity"] == first_assessment.updated_at


def test_orphaned_assessment_is_surfaced_and_empty_orphan_section_is_omitted(client, db_session):
    orphan = _assessment(db_session, None, company_name="Legacy Co")
    db_session.commit()

    response = client.get("/")
    assert response.status_code == 200
    assert "Unmigrated assessments" in response.text
    assert orphan.company_name in response.text
    assert f"/assessments/{orphan.id}" in response.text

    db_session.delete(orphan)
    db_session.commit()
    response = client.get("/")
    assert response.status_code == 200
    assert "Unmigrated assessments" not in response.text


def test_new_engagement_existing_client_creates_hierarchy_and_packs(client, db_session):
    company = _client(db_session, "Existing Co", "it_services", "sme")
    db_session.commit()
    counts = {model: db_session.query(model).count() for model in (Client, Engagement, Assessment, AssessmentPack)}

    response = client.post(
        "/engagements",
        data=_post_data(
            client_mode="existing",
            client_id=company.id,
            company_name="",
            industry="",
            company_size="",
            selected_frameworks=["dpdpa", "iso27001"],
        ),
        follow_redirects=False,
    )

    assert response.status_code == 303
    engagement_id = response.headers["location"].rsplit("/", 1)[-1]
    engagement = db_session.get(Engagement, engagement_id)
    assessment = db_session.query(Assessment).filter_by(engagement_id=engagement_id).one()
    assert db_session.query(Client).count() == counts[Client]
    assert engagement.client_id == company.id
    assert engagement.status == "active"
    assert engagement.type == "gap_assessment"
    assert assessment.company_name == company.name
    assert assessment.frameworks == ["dpdpa", "iso27001"]
    packs = db_session.query(AssessmentPack).filter_by(assessment_id=assessment.id).all()
    assert {pack.framework_id for pack in packs} == {"dpdpa", "iso27001"}
    assert all(pack.pack_version for pack in packs)


def test_new_engagement_new_client_and_duplicate_are_atomic(client, db_session):
    response = client.post("/engagements", data=_post_data(), follow_redirects=False)
    assert response.status_code == 303
    counts = {model: db_session.query(model).count() for model in (Client, Engagement, Assessment, AssessmentPack)}
    created_client = db_session.query(Client).filter_by(name="Fresh Client").one()
    assert created_client.industry == "fintech"
    assert created_client.size == "startup"

    duplicate = client.post("/engagements", data=_post_data(), follow_redirects=False)
    assert duplicate.status_code == 400
    assert "A client named" in duplicate.text
    assert "already exists" in duplicate.text
    assert {model: db_session.query(model).count() for model in (Client, Engagement, Assessment, AssessmentPack)} == counts


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"selected_frameworks": []}, "Select at least one framework to assess against."),
        ({"selected_frameworks": ["gdpr"]}, "One or more selected frameworks are not available for assessment yet."),
        ({"engagement_name": "   "}, "Engagement name is required."),
        ({"engagement_type": "invalid"}, "Select a valid engagement type."),
        ({"client_mode": "existing", "client_id": "does-not-exist"}, "Select an existing client or create a new one."),
    ],
)
def test_new_engagement_validation_is_400_and_has_no_writes(client, db_session, overrides, message):
    counts = {model: db_session.query(model).count() for model in (Client, Engagement, Assessment, AssessmentPack)}

    response = client.post("/engagements", data=_post_data(**overrides), follow_redirects=False)

    assert response.status_code == 400
    assert message in response.text
    assert {model: db_session.query(model).count() for model in (Client, Engagement, Assessment, AssessmentPack)} == counts


def test_engagement_detail_lists_assessments_and_framework_badges(client, db_session):
    company = _client(db_session, "Detail Co")
    engagement = _engagement(db_session, company, "Detail engagement")
    first = _assessment(db_session, engagement, "Detail Co", frameworks=("dpdpa",))
    second = _assessment(db_session, engagement, "Detail Co", frameworks=("dpdpa", "nist_csf"))
    db_session.commit()

    response = client.get(f"/engagements/{engagement.id}")

    assert response.status_code == 200
    assert company.name in response.text
    assert engagement.name in response.text
    assert f"/assessments/{first.id}" in response.text
    assert f"/assessments/{second.id}" in response.text
    assert FrameworkRegistry.get("dpdpa").name in response.text
    assert FrameworkRegistry.get("nist_csf").name in response.text
    assert client.get("/engagements/does-not-exist").status_code == 404
    assert client.get("/clients/does-not-exist").status_code == 404


def test_htmx_fragments_and_fallback_redirects(client, db_session):
    company = _client(db_session, "HTMX Co")
    engagement = _engagement(db_session, company, "HTMX engagement")
    db_session.commit()

    fragment = client.get(
        f"/clients/{company.id}/engagements-list",
        headers={"HX-Request": "true"},
    )
    assert fragment.status_code == 200
    assert "<!DOCTYPE" not in fragment.text
    assert "<html" not in fragment.text
    assert "<nav" not in fragment.text
    assert engagement.name in fragment.text
    for headers in ({"HX-Request": "true", "HX-Boosted": "true"}, {}):
        fallback = client.get(
            f"/clients/{company.id}/engagements-list",
            headers=headers,
            follow_redirects=False,
        )
        assert fallback.status_code == 307
        assert fallback.headers["location"] == f"/clients/{company.id}"

    assert client.get("/engagements/new", follow_redirects=False).status_code == 200
    new_fragment = client.get(
        "/engagements/new/client-fields?mode=new",
        headers={"HX-Request": "true"},
    )
    assert new_fragment.status_code == 200
    assert 'name="company_name"' in new_fragment.text
    existing_fragment = client.get(
        "/engagements/new/client-fields?mode=existing",
        headers={"HX-Request": "true"},
    )
    assert existing_fragment.status_code == 200
    assert 'name="client_id"' in existing_fragment.text
    for headers in ({"HX-Request": "true", "HX-Boosted": "true"}, {}):
        fallback = client.get(
            "/engagements/new/client-fields?mode=existing",
            headers=headers,
            follow_redirects=False,
        )
        assert fallback.status_code == 307
        assert fallback.headers["location"] == "/engagements/new"
    assert client.get("/engagements/new/client-fields?mode=bogus").status_code == 400


def test_zero_row_edges_and_global_empty_state(client, db_session):
    company = _client(db_session, "Empty Client")
    engagement = _engagement(db_session, company, "Empty engagement")
    db_session.commit()

    dashboard = client.get("/")
    assert "No assessments" in dashboard.text
    assert "0%" in dashboard.text
    assert client.get(f"/engagements/{engagement.id}").status_code == 200

    db_session.delete(engagement)
    db_session.commit()
    dashboard = client.get("/")
    assert "No engagements yet" in dashboard.text
    assert f"/engagements/new?client_id={company.id}" in dashboard.text

    db_session.delete(company)
    db_session.commit()
    empty = client.get("/")
    assert empty.status_code == 200
    assert "No clients yet" in empty.text


def test_legacy_entry_point_creates_hierarchy_and_keeps_redirect(client, db_session):
    page = client.get("/assessments/new", follow_redirects=False)
    assert page.status_code == 307
    assert page.headers["location"] == "/engagements/new"

    response = client.post(
        "/assessments",
        data={
            "company_name": "Legacy Entry Co",
            "industry": "it_services",
            "company_size": "sme",
            "description": "Legacy route",
            "selected_frameworks": ["dpdpa", "nist_csf"],
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assessment = db_session.query(Assessment).filter_by(company_name="Legacy Entry Co").one()
    assert assessment.engagement_id is not None
    assert db_session.query(Client).count() == 1
    assert db_session.query(Engagement).count() == 1
    assert db_session.query(AssessmentPack).count() == 2
    assert db_session.query(Assessment).filter(Assessment.engagement_id.is_(None)).count() == 0


def test_json_api_factory_also_preserves_the_hierarchy_invariant(client, db_session):
    payload = {
        "company_name": "API Entry Co",
        "industry": "it_services",
        "company_size": "sme",
        "description": "API compatibility",
    }
    response = client.post(
        "/api/assessments",
        json=payload,
    )

    assert response.status_code == 201
    assessment = db_session.get(Assessment, response.json()["id"])
    assert assessment.engagement_id is not None
    engagement = db_session.get(Engagement, assessment.engagement_id)
    assert engagement is not None
    assert db_session.query(Client).filter_by(name="API Entry Co").count() == 1
    assert db_session.query(AssessmentPack).filter_by(assessment_id=assessment.id).count() == 1

    repeated = client.post("/api/assessments", json=payload)

    assert repeated.status_code == 201
    assert db_session.query(Client).filter_by(name="API Entry Co").count() == 1
    assert db_session.query(Engagement).count() == 2
    assert db_session.query(Assessment).filter_by(company_name="API Entry Co").count() == 2
    assert db_session.query(AssessmentPack).filter(AssessmentPack.framework_id == "dpdpa").count() == 2
