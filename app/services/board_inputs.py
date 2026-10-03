"""Validation and persistence for consultant-entered board inputs."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.finding import Finding
from app.models.initiative_metadata import InitiativeMetadata


RESPONSIBILITIES = ("client", "consultant", "shared")
LEVELS = ("high", "medium", "low")
MAX_BUSINESS_IMPACT = 1200
MAX_RECOMMENDATION = 1500
MAX_INITIATIVE_TITLE = 120
MAX_ASKS = 3
MAX_ASK_CHARS = 400

FINDING_NOT_FOUND = "Finding not found"
ACTION_NOT_FOUND = "Action not found"
GROUP_NOT_FOUND = "Remediation group not found"
ASSESSMENT_NOT_FOUND = "Assessment not found"
INVALID_RESPONSIBILITY = "Responsibility must be client, consultant or shared."
INVALID_LEVEL = "Complexity and benefit must be high, medium or low."
TOO_MANY_ASKS = "A report can carry at most 3 board decisions."
TEXT_TOO_LONG = "{label} must be {limit} characters or fewer."
NO_CHANGES = "No changes to save."

AUDIT_FINDING = "finding.board_fields_updated"
AUDIT_ACTION = "action.responsibility_updated"
AUDIT_INITIATIVE = "initiative.metadata_updated"
AUDIT_ASKS = "assessment.board_asks_updated"


class BoardInputError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BoardInputNotFound(BoardInputError):
    status_code = 404


class InvalidBoardInput(BoardInputError):
    status_code = 400


def _text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.replace("\r\n", "\n").strip()
    return value or None


def _level(value: str | None) -> str | None:
    value = _text(value)
    if value is None:
        return None
    value = value.lower()
    if value not in LEVELS:
        raise InvalidBoardInput(INVALID_LEVEL)
    return value


def _responsibility(value: str | None) -> str | None:
    value = _text(value)
    if value is None:
        return None
    value = value.lower()
    if value not in RESPONSIBILITIES:
        raise InvalidBoardInput(INVALID_RESPONSIBILITY)
    return value


def _bounded(value: str | None, label: str, limit: int) -> str | None:
    value = _text(value)
    if value is not None and len(value) > limit:
        raise InvalidBoardInput(TEXT_TOO_LONG.format(label=label, limit=limit))
    return value


def _audit(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict,
) -> None:
    db.add(
        AuditEvent(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    )


def update_finding_fields(
    db: Session,
    assessment_id: str,
    finding_id: str,
    business_impact: str | None,
    recommendation: str | None,
    actor: str,
) -> Finding:
    finding = (
        db.query(Finding)
        .filter(Finding.id == finding_id, Finding.assessment_id == assessment_id)
        .one_or_none()
    )
    if finding is None:
        raise BoardInputNotFound(FINDING_NOT_FOUND)
    business_impact = _bounded(business_impact, "Why it matters", MAX_BUSINESS_IMPACT)
    recommendation = _bounded(recommendation, "Recommendation", MAX_RECOMMENDATION)

    changes = {}
    for field, value in (
        ("business_impact", business_impact),
        ("recommendation", recommendation),
    ):
        previous = getattr(finding, field)
        if previous != value:
            changes[field] = {"from": previous, "to": value}
            setattr(finding, field, value)
    if changes:
        _audit(
            db,
            actor=actor,
            action=AUDIT_FINDING,
            entity_type="finding",
            entity_id=finding.id,
            metadata={"assessment_id": assessment_id, "changes": changes},
        )
    return finding


def update_action_responsibility(
    db: Session,
    assessment_id: str,
    action_id: str,
    responsibility: str | None,
    actor: str,
) -> Action:
    action = (
        db.query(Action)
        .join(Finding, Action.finding_id == Finding.id)
        .filter(Action.id == action_id, Finding.assessment_id == assessment_id)
        .one_or_none()
    )
    if action is None:
        raise BoardInputNotFound(ACTION_NOT_FOUND)
    responsibility = _responsibility(responsibility)
    previous = action.responsibility
    if previous != responsibility:
        action.responsibility = responsibility
        _audit(
            db,
            actor=actor,
            action=AUDIT_ACTION,
            entity_type="action",
            entity_id=action.id,
            metadata={
                "assessment_id": assessment_id,
                "finding_id": action.finding_id,
                "from": previous,
                "to": responsibility,
            },
        )
    return action


def _roadmap_group_ids(db: Session, assessment: Assessment) -> set[str]:
    from app.services import remediation_groups, report_content

    findings = report_content.assessment_findings(db, assessment).findings
    return {
        group["group_id"]
        for group in remediation_groups.build_groups(findings, assessment.frameworks)
    }


def update_initiative(
    db: Session,
    assessment_id: str,
    group_id: str,
    title: str | None,
    complexity: str | None,
    benefit: str | None,
    actor: str,
) -> InitiativeMetadata:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise BoardInputNotFound(ASSESSMENT_NOT_FOUND)
    title = _bounded(title, "Initiative title", MAX_INITIATIVE_TITLE)
    complexity = _level(complexity)
    benefit = _level(benefit)
    group_id = (group_id or "").strip()
    if group_id not in _roadmap_group_ids(db, assessment):
        raise BoardInputNotFound(GROUP_NOT_FOUND)

    row = (
        db.query(InitiativeMetadata)
        .filter(
            InitiativeMetadata.assessment_id == assessment_id,
            InitiativeMetadata.group_id == group_id,
        )
        .one_or_none()
    )
    if row is None:
        row = InitiativeMetadata(
            assessment_id=assessment_id,
            group_id=group_id,
            title=title,
            complexity=complexity,
            benefit=benefit,
        )
        db.add(row)
        db.flush()
        previous = {"title": None, "complexity": None, "benefit": None}
    else:
        previous = {
            "title": row.title,
            "complexity": row.complexity,
            "benefit": row.benefit,
        }

    values = {"title": title, "complexity": complexity, "benefit": benefit}
    changes = {}
    for field, value in values.items():
        if previous[field] != value:
            changes[field] = {"from": previous[field], "to": value}
            setattr(row, field, value)
    if changes:
        _audit(
            db,
            actor=actor,
            action=AUDIT_INITIATIVE,
            entity_type="initiative_metadata",
            entity_id=row.id,
            metadata={
                "assessment_id": assessment_id,
                "group_id": group_id,
                "changes": changes,
            },
        )
    return row


def board_asks(assessment: Assessment) -> dict:
    if not assessment.board_asks_json:
        return {"consultant": [], "consultant_by": None}
    try:
        payload = json.loads(assessment.board_asks_json)
    except (TypeError, json.JSONDecodeError):
        return {"consultant": [], "consultant_by": None}
    asks = payload.get("asks") if isinstance(payload, dict) else None
    reviewer = payload.get("by") if isinstance(payload, dict) else None
    if not isinstance(asks, list):
        asks = []
    asks = [ask for ask in asks if isinstance(ask, str)]
    return {
        "consultant": asks,
        "consultant_by": reviewer if isinstance(reviewer, str) else None,
    }


def update_board_asks(
    db: Session,
    assessment_id: str,
    asks: list[str],
    actor: str,
) -> dict:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise BoardInputNotFound(ASSESSMENT_NOT_FOUND)
    normalized = [_text(ask) for ask in asks]
    normalized = [ask for ask in normalized if ask is not None]
    if len(normalized) > MAX_ASKS:
        raise InvalidBoardInput(TOO_MANY_ASKS)
    for ask in normalized:
        if len(ask) > MAX_ASK_CHARS:
            raise InvalidBoardInput(TEXT_TOO_LONG.format(label="Board decision", limit=MAX_ASK_CHARS))

    previous = board_asks(assessment)
    if previous["consultant"] == normalized:
        return previous

    reviewer = actor.removeprefix("consultant:")
    assessment.board_asks_json = (
        json.dumps({"asks": normalized, "by": reviewer}) if normalized else None
    )
    result = {"consultant": normalized, "consultant_by": reviewer if normalized else None}
    _audit(
        db,
        actor=actor,
        action=AUDIT_ASKS,
        entity_type="assessment",
        entity_id=assessment.id,
        metadata={"from": previous["consultant"], "to": normalized},
    )
    return result


def initiative_metadata(db: Session, assessment_id: str) -> dict[str, dict]:
    rows = (
        db.query(InitiativeMetadata)
        .filter(InitiativeMetadata.assessment_id == assessment_id)
        .all()
    )
    return {
        row.group_id: {
            "title": row.title,
            "complexity": row.complexity,
            "benefit": row.benefit,
        }
        for row in rows
    }
