"""Recover database rows interrupted by a process restart."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app import database
from app.models.analysis_run import AnalysisRun
from app.models.assessment import Assessment
from app.models.desk_review import DeskReviewSummary
from app.services.run_state import mark_run_failed

logger = logging.getLogger(__name__)

_DESK_REVIEW_INTERRUPTED_MESSAGE = (
    "Desk review was interrupted by a restart. Run desk review again."
)


def recover_interrupted_work() -> dict[str, int]:
    """Fail interrupted work for the single-process local deployment.

    This assumes a single-process deployment. With multiple workers, one
    worker's startup could fail another worker's live run. That is acceptable
    for local-only use and will be revisited when real job infrastructure
    arrives in Track 4.
    """
    counts = {
        "analysis_runs": 0,
        "assessments": 0,
        "desk_review_assessments": 0,
        "desk_review_summaries": 0,
    }
    db = database.SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for run in db.scalars(
            select(AnalysisRun).where(AnalysisRun.status == "running")
        ).all():
            mark_run_failed(run, error_type="Interrupted", completed_at=now)
            counts["analysis_runs"] += 1

        for assessment in db.scalars(
            select(Assessment).where(Assessment.status == "analyzing")
        ).all():
            assessment.status = "error"
            counts["assessments"] += 1

        for assessment in db.scalars(
            select(Assessment).where(Assessment.desk_review_status == "analyzing")
        ).all():
            assessment.desk_review_status = "error"
            counts["desk_review_assessments"] += 1

        for summary in db.scalars(
            select(DeskReviewSummary).where(DeskReviewSummary.status == "analyzing")
        ).all():
            summary.status = "error"
            summary.error_message = _DESK_REVIEW_INTERRUPTED_MESSAGE
            counts["desk_review_summaries"] += 1

        db.commit()
        logger.info(
            "Recovered interrupted work: analysis_runs=%d assessments=%d "
            "desk_review_assessments=%d desk_review_summaries=%d",
            counts["analysis_runs"],
            counts["assessments"],
            counts["desk_review_assessments"],
            counts["desk_review_summaries"],
        )
        return counts
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
