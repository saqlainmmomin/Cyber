from types import SimpleNamespace
from pathlib import Path

from app import template_config
from app.routers.web import templates


def _request(path: str):
    return SimpleNamespace(url=SimpleNamespace(path=path), state=SimpleNamespace())


def _render(path: str, *, assessment=None, review_count=0):
    request = _request(path)
    context = template_config._navigation_context(request)
    return templates.env.get_template("base.html").render(
        request=request,
        branding={
            "firm_name": "CyberAssess",
            "firm_primary_hex": "#2563eb",
            "has_custom_nav_color": False,
        },
        firm_accent="midnight",
        accent_on_accent="#FFFFFF",
        nav_items=context["nav_items"],
        review_count=review_count,
        assessment=assessment,
        content="",
    )


def test_shell_uses_local_assets_and_attribute_theme_state():
    html = _render("/")
    assert "/static/vendor/htmx-2.0.4.min.js" in html
    assert "https://unpkg.com/htmx" not in html
    assert "/static/css/src/fonts.css" in html
    assert "Inter-Regular.woff2" in (
        Path(__file__).resolve().parents[1] / "app/static/css/src/fonts.css"
    ).read_text()
    assert '<html lang="en" data-theme="light" data-accent="midnight"' in html
    assert 'data-nav-key="home" aria-current="page"' in html
    assert 'data-nav-key="clients"' not in html


def test_navigation_marks_assessment_routes_as_engagements(monkeypatch):
    all_available = tuple(dict(item, available=True) for item in template_config.NAV_ITEMS)
    monkeypatch.setattr(template_config, "NAV_ITEMS", all_available)
    context = template_config._navigation_context(_request("/assessments/example"))
    current = {item["key"] for item in context["nav_items"] if item["current"]}
    assert current == {"engagements"}


def test_review_badge_is_present_only_when_nonzero(monkeypatch):
    all_available = tuple(dict(item, available=True) for item in template_config.NAV_ITEMS)
    monkeypatch.setattr(template_config, "NAV_ITEMS", all_available)
    zero = template_config._navigation_context(_request("/"))
    zero_html = templates.env.get_template("base.html").render(
        request=_request("/"),
        branding={"firm_name": "CyberAssess", "firm_primary_hex": "#2563eb", "has_custom_nav_color": False},
        firm_accent="midnight",
        accent_on_accent="#FFFFFF",
        nav_items=zero["nav_items"],
        review_count=0,
    )
    assert '<span class="count">' not in zero_html


def test_review_badge_uses_one_query_for_unresolved_conclusions():
    class Result:
        def all(self):
            return [
                ("pending-id", "proposed", None, "ai"),
                ("approved-id", "approved", None, "consultant:Reviewer"),
            ]

    class Database:
        calls = 0

        def execute(self, _query):
            self.calls += 1
            return Result()

    request = _request("/")
    request.state.db = Database()
    context = template_config._navigation_context(request)
    assert context["review_count"] == 1
    assert request.state.db.calls == 1
