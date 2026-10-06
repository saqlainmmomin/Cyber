"""Focused contracts for the Yozora S9 error and empty-state group."""

from __future__ import annotations

import html
import logging
import re

from fastapi.routing import APIRoute

from app.main import app
from design.harness.seed_s9 import screen_states
from tests.yozora_support import (  # noqa: F401
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
)


REFERENCE_CODE = re.compile(r"\b[0-9a-f]{4}(?:-[0-9a-f]{4}){2}\b")


def _reference(text: str) -> str:
    match = REFERENCE_CODE.search(text)
    assert match, text
    return match.group(0)


def test_browser_404_renders_reference_code_and_logs_path(caplog, http):
    caplog.set_level(logging.WARNING, logger="app.main")

    response = http.get("/s9-missing-page")

    assert response.status_code == 404
    reference = _reference(response.text)
    assert "Page not found" in response.text
    assert "/s9-missing-page" not in response.text
    assert all(secret not in response.text for secret in ("Not Found", "s9-missing-page"))
    records = [record for record in caplog.records if record.name == "app.main"]
    assert any(
        reference in record.getMessage()
        and "/s9-missing-page" in record.getMessage()
        and "HTTPException" in record.getMessage()
        for record in records
    )


def test_error_log_quotes_paths_that_contain_reference_like_text(caplog, http):
    caplog.set_level(logging.WARNING, logger="app.main")

    response = http.get("/s9-missing/reference=forged")

    assert response.status_code == 404
    records = [record for record in caplog.records if record.name == "app.main"]
    assert any(
        "path=b'/s9-missing/reference=forged'" in record.getMessage()
        for record in records
    )


def test_error_actions_are_links_handled_without_inline_javascript(http):
    response = http.get("/design/pages/b7-500?state=error")

    assert response.status_code == 200
    assert "onclick=" not in response.text
    assert 'data-error-action="retry"' in response.text
    assert 'data-error-action="back"' in response.text


def test_forced_500_renders_reference_code_and_does_not_expose_exception(caplog, http):
    caplog.set_level(logging.ERROR, logger="app.main")

    def raise_for_s9():
        raise RuntimeError("s9-secret-exception-message")

    route = APIRoute("/s9-forced-error", raise_for_s9, methods={"GET"})
    app.router.routes.append(route)
    try:
        response = http.get("/s9-forced-error")
    finally:
        app.router.routes.remove(route)

    assert response.status_code == 500
    reference = _reference(response.text)
    assert "This page couldn't be loaded" in html.unescape(response.text)
    assert "s9-secret-exception-message" not in response.text
    records = [record for record in caplog.records if record.name == "app.main"]
    assert any(
        reference in record.getMessage()
        and "/s9-forced-error" in record.getMessage()
        and "RuntimeError" in record.getMessage()
        for record in records
    )


def test_json_errors_and_validation_keep_json_responses(http):
    not_found = http.get("/s9-missing-api", headers={"Accept": "application/json"})
    api_not_found = http.get("/api/s9-missing")
    validation = http.post("/api/assessments", json={})

    assert not_found.status_code == 404
    assert not_found.json() == {"detail": "Not Found"}
    assert api_not_found.status_code == 404
    assert api_not_found.json() == {"detail": "Not Found"}
    assert validation.status_code == 422
    assert isinstance(validation.json()["detail"], list)
    assert "Page not found" not in validation.text


def test_engagement_404_does_not_disclose_the_id_or_existence(db, http):
    _client, engagement, _assessment = seed_engagement(db)

    existing_path = f"/engagements/{engagement.id}/s9-missing"
    missing_path = "/engagements/s9-missing/s9-missing"
    existing = http.get(existing_path)
    missing = http.get(missing_path)

    assert existing.status_code == missing.status_code == 404
    assert "Engagement not found" in existing.text
    assert 'href="/engagements"' in existing.text
    assert existing_path not in existing.text
    assert missing_path not in missing.text
    normalized_existing = REFERENCE_CODE.sub("reference-code", existing.text)
    normalized_missing = REFERENCE_CODE.sub("reference-code", missing.text)
    assert normalized_existing == normalized_missing


def test_s9_preview_registry_covers_error_and_empty_states():
    states = screen_states()

    assert states["b7-404"] == ("page", "engagement")
    assert states["b7-500"] == ("error", "down", "upstream")
    assert states["b7-empty-states"] == (
        "engagements",
        "evidence",
        "review",
        "search",
        "findings",
        "report",
    )


def test_s9_error_previews_render_all_states(http):
    for screen, states in (
        ("b7-404", ("page", "engagement")),
        ("b7-500", ("error", "down", "upstream")),
    ):
        for state in states:
            response = http.get(f"/design/pages/{screen}?state={state}")
            assert response.status_code == 200, (screen, state, response.text[:500])
            assert _reference(response.text)


def test_s9_empty_previews_render_all_states(db, http):
    seed_engagement(db)

    for state in screen_states()["b7-empty-states"]:
        response = http.get(f"/design/pages/b7-empty-states?state={state}")
        assert response.status_code == 200, (state, response.text[:500])
