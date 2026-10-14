"""Stored gap-report fixtures for a retired snapshot creation path."""

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.report_snapshot import ReportSnapshot
from app.routers import reports
from app.services import report_snapshots
from app.services.conclusion_review import reviewer_actor


def stored_gap_snapshot(
    db: Session, assessment: Assessment, *, reviewer: str = "Priya"
) -> ReportSnapshot:
    """Capture legacy gap bytes through the existing renderer and storage service."""
    response = reports._download_pdf_response(
        assessment_id=assessment.id, db=db, allow_failed_draft=True
    )
    snapshot = report_snapshots.create_snapshot(
        db,
        assessment=assessment,
        snapshot_type="gap_report",
        content=bytes(response.body),
        actor=reviewer_actor(reviewer),
    )
    db.commit()
    return snapshot
