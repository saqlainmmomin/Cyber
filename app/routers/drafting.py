"""Routes for consultant-reviewed remediation and narrative drafts."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.services import approved_report, conclusion_review, narrative, remediation_draft
from app.template_config import configure_templates, framework_label

router = APIRouter(tags=["drafting"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)


def _toast(response, message: str, toast_type: str):
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = toast_type
    return response


def _error(status_code: int, message: str) -> JSONResponse:
    response = JSONResponse({"detail": message}, status_code=status_code)
    return _toast(response, message, "error")


def _redirect_success(assessment_id: str, payload: dict) -> JSONResponse:
    response = JSONResponse(payload)
    response.headers["HX-Redirect"] = f"/assessments/{assessment_id}/narrative"
    response.headers["X-Toast-Type"] = "success"
    return response


def _narrative_section_label(section_id: str) -> str:
    if section_id == narrative.EXECUTIVE:
        return "Executive overview"
    if section_id == narrative.CROSS_FRAMEWORK:
        return "Across frameworks"
    framework_id = section_id.removeprefix(narrative.FRAMEWORK_PREFIX)
    return f"{framework_label(framework_id, full=True)} posture"


def _narrative_failure_message(outcomes: dict[str, str]) -> str:
    failed = [
        _narrative_section_label(section_id)
        for section_id, outcome in outcomes.items()
        if outcome == "failed"
    ]
    limited = [
        _narrative_section_label(section_id)
        for section_id, outcome in outcomes.items()
        if outcome == "limit_reached"
    ]
    messages = []
    if failed:
        labels = ", ".join(failed)
        messages.append(
            f"{labels} could not be drafted. The section stays as it was. "
            "Write it yourself or try again."
        )
    if limited:
        labels = ", ".join(limited)
        messages.append(f"Draft limit reached for {labels}. Write this section yourself.")
    return " ".join(messages)


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
    try:
        expected_version = int(form.get("expected_version", ""))
    except (TypeError, ValueError):
        return _error(400, "Expected version must be an integer.")
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
    draft_notice = remediation_draft.DRAFT_NOTICE.replace("Save & Approve", "Save and approve")
    return _toast(
        _partial(
            request,
            assessment_id=assessment_id,
            conclusion_id=conclusion_id,
            recommended_action=draft.recommended_action,
            draft=draft,
            draft_notice=draft_notice,
        ),
        draft_notice,
        "success",
    )


@router.get("/assessments/{assessment_id}/narrative")
def narrative_page(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(404, "Assessment not found")
    current_state = narrative.state(db, assessment)
    ref_by_id = {ref.finding_id: ref.alias for ref in current_state.findings}
    sections = []
    for section in current_state.sections:
        lines = []
        for sentence in section.sentences:
            aliases = [ref_by_id[finding_id] for finding_id in sentence.get("finding_ids", []) if finding_id in ref_by_id]
            lines.append(f"{sentence.get('text', '')} [{', '.join(aliases)}]")
        sections.append(
            {
                "section": section,
                "text": "\n".join(lines),
            }
        )
    return _templates.TemplateResponse(
        request=request,
        name="pages/narrative.html",
        context={
            "request": request,
            "assessment": assessment,
            "state": current_state,
            "sections": sections,
            "released": approved_report.is_released(db, assessment),
            "blockers": narrative.report_blockers(db, assessment),
            "reviewer_name": "",
        },
    )


@router.post("/api/assessments/{assessment_id}/narrative/generate")
async def generate_narrative(
    assessment_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    section_id = str(form.get("section_id", "")).strip() or None
    actor = conclusion_review.reviewer_actor(form.get("reviewer_name"))
    try:
        sections = narrative.generate(db, assessment, actor=actor, section_id=section_id)
        db.commit()
    except HTTPException as exc:
        db.rollback()
        return _error(exc.status_code, str(exc.detail))
    except narrative.NarrativeError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    failed = any(value in ("failed", "limit_reached") for value in sections.values())
    if failed:
        # No HX-Redirect: htmx navigates on a redirect without swapping, so the
        # toast (shown on htmx:afterSwap) would never appear.
        return _toast(
            JSONResponse({"sections": sections}),
            _narrative_failure_message(sections),
            "error",
        )
    return _redirect_success(assessment_id, {"sections": sections})


@router.post("/api/assessments/{assessment_id}/narrative/{section_id}/accept")
async def accept_narrative(
    assessment_id: str,
    section_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    actor = conclusion_review.reviewer_actor(form.get("reviewer_name"))
    try:
        narrative.accept(
            db,
            assessment,
            section_id=section_id,
            text=str(form.get("text", "")),
            findings_sha256=str(form.get("findings_sha256", "")),
            actor=actor,
        )
        db.commit()
    except HTTPException as exc:
        db.rollback()
        return _error(exc.status_code, str(exc.detail))
    except narrative.NarrativeError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    return _redirect_success(
        assessment_id, {"status": "accepted", "section_id": section_id}
    )


@router.post("/api/assessments/{assessment_id}/narrative/{section_id}/discard")
async def discard_narrative(
    assessment_id: str,
    section_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    actor = conclusion_review.reviewer_actor(form.get("reviewer_name"))
    try:
        narrative.discard(db, assessment, section_id=section_id, actor=actor)
        db.commit()
    except narrative.NarrativeError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    return _redirect_success(
        assessment_id, {"status": "discarded", "section_id": section_id}
    )
