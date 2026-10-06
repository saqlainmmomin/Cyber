"""Settings > Data housekeeping: the Archive and purge card is the one home for archive actions."""

from __future__ import annotations

from html.parser import HTMLParser

from sqlalchemy import text

from app.models.audit_event import AuditEvent
from app.services import retention
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)


def _archive(http, engagement_id, **data):
    return http.post(f"/api/engagements/{engagement_id}/archive", data={"reviewer_name": "Priya", **data})


def _unarchive(http, engagement_id, **data):
    return http.post(f"/api/engagements/{engagement_id}/unarchive", data={"reviewer_name": "Priya", **data})


def test_return_to_redirects_only_for_the_exact_settings_path(db, http):
    _client, first, _a = seed_engagement(db, client_name="Acme", name="First")
    _client, second, _a = seed_engagement(db, client_name="Bravo", name="Second")
    _client, third, _a = seed_engagement(db, client_name="Charlie", name="Third")

    response = _archive(http, first.id, return_to="/settings")
    assert response.status_code == 200 and response.headers["HX-Redirect"] == "/settings"
    response = _archive(http, second.id, return_to="https://evil.example")
    assert response.status_code == 200 and response.headers["HX-Redirect"] == f"/engagements/{second.id}"
    response = _archive(http, third.id)
    assert response.status_code == 200 and response.headers["HX-Redirect"] == f"/engagements/{third.id}"

    response = _unarchive(http, first.id, return_to="/settings")
    assert response.status_code == 200 and response.headers["HX-Redirect"] == "/settings"
    response = _unarchive(http, second.id, return_to="/settings/")
    assert response.status_code == 200 and response.headers["HX-Redirect"] == f"/engagements/{second.id}"


def test_settings_lists_archivable_and_archived_engagements_archived_last(db, http):
    _client, archived, _a = seed_engagement(db, client_name="Acme", name="Archived one")
    _client, active, _a = seed_engagement(db, client_name="Bravo", name="Active one")
    _client, closed, _a = seed_engagement(db, client_name="Charlie", name="Closed one", status="closed")
    _client, other, _a = seed_engagement(db, client_name="Delta", name="Other status", status="planning")
    assert _archive(http, archived.id).status_code == 200

    page = http.get("/settings").text
    assert f'data-engagement-archive-row="{other.id}"' not in page
    positions = {
        engagement.id: page.index(f'data-engagement-archive-row="{engagement.id}"')
        for engagement in (archived, active, closed)
    }
    assert positions[active.id] < positions[closed.id] < positions[archived.id]

    def row(engagement_id):
        start = page.index(f'data-engagement-archive-row="{engagement_id}"')
        return page[start:page.index("</li>", start)]

    for engagement in (active, closed):
        markup = row(engagement.id)
        assert 'data-archive-state="active"' in markup
        assert f'hx-post="/api/engagements/{engagement.id}/archive"' in markup
        assert 'name="return_to" value="/settings"' in markup
        assert "data-unarchive-control" not in markup
    assert "· Active" in row(active.id) and "· Closed" in row(closed.id)
    markup = row(archived.id)
    assert 'data-archive-state="archived"' in markup
    assert f'hx-post="/api/engagements/{archived.id}/unarchive"' in markup
    assert f'href="/engagements/{archived.id}/purge"' in markup
    assert "by Priya" in markup and "Eligible for purge from" in markup
    assert "data-archive-control" not in markup


def test_settings_archive_and_unarchive_record_the_consultant(db, http):
    _client, engagement, _a = seed_engagement(db)
    assert _archive(http, engagement.id, reviewer_name="Ananya Rao", return_to="/settings").status_code == 200
    assert _unarchive(http, engagement.id, reviewer_name="Ananya Rao", return_to="/settings").status_code == 200
    actors = {
        event.action: event.actor
        for event in db.query(AuditEvent).filter(AuditEvent.entity_id == engagement.id)
    }
    assert actors[retention.ARCHIVED_EVENT] == "consultant:Ananya Rao"
    assert actors[retention.UNARCHIVED_EVENT] == "consultant:Ananya Rao"


class _FormNesting(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: list[dict] = []
        self.nested: list[dict] = []
        self.hx_inside_settings: list[dict] = []
        self.reviewer_name_inputs = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("id") == "reviewer-name":
            self.reviewer_name_inputs += 1
        in_settings = any(entry.get("id") == "settings-form" for entry in self.stack)
        if in_settings and "hx-post" in attrs:
            self.hx_inside_settings.append(attrs)
        if tag == "form":
            if self.stack:
                self.nested.append(attrs)
            self.stack.append(attrs)

    def handle_endtag(self, tag):
        if tag == "form" and self.stack:
            self.stack.pop()


def _check_forms(html: str):
    parser = _FormNesting()
    parser.feed(html)
    assert parser.nested == []
    assert parser.hx_inside_settings == []
    assert parser.reviewer_name_inputs == 1


def test_settings_page_has_no_nested_forms_and_one_name_field(db, http):
    seed_engagement(db)
    _client, archived, _a = seed_engagement(db, client_name="Bravo", name="Archived one")
    assert _archive(http, archived.id).status_code == 200
    page = http.get("/settings")
    assert page.status_code == 200
    _check_forms(page.text)
    assert 'id="reviewer-name" name="reviewer_name" form="settings-form"' in page.text
    invalid = http.post(
        "/settings",
        data={"archived_retention_years": "0", "accent_theme": "midnight", "reviewer_name": "Priya"},
        follow_redirects=False,
    )
    assert invalid.status_code == 422
    _check_forms(invalid.text)


def test_settings_name_field_still_saves_with_settings(db, http):
    response = http.post(
        "/settings",
        data={"archived_retention_years": "11", "accent_theme": "midnight", "reviewer_name": "Priya"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    actor = db.execute(
        text("SELECT actor FROM audit_events WHERE action = 'firm_settings.updated' ORDER BY rowid DESC LIMIT 1")
    ).scalar_one()
    assert actor == "consultant:Priya"


def test_settings_empty_state(db, http):
    page = http.get("/settings").text
    assert "data-engagement-archive" in page and "No engagements yet." in page


def test_archived_assessment_overview_links_to_settings_and_stays_read_only(db, http):
    _client, engagement, assessment = seed_engagement(db)
    assert _archive(http, engagement.id).status_code == 200
    overview = http.get(f"/assessments/{assessment.id}?tab=overview").text
    assert "data-archived-banner" in overview
    assert 'href="/settings#engagement-archive" data-archive-settings-link' in overview
    assert "data-retention-section" not in overview
    response = http.post(
        f"/engagements/{engagement.id}/magic-links",
        data={"items": "Policy", "contact_email": "client@example.com"},
    )
    assert response.status_code == 409
