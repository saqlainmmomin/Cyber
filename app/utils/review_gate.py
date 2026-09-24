from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.services.approved_report import (
    NOT_RELEASED_MESSAGE,
    RELEASE_BLOCKED_MESSAGE,
    build_approved_report,
)


def require_review_approval(assessment_id: str, db: Session) -> Assessment:
    """Require an active consultant release before serving client output."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    approved = build_approved_report(db, assessment)
    if approved.report_id is None:
        raise HTTPException(404, "No report found. Run analysis first.")

    failed_names = [
        review.name
        for review in approved.framework_reviews.values()
        if review.status == "failed"
    ]
    if failed_names:
        raise HTTPException(
            409,
            RELEASE_BLOCKED_MESSAGE.format(names=", ".join(failed_names)),
        )
    if not approved.release.released:
        raise HTTPException(403, NOT_RELEASED_MESSAGE)
    return assessment
