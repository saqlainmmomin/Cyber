from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.services import approved_report, conclusion_review, report_basis

router = APIRouter(prefix="/api/assessments", tags=["review"])


def _retired() -> None:
    raise HTTPException(410, approved_report.LEGACY_REVIEW_RETIRED)


@router.patch("/{assessment_id}/review/items/{item_id}")
def disposition_item(assessment_id: str, item_id: str):
    _retired()


@router.post("/{assessment_id}/review/approve")
def approve_assessment(assessment_id: str):
    _retired()


@router.post("/{assessment_id}/review/reject")
def reject_assessment(assessment_id: str):
    _retired()


@router.post("/{assessment_id}/report-basis")
def save_report_basis(
    assessment_id: str,
    period_start: str = Form(""),
    period_end: str = Form(""),
    evidence_cutoff: str = Form(""),
    prepared_by: str = Form(""),
    reviewed_by: str = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return JSONResponse({"detail": "Assessment not found"}, status_code=404)
    try:
        basis = report_basis.update_report_basis(
            db,
            assessment,
            period_start=report_basis.parse_date(period_start),
            period_end=report_basis.parse_date(period_end),
            evidence_cutoff=report_basis.parse_date(evidence_cutoff),
            prepared_by=prepared_by,
            reviewed_by=reviewed_by,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except report_basis.ReportBasisError as exc:
        db.rollback()
        response = JSONResponse({"detail": exc.message}, status_code=exc.status_code)
        response.headers["X-Toast-Message"] = quote(exc.message)
        response.headers["X-Toast-Type"] = "error"
        return response

    db.commit()
    response = JSONResponse({"status": "saved", **basis.to_metadata()}, status_code=200)
    response.headers["HX-Redirect"] = f"/assessments/{assessment_id}/conclusions"
    response.headers["X-Toast-Message"] = "Assessment period and sign-off saved"
    response.headers["X-Toast-Type"] = "success"
    return response


@router.post("/{assessment_id}/release")
def release_assessment(
    assessment_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return JSONResponse({"detail": "Assessment not found"}, status_code=404)
    try:
        event = approved_report.record_release(
            db,
            assessment,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except approved_report.ReleaseRefused as exc:
        db.rollback()
        response = JSONResponse(
            {"detail": exc.message, "blockers": list(exc.blockers)},
            status_code=exc.status_code,
        )
        response.headers["X-Toast-Message"] = quote(exc.message)
        response.headers["X-Toast-Type"] = "error"
        return response

    db.commit()
    response = JSONResponse(
        {"status": "released", "release_event_id": event.id},
        status_code=200,
    )
    response.headers["HX-Redirect"] = f"/assessments/{assessment_id}?tab=report"
    response.headers["X-Toast-Message"] = "Report released"
    response.headers["X-Toast-Type"] = "success"
    return response
