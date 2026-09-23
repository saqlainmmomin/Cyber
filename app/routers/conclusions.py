"""Per-Conclusion consultant approval endpoints."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.schemas.conclusions import ConclusionDecisionIn, ConclusionEditIn
from app.services import conclusion_review
from app.services.analysis_pipeline import ConclusionConflict
from app.template_config import configure_templates

router = APIRouter(prefix="/api/assessments", tags=["conclusions"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)

_SUCCESS_MESSAGES = {
    "approve": "Conclusion approved",
    "edit": "Conclusion edited and approved",
    "reject": "Conclusion rejected",
    "reopen": "Conclusion reopened",
}


async def _payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    return dict(await request.form())


def _validated(model_type, payload: dict):
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(422, detail=exc.errors()) from exc


def _toast(response, message: str, toast_type: str, *, encoded: bool = False):
    response.headers["X-Toast-Message"] = quote(message) if encoded else message
    response.headers["X-Toast-Type"] = toast_type
    return response


def _conflict_context(body, route_name: str, card) -> dict:
    diff = []
    if route_name == "edit":
        for field in conclusion_review.EDITABLE_FIELDS:
            submitted = getattr(body, field)
            current = getattr(card.conclusion, field)
            if submitted != current:
                diff.append(
                    {"field": field, "current": current, "submitted": submitted}
                )
    return {
        "submitted_version": body.expected_version,
        "submitted_action": route_name,
        "diff": diff,
    }


async def _decide(
    request: Request,
    *,
    assessment_id: str,
    conclusion_id: str,
    route_name: str,
    db: Session,
):
    schema = ConclusionEditIn if route_name == "edit" else ConclusionDecisionIn
    try:
        body = _validated(schema, await _payload(request))
    except HTTPException:
        db.rollback()
        raise

    edits = (
        {
            field: getattr(body, field)
            for field in conclusion_review.EDITABLE_FIELDS
        }
        if route_name == "edit"
        else None
    )
    try:
        conclusion_review.decide(
            db,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            action=conclusion_review.ACTION_BY_ROUTE[route_name],
            expected_version=body.expected_version,
            actor=conclusion_review.reviewer_actor(body.reviewer_name),
            edits=edits,
        )
    except conclusion_review.ConclusionNotFound as exc:
        db.rollback()
        raise HTTPException(404, exc.message) from exc
    except conclusion_review.InvalidDecision as exc:
        db.rollback()
        return _toast(
            JSONResponse({"detail": exc.message}, status_code=400),
            exc.message,
            "error",
            encoded=True,
        )
    except ConclusionConflict:
        db.rollback()
        try:
            card = conclusion_review.conclusion_card(
                db,
                assessment_id=assessment_id,
                conclusion_id=conclusion_id,
            )
        except conclusion_review.ConclusionNotFound as exc:
            db.rollback()
            raise HTTPException(404, exc.message) from exc
        assessment = db.get(Assessment, assessment_id)
        response = _templates.TemplateResponse(
            request=request,
            name="components/conclusion_card.html",
            context={
                "assessment": assessment,
                "card": card,
                "conflict": _conflict_context(body, route_name, card),
            },
            status_code=409,
        )
        response.headers["X-Conclusion-Conflict"] = "1"
        response = _toast(
            response,
            "Conflict: this conclusion changed since you loaded it. Nothing was saved.",
            "error",
        )
        # Rendering may invoke the patched lock-state seam used by the CAS race
        # contract. Keep conflict rendering observational even in that case.
        db.rollback()
        return response

    db.commit()
    card = conclusion_review.conclusion_card(
        db,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
    )
    assessment = db.get(Assessment, assessment_id)
    response = _templates.TemplateResponse(
        request=request,
        name="components/conclusion_card.html",
        context={"assessment": assessment, "card": card},
    )
    return _toast(response, _SUCCESS_MESSAGES[route_name], "success")


@router.post("/{assessment_id}/conclusions/{conclusion_id}/approve")
async def approve_conclusion(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    db: Session = Depends(get_db),
):
    return await _decide(
        request,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
        route_name="approve",
        db=db,
    )


@router.post("/{assessment_id}/conclusions/{conclusion_id}/edit")
async def edit_conclusion(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    db: Session = Depends(get_db),
):
    return await _decide(
        request,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
        route_name="edit",
        db=db,
    )


@router.post("/{assessment_id}/conclusions/{conclusion_id}/reject")
async def reject_conclusion(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    db: Session = Depends(get_db),
):
    return await _decide(
        request,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
        route_name="reject",
        db=db,
    )


@router.post("/{assessment_id}/conclusions/{conclusion_id}/reopen")
async def reopen_conclusion(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    db: Session = Depends(get_db),
):
    return await _decide(
        request,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
        route_name="reopen",
        db=db,
    )
