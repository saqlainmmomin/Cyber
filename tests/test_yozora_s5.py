"""Focused contracts for the Yozora S5 assessment surfaces."""

from __future__ import annotations

import json
import re

from app.models.desk_review import DeskReviewFinding, DeskReviewSummary
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
    assert "Data landscape" in question_step.text

    screening = http.get("/design/pages/b3-screening-form")
    assert screening.status_code == 200
    assert screening.text.count("Covers") == 9
    assert screening.text.count("<div class=\"qgroup\">") == 9
    assert "Run screening" in screening.text

    sections = http.get("/design/pages/b3-sections")
    assert sections.status_code == 200
    assert 'id="section-content"' in sections.text
    assert "Are notices offered in the languages your data principals read?" in sections.text
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


def _seed_completed_desk_review(db, assessment):
    db.add(
        DeskReviewSummary(
            assessment_id=assessment.id,
            status="completed",
            document_catalog=json.dumps([{"filename": "privacy_notice.pdf"}]),
            coverage_summary=json.dumps({"CH2.NOTICE.1": "partial"}),
        )
    )
    db.add_all([
        DeskReviewFinding(
            assessment_id=assessment.id,
            finding_type="signal",
            framework_id="dpdpa",
            requirement_id="CH2.NOTICE.1",
            content="Breach notice never mentions the Data Protection Board",
            severity="critical",
            source_quote="We will notify affected customers within 72 hours.",
            source_location="Page 3",
        ),
        DeskReviewFinding(
            assessment_id=assessment.id,
            finding_type="absence",
            framework_id="dpdpa",
            requirement_id="CH2.NOTICE.1",
            content="The privacy notice names no grievance response time",
            severity="medium",
        ),
        DeskReviewFinding(
            assessment_id=assessment.id,
            finding_type="evidence",
            framework_id="dpdpa",
            requirement_id="CH2.NOTICE.1",
            content="Purposes are listed",
            source_quote="We use your personal data to provide the ledger service.",
        ),
    ])
    assessment.desk_review_status = "completed"
    db.commit()


def test_desk_review_page_renders_findings_for_a_real_assessment(db, http):
    _client, engagement, assessment = seed_engagement(db)
    _seed_completed_desk_review(db, assessment)

    page = http.get(f"/assessments/{assessment.id}/desk-review")

    assert page.status_code == 200
    assert "<h1>Pre-fill from documents</h1>" in page.text
    assert f'<a href="/assessments/{assessment.id}?tab=questionnaire">Questionnaire</a>' in page.text
    assert f'href="/engagements/{engagement.id}"' in page.text
    nav = _assessment_nav(page.text)
    assert re.search(r'aria-(selected|current)="[^"]+"[^>]*>Questionnaire<', nav)
    assert 'id="desk-review-area"' in page.text
    assert "Desk review complete" in page.text
    assert "Breach notice never mentions the Data Protection Board" in page.text
    assert "The privacy notice names no grievance response time" in page.text
    assert "We use your personal data to provide the ledger service." in page.text
    assert f'hx-post="/assessments/{assessment.id}/run-desk-review"' in page.text
    assert 'hx-target="#desk-review-area"' in page.text


def test_desk_review_page_keeps_live_polling_while_running(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    db.add(DeskReviewSummary(assessment_id=assessment.id, status="analyzing"))
    db.commit()

    page = http.get(f"/assessments/{assessment.id}/desk-review")

    assert page.status_code == 200
    assert f'hx-get="/assessments/{assessment.id}/desk-review-status"' in page.text
    assert 'hx-trigger="every 3s"' in page.text


def test_desk_review_page_404_for_unknown_assessment(http):
    assert http.get("/assessments/does-not-exist/desk-review").status_code == 404


def test_questionnaire_desk_review_card_is_a_summary_linking_to_the_page(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    _seed_completed_desk_review(db, assessment)

    card = http.get(f"/assessments/{assessment.id}/desk-review-status?surface=questionnaire")

    assert card.status_code == 200
    assert "Pre-filled from 1 document" in card.text
    assert "1 missing provisions · 1 red flag" in card.text
    assert f'href="/assessments/{assessment.id}/desk-review"' in card.text
    assert "What the documents show" in card.text
    assert "Breach notice never mentions the Data Protection Board" not in card.text
    assert "The privacy notice names no grievance response time" not in card.text
    assert "Evidence found" not in card.text


def test_scope_edit_reopens_saved_answers_and_complete_view_links_to_it(db, http):
    _client, _engagement, assessment = seed_engagement(
        db,
        client_name="Meridian Ledger Technologies",
        name="FY2026 privacy readiness",
        frameworks=("dpdpa", "iso27001"),
    )
    assessment.scope_answers = json.dumps({"SCP.1": "yes", "SCP.2": "no", "ISO.SCP.4": "yes_office"})
    db.commit()

    complete = http.get(f"/assessments/{assessment.id}?tab=scope")
    assert complete.status_code == 200
    assert "Scope confirmed" in complete.text
    assert f'href="/assessments/{assessment.id}?tab=scope&amp;edit=1"' in complete.text
    assert "Significant data fiduciary obligations" in complete.text
    assert "data-rfi-link" in complete.text

    edit = http.get(f"/assessments/{assessment.id}?tab=scope&edit=1")
    assert edit.status_code == 200
    assert "Scope confirmed" not in edit.text
    assert 'name="SCP.1" value="yes" checked' in edit.text
    assert 'name="SCP.2" value="no" checked' in edit.text
    assert 'name="ISO.SCP.4" value="yes_office" checked' in edit.text
    assert f'<a class="btn ghost" href="/assessments/{assessment.id}?tab=scope">Cancel</a>' in edit.text
    assert 'data-scope-group="SCP.1"' in edit.text


def test_scope_form_missing_answers_preview_marks_each_unanswered_question(db, http):
    _client, _engagement, assessment = seed_engagement(
        db,
        client_name="Meridian Ledger Technologies",
        name="FY2026 privacy readiness",
        frameworks=("iso27001",),
    )
    db.commit()

    page = http.get(f"/assessments/{assessment.id}?tab=scope&state=error")
    assert page.status_code == 200
    assert "Answer 4 more questions" in page.text
    assert page.text.count("Choose an answer.") == 4
    assert "Cancel" not in page.text
