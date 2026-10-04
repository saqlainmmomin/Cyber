"""Focused contracts for the Yozora S5 assessment surfaces."""

from __future__ import annotations

import json
import re

from app.models.desk_review import DeskReviewSummary
from tests.yozora_support import (  # noqa: F401 - fixtures are used by name
    _register_frameworks,
    db,
    db_path,
    engine,
    http,
    seed_engagement,
    upload_root,
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
    assert f'href="/assessments/{assessment.id}?tab=overview&amp;framework=dpdpa"' in page.text
    assert f'href="/assessments/{assessment.id}?tab=documents"' in page.text
    assert "data-visual-mask" in page.text
    assert 'data-assessment-identity' in page.text
    assert 'id="desk-review-area"' not in page.text


def test_engagement_linked_overview_renders_context_block(db, http):
    _client, engagement, assessment = seed_engagement(
        db,
        client_name="Meridian Ledger Technologies",
        name="FY2026 privacy readiness",
    )
    assessment.scope_answers = "{}"
    db.commit()

    page = http.get(f"/assessments/{assessment.id}?tab=overview")

    assert page.status_code == 200
    assert "Retention" in page.text
    assert "Client evidence links" in page.text
    assert f"/engagements/{engagement.id}/aws-evidence" in page.text


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
        rf'<[^>]+id="desk-review-area"[^>]+hx-get="/assessments/{assessment.id}/desk-review-status\?surface=questionnaire"',
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


def test_real_assessment_error_uses_analysis_failure_copy(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    assessment.scope_answers = "{}"
    assessment.status = "error"
    db.commit()

    page = http.get(f"/assessments/{assessment.id}?tab=overview")

    assert page.status_code == 200
    assert "Analysis failed" in page.text
    assert "This framework did not load" not in page.text


def test_questionnaire_desk_review_stats_failure_keeps_http_200(db, http, monkeypatch):
    _client, _engagement, assessment = seed_engagement(db)
    db.add(
        DeskReviewSummary(
            assessment_id=assessment.id,
            status="completed",
            document_catalog=json.dumps([]),
            coverage_summary=json.dumps({}),
        )
    )
    db.commit()

    def fail_builder(*_args, **_kwargs):
        raise RuntimeError("questionnaire builder unavailable")

    monkeypatch.setattr("app.services.question_engine.build_adaptive_questionnaire", fail_builder)

    response = http.get(f"/assessments/{assessment.id}/desk-review-status?surface=questionnaire")

    assert response.status_code == 200


def test_s5_previews_use_real_chrome_and_loaded_partials(db, http):
    question_step = http.get("/design/pages/b3-question-step?state=org")
    assert question_step.status_code == 200
    assert 'data-assessment-identity' in question_step.text
    assert "1 of 4" in question_step.text
    assert "organisation" in question_step.text

    screening = http.get("/design/pages/b3-screening-form")
    assert screening.status_code == 200
    assert screening.text.count("Covers") == 9
    assert screening.text.count("<fieldset class=\"qgroup\">") == 9
    assert "Run screening" in screening.text

    sections = http.get("/design/pages/b3-sections")
    assert sections.status_code == 200
    assert 'id="section-content"' in sections.text
    assert "Does every notice name each purpose in plain language?" in sections.text
    assert 'hx-get="/assessments/assessment-s5-preview/questionnaire/section/' not in sections.text

    desk_review = http.get("/design/pages/b4-desk_review?state=running")
    assert desk_review.status_code == 200
    assert "Analysing 6 documents against India DPDPA and ISO 27001" in desk_review.text
    assert 'hx-get="/assessments/assessment-s5-preview/desk-review-status' not in desk_review.text


def test_b4_desk_review_preview_renders_the_status_endpoint_for_a_real_assessment(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    db.add(
        DeskReviewSummary(
            assessment_id=assessment.id,
            status="error",
            error_message="The analysis service did not respond within 10 minutes.",
        )
    )
    db.commit()

    page = http.get(f"/design/pages/b4-desk_review?state=error&assessment_id={assessment.id}")
    fragment = http.get(f"/assessments/{assessment.id}/desk-review-status")

    assert page.status_code == 200
    assert "<h1>Pre-fill from documents</h1>" in page.text
    assert "The analysis service did not respond within 10 minutes." in page.text
    assert f'hx-post="/assessments/{assessment.id}/run-desk-review"' in page.text
    assert "Retry desk review" in fragment.text
