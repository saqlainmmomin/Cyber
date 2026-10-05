"""S7 cards previews: deterministic states for the three owned card components."""

from types import SimpleNamespace
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.routers.design import PREVIEW_PAGES
from app.routers.web import templates

router = APIRouter(tags=["design"])

SCREEN_STATES = {
    "b5-requirement-card": ("v2", "v2-draft", "contradiction", "v1", "none"),
    "b5-conclusion-card": ("pending", "edit", "approved", "edited", "rejected", "blocked", "no-citation", "superseded", "locked", "conflict", "bulk"),
    "b5-recommended-action": ("empty", "drafting", "drafted", "edited", "error", "saved", "gaps-required", "limit", "stale", "not-open", "not-draftable"),
}

_SHELL = templates.env.from_string(
    """{% extends 'base.html' %}
{% from 'components/seg_rows.html' import review_seg %}
{% block title %}{{ heading }}{% endblock %}
{% block crumbs %}<a href='/'>Assessments</a><b>{{ assessment.company_name }}</b>{% endblock %}
{% block page_head %}<section class='page-head'><div><p class='eyebrow'>{{ eyebrow }}</p><h1>{{ heading }}</h1><p>{{ assessment.company_name }} · FY2026 privacy readiness</p></div></section>{% endblock %}
{% block content %}<div class='desk-review-tabs'>{{ review_seg(assessment, 'conclusions') if show_seg else '' }}</div><div class='preview-card'>{% if screen == 'b5-requirement-card' %}{% include 'components/requirement_card_body.html' %}{% elif screen == 'b5-conclusion-card' %}{% include 'components/conclusion_card.html' %}{% else %}<form>{% include 'partials/remediation_draft.html' %}</form>{% endif %}</div>{% endblock %}"""
)


def _assessment():
    return SimpleNamespace(id="assessment-s7", company_name="Meridian Ledger Technologies", frameworks=["dpdpa", "iso27001"])


def _requirement(state: str):
    if state == "none":
        return SimpleNamespace(source="none", criteria_source="none")
    criterion = SimpleNamespace(
        criterion_id="ISO.A5.18.1",
        result="not_met" if state == "contradiction" else "met",
        symbol="✗" if state == "contradiction" else "✓",
        statement="Access rights are reviewed at defined intervals.",
        claim_ids=["F1"],
        met_without_claim=False,
    )
    claim = SimpleNamespace(claim_id="F1", statement="Access reviews are completed quarterly.", quote="Access review register, Q3 2026", filename="access-register.pdf", kind="design", href="#claim-F1", status="verified")
    return SimpleNamespace(
        source="v1" if state == "v1" else "v2",
        criteria_source="v1" if state == "v1" else ("draft" if state == "v2-draft" else "approved"),
        criteria_label="Control description" if state == "v1" else "Judged against approved test criteria",
        proposed_outcome="non_compliant" if state == "contradiction" else "partially_compliant",
        reason="The access review process is documented, but the latest register is incomplete.",
        criteria=[criterion],
        claims=[claim],
        response=SimpleNamespace(answer_label="Partially implemented", source_label="Entered in the questionnaire"),
        contradictions=[SimpleNamespace(claim_id="F1", note="The evidence shows the latest review was not completed.")] if state == "contradiction" else [],
        unsupported_assertion=False,
        quality=[SimpleNamespace(key="freshness", label="Recent", tone="ok")],
        missing_evidence=[],
        missing_evidence_label="",
        missing_evidence_rfi_note="Approved insufficient-evidence conclusions are added to the next RFI version.",
        other_rfi_requests=[],
        divergence=None,
        analysis_run_id="run-s7-preview",
        no_response_label="No confirmed questionnaire response.",
        no_claims_label="No verified claim addresses this requirement.",
        unsupported_assertion_label="Unsupported assertion",
    )


def _conclusion(state: str):
    outcome = "non_compliant" if state in {"blocked", "no-citation", "conflict"} else "partially_compliant"
    conclusion = SimpleNamespace(id="conclusion-s7", framework_id="iso27001", requirement_id="A.5.18", version=3, outcome=outcome, risk_level="high", rationale="Access rights are not reviewed consistently.", gaps_identified="The latest access review register is incomplete.", recommended_action="Complete and evidence the quarterly access review.", evidence_summary="Access review register, Q3 2026", ai_proposed=True)
    citations = [SimpleNamespace(excerpt="Access review register, Q3 2026", filename="access-register.pdf", resolved=True, evidence_id="evidence-s7", version_number=2, location_ref="page 4", is_current=state != "superseded")]
    if state in {"no-citation", "blocked"}:
        citations = []
    allowed = {
        "pending": ["approved", "edited", "rejected"], "edit": ["approved", "edited", "rejected"], "approved": ["reopened"],
        "edited": ["reopened"], "rejected": ["approved", "edited"], "blocked": ["edited"], "no-citation": ["approved", "edited"],
        "superseded": ["approved", "edited"], "locked": ["reopened"], "conflict": ["approved", "edited"], "bulk": ["reopened"],
    }[state]
    return SimpleNamespace(
        conclusion=conclusion, requirement_title="Access rights", state="approved" if state in {"approved", "edited", "locked", "bulk"} else state,
        allowed_actions=allowed, approval_blocker="Evidence support not captured (legacy)" if state == "blocked" else None,
        citations_captured=state != "blocked", citations=citations, unsupported_assertion=state == "no-citation",
        last_decision=None, legacy_bulk_approval=state == "bulk", locked=state == "locked", withheld_proposal=SimpleNamespace(rationale="A newer proposal is waiting for review.") if state == "locked" else None,
        legacy_report_status=None, previous_outcome=None, requirement=_requirement("contradiction" if state == "conflict" else "v2"),
    )


def _render(request: Request, screen: str, state: str) -> HTMLResponse:
    assessment = _assessment()
    context = {
        "request": request, "assessment": assessment, "screen": screen, "state": state,
        "heading": "Requirement detail" if screen == "b5-requirement-card" else "Conclusion detail",
        "eyebrow": "Review", "show_seg": screen == "b5-recommended-action",
        "nav_items": [], "review_count": 0, "firm_accent": "midnight", "accent_custom_hex": None, "accent_dark_hex": None, "accent_on_accent": "#ffffff",
        "branding": SimpleNamespace(firm_name="CyberAssess", has_custom_nav_color=False, firm_primary_hex=None),
        "card": _conclusion(state) if screen == "b5-conclusion-card" else SimpleNamespace(requirement=_requirement(state)),
        "assessment_id": assessment.id, "conclusion_id": "conclusion-s7", "recommended_action": "", "draft": None, "error": None,
        "draft_notice": "AI draft: review and edit it before saving. Nothing is saved until you choose Save and approve.",
        "drafting": state == "drafting", "preview_state": state,
    }
    if screen == "b5-recommended-action":
        if state in {"drafted", "edited"}:
            context["draft"] = SimpleNamespace(event_id="draft-s7", suggested_owner_role="IT security manager")
            context["recommended_action"] = "Complete and evidence the quarterly access review."
        if state == "error":
            context["error"] = "The AI draft could not be produced. Write the recommended action yourself."
        if state in {"gaps-required", "limit", "stale", "not-open", "not-draftable"}:
            messages = {"gaps-required": "Describe the identified gaps first; the draft is written from them.", "limit": "The AI draft limit for this conclusion has been reached. Write the recommended action yourself.", "stale": "This conclusion changed since you loaded the page. Reload before drafting. Nothing was saved.", "not-open": "AI drafting is only available while the conclusion is awaiting a decision.", "not-draftable": "AI drafting is only available for partially compliant or non-compliant outcomes."}
            response = HTMLResponse(_SHELL.render(**context)); response.headers["X-Toast-Type"] = "error"; response.headers["X-Toast-Message"] = quote(messages[state]); return response
    return HTMLResponse(_SHELL.render(**context))


for _screen in SCREEN_STATES:
    PREVIEW_PAGES[_screen] = lambda request, _screen=_screen: _render(request, _screen, request.query_params.get("state", SCREEN_STATES[_screen][0]))
