"""Focused contracts for the Yozora S5 assessment surfaces."""

from __future__ import annotations

import re

from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    db,
    http,
    seed_engagement,
)


def _assessment_nav(page: str) -> str:
    match = re.search(
        r'<nav class="tabs" aria-label="Assessment">(.*?)</nav>',
        page,
        re.DOTALL,
    )
    assert match, "assessment tab row missing"
    return match.group(1)


def test_assessment_overview_has_five_tabs_and_real_stepper(db, http):
    _client, _engagement, assessment = seed_engagement(
        db,
        client_name="Meridian Ledger Technologies",
        name="FY2026 privacy readiness",
        frameworks=("dpdpa", "iso27001"),
    )
    assessment.name = "Head office"
    assessment.scope_answers = "{}"
    assessment.context_answers = "[]"
    db.commit()

    page = http.get(f"/assessments/{assessment.id}")

    assert page.status_code == 200
    nav = _assessment_nav(page.text)
    assert [label for label in re.findall(r">([^<>]+)</a>", nav)] == [
        "Overview",
        "Scope",
        "Questionnaire",
        "Review",
        "Report",
    ]
    assert "Documents" not in nav
    assert page.text.count('class="stp') == 5
    assert all(label in page.text for label in ("Scope", "Evidence", "Questionnaire", "Review", "Report"))
    assert f'href="/assessments/{assessment.id}?tab=documents"' in page.text
    assert "data-visual-mask" in page.text
    assert 'data-assessment-identity' in page.text
    assert 'id="desk-review-area"' not in page.text


def test_documents_url_keeps_legacy_content_without_documents_tab(db, http):
    _client, _engagement, assessment = seed_engagement(db)

    page = http.get(f"/assessments/{assessment.id}?tab=documents")

    assert page.status_code == 200
    assert 'id="document-list"' in page.text
    assert "Documents" not in _assessment_nav(page.text)


def test_questionnaire_owns_desk_review_target_and_live_htmx_request(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    assessment.context_answers = "[]"
    db.commit()

    page = http.get(f"/assessments/{assessment.id}?tab=questionnaire")

    assert page.status_code == 200
    assert re.search(
        rf'<[^>]+id="desk-review-area"[^>]+hx-get="/assessments/{assessment.id}/desk-review-status"',
        page.text,
    )
    assert 'class="stp' not in page.text
    assert 'hx-target="#desk-review-area"' not in _assessment_nav(page.text)


def test_non_dpdpa_questionnaire_does_not_show_dpdpa_screening_copy(db, http):
    _client, _engagement, assessment = seed_engagement(db, frameworks=("iso27001",))
    assessment.context_answers = "[]"
    db.commit()

    page = http.get(f"/assessments/{assessment.id}?tab=questionnaire")

    assert page.status_code == 200
    assert 'data-screening-unavailable' in page.text
    assert "Start screening" not in page.text
    assert "DPDPA" not in page.text
