from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.assessment import Assessment


def require_review_approval(assessment_id: str, db: Session) -> Assessment:
    """Require manager approval before releasing downloadable output."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, "Assessment not found")
    if assessment.review_status != "approved":
        raise HTTPException(
            403,
            "Report not yet approved for release. Complete the review process first.",
        )
    return assessment
