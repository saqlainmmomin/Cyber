"""Yozora backend item 6: a client contact on magic links, and "Email the firm" on invalid links.

Handoff: tasks/handoffs/2026-10-03-yozora-backend-features.md.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from alembic import command

from app.models.magic_link import MagicLink
from app.services import firm_settings, magic_links, rfi_requests
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

TOKEN_IN_URL = re.compile(r"/magic/([A-Za-z0-9_-]{22})")


def _create(http, engagement_id, **extra):
    data = {"items": "Information security policy\nAccess review record"}
    data.update(extra)
    return http.post(f"/engagements/{engagement_id}/magic-links", data=data)


def _only_link(db, engagement_id):
    return db.query(MagicLink).filter(MagicLink.engagement_id == engagement_id).one()


def test_create_with_a_contact_stores_and_shows_it(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    response = _create(http, engagement.id, contact_name="  Ananya   Rao ", contact_email=" ananya@client.example ")
    assert response.status_code == 200
    link = _only_link(db, engagement.id)
    assert (link.contact_name, link.contact_email) == ("Ananya Rao", "ananya@client.example")
    assert "data-link-contact" in response.text
    assert "Ananya Rao" in response.text and "ananya@client.example" in response.text
    assert TOKEN_IN_URL.search(response.text)  # the token is still shown once, at creation
    page = http.get(f"/engagements/{engagement.id}/requests").text
    assert "Ananya Rao" in page and "ananya@client.example" in page
    assert not TOKEN_IN_URL.search(page)  # and never again
    row = magic_links.magic_link_rows(db, engagement.id)[0]
    assert (row["contact_name"], row["contact_email"]) == ("Ananya Rao", "ananya@client.example")


def test_create_without_a_contact_keeps_working(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    response = _create(http, engagement.id)
    assert response.status_code == 200 and TOKEN_IN_URL.search(response.text)
    link = _only_link(db, engagement.id)
    assert link.contact_name is None and link.contact_email is None
    # Blank fields are stored as no contact.
    _create(http, engagement.id, contact_name="   ", contact_email="")
    assert db.query(MagicLink).filter(MagicLink.contact_name.isnot(None)).count() == 0


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"contact_email": "ananya-at-client"}, magic_links.CONTACT_EMAIL_INVALID),
        ({"contact_email": "a@" + "b" * 250 + ".com"}, magic_links.CONTACT_EMAIL_INVALID),
        ({"contact_name": "A" * 201}, magic_links.CONTACT_NAME_TOO_LONG),
    ],
    ids=["format", "too-long-email", "too-long-name"],
)
def test_invalid_contact_is_refused_and_no_link_is_created(db, http, fields, message):
    _client, engagement, _assessment = seed_engagement(db)
    response = _create(http, engagement.id, **fields)
    assert response.status_code == 200  # the partial re-renders with the error, as for other link errors
    assert message in response.text
    assert not TOKEN_IN_URL.search(response.text)
    assert db.query(MagicLink).count() == 0


def test_validated_contact_unit():
    assert magic_links.validated_contact(None, None) == (None, None)
    assert magic_links.validated_contact(" Ananya ", "a@b.co") == ("Ananya", "a@b.co")
    with pytest.raises(magic_links.MagicLinkValidationError):
        magic_links.validated_contact("", "not an email")


def test_rfi_route_validates_the_contact_before_anything_else(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    response = http.post(
        f"/assessments/{assessment.id}/rfi/versions/missing/magic-links",
        data={"item_ids": "RFI-001", "contact_email": "nope"},
    )
    assert magic_links.CONTACT_EMAIL_INVALID in response.text
    assert db.query(MagicLink).count() == 0


def test_rfi_link_rows_and_partial_show_the_contact(db, http):
    from app.routers.web import templates

    _client, engagement, assessment = seed_engagement(db)
    created = magic_links.create_rfi_link(
        db,
        engagement_id=engagement.id,
        assessment_id=assessment.id,
        snapshot_id="snapshot-1",
        rfi_items=[("RFI-001", "RFI-001: Privacy notice")],
        expires_in_days=7,
        max_uploads=5,
        max_total_mb=10,
    )
    name, email = magic_links.validated_contact("Ananya Rao", "ananya@client.example")
    magic_links.set_contact(db, created.link, contact_name=name, contact_email=email)
    db.commit()
    rows, _items = rfi_requests._link_rows(db, assessment)
    assert [(row.contact_name, row.contact_email) for row in rows] == [("Ananya Rao", "ananya@client.example")]
    html = templates.get_template("partials/rfi_links.html").render(
        assessment=assessment,
        current_issue=SimpleNamespace(id="snapshot-1"),
        current_items=[],
        links=rows,
        coverage={},
        received={},
        error=None,
        new_link_url=None,
    )
    assert "data-link-contact" in html and "Ananya Rao" in html and "ananya@client.example" in html
    assert 'name="contact_name"' in html and 'name="contact_email"' in html


def test_upload_page_greets_the_contact_by_first_name(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    response = _create(http, engagement.id, contact_name="Ananya Rao")
    token = TOKEN_IN_URL.search(response.text).group(1)
    page = http.get(f"/magic/{token}")
    assert page.status_code == 200
    assert "data-contact-greeting" in page.text
    assert f"Ananya, {firm_settings.get(db).firm_name} needs these items." in page.text
    assert "Rao" not in page.text


def test_upload_page_without_a_contact_has_no_greeting(db, http):
    _client, engagement, _assessment = seed_engagement(db)
    token = TOKEN_IN_URL.search(_create(http, engagement.id).text).group(1)
    assert "data-contact-greeting" not in http.get(f"/magic/{token}").text


def _expire(db, engagement_id):
    link = _only_link(db, engagement_id)
    link.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()


def test_invalid_page_offers_the_firm_contact_email_when_set(db, http):
    client, engagement, _assessment = seed_engagement(db, client_name="Kestrel Health", name="Kestrel gap")
    token = TOKEN_IN_URL.search(_create(http, engagement.id, contact_name="Ananya").text).group(1)
    _expire(db, engagement.id)
    firm_settings.update(
        db,
        contact_email="partner@northgate.example",
        archived_retention_years=7,
        accent_theme="midnight",
        actor="consultant:Priya",
    )
    db.commit()
    expired = http.get(f"/magic/{token}")
    assert expired.status_code == 404
    assert 'href="mailto:partner@northgate.example"' in expired.text
    assert f"Email {firm_settings.get(db).firm_name}" in expired.text
    # Never the token, the engagement, the client or the link's contact.
    for secret in (token, engagement.name, client.name, "Ananya"):
        assert secret not in expired.text
    # Byte-identical for every invalid token, as before.
    assert http.get("/magic/AAAAAAAAAAAAAAAAAAAAAA").content == expired.content
    assert http.post(f"/magic/{token}", data={}).content == expired.content


def test_invalid_page_without_a_firm_contact_shows_nothing_extra(db, http):
    response = http.get("/magic/AAAAAAAAAAAAAAAAAAAAAA")
    assert response.status_code == 404
    assert "mailto:" not in response.text and "data-firm-contact" not in response.text
    assert magic_links.INVALID_LINK_MESSAGE in response.text


def test_contact_columns_migration(tmp_path):
    path = tmp_path / "contacts.sqlite3"
    config = alembic_config(path)
    command.upgrade(config, "head")
    with sqlite3.connect(path) as connection:
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(magic_links)")}
    assert columns["contact_name"][2].upper() == "VARCHAR(200)" and columns["contact_name"][3] == 0
    assert columns["contact_email"][2].upper() == "VARCHAR(254)" and columns["contact_email"][3] == 0
    command.downgrade(config, "-1")
    with sqlite3.connect(path) as connection:
        assert "contact_name" not in {row[1] for row in connection.execute("PRAGMA table_info(magic_links)")}
