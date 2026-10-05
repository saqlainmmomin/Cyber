"""Debug-only S7 page previews backed by the live page services."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.engagement import Engagement
from app.routers import design
from app.routers.web import _latest_reviewer_name, templates
from app.services import approved_report, conclusion_review, report_basis, review_queue


SCREEN_STATES = {
    "b5-review-queue": ("default", "shared", "done", "empty"),
    "b5-conclusions": ("default", "legacy-bulk", "empty"),
}


def _preview(screen: str, request: Request, db: Session) -> Response:
    state = request.query_params.get("state", SCREEN_STATES[screen][0])
    if state not in SCREEN_STATES[screen]:
        state = SCREEN_STATES[screen][0]
    assessment_id = request.query_params.get("assessment_id")
    assessment = db.get(Assessment, assessment_id) if assessment_id else db.query(Assessment).first()
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    cards = conclusion_review.conclusion_cards(db, assessment.id)
    if screen == "b5-review-queue":
        groups = review_queue.build_queue(cards)
        total = sum(len(group.entries) for group in groups)
        open_count = sum(entry.card.state in {"pending", "rejected"} for group in groups for entry in group.entries)
        context = {
            "groups": groups,
            "total": total,
            "open_count": open_count,
            "reviewer_name": _latest_reviewer_name(db, assessment.id),
        }
        template_name = "pages/review_queue.html"
    else:
        context = {
            "cards": cards,
            "counts": {
                "pending": sum(card.state == "pending" for card in cards),
                "rejected": sum(card.state == "rejected" for card in cards),
                "approved": sum(card.state == "approved" and not card.legacy_bulk_approval for card in cards),
                "edited": sum(card.state == "edited" for card in cards),
                "legacy_bulk": sum(card.legacy_bulk_approval for card in cards),
            },
            "reviewer_name": _latest_reviewer_name(db, assessment.id),
            "release": approved_report.release_state(db, assessment),
            "report_basis": report_basis.current_basis(db, assessment),
            "period_locked": report_basis.period_locked(db, assessment),
        }
        template_name = "pages/conclusions.html"
    context.update({"request": request, "assessment": assessment, "engagement_row": db.get(Engagement, assessment.engagement_id) if assessment.engagement_id else None, "preview_screen": screen, "preview_state": state})
    return templates.TemplateResponse(request=request, name=template_name, context=context)


for _screen in SCREEN_STATES:
    design.PREVIEW_PAGES[_screen] = lambda request, screen=_screen, db=None: _preview(screen, request, db)
    design.DB_PREVIEWS.add(_screen)
