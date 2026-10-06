"""Yozora S9 previews for error pages and the completed empty states."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.engagement import Engagement
from app.routers import design, web
from app.routers.web import templates


SCREEN_STATES = {
    "b7-404": ("page", "engagement"),
    "b7-500": ("error", "down", "upstream"),
    "b7-empty-states": (
        "engagements",
        "evidence",
        "review",
        "search",
        "findings",
        "report",
    ),
}

PREVIEW_REFERENCE = "7f3a-91c2-0b4e"


def _preview_request(request: Request, path: str, **query: str) -> Request:
    scope = dict(request.scope)
    query_string = urlencode({key: value for key, value in query.items() if value is not None})
    scope.update(path=path, raw_path=path.encode(), query_string=query_string.encode())
    return Request(scope, request.receive)


def _error_preview(request: Request, screen: str):
    state = request.query_params.get("state", SCREEN_STATES[screen][0])
    if state not in SCREEN_STATES[screen]:
        state = SCREEN_STATES[screen][0]

    if screen == "b7-404":
        from app.main import _error_context

        variant = "engagement" if state == "engagement" else "page"
        context = _error_context(request, variant=variant, reference_code=PREVIEW_REFERENCE)
    else:
        context = {
            "error": {
                "crumb": "Something went wrong",
                "heading": "This page couldn't be loaded",
                "message": "Something failed on our side. Try again in a moment. If it keeps happening, send the reference to support.",
                "icon_id": "alert",
                "primary_label": "Try again",
                "primary_icon_id": "rotate",
                "primary_action": "retry",
                "primary_href": "/",
                "secondary_label": "Go to home",
                "secondary_href": "/",
                "secondary_action": "back",
            },
            "down": {
                "crumb": "Maintenance",
                "heading": "The service is down for maintenance",
                "message": "We expect to be back soon. Your saved work is not affected.",
                "icon_id": "clock",
                "primary_label": "Check again",
                "primary_icon_id": "rotate",
                "primary_action": "retry",
                "primary_href": "/",
                "secondary_label": "Go back",
                "secondary_href": "/",
                "secondary_action": "back",
            },
            "upstream": {
                "crumb": "Analysis unavailable",
                "heading": "The analysis service didn't respond",
                "message": "The analysis service stopped responding. Any completed results were saved.",
                "icon_id": "alert",
                "primary_label": "Run analysis again",
                "primary_icon_id": "rotate",
                "primary_action": "retry",
                "primary_href": "/",
                "secondary_label": "Back to engagement",
                "secondary_href": "/engagements",
                "secondary_action": "back",
            },
        }[state]
        context = {
            "request": request,
            "reference_code": PREVIEW_REFERENCE,
            "variant": state,
            **context,
        }

    return templates.TemplateResponse(
        request=request,
        name="pages/error.html",
        context=context,
        status_code=200,
    )


def _empty_preview(request: Request, db: Session):
    state = request.query_params.get("state", SCREEN_STATES["b7-empty-states"][0])
    if state not in SCREEN_STATES["b7-empty-states"]:
        state = SCREEN_STATES["b7-empty-states"][0]

    assessment = db.query(Assessment).order_by(Assessment.created_at, Assessment.id).first()
    engagement = db.query(Engagement).order_by(Engagement.created_at, Engagement.id).first()
    if state == "engagements":
        return web.engagements_page(_preview_request(request, "/engagements", state="empty"), q="", status="active", db=db)
    if state == "evidence" and engagement is not None:
        return web.engagement_evidence_inventory_page(
            _preview_request(request, f"/engagements/{engagement.id}/evidence", state="empty"),
            engagement.id,
            db,
        )
    if state == "review":
        review_route = next(route for route in web.router.routes if route.path == "/review")
        return review_route.endpoint(_preview_request(request, "/review", state="empty"), db)
    if state == "search":
        return web.engagements_page(
            _preview_request(request, "/engagements", q="not-found"),
            q="not-found",
            status="active",
            db=db,
        )
    if state == "findings" and assessment is not None:
        return web.findings_page(
            _preview_request(request, f"/assessments/{assessment.id}/findings"),
            assessment.id,
            db,
        )
    return web.reports_page(_preview_request(request, "/reports"), db)


for _screen in ("b7-404", "b7-500"):
    design.PREVIEW_PAGES[_screen] = lambda request, screen=_screen: _error_preview(request, screen)

design.PREVIEW_PAGES["b7-empty-states"] = _empty_preview
design.DB_PREVIEWS.add("b7-empty-states")
