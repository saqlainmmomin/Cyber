"""S7 narrative and board-input preview pages backed by seeded assessments."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from fastapi import HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.routers import board_inputs as board_inputs_router
from app.routers import drafting
from app.services import approved_report, board_inputs, findings as finding_service, narrative, remediation_groups, report_content
from app.routers.design import DB_PREVIEWS, PREVIEW_PAGES


NARRATIVE_STATES = ("empty", "generating", "drafted", "partly-accepted", "accepted", "error", "not-released")
BOARD_INPUT_STATES = ("empty", "partly", "complete", "dense", "error")


def _live_request(request: Request, path: str) -> Request:
    return Request(dict(request.scope, path=path, raw_path=path.encode()), request.receive)


def _assessment(request: Request, db: Session) -> Assessment:
    assessment_id = request.query_params.get("assessment_id")
    if not assessment_id:
        raise HTTPException(status_code=404, detail="An assessment id is required")
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


def _narrative_sections(db: Session, assessment: Assessment) -> tuple[object, list[dict]]:
    current_state = narrative.state(db, assessment)
    ref_by_id = {ref.finding_id: ref.alias for ref in current_state.findings}
    sections = []
    for section in current_state.sections:
        lines = []
        for sentence in section.sentences:
            aliases = [
                ref_by_id[finding_id]
                for finding_id in sentence.get("finding_ids", [])
                if finding_id in ref_by_id
            ]
            lines.append(f"{sentence.get('text', '')} [{', '.join(aliases)}]")
        sections.append({"section": section, "text": "\n".join(lines)})
    return current_state, sections


def _narrative_preview(request: Request, db: Session) -> Response:
    state = request.query_params.get("state", "empty")
    if state not in NARRATIVE_STATES:
        raise HTTPException(status_code=404, detail="Unknown narrative state")
    assessment = _assessment(request, db)
    current_state, sections = _narrative_sections(db, assessment)
    context = {
        "request": _live_request(request, f"/assessments/{assessment.id}/narrative"),
        "assessment": assessment,
        "state": current_state,
        "sections": sections,
        "released": approved_report.is_released(db, assessment),
        "blockers": narrative.report_blockers(db, assessment),
        "reviewer_name": "",
        "generating": state == "generating",
    }
    return drafting._templates.TemplateResponse("pages/narrative.html", context)


def _board_context(request: Request, db: Session, assessment: Assessment) -> dict:
    page = finding_service.findings_page(db, assessment.id)
    findings = report_content.assessment_findings(db, assessment).findings
    groups = remediation_groups.build_groups(findings, assessment.frameworks)
    return {
        "request": _live_request(request, f"/assessments/{assessment.id}/board-inputs"),
        "assessment": assessment,
        "page": page,
        "groups": groups,
        "initiative_data": board_inputs.initiative_metadata(db, assessment.id),
        "asks": board_inputs.board_asks(assessment),
        "reviewer_name": board_inputs_router._latest_reviewer_name(db, assessment.id),
        "responsibilities": board_inputs.RESPONSIBILITIES,
        "levels": board_inputs.LEVELS,
    }


def _board_preview(request: Request, db: Session) -> Response:
    state = request.query_params.get("state", "empty")
    if state not in BOARD_INPUT_STATES:
        raise HTTPException(status_code=404, detail="Unknown board-input state")
    assessment = _assessment(request, db)
    context = _board_context(request, db, assessment)
    if state == "error" and context["page"].findings:
        first = context["page"].findings[0]
        finding = first.finding
        overlong_recommendation = " ".join(
            [finding.recommendation or ""]
            + ["Name an owner for each step, agree the template with legal counsel and run a test notification before the next audit."] * 14
        ).strip()
        context["page"] = SimpleNamespace(
            findings=[
                replace(first, finding=SimpleNamespace(
                    id=finding.id,
                    title=finding.title,
                    description=finding.description,
                    business_impact=finding.business_impact,
                    recommendation=overlong_recommendation,
                )),
                *context["page"].findings[1:],
            ],
            eligible=context["page"].eligible,
        )
        context["field_errors"] = {
            f"{finding.id}:recommendation": "Recommendation must be 1500 characters or fewer.",
        }
        if context["groups"]:
            group_id = context["groups"][0]["group_id"]
            context["field_errors"][f"{group_id}:title"] = "Initiative title must be 120 characters or fewer."
        context["initiative_data"] = dict(context["initiative_data"])
        if context["groups"]:
            context["initiative_data"].setdefault(context["groups"][0]["group_id"], {})[
                "title"
            ] = "Strengthen incident response, notification routes and runbooks across every business unit and supplier"
    return board_inputs_router._templates.TemplateResponse("pages/board_inputs.html", context)


PREVIEW_PAGES["b5-narrative"] = _narrative_preview
PREVIEW_PAGES["b5-board-inputs"] = _board_preview
DB_PREVIEWS.update({"b5-narrative", "b5-board-inputs"})
