"""Focused contracts for the Yozora S3 firm-level pages."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.firm_settings import FirmSettings
from app.services import assessment_stage
from app.routers import web as web_router
from tests.yozora_support import (  # noqa: F401
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)


def _client(db, name: str, industry: str = "fintech", size: str = "sme") -> Client:
    client = Client(name=name, industry=industry, size=size)
    db.add(client)
    db.flush()
    return client


def _engagement(db, client: Client, name: str, status: str = "active") -> Engagement:
    engagement = Engagement(client_id=client.id, name=name, status=status)
    db.add(engagement)
    db.flush()
    return engagement


def _assessment(db, client: Client, engagement: Engagement | None = None) -> Assessment:
    assessment = Assessment(
        company_name=client.name,
        industry=client.industry,
        company_size=client.size,
        selected_frameworks=json.dumps(["dpdpa"]),
        engagement_id=engagement.id if engagement else None,
        created_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
    )
    db.add(assessment)
    db.flush()
    return assessment


def test_home_moves_unmigrated_assessments_to_settings(db, http):
    client = _client(db, "Meridian Ledger Technologies")
    _assessment(db, client)
    db.commit()

    home = http.get("/").text
    settings = http.get("/settings").text

    assert "Unmigrated assessments" not in home
    assert "Unmigrated assessments" in settings


def test_clients_lists_empty_and_search_states(db, http):
    meridian = _client(db, "Meridian Ledger Technologies")
    loomwire = _client(db, "Loomwire Labs", industry="it_services", size="startup")
    _engagement(db, meridian, "FY2026 readiness")
    _engagement(db, loomwire, "NIST review")
    db.commit()

    page = http.get("/clients")
    assert page.status_code == 200
    assert "Meridian Ledger Technologies" in page.text
    assert "Loomwire Labs" in page.text
    assert 'data-nav-key="clients" aria-current="page"' in page.text

    noresults = http.get("/clients?search=Harbour")
    assert noresults.status_code == 200
    assert 'No clients match &quot;Harbour&quot;' in noresults.text

    db.query(Engagement).delete()
    db.query(Client).delete()
    db.commit()
    empty = http.get("/clients")
    assert "No clients yet" in empty.text


def test_client_detail_has_no_retention_form_and_settings_does(db, http):
    client, _engagement, _assessment = seed_engagement(
        db, client_name="Kestrel Advisory", name="FY2026 advisory"
    )

    detail = http.get(f"/clients/{client.id}")
    settings = http.get("/settings")

    assert detail.status_code == 200
    assert "data-retention-form" not in detail.text
    assert 'id="retention-years"' not in detail.text
    assert 'data-retention-form' in settings.text
    assert 'id="retention-years"' in settings.text


def test_login_redirect_is_preserved_and_preview_keeps_ids(http):
    redirect = http.get("/login", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"].endswith("/")

    preview = http.get("/design/pages/login")
    assert preview.status_code == 200
    assert 'id="username"' in preview.text
    assert 'id="password"' in preview.text


def test_review_lists_only_assessments_waiting_for_decisions(db, http, monkeypatch):
    client = _client(db, "Meridian Ledger Technologies")
    engagement = _engagement(db, client, "FY2026 readiness")
    waiting = _assessment(db, client, engagement)
    other_client = _client(db, "Loomwire Labs")
    other_engagement = _engagement(db, other_client, "NIST review")
    complete = _assessment(db, other_client, other_engagement)
    db.commit()

    def fake_stage(_db, assessment):
        return assessment_stage.Stage(
            "review" if assessment.id == waiting.id else "report",
            "Review" if assessment.id == waiting.id else "Report",
            "2 of 3 approved" if assessment.id == waiting.id else "Released 3 Oct 2026",
            "Review 1 conclusion" if assessment.id == waiting.id else None,
            f"/assessments/{assessment.id}/conclusions" if assessment.id == waiting.id else None,
        )

    monkeypatch.setattr(web_router.assessment_stage, "stage", fake_stage)
    page = http.get("/review")

    assert page.status_code == 200
    assert waiting.company_name in page.text
    assert complete.company_name not in page.text
    assert f"/assessments/{waiting.id}/conclusions" in page.text
