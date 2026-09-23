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
        assessment = Assessment(
            company_name=client.name,
            industry=client.industry,
            company_size=client.size,
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
                    pack_version=framework.version if framework else "unknown",
                )
            )
        db.commit()
        db.refresh(engagement)
        return engagement
    except Exception:
        db.rollback()
        raise
