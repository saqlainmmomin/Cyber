"""Engagement archive, retention, and manual purge routes."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.engagement import Engagement
from app.services import conclusion_review, retention
from app.template_config import configure_templates

router = APIRouter(tags=["retention"])
_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)

READ_ONLY_METHODS = ("GET", "HEAD", "OPTIONS")


def archive_write_guard(request: Request, db: Session = Depends(get_db)) -> None:
    if request.method in READ_ONLY_METHODS:
        return
    ids = retention.engagement_ids_for_path(db, request.path_params)
    if retention.archived_engagement_ids(db, ids):
        raise HTTPException(
            status_code=409,
            detail=retention.ARCHIVED_READ_ONLY,
            headers={
                "X-Toast-Message": quote(retention.ARCHIVED_READ_ONLY),
                "X-Toast-Type": "error",
            },
        )


def _error(status_code: int, message: str, **extra) -> JSONResponse:
    response = JSONResponse(
        {"detail": message, **extra},
        status_code=status_code,
    )
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = "error"
    return response


def _success(
    payload: dict,
    message: str,
    *,
    redirect: str | None = None,
    refresh: bool = False,
) -> JSONResponse:
    response = JSONResponse(payload)
    if redirect is not None:
        response.headers["HX-Redirect"] = redirect
    if refresh:
        response.headers["HX-Refresh"] = "true"
    response.headers["X-Toast-Message"] = message
    response.headers["X-Toast-Type"] = "success"
    return response


def _handle_error(db: Session, exc: retention.RetentionError) -> JSONResponse:
    db.rollback()
    return _error(exc.status_code, exc.message)


def _dependency_text(eligibility: retention.Eligibility) -> str:
    return "; ".join(
        f"{retention.DEPENDENCY_LABELS[dependency.code]} ({dependency.count})"
        for dependency in eligibility.dependencies
        if dependency.count
    )


def _preview_reason_messages(
    eligibility: retention.Eligibility,
) -> list[tuple[str, str]]:
    values = {
        "eligible_at": eligibility.state.eligible_at,
        "dependencies": _dependency_text(eligibility),
    }
    return [
        (reason, retention.REASON_MESSAGES[reason].format(**values))
        for reason in eligibility.reasons
    ]


@router.post("/api/engagements/{engagement_id}/archive")
def archive_engagement_route(
    engagement_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        engagement = retention.archive_engagement(
            db,
            engagement_id=engagement_id,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
        db.commit()
    except retention.RetentionError as exc:
        return _handle_error(db, exc)
    return _success(
        {"engagement_id": engagement.id, "status": engagement.status},
        "Engagement archived",
        redirect=f"/engagements/{engagement.id}",
    )


@router.post("/api/engagements/{engagement_id}/unarchive")
def unarchive_engagement_route(
    engagement_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        engagement = retention.unarchive_engagement(
            db,
            engagement_id=engagement_id,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
        db.commit()
    except retention.RetentionError as exc:
        return _handle_error(db, exc)
    return _success(
        {"engagement_id": engagement.id, "status": engagement.status},
        "Engagement restored",
        redirect=f"/engagements/{engagement.id}",
    )


@router.get("/engagements/{engagement_id}/purge", response_class=HTMLResponse)
def purge_preview_page(
    request: Request,
    engagement_id: str,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        message = (
            retention.ALREADY_PURGED
            if retention._has_purged_event(db, engagement_id)
            else retention.ENGAGEMENT_NOT_FOUND
        )
        raise HTTPException(404, message)
    client = db.get(Client, engagement.client_id)
    if client is None:
        raise HTTPException(404, retention.CLIENT_NOT_FOUND)
    plan = retention.build_purge_plan(db, engagement)
    eligibility = retention.evaluate_purge(db, engagement, plan)
    return _templates.TemplateResponse(
        request=request,
        name="pages/engagement_purge.html",
        context={
            "request": request,
            "engagement": engagement,
            "client": client,
            "plan": plan,
            "eligibility": eligibility,
            "reason_messages": _preview_reason_messages(eligibility),
            "dependency_labels": retention.DEPENDENCY_LABELS,
        },
    )


@router.post("/api/engagements/{engagement_id}/purge")
def purge_engagement_route(
    engagement_id: str,
    confirm_name: str | None = Form(None),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        result = retention.purge_engagement(
            db,
            engagement_id=engagement_id,
            confirm_name=confirm_name,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except retention.PurgeRefused as exc:
        eligibility = exc.eligibility
        dependencies = [
            {"code": dependency.code, "count": dependency.count}
            for dependency in eligibility.dependencies
            if dependency.count
        ]
        return _error(
            409,
            exc.message,
            reasons=list(eligibility.reasons),
            eligible_at=(
                eligibility.state.eligible_at.isoformat()
                if eligibility.state.eligible_at
                else None
            ),
            dependencies=dependencies,
            layout_violations=eligibility.layout_violations,
        )
    except retention.RetentionError as exc:
        return _handle_error(db, exc)
    if not result.blobs_removed:
        return _error(
            500,
            retention.PURGE_BLOBS_PENDING,
            records_purged=True,
            blobs_pending=True,
            engagement_id=result.engagement_id,
        )
    return _success(
        {
            "engagement_id": result.engagement_id,
            "purge_event_id": result.purge_event_id,
            "row_counts": result.row_counts,
            "blobs_removed": True,
        },
        "Engagement permanently purged",
        redirect=f"/clients/{result.client_id}",
    )


@router.post("/api/engagements/{engagement_id}/purge/complete")
def complete_purge_route(
    engagement_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        outcome = retention.complete_pending_purge(
            db,
            engagement_id=engagement_id,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except retention.RetentionError as exc:
        return _handle_error(db, exc)
    return _success(
        {
            "engagement_id": engagement_id,
            "already_complete": outcome.already_complete,
            "removed_roots": list(outcome.removed_roots),
            "missing_roots": list(outcome.missing_roots),
        },
        "Nothing left to remove" if outcome.already_complete else "Stored files removed",
        refresh=True,
    )


@router.post("/api/clients/{client_id}/retention")
def set_client_retention_route(
    client_id: str,
    retention_years: str | None = Form(None),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        client, changed = retention.set_client_retention(
            db,
            client_id=client_id,
            retention_years=retention_years,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
        db.commit()
    except retention.RetentionError as exc:
        return _handle_error(db, exc)
    return _success(
        {"client_id": client.id, "retention_years": client.retention_years},
        "Retention updated" if changed else "Retention unchanged",
        redirect=f"/clients/{client.id}",
    )
