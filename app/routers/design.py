"""Debug-only Yozora component gallery and template preview routes."""

from collections.abc import Callable
from dataclasses import replace
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.assessment import Assessment
from app.routers.web import templates
from app.services import workpaper

router = APIRouter(tags=["design"])

# Debug-only pages that do not have standalone production routes register here.
PREVIEW_PAGES: dict[str, Callable[[Request, Session], Response]] = {}


def login_preview(request: Request, db: Session | None = None) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "error", "loading"}:
        state = "default"
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "preview_state": state},
    )


PREVIEW_PAGES["login"] = login_preview


def workpaper_entry_preview(request: Request, db: Session) -> Response:
    state = request.query_params.get("state", "default")
    if state not in {"default", "legacy", "excluded"}:
        state = "default"
    assessment = db.query(Assessment).order_by(Assessment.created_at, Assessment.id).first()
    entry = None
    if assessment:
        read_model = workpaper.build_workpaper(db, assessment)
        sections = read_model.sections
        entry = next((item for section in sections for item in section.entries), None)
        if entry is None:
            entry = next((item for section in sections for item in section.excluded_entries), None)
    if entry is None:
        assessment = assessment or SimpleNamespace(id="preview-assessment")
        conclusion = SimpleNamespace(
            framework_id="dpdpa", requirement_id="DPDPA-1", version=1, id="preview-conclusion",
            ai_proposed=True, outcome="compliant", risk_level="low", rationale="Documented practice",
            gaps_identified="None recorded", recommended_action="Maintain the control",
            evidence_summary="Privacy notice.pdf supports the conclusion",
        )
        card = SimpleNamespace(
            conclusion=conclusion, requirement_title="Privacy notice and transparency", state="approved",
            locked=False, legacy_bulk_approval=False, legacy_report_status=None, last_decision=None,
            previous_outcome=None, unsupported_assertion=False, withheld_proposal=None,
        )
        entry = SimpleNamespace(
            card=card, anchor="wp-dpdpa-DPDPA-1", in_scope=True, client_response=None,
            mapped_evidence=[], desk_review_findings=[], ai_proposal=None, revisions=[], findings=[],
        )
    if state == "legacy":
        if hasattr(entry.card, "__dataclass_fields__"):
            entry = replace(entry, card=replace(entry.card, legacy_bulk_approval=True))
        else:
            card_values = vars(entry.card).copy()
            card_values["legacy_bulk_approval"] = True
            entry.card = SimpleNamespace(**card_values)
    elif state == "excluded":
        if hasattr(entry, "__dataclass_fields__"):
            entry = replace(entry, in_scope=False)
        else:
            entry.in_scope = False
    return templates.TemplateResponse(
        "components/workpaper_entry.html",
        {"request": request, "assessment": assessment, "entry": entry},
    )


PREVIEW_PAGES["workpaper_entry"] = workpaper_entry_preview


def _debug_only() -> None:
    if settings.env.casefold() == "production":
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/design", response_class=HTMLResponse, include_in_schema=False)
def design_gallery(request: Request) -> Response:
    _debug_only()
    return templates.TemplateResponse(
        "pages/design.html",
        {
            "request": request,
            "dark": "dark" in request.query_params,
            "focus": "focus" in request.query_params,
        },
    )


@router.get("/design/pages/{name}", response_class=HTMLResponse, include_in_schema=False)
def design_preview(request: Request, name: str, db: Session = Depends(get_db)) -> Response:
    _debug_only()
    preview = PREVIEW_PAGES.get(name)
    if preview is None:
        raise HTTPException(status_code=404, detail="Not found")
    return preview(request, db)
