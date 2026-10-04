"""Requirement card, review queue and evidence span routes."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.evidence import Evidence
from app.services import conclusion_review, requirement_card, review_queue, rfi_evidence_requests
from app.template_config import configure_templates

router = APIRouter(tags=["requirement-review"])
_templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")
configure_templates(_templates)


@router.get("/assessments/{assessment_id}/review-queue", response_class=HTMLResponse)
def review_queue_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    groups = review_queue.review_queue(db, assessment_id)
    total = sum(len(group.entries) for group in groups)
    open_count = sum(
        entry.card.state in ("pending", "rejected")
        for group in groups
        for entry in group.entries
    )
    from app.routers.web import _latest_reviewer_name

    return _templates.TemplateResponse(
        request=request,
        name="pages/review_queue.html",
        context={
            "request": request,
            "assessment": assessment,
            "groups": groups,
            "total": total,
            "open_count": open_count,
            "reviewer_name": _latest_reviewer_name(db, assessment_id),
            "shared_evidence_label": requirement_card.SHARED_EVIDENCE_LABEL,
        },
    )


@router.post("/api/assessments/{assessment_id}/divergence-notes/{conclusion_id}/acknowledge")
def acknowledge_divergence(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    analysis_run_id: str = Form(""),
    cluster_id: str = Form(""),
    note: str = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        requirement_card.acknowledge_divergence(
            db,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            analysis_run_id=analysis_run_id,
            cluster_id=cluster_id,
            note=note,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except requirement_card.RequirementCardError as exc:
        db.rollback()
        response = JSONResponse({"detail": exc.message}, status_code=exc.status_code)
        response.headers["X-Toast-Message"] = quote(exc.message)
        response.headers["X-Toast-Type"] = "error"
        return response

    db.commit()
    assessment = db.get(Assessment, assessment_id)
    card = conclusion_review.conclusion_card(
        db,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
    )
    response = _templates.TemplateResponse(
        request=request,
        name="components/conclusion_card.html",
        context={"request": request, "assessment": assessment, "card": card},
    )
    response.headers["X-Toast-Message"] = "Framework divergence acknowledged"
    response.headers["X-Toast-Type"] = "success"
    return response


@router.post("/api/assessments/{assessment_id}/rfi-requests/{conclusion_id}")
def add_rfi_request(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    request_key: str = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        _event, changed = requirement_card.add_rfi_request(
            db,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            request_key=request_key,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except rfi_evidence_requests.RfiRequestError as exc:
        db.rollback()
        response = JSONResponse({"detail": exc.message}, status_code=exc.status_code)
        response.headers["X-Toast-Message"] = quote(exc.message)
        response.headers["X-Toast-Type"] = "error"
        return response

    db.commit()
    assessment = db.get(Assessment, assessment_id)
    card = conclusion_review.conclusion_card(
        db,
        assessment_id=assessment_id,
        conclusion_id=conclusion_id,
    )
    response = _templates.TemplateResponse(
        request=request,
        name="components/conclusion_card.html",
        context={"request": request, "assessment": assessment, "card": card},
    )
    response.headers["X-Toast-Message"] = (
        rfi_evidence_requests.ADDED_TOAST
        if changed
        else rfi_evidence_requests.ALREADY_TOAST
    )
    response.headers["X-Toast-Type"] = "success"
    return response


@router.post("/api/assessments/{assessment_id}/rfi-requests/{conclusion_id}/withdraw")
def withdraw_rfi_request(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    request_key: str = Form(""),
    reviewer_name: str = Form(""),
    origin: str = Form("card"),
    db: Session = Depends(get_db),
):
    try:
        _event, changed = rfi_evidence_requests.withdraw_request(
            db,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            request_key_value=request_key,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except rfi_evidence_requests.RfiRequestError as exc:
        db.rollback()
        response = JSONResponse({"detail": exc.message}, status_code=exc.status_code)
        response.headers["X-Toast-Message"] = quote(exc.message)
        response.headers["X-Toast-Type"] = "error"
        return response

    db.commit()
    toast = (
        rfi_evidence_requests.WITHDRAWN_TOAST
        if changed
        else rfi_evidence_requests.ALREADY_WITHDRAWN_TOAST
    )
    if origin == "rfi":
        response = JSONResponse({"status": "withdrawn" if changed else "unchanged"})
        response.headers["HX-Redirect"] = f"/assessments/{assessment_id}/rfi"
    else:
        assessment = db.get(Assessment, assessment_id)
        card = conclusion_review.conclusion_card(
            db,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
        )
        response = _templates.TemplateResponse(
            request=request,
            name="components/conclusion_card.html",
            context={"request": request, "assessment": assessment, "card": card},
        )
    response.headers["X-Toast-Message"] = toast
    response.headers["X-Toast-Type"] = "success"
    return response


@router.get("/evidence-versions/{version_id}/span", response_class=HTMLResponse)
def evidence_span(
    request: Request,
    version_id: str,
    ref: str = "",
    db: Session = Depends(get_db),
):
    try:
        view = requirement_card.span_view(db, version_id, ref)
    except requirement_card.RequirementCardError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    evidence = db.get(Evidence, view.evidence_id)
    engagement = db.get(Engagement, evidence.engagement_id) if evidence else None
    client = db.get(Client, engagement.client_id) if engagement else None
    return _templates.TemplateResponse(
        request=request,
        name="pages/evidence_span.html",
        context={"request": request, "view": view, "engagement": engagement, "client": client},
    )
