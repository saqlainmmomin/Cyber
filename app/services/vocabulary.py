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
# The one numeric map: each risk level has its own timeframe, one to one. Priority is when to act.
PRIORITY_BY_RISK = {key: rank + 1 for key, rank in RISK_RANK.items()}
PRIORITY_LABELS = {1: "Immediate", 2: "Short-term", 3: "Medium-term", 4: "Long-term"}
PRIORITY_WINDOWS = {1: "0-4 weeks", 2: "1-3 months", 3: "3-6 months", 4: "6-12 months"}
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
    """Return the readiness band for the unrounded score."""
    for threshold, label in reversed(SCORE_BANDS):
        if score >= threshold:
            return label
    return SCORE_BANDS[0][1]


def display_reference(framework_id: str, requirement_id: str) -> str:
    return section_reference(framework_id, requirement_id)


def section_reference(
    framework_id: str, requirement_id: str, *, include_framework: bool = False
) -> str:
    """Resolve a control reference, preserving each screen's framework prefix."""
    framework = FrameworkRegistry.get_or_none(framework_id)
    control = framework.get_control(requirement_id) if framework else None
    reference = control.reference if control and control.reference else requirement_id
    if not include_framework:
        return reference
    name = framework_display_name(framework_id)
    return reference if reference.startswith(name) else f"{name} {reference}"


def framework_display_name(framework_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    return framework.name if framework else _FRAMEWORK_NAME_FALLBACKS.get(
        framework_id, framework_id.replace("_", " ").upper()
    )


def reference_with_framework(framework_id: str, requirement_id: str) -> str:
    return section_reference(framework_id, requirement_id, include_framework=True)


def upload_category_label(category: str) -> str:
    """Use registry labels while retaining unknown stored category strings."""
    for framework_id in FrameworkRegistry.all_ids():
        for request in FrameworkRegistry.get(framework_id).evidence_requests:
            if request.document_type == category:
                return request.label
    return category


READINESS_TARGETS = {
    "dpdpa": "Readiness for DPDP Act obligations",
    "iso27001": "Readiness for ISO 27001 certification",
    "nist_csf": "Readiness against NIST CSF 2.0 target profile",
    "gdpr": "Readiness for GDPR obligations",
    "hipaa": "Readiness for HIPAA Security Rule safeguards",
    "pci_dss": "Readiness for PCI DSS v4.0 assessment",
}


def score_text(score: float | None) -> str:
    return "Not scored" if score is None else f"{score:.1f}%"


def readiness_headline(framework_id: str, score: float, critical: int, high: int) -> str:
    gaps = (
        "No critical or high gaps open."
        if critical + high == 0
        else f"{critical} critical and {high} high {'gap' if critical + high == 1 else 'gaps'} open."
    )
    return f"{READINESS_TARGETS[framework_id]}: {score_band(score)} ({score_text(score)}). {gaps}"


def score_threshold_lines() -> tuple[str, ...]:
    lines = []
    for index in range(len(SCORE_BANDS) - 1, -1, -1):
        threshold, label = SCORE_BANDS[index]
        if index == len(SCORE_BANDS) - 1:
            span = f"{threshold}% and above"
        elif index == 0:
            span = f"below {SCORE_BANDS[index + 1][0]}%"
        else:
            span = f"{threshold}% to below {SCORE_BANDS[index + 1][0]}%"
        lines.append(f"{label}: {span}.")
    return tuple(lines)


SCORE_DISPLAY_NOTE = "The band uses the exact score; scores are shown to one decimal."


def score_threshold_text() -> str:
    return " ".join(score_threshold_lines()) + " " + SCORE_DISPLAY_NOTE
