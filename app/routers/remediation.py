from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import GapItem, GapReport
from app.schemas.remediation import RemediationSummary, RemediationUpdate

router = APIRouter(prefix="/api/assessments", tags=["remediation"])

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
_templates = Jinja2Templates(directory=_templates_dir)
_panel_template = _templates_dir / "partials" / "remediation_panel.html"
_summary_template = _templates_dir / "partials" / "remediation_summary.html"


def _get_report(assessment_id: str, db: Session) -> GapReport:
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if not report:
        raise HTTPException(404, "Report not found")
    return report


def _toast(response, message: str):
    response.headers["X-Toast-Message"] = message
    response.headers["X-Toast-Type"] = "success"
    return response


async def _payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    return dict(await request.form())


@router.patch("/{assessment_id}/gap-items/{item_id}/remediation")
async def update_remediation(
    request: Request,
    assessment_id: str,
    item_id: str,
    db: Session = Depends(get_db),
):
    payload = {
        key: (None if value == "" else value)
        for key, value in (await _payload(request)).items()
    }
    try:
        update = RemediationUpdate.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(422, detail=exc.errors()) from exc
    report = _get_report(assessment_id, db)
    item = (
        db.query(GapItem)
        .filter(GapItem.id == item_id, GapItem.report_id == report.id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Gap item not found")

    fields = update.model_fields_set
    if "remediation_status" in fields:
        item.remediation_status = update.remediation_status or "open"
        if item.remediation_status == "closed":
            item.remediation_closed_at = item.remediation_closed_at or datetime.now(timezone.utc)
        else:
            item.remediation_closed_at = None
    if "remediation_owner" in fields:
        item.remediation_owner = update.remediation_owner
    if "remediation_target_date" in fields:
        item.remediation_target_date = update.remediation_target_date
    if "remediation_notes" in fields:
        item.remediation_notes = update.remediation_notes

    db.commit()
    db.refresh(item)

    if _panel_template.exists():
        rendered = _templates.TemplateResponse(
            request=request,
            name="partials/remediation_panel.html",
            context={"item": item, "assessment_id": assessment_id},
        )
        return _toast(rendered, "Remediation updated")

    return _toast(
        JSONResponse(
            {
                "item_id": item.id,
                "remediation_status": item.remediation_status or "open",
                "remediation_owner": item.remediation_owner,
                "remediation_target_date": (
                    item.remediation_target_date.isoformat()
                    if item.remediation_target_date
                    else None
                ),
                "remediation_notes": item.remediation_notes,
                "remediation_closed_at": (
                    item.remediation_closed_at.isoformat()
                    if item.remediation_closed_at
                    else None
                ),
            }
        ),
        "Remediation updated",
    )


@router.get("/{assessment_id}/remediation-summary")
def get_remediation_summary(
    request: Request,
    assessment_id: str,
    db: Session = Depends(get_db),
):
    report = _get_report(assessment_id, db)
    items = db.query(GapItem).filter(GapItem.report_id == report.id).all()

    counts = {"open": 0, "in_progress": 0, "closed": 0, "accepted_risk": 0}
    for item in items:
        status = item.remediation_status or "open"
        if status in counts:
            counts[status] += 1
    counts["total"] = len(items)

    summary = RemediationSummary(**counts)
    if _summary_template.exists():
        return _templates.TemplateResponse(
            request=request,
            name="partials/remediation_summary.html",
            context={
                "assessment_id": assessment_id,
                "remediation_counts": summary.model_dump(),
            },
        )
    return summary
