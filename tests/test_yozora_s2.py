"""Focused contracts for the Yozora S2 macro layer and debug gallery."""

from __future__ import annotations

import re
from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.config import settings
from app.routers.design import design_gallery, design_preview
from app.routers.web import templates


ROOT = Path(__file__).resolve().parents[1]
CSS_CLASSES = set(
    re.findall(
        r"\.([A-Za-z_][A-Za-z0-9_-]*)",
        (ROOT / "design/yozora-components.css").read_text()
        + (ROOT / "design/yozora-patterns.css").read_text(),
    )
)


def _render(template_name: str, **context) -> str:
    return templates.env.get_template(template_name).render(**context)


def test_design_gallery_is_debug_only_and_dark_query_is_rendered(monkeypatch):
    monkeypatch.setattr(settings, "env", "development")
    request = SimpleNamespace(query_params={}, url=SimpleNamespace(path="/design"), state=SimpleNamespace())
    response = design_gallery(request)
    assert response.status_code == 200
    assert 'data-theme="light"' in response.body.decode()
    assert "Evidence request" in response.body.decode()

    dark = design_gallery(SimpleNamespace(query_params={"dark": ""}, url=request.url, state=request.state))
    assert dark.status_code == 200
    assert 'data-theme="dark"' in dark.body.decode()

    monkeypatch.setattr(settings, "env", "production")
    with pytest.raises(HTTPException) as gallery_error:
        design_gallery(request)
    assert gallery_error.value.status_code == 404
    with pytest.raises(HTTPException) as preview_error:
        design_preview(request, "unknown")
    assert preview_error.value.status_code == 404


def test_gallery_macro_output_uses_only_shared_css_classes():
    html = _render("pages/design.html", dark=False, focus=False)
    rendered_classes = {
        token
        for value in re.findall(r'class="([^"]+)"', html)
        for token in value.split()
    }
    # The gallery's approved page scaffold is intentionally local to the
    # baseline; component macros themselves must use the shared CSS vocabulary.
    assert rendered_classes - CSS_CLASSES <= {"g", "row", "w"}


def test_every_macro_output_uses_only_shared_css_classes():
    fixture = templates.env.from_string(
        """
        {% from "components/ui.html" import icon, button, link_button, pill, chip, status, field, checkbox, radio, switch, empty_state, skeleton, alert, progress_bar, key_value, stat, ring, distribution, toast, toast_container, modal, menu, code_block, disclosure, tooltip, swatches, drop, request_marker, request_picker, request_card %}
        {% from "components/layout.html" import page_header, breadcrumb, tabs, engagement_tabs, assessment_tabs, seg, stepper, table, rows_list, line_list, nav, brand, user_menu, review_list_item, review_detail, citation, recommendation, check_list, progress_ticks, filter_toolbar, pager, popover, login_shell %}
        {{ icon("check") }}{{ button("Save") }}{{ link_button("Open", "/design") }}{{ pill("Okay", "ok") }}{{ chip("ISO") }}{{ status("Open") }}
        {{ field("Name", name="name") }}{{ checkbox("Include", checked=true) }}{{ radio("A", "choice", "a") }}{{ switch("Enabled") }}
        {{ empty_state("Empty", "Nothing here.", "Add", "/design") }}{{ skeleton() }}{{ alert("Notice") }}{{ progress_bar(50) }}
        {{ key_value([{"label":"A", "value":"B"}]) }}{{ stat("Count", "1") }}{{ ring(50) }}{{ distribution([{"tone":"ok", "label":"Okay", "value":1}]) }}
        {{ toast("Saved") }}{{ toast_container([{"message":"Saved", "tone":"success", "action_label":"Undo"}]) }}{{ modal("Delete", "This is permanent.") }}
        {{ menu([{"label":"Settings"}], open=true) }}{{ code_block("a.txt", "text") }}{{ disclosure("More", "Details") }}{{ tooltip("Help", "Helpful") }}
        {{ swatches([{"value":"a", "color":"#fff", "label":"A"}], "a") }}{{ drop("Upload") }}{{ request_marker() }}{{ request_picker([{"checked":true, "label":"Policy", "help":"Required"}]) }}
        {{ request_card("A", "a@example.com", "Active", 0, 1, "18 Oct 2026", []) }}
        {{ page_header("Page") }}{{ breadcrumb([{"label":"Home", "href":"/design"}, {"label":"Page", "href":"/design"}]) }}{{ tabs([{"label":"One", "href":"/design", "current":true}]) }}
        {{ engagement_tabs({"id":1}, "overview") }}{{ assessment_tabs({"id":1}, "overview") }}{{ seg([{"label":"One", "key":"one", "href":"/design"}], "one") }}
        {{ stepper([{"label":"Scope", "state":"done", "href":"/design"}, {"label":"Evidence", "state":"current", "href":"/design"}, {"label":"Report", "state":"next", "href":"/design"}]) }}
        {{ table(["Name"], [["One"]]) }}{{ rows_list([{"title":"One", "body":"Body", "icon_id":"check", "action_label":"Open", "href":"/design"}]) }}{{ line_list([{"title":"One", "body":"Body", "action_label":"Open", "href":"/design"}]) }}
        {{ nav([{"label":"Home", "href":"/design", "icon_id":"home", "current":true, "count":1}]) }}{{ brand() }}{{ user_menu("A", "A") }}{{ review_list_item("One", "Body", selected=true, decided=true, tone="ok") }}
        {{ review_detail("One") }}{{ citation("Source", "Quote") }}{{ recommendation("Recommendation", "Body") }}{{ check_list([{"tone":"ok", "label":"Check", "result":"Pass"}]) }}
        {{ progress_ticks(1, 2) }}{{ filter_toolbar() }}{{ pager("/design", "/design", "1") }}{{ popover("More", "Title", "Body") }}{{ login_shell("Firm") }}
        """
    ).render()
    rendered_classes = {
        token
        for value in re.findall(r'class="([^\"]+)"', fixture)
        for token in value.split()
    }
    assert rendered_classes <= CSS_CLASSES


@pytest.mark.parametrize(
    ("status", "label"),
    [
        ("quarantined", "Scanning"),
        ("active", "Available"),
        ("rejected", "Rejected"),
        ("invalidated", "Out of date"),
    ],
)
def test_evidence_status_badge_uses_design_vocabulary(status, label):
    html = _render("components/evidence_status_badge.html", status=status)
    assert label in html
    assert "bg-" not in html


def test_archived_evidence_badge_is_not_rendered():
    assert _render("components/evidence_status_badge.html", status="archived").strip() == ""


def test_control_outline_token_is_generated_and_distinct_from_line_strong():
    token_css = (ROOT / "app/static/css/yozora-tokens.css").read_text()
    tokens = __import__("design.tokens_tool", fromlist=["load_tokens"]).load_tokens()
    assert tokens[":root"]["--line-control"] == "rgba(30,36,56,.52)"
    assert tokens["[data-theme=dark]"]["--line-control"] == "rgba(255,255,255,.36)"
    assert "--line-control: rgba(30,36,56,.52);" in token_css
    assert "--line-control: rgba(255,255,255,.36);" in token_css

    components = (ROOT / "design/yozora-components.css").read_text()
    patterns = (ROOT / "design/yozora-patterns.css").read_text()
    for control_rule in (
        ".btn.secondary",
        ".choice input",
        ".choice input.switch,.switch",
        ".field input[type=file]::file-selector-button",
    ):
        assert control_rule in components
    assert components.count("var(--line-control)") >= 7
    assert ".swatches i" in patterns and "var(--line-control)" in patterns
    assert ".drop" in patterns and "var(--line-control)" in patterns
    assert ".mk" in patterns and "var(--line-control)" in patterns
    assert "--line-strong" in components  # non-control borders remain on their original token


def test_superseded_and_legacy_evidence_versions_keep_a_neutral_pill():
    assert "Superseded" in _render("components/evidence_status_badge.html", status="superseded")
    assert "Legacy (not migrated)" in _render("components/evidence_status_badge.html", status="legacy")
