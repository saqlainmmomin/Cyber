"""S8 versions-group previews backed by the live report page templates."""

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.routers import design

PREVIOUS_ASSESSMENT_ID = "assessment-s8-previous"


def _live_request(request: Request, path: str) -> Request:
    return Request(dict(request.scope, path=path, raw_path=path.encode()), request.receive)


def _snapshots_preview(request: Request, db: Session):
    from app.routers.web import snapshots_page

    assessment_id = request.query_params.get("assessment_id")
    if not assessment_id:
        raise HTTPException(status_code=404, detail="Pass ?assessment_id=<id>")
    return snapshots_page(
        _live_request(request, "/design/pages/b6-report_snapshots"),
        assessment_id,
        db,
    )


def _soa_preview(request: Request, db: Session):
    from app.routers.soa import soa_page

    assessment_id = request.query_params.get("assessment_id")
    if not assessment_id:
        raise HTTPException(status_code=404, detail="Pass ?assessment_id=<id>")
    return soa_page(
        assessment_id,
        _live_request(request, "/design/pages/b6-soa"),
        db,
    )


def _comparison_preview(request: Request, db: Session):
    from app.routers.web import comparison_page

    assessment_id = request.query_params.get("assessment_id")
    if not assessment_id:
        raise HTTPException(status_code=404, detail="Pass ?assessment_id=<id>")
    return comparison_page(
        _live_request(request, "/design/pages/b6-comparison"),
        assessment_id,
        PREVIOUS_ASSESSMENT_ID,
        db,
    )


def _load_s8_preview(name, handler):
    design.PREVIEW_PAGES[name] = handler


for _name, _handler in {
    "b6-report_snapshots": _snapshots_preview,
    "b6-soa": _soa_preview,
    "b6-comparison": _comparison_preview,
}.items():
    _load_s8_preview(_name, _handler)
design.DB_PREVIEWS.update({"b6-report_snapshots", "b6-soa", "b6-comparison"})
