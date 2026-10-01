"""Routes for consultant-reviewed Stage 3 remediation drafts."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import conclusion_review, remediation_draft
from app.template_config import configure_templates

router = APIRouter(tags=["drafting"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)


def _toast(response, message: str, toast_type: str):
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = toast_type
    return response


def _partial(
    request: Request,
    *,
    assessment_id: str,
    conclusion_id: str,
    recommended_action: str,
    draft: remediation_draft.RemediationDraft | None = None,
    error: str | None = None,
    draft_notice: str | None = None,
):
    return _templates.TemplateResponse(
        request=request,
        name="partials/remediation_draft.html",
        context={
            "assessment_id": assessment_id,
            "conclusion_id": conclusion_id,
            "recommended_action": recommended_action,
            "draft": draft,
            "error": error,
            "draft_notice": draft_notice,
        },
    )


@router.post("/api/assessments/{assessment_id}/recommended-action-drafts/{conclusion_id}")
async def draft_recommended_action(
    request: Request,
    assessment_id: str,
    conclusion_id: str,
    db: Session = Depends(get_db),
):
    form = await request.form()
    expected_version = int(form.get("expected_version", ""))
    outcome = str(form.get("outcome", ""))
    gaps_identified = str(form.get("gaps_identified", ""))
    recommended_action = str(form.get("recommended_action", ""))
    regenerate = form.get("regenerate") == "1"
    actor = conclusion_review.reviewer_actor(form.get("reviewer_name"))
    try:
        draft = remediation_draft.draft(
            db,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            expected_version=expected_version,
            outcome=outcome,
            gaps_identified=gaps_identified,
            actor=actor,
            regenerate=regenerate,
        )
    except remediation_draft.RemediationDraftFailed as exc:
        db.commit()
        return _toast(
            _partial(
                request,
                assessment_id=assessment_id,
                conclusion_id=conclusion_id,
                recommended_action=recommended_action,
                error=exc.message,
            ),
            exc.message,
            "error",
        )
    except remediation_draft.RemediationDraftError as exc:
        db.rollback()
        return _toast(
            JSONResponse({"detail": exc.message}, status_code=exc.status_code),
            exc.message,
            "error",
        )

    db.commit()
    return _toast(
        _partial(
            request,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            recommended_action=draft.recommended_action,
            draft=draft,
            draft_notice=remediation_draft.DRAFT_NOTICE,
        ),
        remediation_draft.DRAFT_NOTICE,
        "success",
    )
