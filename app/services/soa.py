"""ISO 27001 Statement of Applicability data and justification history."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.services import approved_report, conclusion_review


FRAMEWORK_ID = "iso27001"
AUDIT_ENTITY_TYPE = "assessment"
AUDIT_ACTION = "assessment.soa_justification_updated"
JUSTIFICATION_MAX_CHARS = 1000
APPLICABILITY_LABELS = {
    "applicable": "Applicable",
    "excluded": "Excluded",
    "not_assessed": "Not determined",
    "pending": "Awaiting decision",
}
IMPLEMENTATION_LABELS = {
    "compliant": "Implemented",
    "partially_compliant": "Partially implemented",
    "non_compliant": "Not implemented",
    "insufficient_evidence": "Not determined: insufficient evidence",
    "not_applicable": "Not applicable",
}
NOT_ASSESSED_LABEL = "Not assessed: outside the assessment scope"
PENDING_LABEL = "Not determined: awaiting consultant decision"
INTRO_TEXT = (
    "Every Annex A control of {framework}, with its applicability, implementation status and "
    "justification. Applicability and implementation status are derived from the consultant-approved "
    "conclusion for each control; justifications are recorded by the consultant."
)
RELIANCE_TEXT = (
    "This statement records the assessor's view at the evidence cut-off. It does not replace the "
    "organization's own Statement of Applicability."
)
NOT_ASSESSED_NOTE = (
    "{count} Annex A control(s) were outside the scope of this assessment. Their applicability has "
    "not been determined; the organization must decide it before relying on this statement."
)
MISSING_JUSTIFICATION_NOTE = "{count} control(s) have no recorded justification."
NOT_IN_SCOPE_MESSAGE = "ISO 27001 is not in scope for this assessment."
UNKNOWN_CONTROL_MESSAGE = "That control is not an ISO 27001 Annex A control."
TOO_LONG_MESSAGE = f"Keep the justification to {JUSTIFICATION_MAX_CHARS} characters or fewer."
SAVED_MESSAGE = "Justification saved"
TOTAL_KEYS = (
    "controls",
    "applicable",
    "excluded",
    "not_assessed",
    "pending",
    "implemented",
    "partially_implemented",
    "not_implemented",
    "not_determined",
    "justification_missing",
)


class SoAError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class Justification:
    text: str
    recorded_by: str
    recorded_at: datetime


def applies(framework_ids) -> bool:
    return FRAMEWORK_ID in framework_ids


def _metadata(event: AuditEvent) -> dict | None:
    try:
        metadata = json.loads(event.metadata_json or "")
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(metadata, dict) or metadata.get("framework_id") != FRAMEWORK_ID:
        return None
    requirement_id = metadata.get("requirement_id")
    after = metadata.get("after")
    if not isinstance(requirement_id, str) or (after is not None and not isinstance(after, str)):
        return None
    return metadata


def current_justifications(db: Session, assessment: Assessment) -> dict[str, Justification]:
    events = db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.action == AUDIT_ACTION,
            AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
            AuditEvent.entity_id == assessment.id,
        )
        .order_by(AuditEvent.created_at, literal_column("audit_events.rowid"))
    ).scalars().all()
    current: dict[str, Justification] = {}
    for event in events:
        metadata = _metadata(event)
        if metadata is None:
            continue
        requirement_id = metadata["requirement_id"]
        after = metadata["after"]
        if after is None:
            current.pop(requirement_id, None)
        else:
            current[requirement_id] = Justification(
                text=after,
                recorded_by=event.actor.removeprefix(conclusion_review.REVIEWER_ACTOR_PREFIX),
                recorded_at=event.created_at,
            )
    return current


def record_justification(
    db: Session,
    assessment: Assessment,
    *,
    requirement_id: str,
    justification: str | None,
    actor: str,
) -> str | None:
    if not applies(assessment.frameworks):
        raise SoAError(NOT_IN_SCOPE_MESSAGE, status_code=404)
    if FrameworkRegistry.get(FRAMEWORK_ID).get_control(requirement_id) is None:
        raise SoAError(UNKNOWN_CONTROL_MESSAGE)

    cleaned = re.sub(r"\s+", " ", justification or "").strip()
    value = cleaned or None
    if value is not None and len(value) > JUSTIFICATION_MAX_CHARS:
        raise SoAError(TOO_LONG_MESSAGE)

    current = current_justifications(db, assessment).get(requirement_id)
    before = current.text if current else None
    if before == value:
        return value

    db.add(
        AuditEvent(
            actor=actor,
            action=AUDIT_ACTION,
            entity_type=AUDIT_ENTITY_TYPE,
            entity_id=assessment.id,
            metadata_json=json.dumps(
                {
                    "framework_id": FRAMEWORK_ID,
                    "requirement_id": requirement_id,
                    "before": before,
                    "after": value,
                },
                sort_keys=True,
            ),
        )
    )
    db.flush()
    return value


def build_soa(
    db: Session,
    assessment: Assessment,
    approved: approved_report.ApprovedReport,
) -> dict | None:
    if not applies(assessment.frameworks):
        return None

    framework = FrameworkRegistry.get(FRAMEWORK_ID)
    review = approved.framework_reviews[FRAMEWORK_ID]
    approved_rows = {row.requirement_id: row for row in review.rows}
    justifications = current_justifications(db, assessment)
    rows = []
    for domain in framework.domains.values():
        for section in domain.sections.values():
            for control in section.controls:
                justification = justifications.get(control.id)
                approved_row = approved_rows.get(control.id)
                if control.id not in review.in_scope_ids:
                    applicability = "not_assessed"
                    outcome = None
                    implementation_label = NOT_ASSESSED_LABEL
                elif approved_row is None:
                    applicability = "pending"
                    outcome = None
                    implementation_label = PENDING_LABEL
                else:
                    outcome = approved_row.compliance_status
                    applicability = "excluded" if outcome == "not_applicable" else "applicable"
                    implementation_label = IMPLEMENTATION_LABELS[outcome]
                rows.append(
                    {
                        "control_id": control.id,
                        "reference": control.reference,
                        "title": control.title,
                        "theme": domain.title,
                        "applicability": applicability,
                        "applicability_label": APPLICABILITY_LABELS[applicability],
                        "outcome": outcome,
                        "implementation_label": implementation_label,
                        "justification": justification.text if justification else None,
                        "justification_by": justification.recorded_by if justification else None,
                        "justification_on": (
                            justification.recorded_at.date().isoformat() if justification else None
                        ),
                    }
                )

    totals = {key: 0 for key in TOTAL_KEYS}
    totals["controls"] = len(rows)
    for row in rows:
        totals[row["applicability"]] += 1
        if row["applicability"] == "applicable":
            totals[
                {
                    "compliant": "implemented",
                    "partially_compliant": "partially_implemented",
                    "non_compliant": "not_implemented",
                    "insufficient_evidence": "not_determined",
                }.get(row["outcome"], "not_determined")
            ] += 1
        if row["justification"] is None:
            totals["justification_missing"] += 1
    notes = []
    if totals["not_assessed"]:
        notes.append(NOT_ASSESSED_NOTE.format(count=totals["not_assessed"]))
    if totals["justification_missing"]:
        notes.append(MISSING_JUSTIFICATION_NOTE.format(count=totals["justification_missing"]))

    return {
        "framework_id": FRAMEWORK_ID,
        "framework_name": framework.name,
        "framework_version": framework.version,
        "intro": INTRO_TEXT.format(framework=f"{framework.name}:{framework.version}"),
        "reliance": RELIANCE_TEXT,
        "notes": notes,
        "totals": totals,
        "rows": rows,
    }
