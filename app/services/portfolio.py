"""Pure helpers for the Client -> Engagement portfolio views."""

from collections.abc import Sequence
from datetime import datetime


STAGE_RANK = {
    "created": 0,
    "scoped": 1,
    "documents_uploaded": 2,
    "context_gathered": 3,
    "questionnaire_done": 4,
    "analyzing": 5,
    "completed": 6,
}
STAGE_RANK_MAX = 6

_STATUS_LABELS = {
    "empty": "No assessments",
    "error": "Error",
    "completed": "Completed",
    "analyzing": "Analyzing…",
    "created": "New",
    "scoped": "Scoped",
    "documents_uploaded": "Documents Uploaded",
    "context_gathered": "Context Gathered",
    "questionnaire_done": "Questionnaire Done",
}


def derive_status(assessments) -> str:
    """Derive an engagement status from its non-archived assessments."""
    if not assessments:
        return "empty"
    if any(assessment.status == "error" for assessment in assessments):
        return "error"
    if all(assessment.status == "completed" for assessment in assessments):
        return "completed"
    if any(assessment.status == "analyzing" for assessment in assessments):
        return "analyzing"
    return min(
        assessments,
        key=lambda assessment: STAGE_RANK.get(assessment.status, 0),
    ).status


def derive_progress_pct(assessments) -> int:
    """Return the stage-weighted average progress for an engagement."""
    if not assessments:
        return 0
    return round(
        100
        * sum(STAGE_RANK.get(assessment.status, 0) for assessment in assessments)
        / (STAGE_RANK_MAX * len(assessments))
    )


def derive_last_activity(assessments, fallback: datetime) -> datetime:
    """Return the latest assessment activity, or the owning row's timestamp."""
    if not assessments:
        return fallback
    return max(assessment.updated_at for assessment in assessments)


def framework_badges(framework_ids: Sequence[str]) -> list[dict[str, str]]:
    """Resolve framework display metadata without requiring a registered id."""
    from app.frameworks.registry import FrameworkRegistry

    badges = []
    for framework_id in framework_ids:
        framework = FrameworkRegistry.get_or_none(framework_id)
        badges.append(
            {
                "id": framework_id,
                "name": framework.name if framework else framework_id.upper(),
                "version": framework.version if framework else "",
            }
        )
    return badges


def engagement_status_label(status: str) -> str:
    """Return the label shared by the engagement status badge and card context."""
    return _STATUS_LABELS.get(status, status.replace("_", " ").title())


def build_engagement_card(engagement, assessments) -> dict:
    """Build the template-safe engagement card contract."""
    active_assessments = [
        assessment for assessment in assessments if assessment.status != "archived"
    ]
    framework_ids = []
    seen_framework_ids = set()
    for assessment in active_assessments:
        for framework_id in assessment.frameworks:
            if framework_id not in seen_framework_ids:
                seen_framework_ids.add(framework_id)
                framework_ids.append(framework_id)

    derived_status = derive_status(active_assessments)
    return {
        "id": engagement.id,
        "name": engagement.name,
        "type": engagement.type,
        "status": engagement.status,
        "derived_status": derived_status,
        "derived_status_label": engagement_status_label(derived_status),
        "progress_pct": derive_progress_pct(active_assessments),
        "assessment_count": len(active_assessments),
        "framework_ids": framework_ids,
        "framework_badges": framework_badges(framework_ids),
        "last_activity": derive_last_activity(active_assessments, engagement.updated_at),
    }


def build_client_card(client, engagements: Sequence[dict]) -> dict:
    """Build the template-safe client card contract."""
    sorted_engagements = sorted(
        engagements,
        key=lambda engagement: engagement["last_activity"],
        reverse=True,
    )
    return {
        "id": client.id,
        "name": client.name,
        "industry": client.industry,
        "size": client.size,
        "retention_years": client.retention_years,
        "engagement_count": len(sorted_engagements),
        "last_activity": max(
            (engagement["last_activity"] for engagement in sorted_engagements),
            default=client.updated_at,
        ),
        "engagements": sorted_engagements,
    }
