"""Requests hub: per-assessment next step and the collapsed free-text request."""

from __future__ import annotations

import re

from tests.test_p5_6_rfi_rebuild import (  # noqa: F401  (fixtures)
    _create_rfi_link,
    _generate,
    _issue,
    _register_frameworks,
    _seed,
    db,
    db_path,
    http,
)


def _requests_page(http, assessment) -> str:
    response = http.get(f"/engagements/{assessment.engagement_id}/requests")
    assert response.status_code == 200
    return response.text


def _next_step(page: str) -> re.Match:
    match = re.search(
        r'<a class="btn ghost sm" href="(?P<href>[^"]+)" data-request-next-step="(?P<tab>[a-z]+)">(?P<label>[^<]+)</a>',
        page,
    )
    assert match is not None
    return match


def _details_block(page: str, marker: str) -> str:
    """Return the <details> element carrying ``marker``, including nested disclosures."""
    start = page.rindex("<details", 0, page.index(marker))
    depth, cursor = 0, start
    for match in re.finditer(r"<details\b|</details>", page[start:]):
        depth += 1 if match.group(0) == "<details" else -1
        if depth == 0:
            cursor = start + match.end()
            break
    return page[start:cursor]


def test_next_step_follows_the_rfi_lifecycle(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    step = _next_step(_requests_page(http, assessment))
    assert step["tab"] == "items" and step["label"] == "Prepare RFI"
    assert step["href"] == f"/assessments/{assessment.id}/rfi?tab=items"

    snapshot_id = _generate(http, assessment).json()["snapshot_id"]
    step = _next_step(_requests_page(http, assessment))
    assert step["tab"] == "versions" and step["label"] == "Review draft version 1"

    assert _issue(http, assessment, snapshot_id).status_code == 200
    page = _requests_page(http, assessment)
    step = _next_step(page)
    assert step["tab"] == "links" and step["label"] == "Create client link"
    assert step["href"] == f"/assessments/{assessment.id}/rfi?tab=links"
    assert "0 of" in page and "received" in page

    assert _create_rfi_link(http, assessment, snapshot_id, ["RFI-001"]).status_code == 200
    page = _requests_page(http, assessment)
    step = _next_step(page)
    assert step["tab"] == "links" and step["label"] == "View links"
    assert f'data-href="/assessments/{assessment.id}/rfi"' in page
    assert page.count("data-request-next-step=") == 1


def test_request_something_else_follows_the_link_cards_and_starts_closed(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    snapshot_id = _generate(http, assessment).json()["snapshot_id"]
    assert _issue(http, assessment, snapshot_id).status_code == 200
    assert _create_rfi_link(http, assessment, snapshot_id, ["RFI-001"]).status_code == 200
    page = _requests_page(http, assessment)
    assert page.index("data-request-something-else") > page.index("data-link-id")
    tag = re.search(r"<details[^>]*data-request-something-else[^>]*>", page).group(0)
    assert " open" not in tag
    assert "New link" not in page.replace('aria-label="New link"', "")


def test_free_text_form_posts_from_inside_the_disclosure(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    page = _requests_page(http, assessment)
    disclosure = _details_block(page, "data-request-something-else")
    assert f'hx-post="/engagements/{assessment.engagement_id}/magic-links"' in disclosure
    assert 'id="new-link-form"' in disclosure and 'id="requested-items"' in disclosure
    assert "Upload limits" in disclosure and "Create link" in disclosure
    assert "No client links yet" in page
    assert "then send its items from the Client links tab" in page
