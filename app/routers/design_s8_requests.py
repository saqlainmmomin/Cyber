"""S8 Requests/RFI previews backed by the real consultant templates."""

from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.routers import design, magic
from app.routers.web import templates
from app.services import rfi_requests


def _assessment_context(request: Request, db: Session):
    assessment_id = request.query_params.get("assessment_id")
    assessment = db.get(Assessment, assessment_id) if assessment_id else None
    if assessment is None:
        raise HTTPException(404, "Pass ?assessment_id=<id>")
    engagement = db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None
    client = db.get(Client, engagement.client_id) if engagement else None
    return assessment, engagement, client


def _magic_links_preview(request: Request, db: Session):
    state = request.query_params.get("state", "default")
    if state not in {state for state in SCREEN_STATES["b6-magic_links"]}:
        raise HTTPException(404, "Unknown state")
    assessment, engagement, client = _assessment_context(request, db)
    if engagement is None:
        raise HTTPException(404, "Engagement not found")
    context = magic._consultant_context(request, db, engagement.id)
    context["preview_state"] = state
    if state == "newlink":
        context["new_link_url"] = "https://app.yozora.example/m/q7Hk2xW9pLr4vTn8cBz3sYdF6aEu1oGj"
    elif state == "error":
        context["error"] = "Total size must be between 1 and 500 MB."
    return templates.TemplateResponse("pages/requests.html", context)


def _rfi_preview(request: Request, db: Session):
    state = request.query_params.get("state", "default")
    if state not in {state for state in SCREEN_STATES["b6-rfi"]}:
        raise HTTPException(404, "Unknown state")
    assessment, engagement, client = _assessment_context(request, db)
    context = rfi_requests.page_context(db, assessment)
    context.update(
        {
            "request": request,
            "engagement": engagement,
            "client": client,
            "preview_state": state,
            "rfi_tab": "versions" if state in {"versions", "issue"} else "items",
        }
    )
    return templates.TemplateResponse("pages/rfi.html", context)


SCREEN_STATES = {
    "b6-magic_links": ("default", "empty", "error", "loading", "newlink", "revoke"),
    "b6-rfi": ("default", "error", "issue", "loading", "noscope", "versions"),
}

design.PREVIEW_PAGES["b6-magic_links"] = _magic_links_preview
design.PREVIEW_PAGES["b6-rfi"] = _rfi_preview
design.DB_PREVIEWS.update(SCREEN_STATES)
