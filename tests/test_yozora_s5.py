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


def test_assessment_overview_has_six_tabs_and_real_stepper(db, http):
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
        "Evidence",
        "Questionnaire",
        "Review",
        "Report",
    ]
    assert "Documents" not in nav
    assert page.text.count('class="stp') == 5
    assert all(label in page.text for label in ("Scope", "Evidence", "Questionnaire", "Review", "Report"))
    assert f'href="/assessments/{assessment.id}?tab=overview&amp;framework=dpdpa"' in page.text
    assert f'href="/assessments/{assessment.id}?tab=documents"' in page.text
    assert "data-retention-section" not in page.text
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
    assert "data-retention-section" not in page.text
    assert "Client evidence links" not in page.text
    assert f"/engagements/{engagement.id}/aws-evidence" not in page.text
    requests_page = http.get(f"/engagements/{engagement.id}/requests")
    assert requests_page.status_code == 200 and "Request something else" in requests_page.text


def test_documents_url_redirects_to_evidence_without_documents_tab(db, http):
    # S5 kept the old documents view rendering; S6 turns ?tab=documents into a 303 to the inventory.
    _client, engagement, assessment = seed_engagement(db)

    redirect = http.get(f"/assessments/{assessment.id}?tab=documents", follow_redirects=False)

    assert redirect.status_code == 303
    assert redirect.headers["location"] == f"/assessments/{assessment.id}/evidence"
    page = http.get(f"/assessments/{assessment.id}?tab=overview")
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
    assert "Analysing 6 documents against DPDPA and ISO 27001" in desk_review.text
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


def test_incomplete_scope_form_is_rerendered_with_each_unanswered_question(db, http):
    _client, _engagement, assessment = seed_engagement(
        db,
        client_name="Meridian Ledger Technologies",
        name="FY2026 privacy readiness",
        frameworks=("iso27001",),
    )
    db.commit()

    page = http.post(
        f"/assessments/{assessment.id}/scope/save",
        data={"scope_form": "1", "ISO.SCP.4": "fully_remote"},
        follow_redirects=False,
    )
    assert page.status_code == 400
    assert "Answer 3 more questions" in page.text
    assert page.text.count("Choose an answer.") == 3
    assert 'name="ISO.SCP.4" value="fully_remote" checked' in page.text
    assert "Cancel" not in page.text
    db.refresh(assessment)
    assert assessment.scope_answers is None

    complete = {"scope_form": "1", "ISO.SCP.1": "specific_services", "ISO.SCP.2": "no", "ISO.SCP.3": "no", "ISO.SCP.4": "fully_remote"}
    saved = http.post(f"/assessments/{assessment.id}/scope/save", data=complete, follow_redirects=False)
    assert saved.status_code == 303
    db.refresh(assessment)
    assert json.loads(assessment.scope_answers) == {key: value for key, value in complete.items() if key != "scope_form"}


def test_live_assessment_routes_ignore_mockup_state_query(db, http):
    _client, _engagement, assessment = seed_engagement(db, frameworks=("iso27001",))
    db.commit()

    scope = http.get(f"/assessments/{assessment.id}?tab=scope&state=error")
    assert "Choose an answer." not in scope.text
    saving = http.get(f"/assessments/{assessment.id}?tab=scope&state=saving")
    assert 'aria-label="Saving scope"' not in saving.text
    assert "Save scope and prepare evidence request" in saving.text
    redirect = http.get(f"/assessments/{assessment.id}/scope?state=saving", follow_redirects=False)
    assert "state=" not in redirect.headers["location"]

    assessment.scope_answers = "{}"
    db.commit()
    overview = http.get(f"/assessments/{assessment.id}?tab=overview&state=loading")
    assert 'aria-label="Loading framework"' not in overview.text
    error = http.get(f"/assessments/{assessment.id}?tab=overview&state=error")
    assert "This framework did not load" not in error.text


def test_transient_states_render_through_design_previews_only(db, http):
    _client, _engagement, assessment = seed_engagement(db, frameworks=("iso27001",))
    db.commit()

    scope_error = http.get(f"/design/pages/b3-scope?state=error&assessment_id={assessment.id}")
    assert scope_error.status_code == 200
    assert "Answer 4 more questions" in scope_error.text
    assert scope_error.text.count("Choose an answer.") == 4
    assert 'data-assessment-identity' in scope_error.text
    saving = http.get(f"/design/pages/b3-scope?state=saving&assessment_id={assessment.id}")
    assert 'aria-label="Saving scope"' in saving.text

    assessment.scope_answers = "{}"
    db.commit()
    loading = http.get(f"/design/pages/b3-hub?state=loading&assessment_id={assessment.id}")
    assert 'aria-label="Loading framework"' in loading.text
    hub_error = http.get(f"/design/pages/b3-hub?state=error&assessment_id={assessment.id}")
    assert "This framework did not load" in hub_error.text
    checklist = http.get(f"/design/pages/b3-scope-complete?state=error&assessment_id={assessment.id}")
    assert "Scope confirmed" in checklist.text

    assert http.get(f"/design/pages/b3-hub?state=archived&assessment_id={assessment.id}").status_code == 404
    assert http.get("/design/pages/b3-hub?state=loading").status_code == 404


def test_framework_tab_swap_keeps_the_overview_hub_state(db, http):
    _client, _engagement, assessment = seed_engagement(db, frameworks=("dpdpa", "iso27001"))
    db.commit()

    empty = http.get(f"/assessments/{assessment.id}/tab/iso27001", headers={"HX-Request": "true"})
    assert empty.status_code == 200
    assert "No scores yet" in empty.text
    assert "Set the scope to choose which requirements apply." in empty.text

    assessment.scope_answers = "{}"
    db.commit()
    evidence = http.get(f"/assessments/{assessment.id}/tab/iso27001", headers={"HX-Request": "true"})
    assert "No scores yet" in evidence.text
    assert "Scores appear once the analysis has run" in evidence.text

    assessment.status = "error"
    db.commit()
    failed = http.get(f"/assessments/{assessment.id}/tab/dpdpa", headers={"HX-Request": "true"})
    assert "Analysis failed" in failed.text

    assert http.get(f"/assessments/{assessment.id}/tab/gdpr").status_code == 404


def test_hub_state_keys_on_stage_constants_and_never_shows_the_skeleton():
    from types import SimpleNamespace

    from app.routers.web import _assessment_hub_state
    from app.services import assessment_stage as st

    def hub(stage, note, next_label=None, status="created"):
        return _assessment_hub_state(
            st.Stage(stage, st.STAGE_LABELS[stage], note, next_label, "/x" if next_label else None),
            SimpleNamespace(status=status),
        )

    assert hub("scope", "anything", st.SET_SCOPE) == "empty"
    assert hub("evidence", "No documents yet", st.UPLOAD_EVIDENCE) == "evidence"
    assert hub("evidence", "5 documents ready to pre-fill", st.PREFILL) == "questionnaire"
    assert hub("evidence", "Pre-fill running") == "questionnaire"
    assert hub("evidence", "renamed note") == "questionnaire"
    assert hub("questionnaire", "10 of 45 answered", st.CONTINUE_QUESTIONNAIRE) == "questionnaire"
    assert hub("questionnaire", "45 of 45 answered", st.RUN_ANALYSIS) == "questionnaire"
    assert hub("questionnaire", "Analysis running") == "questionnaire"
    assert hub("review", "3 of 6 approved", st.review_label(3)) == "default"
    assert hub("report", "6 of 6 approved", st.RELEASE_REPORT) == "report"
    assert hub("report", "Released", st.GENERATE_BOARD_REPORT) == "report"
    assert hub("review", "x", status="error") == "analysis_error"
    assert hub("review", "x", status="archived") == "archived"


def test_scope_stepper_step_has_no_note(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    page = http.get(f"/assessments/{assessment.id}?tab=overview")
    assert page.status_code == 200
    assert "Scope not set" not in page.text


def test_questionnaire_prefill_buttons_step_down_until_context_is_done(db, http):
    _client, _engagement, assessment = seed_engagement(db)
    db.add(DeskReviewSummary(assessment_id=assessment.id, status="error", error_message="Timed out."))
    db.commit()

    before = http.get(f"/assessments/{assessment.id}/desk-review-status?surface=questionnaire")
    assert re.search(r'class="btn secondary lead"[^>]*\n?[^>]*hx-post="[^"]*run-desk-review', before.text)
    assert "btn primary" not in before.text

    assessment.context_answers = "[]"
    db.commit()
    after = http.get(f"/assessments/{assessment.id}/desk-review-status?surface=questionnaire")
    assert "btn primary lead" in after.text


def test_questionnaire_summary_keeps_the_partial_failure_alert(db, http):
    _client, _engagement, assessment = seed_engagement(db, frameworks=("dpdpa", "iso27001"))
    _seed_completed_desk_review(db, assessment)
    summary = db.query(DeskReviewSummary).filter_by(assessment_id=assessment.id).one()
    summary.raw_ai_response = json.dumps({
        "schema_version": 2,
        "frameworks": {"dpdpa": {"status": "completed"}, "iso27001": {"status": "error"}},
    })
    db.commit()

    card = http.get(f"/assessments/{assessment.id}/desk-review-status?surface=questionnaire")
    assert "data-desk-review-failed-frameworks" in card.text
    assert "Desk review failed for ISO 27001" in card.text
    assert "Findings for DPDPA were saved" in card.text
