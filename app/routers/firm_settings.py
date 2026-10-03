"""Firm settings page (Yozora): contact email for clients, accent theme, archived-engagement retention,
and the data-housekeeping list of assessments that are not filed under an engagement."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.routers.web import templates
from app.services import firm_settings
from app.services.conclusion_review import reviewer_actor

router = APIRouter(tags=["settings"])

SAVED_MESSAGE = "Settings saved"
UNCHANGED_MESSAGE = "Nothing changed"


def unmigrated_assessments(db: Session) -> list[Assessment]:
    """Assessments that predate clients and engagements (formerly listed on the dashboard)."""
    return (
        db.query(Assessment)
        .filter(
            Assessment.engagement_id.is_(None),
            Assessment.status != "archived",
        )
        .order_by(Assessment.created_at.desc())
        .all()
    )


def _render(
    request: Request,
    db: Session,
    *,
    status_code: int = 200,
    errors: dict[str, str] | None = None,
    form_values: dict | None = None,
    saved: str | None = None,
):
    current = firm_settings.get(db)
    values = form_values or {
        "contact_email": current.contact_email or "",
        "archived_retention_years": str(current.archived_retention_years),
        "accent_theme": current.accent_choice,
        "accent_custom_hex": current.accent_custom_hex or "",
    }
    response = templates.TemplateResponse(
        request=request,
        name="pages/firm_settings.html",
        context={
            "request": request,
            "firm": current,
            "values": values,
            "errors": errors or {},
            "saved": saved,
            "accent_presets": firm_settings.ACCENT_PRESETS,
            "custom_accent": firm_settings.CUSTOM_ACCENT,
            "retention_range": firm_settings.RETENTION_YEARS_RANGE,
            "unmigrated_assessments": unmigrated_assessments(db),
        },
        status_code=status_code,
    )
    if errors:
        response.headers["X-Toast-Message"] = "Check the highlighted fields"
        response.headers["X-Toast-Type"] = "error"
    return response


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, saved: str | None = None, db: Session = Depends(get_db)):
    message = {"1": SAVED_MESSAGE, "0": UNCHANGED_MESSAGE}.get(saved or "")
    return _render(request, db, saved=message)


@router.post("/settings", response_class=HTMLResponse)
async def save_settings(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    form_values = {
        "contact_email": str(form.get("contact_email") or ""),
        "archived_retention_years": str(form.get("archived_retention_years") or ""),
        "accent_theme": str(form.get("accent_theme") or ""),
        "accent_custom_hex": str(form.get("accent_custom_hex") or ""),
    }
    try:
        _view, changes = firm_settings.update(
            db,
            contact_email=form_values["contact_email"],
            archived_retention_years=form_values["archived_retention_years"],
            accent_theme=form_values["accent_theme"],
            accent_custom_hex=form_values["accent_custom_hex"],
            actor=reviewer_actor(str(form.get("reviewer_name") or "")),
        )
        db.commit()
    except firm_settings.FirmSettingsValidationError as exc:
        db.rollback()
        return _render(request, db, status_code=422, errors=exc.errors, form_values=form_values)
    return RedirectResponse(f"/settings?saved={1 if changes else 0}", status_code=303)
