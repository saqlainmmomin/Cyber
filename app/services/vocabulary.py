"""Shared user-visible labels, with explicit compatibility labels for pinned exports."""

from __future__ import annotations

from app.frameworks.registry import FrameworkRegistry

_FRAMEWORK_NAME_FALLBACKS = {
    "dpdpa": "India DPDPA",
    "iso27001": "ISO 27001",
    "nist_csf": "NIST CSF",
    "pci_dss": "PCI-DSS",
    "hipaa": "HIPAA",
    "gdpr": "GDPR",
}

OUTCOMES = {
    "compliant": "Compliant",
    "partially_compliant": "Partially compliant",
    "non_compliant": "Non-compliant",
    "insufficient_evidence": "Insufficient evidence",
    "not_applicable": "Not applicable",
}
# Existing PDF table labels are pinned by the DPDPA golden.
OUTCOME_SHORT = {
    "compliant": "Compliant",
    "partially_compliant": "Partial",
    "non_compliant": "Non-Compliant",
    "insufficient_evidence": "Insufficient evidence",
    "not_applicable": "N/A",
    "not_assessed": "N/A",
}
# Board-document and PDF goldens retain their current wording until WP 2.3.
LEGACY_OUTCOMES = {
    "compliant": "Compliant",
    "partially_compliant": "Partially Compliant",
    "non_compliant": "Non-Compliant",
    "insufficient_evidence": "Insufficient Evidence",
    "not_applicable": "Not Applicable",
}
LEGACY_PDF_OUTCOMES = {
    **LEGACY_OUTCOMES,
    "non_compliant": "Non Compliant",
    "not_applicable": "Not Applicable",
    "not_assessed": "Not Assessed",
}
RISK_LEVELS = ("critical", "high", "medium", "low")
RISK_LABELS = dict(zip(RISK_LEVELS, ("Critical", "High", "Medium", "Low")))
RISK_RANK = {key: rank for rank, key in enumerate(RISK_LEVELS)}
PRIORITY_LABELS = {1: "Immediate", 2: "Short-term", 3: "Medium-term", 4: "Long-term"}
LEGACY_PRIORITY_LABELS = {1: "Immediate", 2: "Short-Term", 3: "Medium-Term", 4: "Ongoing"}
REVIEW_STATES = {
    "pending": "Pending",
    "approved": "Approved",
    "edited": "Edited and approved",
    "rejected": "Rejected",
}
REVIEW_ACTION_LABELS = {**REVIEW_STATES, "reopened": "Reopened"}
RELEASE_STATES = {"draft": "Draft", "released": "Released", "issued": "Issued"}
REMEDIATION_STATUSES = {
    "open": "Open",
    "in_progress": "In progress",
    "closed": "Closed and awaiting verification",
    "verified": "Verified",
}
FINDING_STATUS_LABELS = {
    "open": REMEDIATION_STATUSES["open"],
    "in_progress": REMEDIATION_STATUSES["in_progress"],
    "resolved": REMEDIATION_STATUSES["verified"],
    "accepted_risk": "Accepted risk",
}
LEGACY_REMEDIATION_STATUSES = {
    **REMEDIATION_STATUSES,
    "closed": "Closed, awaiting verification",
    "verified": "Closed and verified",
}
LEGACY_FINDING_STATUSES = {**FINDING_STATUS_LABELS, "resolved": "Resolved"}
SCORE_BANDS = ((0, "Not ready"), (40, "Partly ready"), (60, "Mostly ready"), (80, "Ready"))


def _label(labels: dict, key: str | None) -> str:
    return labels.get(key, (key or "").replace("_", " ").capitalize())


def outcome_label(key: str | None) -> str:
    return _label(OUTCOMES, key)


def risk_label(key: str | None) -> str:
    return _label(RISK_LABELS, key)


def priority_label(priority: int | None) -> str:
    return PRIORITY_LABELS.get(priority, "")


def review_label(key: str | None) -> str:
    return _label(REVIEW_ACTION_LABELS, key)


def release_label(key: str | None) -> str:
    return _label(RELEASE_STATES, key)


def remediation_label(key: str | None) -> str:
    return _label(REMEDIATION_STATUSES, key)


def score_band(score: float) -> str:
    """Band the unrounded score; exports switch to these labels in WP 2.3."""
    for threshold, label in reversed(SCORE_BANDS):
        if score >= threshold:
            return label
    return SCORE_BANDS[0][1]


def display_reference(framework_id: str, requirement_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    control = framework.get_control(requirement_id) if framework else None
    return control.reference if control and control.reference else requirement_id


def framework_display_name(framework_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    return framework.name if framework else _FRAMEWORK_NAME_FALLBACKS.get(
        framework_id, framework_id.replace("_", " ").upper()
    )


def reference_with_framework(framework_id: str, requirement_id: str) -> str:
    reference = display_reference(framework_id, requirement_id)
    name = framework_display_name(framework_id)
    return reference if reference.startswith(name) else f"{name} {reference}"
