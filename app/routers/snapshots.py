"""Assessment report snapshot endpoints."""

from pathlib import Path
import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.routers import reports
from app.services import report_snapshots, workpaper
from app.services.conclusion_review import reviewer_actor
from app.template_config import configure_templates
from app.utils.review_gate import require_review_approval

router = APIRouter(prefix="/api/assessments", tags=["snapshots"])

_templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)
configure_templates(_templates)


def _error(status_code: int, message: str) -> JSONResponse:
    response = JSONResponse({"detail": message}, status_code=status_code)
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = "error"
    return response


def _success(snapshot, assessment_id: str, message: str) -> JSONResponse:
    response = JSONResponse(
        {
            "snapshot_id": snapshot.id,
            "type": snapshot.type,
            "is_issued": snapshot.is_issued,
        },
        status_code=200,
    )
    response.headers["HX-Redirect"] = f"/assessments/{assessment_id}/snapshots"
    response.headers["X-Toast-Message"] = message
    response.headers["X-Toast-Type"] = "success"
    return response


def _render(db: Session, assessment: Assessment, snapshot_type: str) -> bytes:
    if snapshot_type == "gap_report":
        response = reports._download_pdf_response(
            assessment_id=assessment.id,
            db=db,
            allow_failed_draft=True,
        )
        return bytes(response.body)
    wp = workpaper.build_workpaper(db, assessment)
    return (
        _templates.get_template("pages/workpaper.html")
        .render(assessment=assessment, wp=wp)
        .encode("utf-8")
    )


@router.post("/{assessment_id}/snapshots")
def generate_snapshot(
    assessment_id: str,
    type: str = Form(""),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    if not type:
        db.rollback()
        return _error(400, "Choose a report type to generate.")
    if type not in report_snapshots.SNAPSHOT_TYPES:
        db.rollback()
        return _error(400, "Unknown report type.")
    if type == "integrated_report":
        db.rollback()
        return _error(400, "Integrated engagement reports are not available yet.")

    try:
        content = _render(db, assessment, type)
    except HTTPException as exc:
        db.rollback()
        return _error(exc.status_code, str(exc.detail))

    try:
        snapshot = report_snapshots.create_snapshot(
            db,
            assessment=assessment,
            snapshot_type=type,
            content=content,
            actor=reviewer_actor(reviewer_name),
        )
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)

    try:
        db.commit()
    except Exception:
        db.rollback()
        report_snapshots.snapshot_path(snapshot).unlink(missing_ok=True)
        return _error(500, "The report version could not be saved. Try again.")
    return _success(snapshot, assessment_id, "Draft version generated")


@router.post("/{assessment_id}/snapshots/{snapshot_id}/issue")
def issue_snapshot_route(
    assessment_id: str,
    snapshot_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    try:
        snapshot = report_snapshots.load_snapshot(
            db,
            assessment_id=assessment_id,
            snapshot_id=snapshot_id,
        )
        require_review_approval(assessment_id, db)
        snapshot = report_snapshots.issue_snapshot(
            db,
            snapshot,
            actor=reviewer_actor(reviewer_name),
        )
    except HTTPException as exc:
        db.rollback()
        return _error(exc.status_code, str(exc.detail))
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    db.commit()
    return _success(snapshot, assessment_id, "Version issued")


@router.get("/{assessment_id}/snapshots/{snapshot_id}/file")
def snapshot_file_route(
    assessment_id: str,
    snapshot_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    try:
        snapshot = report_snapshots.load_snapshot(
            db,
            assessment_id=assessment_id,
            snapshot_id=snapshot_id,
        )
        content = report_snapshots.read_snapshot_bytes(db, snapshot)
        metadata = report_snapshots.generated_event(db, snapshot.id)
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)

    headers = {"X-Snapshot-Sha256": metadata["sha256"]}
    if snapshot.format == "pdf":
        safe_company = re.sub(
            r"[^A-Za-z0-9._-]+", "_", assessment.company_name
        ).strip("_") or "report"
        row = next(
            row
            for row in report_snapshots.snapshot_rows(db, assessment)[snapshot.type]
            if row.snapshot.id == snapshot.id
        )
        headers["Content-Disposition"] = (
            f'attachment; filename="{safe_company}_{snapshot.type}_v{row.sequence}_'
            f'{snapshot.id[:8]}.pdf"'
        )
    return Response(
        content=content,
        media_type=report_snapshots.MEDIA_TYPES[snapshot.format],
        headers=headers,
    )
