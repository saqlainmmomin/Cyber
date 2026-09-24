"""Finding and Action endpoints for P3-1."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.schemas.findings import (
    ActionCloseIn,
    ActionCreateIn,
    ActionReopenIn,
    ActionStatusIn,
    ActionUpdateIn,
    ActionVerifyIn,
    FindingCreateIn,
)
from app.services import conclusion_review
from app.services import findings as finding_service
from app.template_config import configure_templates

router = APIRouter(prefix="/api/assessments", tags=["findings"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)


async def _payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    payload = (
        await request.json()
        if "application/json" in content_type
        else dict(await request.form())
    )
    return {key: None if value == "" else value for key, value in payload.items()}


def _validated(model_type, payload: dict):
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(422, detail=exc.errors()) from exc


def _toast(response, message: str, toast_type: str):
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = toast_type
    return response


def _error(db: Session, exc: finding_service.FindingError):
    db.rollback()
    if isinstance(exc, finding_service.FindingNotFound):
        raise HTTPException(404, exc.message) from exc
    return _toast(
        JSONResponse({"detail": exc.message}, status_code=exc.status_code),
        exc.message,
        "error",
    )


def _card_response(
    request: Request,
    db: Session,
    *,
    assessment_id: str,
    finding_id: str,
    message: str,
):
    view = finding_service.finding_view(
        db, assessment_id=assessment_id, finding_id=finding_id
    )
    assessment = db.get(Assessment, assessment_id)
    response = _templates.TemplateResponse(
        request=request,
        name="components/finding_card.html",
        context={"assessment": assessment, "view": view},
    )
    return _toast(response, message, "success")


@router.post("/{assessment_id}/findings")
async def create_finding_route(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(FindingCreateIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding = finding_service.create_finding(
            db,
            assessment_id=assessment_id,
            conclusion_id=body.conclusion_id,
            conclusion_version=body.conclusion_version,
            title=body.title,
            description=body.description,
            severity=body.severity,
            priority=body.priority,
            action_title=body.action_title,
            action_owner=body.action_owner,
            action_target_date=body.action_target_date,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    response = JSONResponse({"finding_id": finding.id})
    response.headers["HX-Redirect"] = (
        f"/assessments/{assessment_id}/findings#finding-{finding.id}"
    )
    return response


@router.post("/{assessment_id}/findings/{finding_id}/actions")
async def add_action_route(
    request: Request,
    assessment_id: str,
    finding_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(ActionCreateIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding_service.add_action(
            db,
            assessment_id=assessment_id,
            finding_id=finding_id,
            title=body.title,
            owner=body.owner,
            target_date=body.target_date,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    return _card_response(
        request,
        db,
        assessment_id=assessment_id,
        finding_id=finding_id,
        message="Action added",
    )


@router.post("/{assessment_id}/findings/{finding_id}/actions/{action_id}/status")
async def change_action_status_route(
    request: Request,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(ActionStatusIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding_service.change_action_status(
            db,
            assessment_id=assessment_id,
            finding_id=finding_id,
            action_id=action_id,
            status=body.status,
            expected_history_length=body.expected_history_length,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    return _card_response(
        request,
        db,
        assessment_id=assessment_id,
        finding_id=finding_id,
        message="Action status updated",
    )


@router.post("/{assessment_id}/findings/{finding_id}/actions/{action_id}/update")
async def update_action_route(
    request: Request,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(ActionUpdateIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding_service.update_action(
            db,
            assessment_id=assessment_id,
            finding_id=finding_id,
            action_id=action_id,
            title=body.title,
            owner=body.owner,
            target_date=body.target_date,
            expected_history_length=body.expected_history_length,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    return _card_response(
        request,
        db,
        assessment_id=assessment_id,
        finding_id=finding_id,
        message="Action updated",
    )


@router.post("/{assessment_id}/findings/{finding_id}/actions/{action_id}/close")
async def close_action_route(
    request: Request,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(ActionCloseIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding_service.close_action(
            db,
            assessment_id=assessment_id,
            finding_id=finding_id,
            action_id=action_id,
            evidence_version_id=body.evidence_version_id,
            expected_history_length=body.expected_history_length,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    return _card_response(
        request,
        db,
        assessment_id=assessment_id,
        finding_id=finding_id,
        message="Action closed",
    )


@router.post("/{assessment_id}/findings/{finding_id}/actions/{action_id}/verify")
async def verify_action_route(
    request: Request,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(ActionVerifyIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding_service.verify_action(
            db,
            assessment_id=assessment_id,
            finding_id=finding_id,
            action_id=action_id,
            expected_history_length=body.expected_history_length,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    return _card_response(
        request,
        db,
        assessment_id=assessment_id,
        finding_id=finding_id,
        message="Closure verified",
    )


@router.post("/{assessment_id}/findings/{finding_id}/actions/{action_id}/reopen")
async def reopen_action_route(
    request: Request,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    db: Session = Depends(get_db),
):
    try:
        body = _validated(ActionReopenIn, await _payload(request))
    except HTTPException:
        db.rollback()
        raise
    try:
        finding_service.reopen_action(
            db,
            assessment_id=assessment_id,
            finding_id=finding_id,
            action_id=action_id,
            expected_history_length=body.expected_history_length,
            notes=body.notes,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
        )
    except finding_service.FindingError as exc:
        return _error(db, exc)
    db.commit()
    return _card_response(
        request,
        db,
        assessment_id=assessment_id,
        finding_id=finding_id,
        message="Action reopened",
    )
