"""Assessment report snapshot endpoints."""

import re
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.routers import reports
from app.services import (
    board_report,
    report_snapshots,
    rfi_requests,
    standalone_workpaper,
)
from app.services.conclusion_review import reviewer_actor
from app.services import approved_report
from app.utils import html_pdf
from app.utils.review_gate import require_review_approval

router = APIRouter(prefix="/api/assessments", tags=["snapshots"])

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


def _rfi_success(snapshot, assessment_id: str, message: str) -> JSONResponse:
    response = JSONResponse(
        {
            "snapshot_id": snapshot.id,
            "type": snapshot.type,
            "is_issued": snapshot.is_issued,
        },
        status_code=200,
    )
    response.headers["HX-Redirect"] = f"/assessments/{assessment_id}/rfi"
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
    return standalone_workpaper.render(db, assessment).encode("utf-8")


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

    snapshot = None
    try:
        if type == report_snapshots.BOARD_REPORT_SNAPSHOT_TYPE:
            snapshot = board_report.generate_version(
                db,
                assessment,
                actor=reviewer_actor(reviewer_name),
            )
        else:
            content = _render(db, assessment, type)
            snapshot = report_snapshots.create_snapshot(
                db,
                assessment=assessment,
                snapshot_type=type,
                content=content,
                actor=reviewer_actor(reviewer_name),
            )
    except HTTPException as exc:
        db.rollback()
        return _error(exc.status_code, str(exc.detail))
    except html_pdf.RendererUnavailable as exc:
        db.rollback()
        return _error(503, exc.message)
    except html_pdf.OfflineRenderError as exc:
        db.rollback()
        return _error(500, exc.message)
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)

    try:
        db.commit()
    except Exception:
        db.rollback()
        if snapshot is not None:
            for path in report_snapshots.snapshot_files(snapshot):
                path.unlink(missing_ok=True)
        return _error(500, "The report version could not be saved. Try again.")
    return _success(snapshot, assessment_id, "Draft version generated")


@router.get(
    "/{assessment_id}/board-report/preview",
    response_class=HTMLResponse,
)
def board_report_preview(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Assessment not found")
    require_review_approval(assessment_id, db)
    document = board_report.build_document(
        db,
        assessment,
        snapshot_id=None,
        version_label=board_report.PREVIEW_VERSION_LABEL,
        generated_at=datetime.now(timezone.utc),
    )
    db.rollback()
    return HTMLResponse(board_report.render_html(document, embed_fonts=False))


@router.post("/{assessment_id}/rfi/versions")
def generate_rfi_version(
    assessment_id: str,
    omit: list[str] = Form(default=[]),
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        db.rollback()
        return _error(404, "Assessment not found")
    snapshot = None
    try:
        snapshot = rfi_requests.generate_version(
            db,
            assessment,
            omitted=omit,
            actor=reviewer_actor(reviewer_name),
        )
    except rfi_requests.RfiError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    try:
        db.commit()
    except Exception:
        db.rollback()
        if snapshot is not None:
            getattr(report_snapshots.snapshot_path(snapshot), "unlink")(missing_ok=True)
            getattr(report_snapshots.rfi_document_path(snapshot), "unlink")(missing_ok=True)
        return _error(500, "The report version could not be saved. Try again.")
    return _rfi_success(snapshot, assessment_id, "Draft RFI version generated")


@router.post("/{assessment_id}/rfi/versions/{snapshot_id}/issue")
def issue_rfi_version(
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
        snapshot = rfi_requests.issue_version(
            db,
            assessment,
            snapshot_id,
            actor=reviewer_actor(reviewer_name),
        )
        db.commit()
    except rfi_requests.RfiError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    except Exception:
        db.rollback()
        return _error(500, "The report version could not be saved. Try again.")
    return _rfi_success(snapshot, assessment_id, "RFI version issued")


@router.get("/{assessment_id}/rfi/versions/{snapshot_id}/docx")
def rfi_version_docx(
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
        document = report_snapshots.read_rfi_document(db, snapshot)
        row = next(
            row
            for row in report_snapshots.rfi_snapshot_rows(
                db,
                assessment,
                current_source=None,
            )
            if row.snapshot.id == snapshot.id
        )
        content = rfi_requests.render_docx(
            document,
            generated_at=snapshot.generated_at,
            version_label=f"v{row.sequence}",
        )
        metadata = report_snapshots.generated_event(db, snapshot.id)
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)
    except StopIteration:
        db.rollback()
        return _error(404, rfi_requests.RFI_NOT_FOUND_MESSAGE)

    safe_company = re.sub(
        r"[^A-Za-z0-9._-]+", "_", assessment.company_name
    ).strip("_") or "report"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_company}_rfi_v{row.sequence}_'
                f'{snapshot.id[:8]}.docx"'
            ),
            "X-RFI-Document-Sha256": metadata["document_sha256"],
        },
    )


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
        if snapshot.type == report_snapshots.RFI_SNAPSHOT_TYPE:
            db.rollback()
            return _error(400, rfi_requests.RFI_WRONG_ROUTE_MESSAGE)
        require_review_approval(assessment_id, db)
        release_event = approved_report.latest_release_event(db, assessment_id)
        if release_event is None or not report_snapshots.generated_after(
            db, snapshot.id, release_event.id
        ):
            raise report_snapshots.SnapshotNotIssuable(
                report_snapshots.SNAPSHOT_STALE_MESSAGE
            )
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
        rows = (
            report_snapshots.rfi_snapshot_rows(db, assessment, current_source=None)
            if snapshot.type == report_snapshots.RFI_SNAPSHOT_TYPE
            else report_snapshots.snapshot_rows(db, assessment)[snapshot.type]
        )
        row = next(row for row in rows if row.snapshot.id == snapshot.id)
        headers["Content-Disposition"] = (
            f'attachment; filename="{safe_company}_{snapshot.type}_v{row.sequence}_'
            f'{snapshot.id[:8]}.pdf"'
        )
    return Response(
        content=content,
        media_type=report_snapshots.MEDIA_TYPES[snapshot.format],
        headers=headers,
    )
