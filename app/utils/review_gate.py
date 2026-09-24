from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.report import GapReport
from app.services.scoring import failed_framework_ids, report_framework_scores

RELEASE_BLOCKED_MESSAGE = "Analysis failed for {names}. Run analysis again before releasing this report."


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
    report = (
        db.query(GapReport)
        .filter(GapReport.assessment_id == assessment_id)
        .first()
    )
    if report:
        failed = failed_framework_ids(
            report_framework_scores(report, assessment),
            assessment.frameworks,
        )
        if failed:
            from app.frameworks.registry import FrameworkRegistry

            names = ", ".join(FrameworkRegistry.get(framework_id).name for framework_id in failed)
            raise HTTPException(409, RELEASE_BLOCKED_MESSAGE.format(names=names))
    return assessment
