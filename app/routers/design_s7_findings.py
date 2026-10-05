"""Debug-only S7 findings previews backed by the deterministic harness seed."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.routers import design
from app.routers.web import templates
from app.services import findings as finding_service


SCREEN_STATES = {
    "b5-findings": ("default", "create", "empty"),
    "b5-finding-card": (
        "open",
        "in-progress",
        "no-evidence",
        "verify",
        "verified",
        "legacy",
        "source-changed",
        "migrated",
        "add-action",
    ),
    "b7-dark-dense": ("dense",),
}


def _preview(screen: str, request: Request, db: Session) -> Response:
    state = request.query_params.get("state", SCREEN_STATES[screen][0])
    if state not in SCREEN_STATES[screen]:
        state = SCREEN_STATES[screen][0]
    assessment_id = request.query_params.get("assessment_id")
    assessment = db.get(Assessment, assessment_id) if assessment_id else db.query(Assessment).first()
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    page = finding_service.findings_page(db, assessment.id)
    return templates.TemplateResponse(
        request=request,
        name="pages/findings.html",
        context={
            "request": request,
            "assessment": assessment,
            "page": page,
            "reviewer_name": "Priya Sharma",
            "preview_screen": screen,
            "preview_state": state,
        },
    )


for _screen in SCREEN_STATES:
    design.PREVIEW_PAGES[_screen] = lambda request, screen=_screen, db=None: _preview(screen, request, db)
    design.DB_PREVIEWS.add(_screen)
