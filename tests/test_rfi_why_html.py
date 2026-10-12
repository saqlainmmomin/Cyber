"""The request page keeps signed checks in a closed, optional fold."""

from copy import deepcopy
from html import unescape

from lxml import html
import re

import pytest

from app.services import rfi_requests
from tests.test_p5_6_rfi_rebuild import (  # noqa: F401
    _register_frameworks,
    _seed,
    db,
    db_path,
    http,
)


def test_iso_access_request_has_closed_why_fold(db, http):
    assessment = _seed(db, frameworks=("iso27001",))
    document = rfi_requests.build_rfi_document(db, assessment)
    item = next(
        item for item in document["items"]
        if item.get("document_type") == "access_control_policy"
    )
    response = http.get(f"/assessments/{assessment.id}/rfi")
    assert response.status_code == 200
    row = response.text.split(f'data-rfi-item="{item["item_id"]}"', 1)[1]
    fold = re.search(r"(<details data-rfi-why[^>]*>)(.*?)</details>", row, re.S)
    assert fold is not None
    assert "open" not in fold.group(1)
    assert "Why we ask: 20 checks across 7 controls" in fold.group(2)
    soup = html.fromstring(response.text)
    rendered_item = soup.xpath(f'//*[@data-rfi-item="{item["item_id"]}"]')[0]
    request = rendered_item.xpath('.//*[@data-rfi-request-text]')[0]
    assert request is not None
    artifacts = request.xpath(".//ul/li")
    assert len(artifacts) == 17
    top_list = request.xpath(".//ul")[0]
    assert len(top_list.xpath("./li")) == 12
    assert len(top_list.xpath(".//ul")[0].xpath("./li")) == 5
    assert "Example" in [text.strip() for text in request.itertext()]
    assert "Good looks like" in [text.strip() for text in request.itertext()]
    assert "Period (auditor)" in request.text_content()
    assert "Sample size (auditor)" in request.text_content()
    assert item["summary"] in request.text_content()
    assert item["example"] in request.text_content()
    assert item["good_looks_like"] in request.text_content()
    assert "max-width:70ch" in html.tostring(request, encoding="unicode")
    criteria = [criterion for control in item["why_we_ask"] for criterion in control["criteria"]]
    assert len(criteria) == 20
    for control in item["why_we_ask"]:
        assert f'{control["requirement_id"]} {control["title"]}' in unescape(fold.group(2))
    for criterion in criteria:
        assert criterion["statement"] not in request.text_content()
        assert criterion["statement"] in unescape(fold.group(2))
        assert f'Evidence hint: {criterion["evidence_hint_label"]}' in unescape(fold.group(2))
        assert "_" not in criterion["evidence_hint_label"]
        assert f'Source basis: {criterion["source_basis"]}' in unescape(fold.group(2))
        label = "Design" if criterion["kind"] == "design" else "Operating"
        assert f'<span class="chip">{label}</span>' in fold.group(2)


@pytest.mark.parametrize("stored_value", ["absent", None, []])
def test_legacy_snapshot_items_render_without_why_fold(db, http, monkeypatch, stored_value):
    assessment = _seed(db, frameworks=("iso27001",))
    context = rfi_requests.page_context(db, assessment)
    stored_document = deepcopy(context["preview"])
    for item in stored_document["items"]:
        item.pop("why_we_ask", None)
        for key in ("summary", "what_to_send", "example", "good_looks_like"):
            item.pop(key, None)
        if stored_value != "absent":
            item["why_we_ask"] = stored_value
        item["request"] = "Previously stored request text.\nSource basis: preserved legacy basis."
    context["preview"] = stored_document
    monkeypatch.setattr(rfi_requests, "page_context", lambda *_args: context)
    response = http.get(f"/assessments/{assessment.id}/rfi")
    assert response.status_code == 200
    assert "data-rfi-why" not in response.text
    assert response.text.count("Previously stored request text.\nSource basis: preserved legacy basis.") == len(stored_document["items"])

    soup = html.fromstring(response.text)
    requests = soup.xpath("//*[@data-rfi-request-text]")
    assert requests
    assert all("cc-pre" in block.get("class", "").split() for block in requests)


def test_framework_pill_is_shown_once_per_request_not_once_per_control():
    from pathlib import Path

    template = Path("app/templates/pages/rfi.html").read_text(encoding="utf-8")
    assert 'item.requirements | map("first") | unique' in template
    assert "for framework_id, requirement_id in item.requirements %}{{ pill(" not in template


def test_request_row_wraps_so_the_text_keeps_the_width_on_a_phone():
    from pathlib import Path

    template = Path("app/templates/pages/rfi.html").read_text(encoding="utf-8")
    assert 'data-rfi-kind="{{ item.kind }}" style="flex-wrap:wrap"' in template
    assert 'class="txt" style="flex:1 1 280px;min-width:0"' in template


def test_fold_shows_readable_hints_and_keeps_source_basis_for_the_consultant():
    from pathlib import Path

    template = Path("app/templates/pages/rfi.html").read_text(encoding="utf-8")
    assert 'criterion.get("evidence_hint_label") or criterion.evidence_hint' in template
    assert "Source basis: {{ criterion.source_basis }}" in template
