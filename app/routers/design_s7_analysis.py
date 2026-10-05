"""S7 analysis-group design previews."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

from fastapi import HTTPException, Request
from fastapi.responses import Response
from starlette.templating import _TemplateResponse

from app.database import SessionLocal
from app.models.assessment import Assessment
from app.models.engagement import Engagement
from app.models.report import GapItem
from app.routers.design import PREVIEW_PAGES
from app.routers.web import templates

SHELL = """
{% extends "base.html" %}
{% from "components/layout.html" import assessment_tabs %}
{% from "components/ui.html" import icon %}
{% block title %}{{ heading }}{% endblock %}
{% block crumbs %}<a class="hide-sm" href="/">{{ assessment.company_name }}</a>{{ icon("slash") }}{% if engagement %}<a class="hide-sm" href="/engagements/{{ engagement.id }}">{{ engagement.name }}</a>{{ icon("slash") }}{% endif %}<a href="/assessments/{{ assessment.id }}">{{ assessment.display_name }}</a>{% for label, href in trail %}{{ icon("slash") }}{% if href %}<a href="{{ href }}">{{ label }}</a>{% else %}<b>{{ label }}</b>{% endif %}{% endfor %}{% endblock %}
{% macro specimen_head() %}<div style="display:flex;align-items:center;gap:var(--s-2);flex-wrap:wrap;margin-bottom:var(--s-4)"><span class="chip">State</span><h2>{{ specimen }}</h2></div>{% endmacro %}
{% macro page_head(first=False) %}<div class="page-head"{% if first %} style="margin-top:0"{% endif %}><div><h1>{{ heading }}</h1><p class="meta-line">{{ meta_line }}</p></div><div class="acts"></div></div>{{ assessment_tabs(assessment, tab) }}{% endmacro %}
{% block content %}{% if head_inside %}<section style="margin-top:var(--s-12)">{{ specimen_head() }}{{ page_head(True) }}{% else %}{{ page_head() }}<section style="margin-top:var(--s-12)">{{ specimen_head() }}{% endif %}{% if layout == "analysis" %}<div class="glass card"><div id="analysis-area">{% include partial %}</div></div>{% elif layout == "finding" %}{% include partial %}{% else %}{% include partial %}{% endif %}{% if toast %}<div style="margin-top:var(--s-4)"><div class="toast">{{ icon("check") }}<span>{{ toast }}</span></div></div>{% endif %}</section>{% endblock %}
"""

STATE_HEADS = {
    "b5-analysis": {"running": "Running", "complete": "Complete", "error": "Failed for one framework", "error-all": "Failed with no detail", "gate": "Blocked by an incomplete questionnaire", "gate-no-override": "Blocked, no override offered"},
    "b5-release": {"blocked": "Not ready", "ready": "Ready", "confirm": "Confirming the release", "released": "Released", "stale": "Out of date after release"},
    "b5-basis": {"empty": "Not recorded", "filled": "Recorded", "invalid": "Invalid dates", "locked": "Locked", "saved": "Saved"},
    "b5-review-finding-card": {"draft": "Draft", "needs-review": "Flagged for review, no quote", "notes": "Adding notes", "accepted": "Accepted", "rejected": "Rejected with notes"},
}


def _meta_line(basis) -> str:
    from app.template_config import display_date
    if not basis.period_recorded:
        return "Period not set · Evidence cut-off not set"
    return f"{display_date(basis.period_start)} – {display_date(basis.period_end)} · Evidence cut-off {display_date(basis.evidence_cutoff)}"


def _page(request: Request, screen: str) -> Response:
    state = request.query_params.get("state", "")
    if state not in STATE_HEADS[screen]:
        raise HTTPException(404, "Not found")
    with SessionLocal() as db:
        assessment_id = request.query_params.get("assessment_id")
        assessment = db.get(Assessment, assessment_id) if assessment_id else db.query(Assessment).first()
        if assessment is None:
            raise HTTPException(404, "Not found")
        engagement = db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None
        return _render(request, db, screen, state, assessment, engagement)


def _render(request, db, screen, state, assessment, engagement) -> Response:
    from app.routers import web
    from app.routers.analysis import COMPLETION_OVERRIDE_REASONS
    from app.services import approved_report, report_basis

    basis = report_basis.current_basis(db, assessment)
    context = {"request": request, "assessment": assessment, "engagement": engagement, "specimen": STATE_HEADS[screen][state], "layout": "plain", "head_inside": False, "toast": "", "meta_line": _meta_line(basis), "assessment_id": assessment.id}
    context["trail"] = [("Review", f"/assessments/{assessment.id}/review-queue")]

    if screen == "b5-analysis":
        context.update({"heading": "Review", "tab": "review", "partial": f"partials/analysis_{'gate_blocked' if state.startswith('gate') else state}.html", "layout": "analysis"})
        if state == "running":
            context.update(document_count=14, response_count=212)
        elif state.startswith("gate"):
            context.update(message=("The questionnaire has 24 required questions without an answer. Answer them, or run the analysis with an override." if state == "gate" else "No evidence has been uploaded and the questionnaire is empty. Add documents or answer the questionnaire first."), show_override=state == "gate", override_reasons=COMPLETION_OVERRIDE_REASONS if state == "gate" else {})
        else:
            response = web.analysis_status(request, assessment.id, db=db)
            context.update(response.context)
            context["partial"] = f"partials/analysis_{state}.html"
            if state == "error":
                context["framework_display"] = context.get("framework_display", {})
    elif screen == "b5-release":
        context.update({"heading": "Release", "tab": "report", "partial": "partials/release_panel.html", "trail": [("Report", f"/assessments/{assessment.id}?tab=report"), ("Release", "")]})
        context["release"] = approved_report.release_state(db, assessment)
        context["release_confirm"] = state == "confirm"
        if state == "blocked":
            context["release"] = SimpleNamespace(released=False, stale=False, blockers=("3 in-scope conclusions are not approved", "The assessment period is not recorded"))
        context["counts"] = SimpleNamespace(approved=6)
        if state == "released": context["toast"] = "Report released"
    elif screen == "b5-basis":
        shown = basis
        errors = {}
        if state == "empty":
            shown = report_basis.EMPTY_BASIS
        elif state == "invalid":
            errors = {"period_end": "The period end must be after the period start."}
            shown = replace(basis, period_end=basis.period_start - timedelta(days=1))
        context.update({"heading": "Period and sign-off", "tab": "report", "partial": "partials/report_basis_panel.html", "report_basis": shown, "period_locked": report_basis.period_locked(db, assessment), "field_errors": errors, "head_inside": True, "trail": [("Report", f"/assessments/{assessment.id}?tab=report"), ("Period and sign-off", "")]})
        if state == "empty": context["meta_line"] = _meta_line(shown)
        if state == "saved": context["toast"] = "Period and sign-off saved"
    else:
        context.update({"heading": "Finding review", "tab": "review", "partial": "partials/review_finding_card.html", "layout": "finding", "trail": [("Review", f"/assessments/{assessment.id}/review-queue"), ("Findings", ""), ("Finding review", "")]})
        context["item"] = db.query(GapItem).order_by(GapItem.id).first()
        context["notes_open"] = state == "notes"

    template = templates.env.from_string(SHELL)
    return _TemplateResponse(template, context)


for _screen in STATE_HEADS:
    PREVIEW_PAGES[_screen] = lambda request, screen=_screen: _page(request, screen)
