"""Framework-aware document-category vocabulary."""

from __future__ import annotations

from collections.abc import Sequence

from app.frameworks.registry import FrameworkRegistry
from app.schemas.assessment import DocumentCategory

OTHER_CATEGORY = "other"
LEGACY_UPLOAD_CATEGORIES = tuple(category.value for category in DocumentCategory)
DPDPA_DOCUMENT_TYPES = (
    "privacy_policy",
    "consent_forms",
    "retention_policy",
    "breach_procedure",
    "grievance_mechanism",
    "security_policy",
    "data_flow_diagram",
    "vendor_agreements",
    "cross_border_safeguards",
    "age_verification",
    "parental_consent",
    "dpo_appointment",
    "dpia_reports",
    "audit_reports",
    "hr_privacy_notices",
)


def document_categories(framework_ids: Sequence[str]) -> tuple[str, ...]:
    categories: list[str] = [
        category for category in LEGACY_UPLOAD_CATEGORIES if category != OTHER_CATEGORY
    ]
    for framework_id in framework_ids:
        if framework_id == "dpdpa":
            values = DPDPA_DOCUMENT_TYPES
        else:
            values = tuple(
                request.document_type
                for request in FrameworkRegistry.get(framework_id).evidence_requests
            )
        for value in values:
            if value not in categories and value != OTHER_CATEGORY:
                categories.append(value)
    categories.append(OTHER_CATEGORY)
    return tuple(categories)
