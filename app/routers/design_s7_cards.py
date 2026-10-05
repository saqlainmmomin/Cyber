"""S7 cards previews: deterministic states for the three owned card components.

The card data is a fixture shaped like ``conclusion_review.ConclusionCard`` and
``requirement_card.RequirementCard`` (the mockup's Meridian Ledger access-review
example). The shell around it (side menu, breadcrumb, period line, tabs) comes from
the seeded assessment named by ``?assessment_id=``, rendered as if at the live
conclusions URL so it uses the same context processors as the real pages.
"""

from datetime import datetime
from types import SimpleNamespace
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.routers.design import PREVIEW_PAGES
from app.routers.web import templates
from app.services.report_basis import PERIOD_REQUIRED_MESSAGE

router = APIRouter(tags=["design"])

SCREEN_STATES = {
    "b5-requirement-card": ("v2", "v2-draft", "contradiction", "v1", "none"),
    "b5-conclusion-card": ("pending", "edit", "approved", "edited", "rejected", "blocked", "no-citation", "superseded", "locked", "conflict", "bulk"),
    "b5-recommended-action": ("empty", "drafting", "drafted", "edited", "error", "saved", "gaps-required", "limit", "stale", "not-open", "not-draftable"),
}

STATE_HEADS = {
    "b5-requirement-card": {"v2": "Full analysis, RFI request available", "v2-draft": "Request already on the draft RFI, divergence acknowledged", "contradiction": "Contradiction and shared evidence", "v1": "Earlier analysis pipeline", "none": "No analysis run linked"},
    "b5-conclusion-card": {"pending": "Pending", "edit": "Editing before approval", "approved": "Approved", "edited": "Edited and approved", "rejected": "Rejected", "blocked": "Approval blocked", "no-citation": "No supporting citation", "superseded": "Citation from a superseded version", "locked": "Locked, newer proposal withheld", "conflict": "Changed by someone else", "bulk": "Approved in bulk"},
    "b5-recommended-action": {"empty": "Empty, draft button available", "drafting": "Drafting", "drafted": "Draft present, editable", "edited": "Draft edited by hand", "error": "Draft could not be produced", "saved": "Saved after approval", "gaps-required": "Gaps not described yet", "limit": "Draft limit reached", "stale": "Conclusion changed since the page loaded", "not-open": "Conclusion not awaiting a decision", "not-draftable": "Outcome not draftable"},
}

_SHELL = templates.env.from_string(
    """{% extends "base.html" %}
{% from "components/layout.html" import assessment_tabs %}
{% from "components/seg_rows.html" import review_seg %}
{% block title %}{{ heading }}{% endblock %}
{% block crumbs %}<a class="hide-sm" href="/">{{ assessment.company_name }}</a><svg class="i sl hide-sm"><use href="#i-slash"/></svg>{% if engagement %}<a class="hide-sm" href="/engagements/{{ engagement.id }}">{{ engagement.name }}</a><svg class="i sl hide-sm"><use href="#i-slash"/></svg>{% endif %}<a href="/assessments/{{ assessment.id }}">{{ assessment.display_name }}</a><svg class="i sl"><use href="#i-slash"/></svg><a href="/assessments/{{ assessment.id }}/review-queue">Review</a><svg class="i sl"><use href="#i-slash"/></svg><a href="/assessments/{{ assessment.id }}/conclusions">Conclusions</a><svg class="i sl"><use href="#i-slash"/></svg><b>{{ last_crumb }}</b>{% endblock %}
{% block content %}<div{% if screen != "b5-requirement-card" %} class="review-page"{% endif %}><div class="page-head"><div><h1>{{ heading }}</h1><p class="meta-line">{{ meta_line }}</p></div><div class="acts"></div></div>{{ assessment_tabs(assessment, "review") }}{% if show_seg %}<div class="cc-seg">{{ review_seg(assessment, "conclusions") }}</div>{% endif %}<section class="cc-specimen"><div class="cc-specimen-head"><span class="chip">State</span><h2>{{ specimen }}</h2></div>{% if toast_message %}<div class="stack-start cc-toast-row"><div class="toast bad" role="alert"><svg class="i lead-i"><use href="#i-alert"/></svg><span class="grow">{{ toast_message }}</span></div></div>{% endif %}{% if screen == "b5-requirement-card" %}<div class="solid cc-req-solid">{% include "components/requirement_card_body.html" %}</div><div class="hrow cc-back"><a class="btn secondary" href="/assessments/{{ assessment.id }}/conclusions">Back to conclusion</a></div>{% else %}{% include "components/conclusion_card.html" %}{% endif %}</section></div>{% endblock %}"""
)

_MOMENT = datetime(2026, 9, 24, 14, 32)
_RATIONALE = "Quarterly access reviews skipped three production systems, so access to the payments ledger, card vault and data warehouse is not checked."
_GAPS = "Three production systems were not part of the Q1 access review."
_ACTION = "Extend the quarterly access review to every production system."
_DRAFT = "Extend the quarterly access review to every production system, including the payments ledger, card vault and data warehouse. Record the reviewer and date for each system, and keep the sign-off sheet with the review."


def _assessment(request: Request, db):
    """The seeded assessment and engagement for the shell, or a stand-in when none exists."""
    from app.models.assessment import Assessment
    from app.models.engagement import Engagement
    from app.services import report_basis

    assessment_id = request.query_params.get("assessment_id")
    assessment = db.get(Assessment, assessment_id) if assessment_id else None
    if assessment is not None:
        engagement = db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None
        return assessment, engagement, report_basis.current_basis(db, assessment)
    stand_in = SimpleNamespace(id="assessment-s7", company_name="Meridian Ledger Technologies", display_name="Head office", frameworks=["dpdpa", "iso27001"], engagement_id=None)
    return stand_in, None, None


def _meta_line(basis) -> str:
    from app.template_config import display_date

    if basis is None or not basis.period_recorded:
        return "Period not set · Evidence cut-off not set"
    return f"{display_date(basis.period_start)} – {display_date(basis.period_end)} · Evidence cut-off {display_date(basis.evidence_cutoff)}"


def _requirement(state: str):
    if state == "none":
        return SimpleNamespace(source="none", criteria_source="none")
    if state == "v1":
        return SimpleNamespace(
            source="v1", criteria_source="v1", proposed_outcome="non_compliant", reason=None,
            criteria_label="Proposed by the v1 analysis: no criteria checklist or verified claims are available for this requirement.",
            criteria=(), claims=(), response=None, contradictions=(), unsupported_assertion=False,
            quality=(), missing_evidence=(), missing_evidence_label=None, other_rfi_requests=(), divergence=None,
        )
    claims = (
        SimpleNamespace(claim_id="F1", statement="Reviews covered 11 of 14 production systems. The payments ledger, card vault and data warehouse were not reviewed.", quote="Reviews covered 11 of 14 production systems. The payments ledger, card vault and data warehouse were not reviewed.", kind="operating", filename="access_review_q1.docx", href="#claim-F1"),
    )
    criteria = (
        SimpleNamespace(criterion_id="ISO.A5.18.TC1", statement="A documented access review procedure exists", result="met", symbol="✓", claim_ids=("F1",), met_without_claim=False),
        SimpleNamespace(criterion_id="ISO.A5.18.TC2", statement="Reviews cover all production systems", result="not_met", symbol="✗", claim_ids=("F1",), met_without_claim=False),
        SimpleNamespace(criterion_id="ISO.A5.18.TC3", statement="Reviews are completed quarterly", result="met", symbol="✓", claim_ids=("F1",), met_without_claim=False),
        SimpleNamespace(criterion_id="ISO.A5.18.TC4", statement="Reviewers are independent of system owners", result="no_evidence", symbol="?", claim_ids=(), met_without_claim=True),
    )
    drafted = state in {"v2-draft", "contradiction"}
    missing = (
        SimpleNamespace(
            document_type="access_review_signoff", label="Access review sign-off sheet", what_it_would_show="Would show who reviewed each system and when.",
            request_key="rfi-access-signoff", request_text="Please send the signed access review sheet for each production system for the period 1 Apr 2025 to 31 Mar 2026.",
            rfi_state="drafted" if drafted else "available", rfi_status_label="On the draft RFI, version 2" if drafted else "",
        ),
    )
    other = (
        SimpleNamespace(state="drafted", status_label="On the draft RFI, version 2", request=SimpleNamespace(request_key="rfi-privileged-list", title="Privileged access list", request="Please send the list of privileged accounts and their owners.")),
    )
    divergence = None
    if state in {"v2", "v2-draft"}:
        divergence = SimpleNamespace(
            cluster_id="CLUSTER_006", analysis_run_id="run-s7-preview",
            sentence="ISO 27001 asks for review of every system. DPDPA asks for safeguards in proportion to risk, so a pass under one is not a pass under the other.",
            acknowledged=state == "v2-draft", acknowledged_by="Priya Sharma", acknowledged_at=datetime(2026, 9, 24, 14, 20), note="Kept as non-compliant under both.",
        )
    return SimpleNamespace(
        source="v2", criteria_source="approved", criteria_label=None, analysis_run_id="run-s7-preview",
        proposed_outcome="non_compliant", reason="Three production systems were left out of the Q1 access review, so the requirement to review all systems is not met.",
        criteria=criteria, claims=claims,
        response=SimpleNamespace(answer_label="Yes, every production system is reviewed each quarter.", source_label="Client questionnaire"),
        contradictions=(SimpleNamespace(claim_id="F1", note="The questionnaire says every system is reviewed. The review report lists 11 of 14."),) if state == "contradiction" else (),
        unsupported_assertion=False,
        quality=(SimpleNamespace(key="period:dated", label="Dated within the period", tone="neutral"), SimpleNamespace(key="currency:current", label="Approved copy", tone="neutral"), SimpleNamespace(key="support:needs_review", label="Sample size not recorded", tone="warn")),
        missing_evidence=missing, missing_evidence_label=None, other_rfi_requests=other, divergence=divergence,
    )


def _citation(**overrides):
    values = {"excerpt": "Access reviews were completed for 11 of 14 production systems; the payments ledger, card vault and data warehouse were not reviewed.", "filename": "access_review_q1.docx", "resolved": True, "evidence_id": "evidence-s7", "version_number": 2, "location_ref": "page 2", "is_current": True}
    values.update(overrides)
    return SimpleNamespace(**values)


def _conclusion_card(state: str, *, requirement=True, decided_card=True):
    edited = state == "edited" and requirement
    ungapped = state in {"gaps-required", "stale", "not-open", "not-draftable"}
    conclusion = SimpleNamespace(
        id="conclusion-s7", framework_id="iso27001", requirement_id="A.5.18", version=4 if edited else 3,
        outcome="partially_compliant" if edited else ("compliant" if state == "not-draftable" and not requirement else "non_compliant"), risk_level="medium" if edited else "high",
        rationale="Quarterly access reviews skipped three production systems. A compensating monthly review covers two of them." if edited else _RATIONALE,
        gaps_identified="" if ungapped and not requirement else _GAPS, recommended_action=_DRAFT if state == "saved" else _ACTION, evidence_summary="", ai_proposed=not edited,
    )
    citations = [_citation()]
    if state == "superseded":
        citations.append(_citation(excerpt="Reviews were completed for all production systems.", filename="access_review_q4_2024.docx", location_ref="page 1", is_current=False, version_number=1))
    if state == "no-citation":
        citations = []
    decided = {"approved": "approved", "saved": "approved", "locked": "approved", "bulk": "approved", "edited": "edited", "rejected": "rejected"}.get(state) if decided_card else None
    card_state = decided or "pending"
    allowed = {"approved": ("reopened",), "edited": ("reopened",), "rejected": ("approved", "edited")}.get(card_state, ("approved", "edited", "rejected"))
    last_decision = None
    if decided:
        moment = {"edited": datetime(2026, 9, 24, 14, 40), "rejected": datetime(2026, 9, 24, 14, 45), "bulk": datetime(2026, 9, 2, 9, 0)}.get(state, _MOMENT)
        last_decision = {"action": decided, "actor_display": "Priya Sharma", "created_at": moment}
    return SimpleNamespace(
        conclusion=conclusion, requirement_title="Access rights", state=card_state, locked=state == "locked", allowed_actions=allowed,
        approval_blocker=PERIOD_REQUIRED_MESSAGE if state == "blocked" else None,
        citations_captured=True, citations=citations, unsupported_assertion=state == "no-citation",
        last_decision=last_decision, legacy_bulk_approval=state == "bulk",
        withheld_proposal={"outcome": "compliant", "citation_count": 2} if state == "locked" else None,
        legacy_report_status=None, previous_outcome="non_compliant" if edited else None,
        requirement=_requirement("card") if requirement else None,
    )


def _render(request: Request, screen: str, state: str) -> HTMLResponse:
    from app.database import SessionLocal

    with SessionLocal() as db:
        return _render_with(request, db, screen, state)


def _render_with(request: Request, db, screen: str, state: str) -> HTMLResponse:
    assessment, engagement, basis = _assessment(request, db)
    context = {
        "request": request, "assessment": assessment, "engagement": engagement, "screen": screen, "state": state,
        "heading": "Requirement detail" if screen == "b5-requirement-card" else "Conclusion detail",
        "last_crumb": "Requirement detail" if screen == "b5-requirement-card" else "Access rights",
        "specimen": STATE_HEADS[screen][state], "meta_line": _meta_line(basis),
        "show_seg": screen == "b5-recommended-action",
    }
    if screen == "b5-requirement-card":
        context["card"] = SimpleNamespace(conclusion=SimpleNamespace(id="conclusion-s7"), requirement=_requirement(state))
        context["group_evidence"] = state == "contradiction"
    elif screen == "b5-conclusion-card":
        context["card"] = _conclusion_card(state)
        context["card_editing"] = state == "edit"
        if state == "conflict":
            context["conflict"] = SimpleNamespace(submitted_version=2, diff=[SimpleNamespace(field="outcome", current="non_compliant", submitted="partially_compliant"), SimpleNamespace(field="risk_level", current="high", submitted="medium")])
    else:
        context.update(card=_conclusion_card(state, requirement=False, decided_card=False), edit_focus=True, card_editing=state != "saved", drafting=state == "drafting", recommended_action="")
        if state in {"drafted", "edited"}:
            context["draft"] = SimpleNamespace(event_id="draft-s7", suggested_owner_role="Head of IT")
            context["recommended_action"] = _DRAFT if state == "drafted" else _DRAFT + " Report exceptions to the head of IT each quarter."
            context["draft_notice"] = "AI draft: review and edit it before saving. Nothing is saved until you choose Save and approve." if state == "drafted" else "Edited from the model draft. Nothing is saved until you choose Save and approve."
        if state == "error":
            context["error"] = "The AI draft could not be produced. Write the recommended action yourself."
    # Shell from the live conclusions URL: side menu, review count and firm tile.
    path = f"/assessments/{assessment.id}/conclusions"
    live_request = Request(dict(request.scope, path=path, raw_path=path.encode()), request.receive)
    for processor in templates.context_processors:
        context.update(processor(live_request))
    context["request"] = request
    messages = {}
    if screen == "b5-recommended-action" and state in {"gaps-required", "limit", "stale", "not-open", "not-draftable"}:
        messages = {"gaps-required": "Describe the identified gaps first; the draft is written from them.", "limit": "The AI draft limit for this conclusion has been reached. Write the recommended action yourself.", "stale": "This conclusion changed since you loaded the page. Reload before drafting. Nothing was saved.", "not-open": "AI drafting is only available while the conclusion is awaiting a decision.", "not-draftable": "AI drafting is only available for partially compliant or non-compliant outcomes."}
    context["toast_message"] = messages.get(state)
    response = HTMLResponse(_SHELL.render(**context))
    if context["toast_message"]:
        response.headers["X-Toast-Type"] = "error"
        response.headers["X-Toast-Message"] = quote(messages[state])
    return response


for _screen in SCREEN_STATES:
    PREVIEW_PAGES[_screen] = lambda request, _screen=_screen: _render(request, _screen, request.query_params.get("state", SCREEN_STATES[_screen][0]))
