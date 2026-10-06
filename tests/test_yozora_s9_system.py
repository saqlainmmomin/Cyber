"""Contracts for the S9 shared behaviour layer."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
import pytest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "templates"


def _template_env() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)


def test_global_script_uses_safe_toast_markup_and_preserves_response_headers():
    source = (ROOT / "app/static/js/app.js").read_text()
    start = source.index("function toast(")
    end = source.index("window.toast = toast;", start)
    toast_source = source[start:end]

    assert "function toast(" in source
    assert "textContent" in toast_source
    assert "innerHTML" not in toast_source
    assert "X-Toast-Message" in source
    assert "X-Toast-Type" in source
    assert "decodeURIComponent" in source
    assert "X-Conclusion-Conflict" in source
    assert "status === 401" in source
    assert "htmx:sendError" in source
    assert "classList.add('loading')" in source


def test_system_css_contains_hidden_guard_and_transition_variants():
    components = (ROOT / "design/yozora-components.css").read_text()
    patterns = (ROOT / "design/yozora-patterns.css").read_text()

    assert "[hidden]{display:none!important}" in patterns
    assert ".htmx-swapping" in patterns
    assert ".htmx-settling" in patterns
    assert ".swap-in" in patterns
    assert ".btn.loading" in components
    assert ".anchor .menu.flip-y" in patterns
    assert ".toast.bad" in components
    assert ".toast.info" in components
    assert "max-width:600px" in components
    assert ".modal-open" in components


def test_system_macros_cover_action_toast_typed_confirmation_and_menu_states():
    env = _template_env()
    rendered = env.from_string(
        """
        {% from "components/ui.html" import toast, modal, menu %}
        {{ toast("Saved", "success", "Undo") }}
        {{ toast("Failed", "error", "Try again") }}
        {{ modal("Purge", "Permanent", typed_value="FY2026", typed_help="FY2026") }}
        {{ menu([{"label": "Current", "selected": true}, {"label": "Delete", "bad": true, "disabled": true}], heading="Versions") }}
        """
    ).render()

    assert 'class="toast"' in rendered
    assert 'class="toast bad"' in rendered
    assert "Undo" in rendered and "Try again" in rendered
    assert 'data-confirm-value="FY2026"' in rendered
    assert 'disabled' in rendered
    assert 'class="gh"' in rendered
    assert 'aria-disabled="true"' in rendered
    assert 'aria-selected="true"' in rendered


def test_s9_templates_parse_without_rendering_application_services():
    env = _template_env()
    for name in (
        "components/ui.html",
        "pages/design.html",
        "pages/design_s9_system.html",
    ):
        env.get_template(name)


def test_s9_preview_registry_covers_the_system_mockups():
    pytest.importorskip("boto3")
    from app.routers.design_s9_system import SCREEN_STATES

    assert set(SCREEN_STATES) == {
        "b7-toasts",
        "b7-skeleton-table",
        "b7-skeleton-detail",
        "b7-htmx-swaps",
        "b7-modals",
        "b7-menus-popovers",
        "b7-mobile-shell",
    }
    assert SCREEN_STATES["b7-modals"] == ("delete", "purge", "send", "invite", "discard", "failed")
