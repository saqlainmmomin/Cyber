"""Integrated engagement report snapshot endpoints."""

import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assessment import Assessment
from app.models.client import Client
from app.models.engagement import Engagement
from app.services import conclusion_review, report_content, report_snapshots
from app.utils import pdf_export

router = APIRouter(prefix="/api/engagements", tags=["integrated-reports"])

NO_INCLUDED = (
    "No assessment in this engagement is approved for release with a report. "
    "Nothing was generated."
)
INTEGRATED_NOT_RELEASABLE = (
    "Every assessment in this version must still be approved for release before "
    "it can be issued."
)


def _error(status_code: int, message: str) -> JSONResponse:
    response = JSONResponse({"detail": message}, status_code=status_code)
    response.headers["X-Toast-Message"] = quote(message)
    response.headers["X-Toast-Type"] = "error"
    return response


def _success(snapshot, engagement_id: str, message: str) -> JSONResponse:
    response = JSONResponse(
        {
            "snapshot_id": snapshot.id,
            "type": snapshot.type,
            "is_issued": snapshot.is_issued,
        }
    )
    response.headers["HX-Redirect"] = (
        f"/engagements/{engagement_id}/integrated-reports"
    )
    response.headers["X-Toast-Message"] = message
    response.headers["X-Toast-Type"] = "success"
    return response


@router.post("/{engagement_id}/integrated-reports")
def generate_integrated_report(
    engagement_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        db.rollback()
        return _error(404, "Engagement not found")

    data = report_content.integrated_report(db, engagement)
    if not data.sections:
        db.rollback()
        return _error(400, NO_INCLUDED)
    content = pdf_export.generate_integrated_pdf(data)
    try:
        snapshot = report_snapshots.create_engagement_snapshot(
            db,
            engagement=engagement,
            content=content,
            actor=conclusion_review.reviewer_actor(reviewer_name),
            source=data.source,
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
    return _success(snapshot, engagement_id, "Draft version generated")


@router.post("/{engagement_id}/integrated-reports/{snapshot_id}/issue")
def issue_integrated_report(
    engagement_id: str,
    snapshot_id: str,
    reviewer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        db.rollback()
        return _error(404, "Engagement not found")
    try:
        snapshot = report_snapshots.load_engagement_snapshot(
            db,
            engagement_id=engagement_id,
            snapshot_id=snapshot_id,
        )
        generated = report_snapshots.generated_event(db, snapshot.id)
        source = generated.get("source") or {}
        for source_assessment in source.get("assessments", []):
            assessment = db.get(Assessment, source_assessment.get("assessment_id"))
            if assessment is None or assessment.review_status != "approved":
                db.rollback()
                return _error(403, INTEGRATED_NOT_RELEASABLE)
        snapshot = report_snapshots.issue_snapshot(
            db,
            snapshot,
            actor=conclusion_review.reviewer_actor(reviewer_name),
        )
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)

    try:
        db.commit()
    except Exception:
        db.rollback()
        return _error(500, "The report version could not be saved. Try again.")
    return _success(snapshot, engagement_id, "Version issued")


@router.get("/{engagement_id}/integrated-reports/{snapshot_id}/file")
def integrated_report_file(
    engagement_id: str,
    snapshot_id: str,
    db: Session = Depends(get_db),
):
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        db.rollback()
        return _error(404, "Engagement not found")
    client = db.get(Client, engagement.client_id)
    if client is None:
        db.rollback()
        return _error(404, "Client not found")
    try:
        snapshot = report_snapshots.load_engagement_snapshot(
            db,
            engagement_id=engagement_id,
            snapshot_id=snapshot_id,
        )
        content = report_snapshots.read_snapshot_bytes(db, snapshot)
        metadata = report_snapshots.generated_event(db, snapshot.id)
        row = next(
            row
            for row in report_snapshots.engagement_snapshot_rows(
                db, engagement, current_source=None
            )
            if row.snapshot.id == snapshot.id
        )
    except report_snapshots.SnapshotError as exc:
        db.rollback()
        return _error(exc.status_code, exc.message)

    safe_client = re.sub(r"[^A-Za-z0-9._-]+", "_", client.name).strip("_") or "report"
    headers = {
        "X-Snapshot-Sha256": metadata["sha256"],
        "Content-Disposition": (
            f'attachment; filename="{safe_client}_integrated_report_v'
            f'{row.sequence}_{snapshot.id[:8]}.pdf"'
        ),
    }
    return Response(
        content=content,
        media_type="application/pdf",
        headers=headers,
    )
