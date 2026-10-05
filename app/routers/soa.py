"""Statement of Applicability editor endpoints."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import literal_column
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.conclusion import Conclusion, ConclusionRevision
from app.services import approved_report, soa
from app.services.conclusion_review import reviewer_actor
from app.services import report_basis
from app.template_config import configure_templates


router = APIRouter(tags=["soa"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)


def _toast(response, message: str, toast_type: str):
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = toast_type
    return response


def _latest_reviewer_name(db: Session, assessment_id: str) -> str:
    event = (
        db.query(ConclusionRevision)
        .join(Conclusion, ConclusionRevision.conclusion_id == Conclusion.id)
        .filter(
            Conclusion.assessment_id == assessment_id,
            ConclusionRevision.actor.startswith("consultant:"),
        )
        .order_by(
            ConclusionRevision.created_at.desc(),
            literal_column("conclusion_revisions.rowid").desc(),
        )
        .first()
    )
    return event.actor.removeprefix("consultant:") if event else ""


@router.get("/assessments/{assessment_id}/soa", response_class=HTMLResponse)
def soa_page(assessment_id: str, request: Request, db: Session = Depends(get_db)):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if not soa.applies(assessment.frameworks):
        raise HTTPException(status_code=404, detail=soa.NOT_IN_SCOPE_MESSAGE)
    approved = approved_report.build_approved_report(db, assessment)
    statement = soa.build_soa(db, assessment, approved)
    rationale = {
        row.requirement_id: row.current_state
        for row in approved.framework_reviews[soa.FRAMEWORK_ID].rows
        if row.compliance_status == "not_applicable" and row.current_state
    }
    return _templates.TemplateResponse(
        request=request,
        name="pages/soa.html",
        context={
            "request": request,
            "assessment": assessment,
            "soa": statement,
            "rationale": rationale,
            "max_chars": soa.JUSTIFICATION_MAX_CHARS,
            "reviewer_name": _latest_reviewer_name(db, assessment_id),
            "report_basis": report_basis.current_basis(db, assessment),
            "preview_state": request.query_params.get("state", "") if request.url.path.startswith("/design/pages/") else "",
        },
    )


@router.post("/api/assessments/{assessment_id}/soa/justifications")
def save_justification(
    assessment_id: str,
    requirement_id: str = Form(""),
    justification: str | None = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _toast(
            JSONResponse({"detail": "Assessment not found"}, status_code=404),
            "Assessment not found",
            "error",
        )
    try:
        saved = soa.record_justification(
            db,
            assessment,
            requirement_id=requirement_id,
            justification=justification,
            actor=reviewer_actor(reviewer_name),
        )
    except soa.SoAError as exc:
        db.rollback()
        return _toast(
            JSONResponse({"detail": exc.message}, status_code=exc.status_code),
            exc.message,
            "error",
        )
    db.commit()
    response = JSONResponse(
        {
            "status": "saved",
            "requirement_id": requirement_id,
            "justification": saved,
        }
    )
    response.headers["X-Toast-Message"] = soa.SAVED_MESSAGE
    response.headers["X-Toast-Type"] = "success"
    return response
