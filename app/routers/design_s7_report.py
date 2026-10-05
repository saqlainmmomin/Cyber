"""S7 report preview states backed by the live assessment report template."""

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.routers import design


def _report_loading(request: Request, db: Session):
    from app.routers.web import render_assessment_detail

    assessment_id = request.query_params.get("assessment_id")
    if not assessment_id:
        raise HTTPException(status_code=404, detail="Not found")
    path = f"/assessments/{assessment_id}"
    live_request = Request(dict(request.scope, path=path, raw_path=path.encode()), request.receive)
    return render_assessment_detail(live_request, db, assessment_id, tab="report", preview_state="loading")


design.PREVIEW_PAGES["b5-report-loading"] = _report_loading
design.DB_PREVIEWS.add("b5-report-loading")
