"""S8 client-facing upload and invalid-link contracts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

from app.models.magic_link import MagicLink
from app.services import firm_settings, magic_links
from design.harness.seed_s8_client import SCREEN_STATES
from tests.yozora_support import (  # noqa: F401 - fixtures are imported by name
    _register_frameworks,
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
    return db.query(MagicLink).filter_by(engagement_id=engagement_id).one()


def test_upload_page_uses_client_shell_and_first_name_only(db, http):
    _client, engagement, _assessment = seed_engagement(db, client_name="Client sentinel")
    response = _create(http, engagement.id, contact_name="Ananya Rao")
    token = TOKEN_IN_URL.search(response.text).group(1)

    page = http.get(f"/magic/{token}")

    assert page.status_code == 200
    assert 'id="file-upload"' in page.text
    assert 'id="item-key"' in page.text
    assert 'class="req solid client-request"' in page.text
    assert 'class="btn secondary touch lead"' in page.text
    assert "data-contact-greeting" in page.text
    assert f"Ananya, {firm_settings.get(db).firm_name} needs these items." in page.text
    assert "Rao" not in page.text
    assert "Client sentinel" not in page.text
    assert page.headers["content-security-policy"].startswith(
        "default-src 'none'; style-src 'self' 'unsafe-inline';"
    )


def test_invalid_pages_are_state_specific_and_never_reveal_link_context(db, http):
    client, engagement, _assessment = seed_engagement(
        db, client_name="Client sentinel", name="Engagement sentinel"
    )
    response = _create(http, engagement.id, contact_name="Ananya Rao")
    token = TOKEN_IN_URL.search(response.text).group(1)
    link = _only_link(db, engagement.id)
    link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    firm_settings.update(
        db,
        contact_email="partner@northgate.example",
        archived_retention_years=7,
        accent_theme="midnight",
        actor="consultant",
    )
    db.commit()

    expired = http.get(f"/magic/{token}")
    revoked_link = magic_links.create_link(
        db,
        engagement_id=engagement.id,
        item_titles=["Another item"],
        expires_in_days=7,
        max_uploads=20,
        max_total_mb=100,
        actor="consultant",
    )
    magic_links.revoke_link(db, engagement_id=engagement.id, link_id=revoked_link.link.id)
    db.commit()
    revoked = http.get(f"/magic/{revoked_link.token}")
    unknown = http.get("/magic/AAAAAAAAAAAAAAAAAAAAAA")

    assert expired.status_code == revoked.status_code == unknown.status_code == 404
    assert "This link has expired" in expired.text
    assert "This link was turned off" in revoked.text
    assert "We could not find this link" in unknown.text
    assert "expired on" in expired.text
    for page, page_token in ((expired, token), (revoked, revoked_link.token), (unknown, "AAAAAAAAAAAAAAAAAAAAAA")):
        assert 'href="mailto:partner@northgate.example"' in page.text
        assert f"Email {firm_settings.get(db).firm_name}" in page.text
        for secret in (page_token, engagement.name, client.name, "Ananya"):
            assert secret not in page.text


def test_invalid_page_hides_firm_contact_when_not_configured(db, http):
    response = http.get("/magic/AAAAAAAAAAAAAAAAAAAAAA")

    assert response.status_code == 404
    assert "mailto:" not in response.text
    assert "Email " not in response.text


def test_client_preview_states_are_registered():
    assert SCREEN_STATES == {
        "b6-magic_upload": ("default", "uploading", "done", "error"),
        "b6-magic_invalid": ("expired", "revoked", "unknown"),
        "b7-link-expired": ("expired",),
    }
