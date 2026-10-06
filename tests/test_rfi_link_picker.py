"""RFI Client links picker: grouping, coverage labels, error re-render and redirects."""

from __future__ import annotations

import re
from pathlib import Path

from app.models.magic_link import MagicLink
from app.models.report_snapshot import ReportSnapshot

from tests.test_p5_6_rfi_rebuild import (  # noqa: F401  (fixtures)
    _create_rfi_link,
    _document,
    _generate,
    _issue,
    _register_frameworks,
    _seed,
    db,
    db_path,
    http,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _issued(db, http, frameworks=("iso27001",)):
    assessment = _seed(db, frameworks=frameworks)
    snapshot_id = _generate(http, assessment).json()["snapshot_id"]
    assert _issue(http, assessment, snapshot_id).status_code == 200
    items = _document(db, db.get(ReportSnapshot, snapshot_id))["items"]
    return assessment, snapshot_id, [item["item_id"] for item in items]


def _links_tab(http, assessment) -> str:
    response = http.get(f"/assessments/{assessment.id}/rfi?tab=links")
    assert response.status_code == 200
    return response.text


def _between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    return text[start:text.index(end_marker, start)]


def _details_tag(text: str) -> str:
    match = re.search(r"<div data-rfi-link-details[^>]*>", text)
    assert match is not None
    return match.group(0)


def test_issued_rfi_without_links_lists_every_item_as_unassigned(db, http):
    assessment, _snapshot_id, item_ids = _issued(db, http)
    page = _links_tab(http, assessment)
    unassigned = _between(page, "data-rfi-unassigned-items", "</div>\n")
    for item_id in item_ids:
        assert f'value="{item_id}"' in unassigned
    assert "data-rfi-covered-items" not in page
    assert "hidden" in _details_tag(page)
    assert page.count("data-rfi-coverage=") == len(item_ids)
    assert page.count("data-rfi-unsent") == len(item_ids)
    assert 'data-rfi-selected-count aria-live="polite">No items selected' in page


def test_covered_items_move_to_a_disclosure_naming_the_contact(db, http):
    assessment, snapshot_id, item_ids = _issued(db, http)
    response = _create_rfi_link(
        http, assessment, snapshot_id, item_ids[:3], contact_name="Ananya Rao"
    )
    assert response.status_code == 200
    page = _links_tab(http, assessment)
    covered = _between(page, "data-rfi-covered-items", "</details>")
    assert "3 items already in an active link" in covered
    for item_id in item_ids[:3]:
        assert f'value="{item_id}"' in covered
    assert covered.count("In a link to Ananya Rao, expires") == 3
    unassigned = _between(page, "data-rfi-unassigned-items", "data-rfi-covered-items")
    for item_id in item_ids[3:]:
        assert f'value="{item_id}"' in unassigned
    for item_id in item_ids[:3]:
        assert f'value="{item_id}"' not in unassigned
    assert page.count("data-rfi-coverage=") == len(item_ids)
    assert page.count("data-rfi-unsent") == len(item_ids) - 3
    assert " open" not in re.search(r"<details[^>]*data-rfi-covered-items[^>]*>", page).group(0)


def test_validation_error_keeps_selection_and_typed_values(db, http):
    assessment, snapshot_id, _item_ids = _issued(db, http)
    response = http.post(
        f"/assessments/{assessment.id}/rfi/versions/{snapshot_id}/magic-links",
        data={
            "item_ids": "RFI-002",
            "contact_name": "Typed Name",
            "contact_email": "nope",
            "expires_in_days": "9",
        },
    )
    assert response.status_code == 200
    assert "data-rfi-link-error" in response.text
    assert 'value="RFI-002" checked' in response.text
    assert "hidden" not in _details_tag(response.text)
    assert 'value="nope"' in response.text
    assert 'value="Typed Name"' in response.text
    assert 'name="expires_in_days" type="number" value="9"' in response.text
    assert db.query(MagicLink).count() == 0


def test_validation_error_opens_covered_group_when_a_covered_item_is_selected(db, http):
    assessment, snapshot_id, item_ids = _issued(db, http)
    assert _create_rfi_link(http, assessment, snapshot_id, item_ids[:2]).status_code == 200
    response = http.post(
        f"/assessments/{assessment.id}/rfi/versions/{snapshot_id}/magic-links",
        data={"item_ids": item_ids[0], "contact_email": "nope"},
    )
    tag = re.search(r"<details[^>]*data-rfi-covered-items[^>]*>", response.text).group(0)
    assert " open" in tag
    assert f'value="{item_ids[0]}" checked' in response.text


def test_generate_and_issue_redirect_to_the_next_tab(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    generated = _generate(http, assessment)
    assert generated.status_code == 200
    assert generated.headers["HX-Redirect"] == f"/assessments/{assessment.id}/rfi?tab=versions"
    issued = _issue(http, assessment, generated.json()["snapshot_id"])
    assert issued.status_code == 200
    assert issued.headers["HX-Redirect"] == f"/assessments/{assessment.id}/rfi?tab=links"


def test_free_text_error_reopens_request_something_else(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    response = http.post(
        f"/engagements/{assessment.engagement_id}/magic-links",
        data={"items": "", "contact_email": "client@example.com"},
    )
    assert response.status_code == 200
    tag = re.search(r"<details[^>]*data-request-something-else[^>]*>", response.text)
    assert tag is not None and " open" in tag.group(0)
    page = http.get(f"/engagements/{assessment.engagement_id}/requests")
    plain = re.search(r"<details[^>]*data-request-something-else[^>]*>", page.text).group(0)
    assert " open" not in plain


def test_revoked_link_returns_items_to_unassigned(db, http):
    assessment, snapshot_id, item_ids = _issued(db, http)
    assert _create_rfi_link(http, assessment, snapshot_id, item_ids[:2]).status_code == 200
    link = db.query(MagicLink).one()
    page = _links_tab(http, assessment)
    assert page.count("data-rfi-unsent") == len(item_ids) - 2
    revoke = http.post(f"/engagements/{assessment.engagement_id}/magic-links/{link.id}/revoke")
    assert revoke.status_code == 200
    page = _links_tab(http, assessment)
    assert page.count("data-rfi-unsent") == len(item_ids)
    assert "data-rfi-covered-items" not in page


def test_rfi_templates_have_no_apostrophes():
    for template in (
        REPO_ROOT / "app/templates/pages/rfi.html",
        REPO_ROOT / "app/templates/partials/rfi_links.html",
    ):
        source = template.read_text()
        assert "'" not in source and "|safe" not in source and "CyberAssess" not in source


def test_active_link_from_an_older_version_is_explained(db, http):
    assessment, first_id, item_ids = _issued(db, http)
    assert _create_rfi_link(http, assessment, first_id, item_ids[:2]).status_code == 200
    page = _links_tab(http, assessment)
    assert "data-rfi-older-links" not in page
    second = _generate(http, assessment)
    assert second.status_code == 200
    assert _issue(http, assessment, second.json()["snapshot_id"]).status_code == 200
    page = _links_tab(http, assessment)
    assert "data-rfi-older-links" in page
    assert "data-rfi-covered-items" not in page


def test_page_has_back_link_and_unissued_links_tab_points_to_versions(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    page = _links_tab(http, assessment)
    assert f'href="/engagements/{assessment.engagement_id}/requests" data-rfi-back-link' in page
    assert f'href="/assessments/{assessment.id}/rfi?tab=versions">Go to versions' in page
    assert "data-rfi-link-form" not in page
