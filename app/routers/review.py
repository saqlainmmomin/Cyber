from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.report import GapItem, GapReport
from app.schemas.review import ReviewApproval, ReviewItemUpdate, ReviewRejection

router = APIRouter(prefix="/api/assessments", tags=["review"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)


async def _payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    return dict(await request.form())


def _validated(model_type, payload: dict):
    normalized = {
        key: (None if value == "" and key != "reviewer_name" else value)
        for key, value in payload.items()
    }
    try:
        return model_type.model_validate(normalized)
    except ValidationError as exc:
        raise HTTPException(422, detail=exc.errors()) from exc


def _get_report(assessment_id: str, db: Session) -> GapReport:
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if not report:
        raise HTTPException(404, "Report not found")
    return report


def _toast(response, message: str, toast_type: str = "success"):
    response.headers["X-Toast-Message"] = message
    response.headers["X-Toast-Type"] = toast_type
    return response


@router.patch("/{assessment_id}/review/items/{item_id}")
async def disposition_item(
    request: Request,
    assessment_id: str,
    item_id: str,
    db: Session = Depends(get_db),
):
    update = _validated(ReviewItemUpdate, await _payload(request))
    report = _get_report(assessment_id, db)
    item = (
        db.query(GapItem)
        .filter(GapItem.id == item_id, GapItem.report_id == report.id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Gap item not found")

    fields = update.model_fields_set
    if "review_status" in fields and update.review_status:
        item.review_status = update.review_status
        item.reviewed_at = datetime.now(timezone.utc)
    if "compliance_status" in fields and update.compliance_status is not None:
        item.compliance_status = update.compliance_status
    if "gap_description" in fields and update.gap_description is not None:
        item.gap_description = update.gap_description
    if "risk_level" in fields and update.risk_level is not None:
        item.risk_level = update.risk_level
    if "reviewer_notes" in fields:
        item.reviewer_notes = update.reviewer_notes

    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if assessment.review_status != "under_review":
        assessment.review_status = "under_review"

    db.commit()
    db.refresh(item)

    label = (update.review_status or "updated").replace("_", " ").title()
    rendered = _templates.TemplateResponse(
        request=request,
        name="partials/review_finding_card.html",
        context={"item": item, "assessment": assessment},
    )
    return _toast(rendered, f"Finding {label}")


@router.post("/{assessment_id}/review/approve")
async def approve_assessment(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    approval = _validated(ReviewApproval, await _payload(request))
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    report = _get_report(assessment_id, db)
    draft_count = (
        db.query(GapItem)
        .filter(
            GapItem.report_id == report.id,
            or_(GapItem.review_status.is_(None), GapItem.review_status == "draft"),
        )
        .count()
    )
    if draft_count:
        raise HTTPException(
            400,
            f"{draft_count} findings still in draft. Review all findings before approving.",
        )

    reviewer_name = approval.reviewer_name.strip() or "Manager Review"
    assessment.review_status = "approved"
    now = datetime.now(timezone.utc)
    for item in db.query(GapItem).filter(GapItem.report_id == report.id).all():
        item.reviewed_by = reviewer_name
        item.reviewed_at = item.reviewed_at or now
    db.commit()

    response = JSONResponse({"status": "approved"})
    response.headers["HX-Redirect"] = f"/assessments/{assessment_id}?tab=report"
    return _toast(response, "Assessment approved for release")


@router.post("/{assessment_id}/review/reject")
async def reject_assessment(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    rejection = _validated(ReviewRejection, await _payload(request))
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    assessment.review_status = "rejected"
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if report:
        reviewer_name = rejection.reviewer_name.strip() or "Manager Review"
        now = datetime.now(timezone.utc)
        for item in db.query(GapItem).filter(GapItem.report_id == report.id).all():
            if not item.reviewed_by:
                item.reviewed_by = reviewer_name
            if rejection.rejection_reason and not item.reviewer_notes:
                item.reviewer_notes = rejection.rejection_reason
            item.reviewed_at = item.reviewed_at or now
    db.commit()

    return _toast(
        JSONResponse({"status": "rejected"}),
        "Assessment rejected - re-analysis may be needed",
        "error",
    )
