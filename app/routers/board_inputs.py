"""Consultant board-input capture routes."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.action import Action
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.finding import Finding
from app.models.initiative_metadata import InitiativeMetadata
from app.services import (
    board_inputs,
    conclusion_review,
    findings as finding_service,
    remediation_groups,
    report_content,
)
from app.template_config import configure_templates


router = APIRouter(tags=["board-inputs"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)


def _toast(response, message: str, toast_type: str):
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = toast_type
    return response


def _success(changed: bool) -> JSONResponse:
    message = "Board inputs saved." if changed else board_inputs.NO_CHANGES
    return _toast(
        JSONResponse({"status": "saved", "changed": changed}),
        message,
        "success",
    )


def _error(db: Session, exc: board_inputs.BoardInputError) -> JSONResponse:
    db.rollback()
    return _toast(
        JSONResponse({"detail": exc.message}, status_code=exc.status_code),
        exc.message,
        "error",
    )


def _latest_reviewer_name(db: Session, assessment_id: str) -> str:
    event = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_id == assessment_id,
            AuditEvent.actor.startswith("consultant:"),
            AuditEvent.action.in_(
                (
                    board_inputs.AUDIT_FINDING,
                    board_inputs.AUDIT_ACTION,
                    board_inputs.AUDIT_INITIATIVE,
                    board_inputs.AUDIT_ASKS,
                )
            ),
        )
        .order_by(AuditEvent.created_at.desc())
        .first()
    )
    return event.actor.removeprefix("consultant:") if event else ""


@router.get("/assessments/{assessment_id}/board-inputs", response_class=HTMLResponse)
def board_inputs_page(
    assessment_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        message = board_inputs.ASSESSMENT_NOT_FOUND
        raise HTTPException(
            status_code=404,
            detail=message,
            headers={"X-Toast-Message": quote(message), "X-Toast-Type": "error"},
        )
    page = finding_service.findings_page(db, assessment_id)
    findings = report_content.assessment_findings(db, assessment).findings
    groups = remediation_groups.build_groups(findings, assessment.frameworks)
    return _templates.TemplateResponse(
        request=request,
        name="pages/board_inputs.html",
        context={
            "request": request,
            "assessment": assessment,
            "page": page,
            "groups": groups,
            "initiative_data": board_inputs.initiative_metadata(db, assessment_id),
            "asks": board_inputs.board_asks(assessment),
            "reviewer_name": _latest_reviewer_name(db, assessment_id),
            "responsibilities": board_inputs.RESPONSIBILITIES,
            "levels": board_inputs.LEVELS,
        },
    )


@router.post(
    "/api/assessments/{assessment_id}/board-inputs/observations/{finding_id}"
)
def save_finding_inputs(
    assessment_id: str,
    finding_id: str,
    business_impact: str | None = Form(""),
    recommendation: str | None = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    finding = (
        db.query(Finding)
        .filter_by(id=finding_id, assessment_id=assessment_id)
        .one_or_none()
    )
    before = (finding.business_impact, finding.recommendation) if finding else None
    try:
        saved = board_inputs.update_finding_fields(
            db,
            assessment_id,
            finding_id,
            business_impact,
            recommendation,
            conclusion_review.reviewer_actor(reviewer_name),
        )
    except board_inputs.BoardInputError as exc:
        return _error(db, exc)
    db.commit()
    return _success(before != (saved.business_impact, saved.recommendation))


@router.post(
    "/api/assessments/{assessment_id}/board-inputs/actions/{action_id}/responsibility"
)
def save_action_responsibility(
    assessment_id: str,
    action_id: str,
    responsibility: str | None = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    action = (
        db.query(Action)
        .join(Finding, Action.finding_id == Finding.id)
        .filter(Action.id == action_id, Finding.assessment_id == assessment_id)
        .one_or_none()
    )
    before = action.responsibility if action else None
    try:
        saved = board_inputs.update_action_responsibility(
            db,
            assessment_id,
            action_id,
            responsibility,
            conclusion_review.reviewer_actor(reviewer_name),
        )
    except board_inputs.BoardInputError as exc:
        return _error(db, exc)
    db.commit()
    return _success(before != saved.responsibility)


@router.post("/api/assessments/{assessment_id}/board-inputs/initiatives")
def save_initiative(
    assessment_id: str,
    group_id: str = Form(""),
    title: str | None = Form(""),
    complexity: str | None = Form(""),
    benefit: str | None = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(InitiativeMetadata)
        .filter(
            InitiativeMetadata.assessment_id == assessment_id,
            InitiativeMetadata.group_id == group_id.strip(),
        )
        .one_or_none()
    )
    before = (
        (existing.title, existing.complexity, existing.benefit) if existing else None
    )
    try:
        saved = board_inputs.update_initiative(
            db,
            assessment_id,
            group_id,
            title,
            complexity,
            benefit,
            conclusion_review.reviewer_actor(reviewer_name),
        )
    except board_inputs.BoardInputError as exc:
        return _error(db, exc)
    db.commit()
    after = (saved.title, saved.complexity, saved.benefit)
    return _success(before != after)


@router.post("/api/assessments/{assessment_id}/board-inputs/asks")
def save_board_asks(
    assessment_id: str,
    ask_1: str | None = Form(""),
    ask_2: str | None = Form(""),
    ask_3: str | None = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    before = board_inputs.board_asks(assessment) if assessment else None
    try:
        saved = board_inputs.update_board_asks(
            db,
            assessment_id,
            [ask_1 or "", ask_2 or "", ask_3 or ""],
            conclusion_review.reviewer_actor(reviewer_name),
        )
    except board_inputs.BoardInputError as exc:
        return _error(db, exc)
    db.commit()
    return _success(before["consultant"] != saved["consultant"] if before else True)
