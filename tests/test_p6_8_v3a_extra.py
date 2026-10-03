"""Regression coverage for the V3-A board-inputs form triggers."""

from __future__ import annotations

from html.parser import HTMLParser

from tests.p6_8_v3_support import db, db_path, engine, fixture_assessment, gate, http


class _BoardActionFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "form":
            attributes = dict(attrs)
            if "data-board-action" in attributes:
                self.forms.append(attributes)


def test_board_action_forms_submit_when_responsibility_changes(db, http, fixture_assessment):
    page = http.get(f"/assessments/{fixture_assessment.id}/board-inputs")
    assert page.status_code == 200

    parser = _BoardActionFormParser()
    parser.feed(page.text)

    assert parser.forms
    for form in parser.forms:
        assert form.get("hx-trigger") == "change", form
