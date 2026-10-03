"""Shared Client -> Engagement -> Assessment creation service."""

import json

from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.assessment_pack import AssessmentPack
from app.models.client import Client
from app.models.engagement import Engagement


def create_engagement_with_assessment(
    db: Session,
    *,
    client: Client,
    engagement_name: str,
    engagement_type: str,
    description: str | None,
    framework_ids: list[str],
) -> Engagement:
    """Create an engagement hierarchy atomically and return its engagement."""
    try:
        engagement = Engagement(
            client_id=client.id,
            name=engagement_name,
            type=engagement_type,
            status="active",
        )
        db.add(engagement)
        db.flush()
        _add_assessment(
            db,
            engagement=engagement,
            client=client,
            description=description,
            framework_ids=framework_ids,
        )
        db.commit()
        db.refresh(engagement)
        return engagement
    except Exception:
        db.rollback()
        raise


def _add_assessment(
    db: Session,
    *,
    engagement: Engagement,
    client: Client,
    description: str | None,
    framework_ids: list[str],
    name: str | None = None,
) -> Assessment:
    """An assessment in the engagement, inheriting the client's name, industry and size, with its packs."""
    assessment = Assessment(
        company_name=client.name,
        industry=client.industry,
        company_size=client.size,
        name=name or None,
        description=description or None,
        selected_frameworks=json.dumps(framework_ids),
        engagement_id=engagement.id,
    )
    db.add(assessment)
    db.flush()
    for framework_id in framework_ids:
        framework = FrameworkRegistry.get_or_none(framework_id)
        db.add(
            AssessmentPack(
                assessment_id=assessment.id,
                framework_id=framework_id,
                pack_version=framework.pack_version if framework else "unknown",
            )
        )
    return assessment


def add_assessment_to_engagement(
    db: Session,
    *,
    engagement: Engagement,
    client: Client,
    name: str | None,
    description: str | None,
    framework_ids: list[str],
) -> Assessment:
    """Add one more assessment to an existing engagement (Yozora "Add assessment"); commits."""
    try:
        assessment = _add_assessment(
            db,
            engagement=engagement,
            client=client,
            description=description,
            framework_ids=framework_ids,
            name=name,
        )
        db.commit()
        db.refresh(assessment)
        return assessment
    except Exception:
        db.rollback()
        raise
