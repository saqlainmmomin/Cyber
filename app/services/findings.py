"""Findings and Actions (P3-1): one Finding per individually approved gap Conclusion, and append-only Action history in actions.history_json. Never commits."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import literal_column, select, update
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion, ConclusionRevision
from app.models.finding import Finding
from app.services import conclusion_review
from app.services.analysis_pipeline import HUMAN_DECISION_ACTIONS
from app.services.conclusion_review import (
    GAP_OUTCOMES,
    REVIEWER_ACTOR_PREFIX,
    RISK_LEVELS,
    ConclusionCard,
)
from app.services.workpaper import anchor_for

FINDING_STATUSES = ("open", "in_progress", "resolved", "accepted_risk")
NEW_FINDING_STATUS = "open"
ACTION_STATUSES = ("open", "in_progress", "closed", "verified")
NEW_ACTION_STATUS = "open"
ACTION_TRANSITIONS = {
    "open": ("in_progress",),
    "in_progress": ("open",),
    "closed": (),
    "verified": (),
}
CLOSURE_STATUSES = ("closed", "verified")
ELIGIBLE_STATES = ("approved", "edited")
PRIORITIES = (1, 2, 3, 4)
PRIORITY_BY_SEVERITY = {"critical": 1, "high": 1, "medium": 2, "low": 3}
HISTORY_KEYS = ("actor", "action", "timestamp", "notes", "changes")
HISTORY_ACTIONS = ("created", "status_changed", "updated")
LEGACY_HISTORY_ACTION = "imported"
TRACKED_FIELDS = ("title", "owner", "target_date")
HISTORY_LABELS = {
    "created": "Action created",
    "status_changed": "Status changed",
    "updated": "Details updated",
    "imported": "Imported from legacy remediation",
}
MAX_TITLE = 255
MAX_OWNER = 255
MAX_NOTES = 2000
FINDING_CREATED_EVENT = "finding_created"
FINDING_ENTITY = "finding"

STALE_CONCLUSION = "This conclusion changed since you loaded the page. Reload before creating a finding. Nothing was saved."
NOT_APPROVED = "Only an individually approved or edited conclusion can become a finding."
LEGACY_BULK = "This conclusion has a legacy bulk approval. Reopen and approve it individually before creating a finding."
NO_GAP = "Only a conclusion with a gap (partially compliant, non-compliant or insufficient evidence) can become a finding."
DUPLICATE = "A finding already exists for this conclusion."
STALE_ACTION = "This action changed since you loaded the page. Reload and try again. Nothing was saved."
CLOSURE_RESERVED = "Closing or verifying an action requires closure evidence and is not available yet."
TERMINAL = "This action is closed and cannot be changed here."
UNREADABLE_HISTORY = "This action's history could not be read. Nothing was saved."
NO_CHANGES = "No changes to save."
TITLE_TOO_LONG = "Titles must be 255 characters or fewer."


class FindingError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class FindingNotFound(FindingError):
    status_code = 404


class InvalidFindingRequest(FindingError):
    status_code = 400


class FindingConflict(FindingError):
    status_code = 409


@dataclass(frozen=True)
class HistoryEntryView:
    sequence: int
    action: str
    label: str
    actor_display: str
    timestamp: str
    notes: str | None
    changes: dict


@dataclass(frozen=True)
class ActionView:
    action: Action
    history: list[HistoryEntryView]
    history_readable: bool
    history_length: int
    allowed_statuses: tuple[str, ...]
    editable: bool


@dataclass(frozen=True)
class FindingView:
    finding: Finding
    card: ConclusionCard | None
    origin: str
    created_by: str | None
    source_approved: bool
    workpaper_href: str | None
    actions: list[ActionView]


@dataclass(frozen=True)
class EligibleConclusion:
    card: ConclusionCard
    workpaper_href: str
    prefill: dict


@dataclass(frozen=True)
class FindingsPage:
    eligible: list[EligibleConclusion]
    findings: list[FindingView]


def load_history(raw: str) -> list[dict]:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise InvalidFindingRequest(UNREADABLE_HISTORY) from None
    if not isinstance(value, list) or not all(isinstance(entry, dict) for entry in value):
        raise InvalidFindingRequest(UNREADABLE_HISTORY)
    return value


def _text(value: str | None) -> str | None:
    normalized = value.strip() if value is not None else ""
    return normalized or None


def _notes(value: str | None) -> str | None:
    normalized = _text(value)
    if normalized is not None and len(normalized) > MAX_NOTES:
        raise InvalidFindingRequest("Notes must be 2000 characters or fewer.")
    return normalized


def _title(value: str | None, message: str) -> str:
    normalized = _text(value)
    if normalized is None:
        raise InvalidFindingRequest(message)
    if len(normalized) > MAX_TITLE:
        raise InvalidFindingRequest(TITLE_TOO_LONG)
    return normalized


def _owner(value: str | None) -> str | None:
    normalized = _text(value)
    if normalized is not None and len(normalized) > MAX_OWNER:
        raise InvalidFindingRequest("Owner must be 255 characters or fewer.")
    return normalized


def _stored_date(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)


def _date_value(value: datetime | None) -> str | None:
    return value.date().isoformat() if value is not None else None


def _entry(
    *,
    actor: str,
    action: str,
    notes: str | None,
    changes: dict,
    now: datetime | None,
) -> dict:
    return {
        "actor": actor,
        "action": action,
        "timestamp": (now or datetime.now(timezone.utc)).isoformat(),
        "notes": notes,
        "changes": changes,
    }


def _created_entry(
    *,
    title: str,
    owner: str | None,
    target_date: date | None,
    notes: str | None,
    actor: str,
    now: datetime | None,
) -> dict:
    return _entry(
        actor=actor,
        action="created",
        notes=notes,
        changes={
            "title": {"from": None, "to": title},
            "owner": {"from": None, "to": owner},
            "target_date": {
                "from": None,
                "to": target_date.isoformat() if target_date else None,
            },
            "status": {"from": None, "to": NEW_ACTION_STATUS},
        },
        now=now,
    )


def _finding(db: Session, assessment_id: str, finding_id: str) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.assessment_id != assessment_id:
        raise FindingNotFound("Finding not found")
    return finding


def _action(db: Session, finding: Finding, action_id: str) -> Action:
    action = db.get(Action, action_id)
    if action is None or action.finding_id != finding.id:
        raise FindingNotFound("Action not found")
    return action


def _append(
    db: Session,
    action: Action,
    *,
    expected_history_length: int,
    build_entry,
) -> Action:
    raw = action.history_json
    history = load_history(raw)
    if len(history) != expected_history_length:
        raise FindingConflict(STALE_ACTION)
    entry, field_values = build_entry()
    result = db.execute(
        update(Action)
        .where(Action.id == action.id, Action.history_json == raw)
        .values(history_json=json.dumps(history + [entry]), **field_values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise FindingConflict(STALE_ACTION)
    db.expire(action)
    return action


def create_finding(
    db: Session,
    *,
    assessment_id: str,
    conclusion_id: str | None,
    conclusion_version: int,
    title: str | None,
    description: str | None,
    severity: str,
    priority: int,
    action_title: str | None,
    action_owner: str | None,
    action_target_date: date | None,
    notes: str | None,
    actor: str,
    now: datetime | None = None,
) -> Finding:
    conclusion = db.get(Conclusion, conclusion_id) if conclusion_id else None
    if conclusion is None or conclusion.assessment_id != assessment_id:
        raise FindingNotFound("Conclusion not found")
    if conclusion.version != conclusion_version:
        raise FindingConflict(STALE_CONCLUSION)
    try:
        card = conclusion_review.conclusion_card(
            db, assessment_id=assessment_id, conclusion_id=conclusion.id
        )
    except conclusion_review.ConclusionNotFound:
        raise FindingNotFound("Conclusion not found") from None
    if card.state not in ELIGIBLE_STATES:
        raise InvalidFindingRequest(NOT_APPROVED)
    if card.legacy_bulk_approval:
        raise InvalidFindingRequest(LEGACY_BULK)
    if conclusion.outcome not in GAP_OUTCOMES:
        raise InvalidFindingRequest(NO_GAP)
    exists = db.execute(
        select(Finding.id).where(Finding.conclusion_id == conclusion.id).limit(1)
    ).scalar_one_or_none()
    if exists is not None:
        raise InvalidFindingRequest(DUPLICATE)

    finding_title = _title(title, "A finding needs a title and a description.")
    finding_description = _text(description)
    if finding_description is None:
        raise InvalidFindingRequest("A finding needs a title and a description.")
    if severity not in RISK_LEVELS:
        raise InvalidFindingRequest("Unknown severity.")
    if priority not in PRIORITIES:
        raise InvalidFindingRequest("Priority must be between 1 and 4.")
    first_title = _title(action_title, "An action needs a title.")
    first_owner = _owner(action_owner)
    entry_notes = _notes(notes)

    finding = Finding(
        assessment_id=assessment_id,
        conclusion_id=conclusion.id,
        title=finding_title,
        description=finding_description,
        severity=severity,
        priority=priority,
        status=NEW_FINDING_STATUS,
    )
    db.add(finding)
    db.flush()
    first_action = Action(
        finding_id=finding.id,
        title=first_title,
        owner=first_owner,
        target_date=_stored_date(action_target_date),
        status=NEW_ACTION_STATUS,
        history_json=json.dumps(
            [
                _created_entry(
                    title=first_title,
                    owner=first_owner,
                    target_date=action_target_date,
                    notes=entry_notes,
                    actor=actor,
                    now=now,
                )
            ]
        ),
    )
    db.add(first_action)
    db.flush()
    revision = db.execute(
        select(ConclusionRevision)
        .where(
            ConclusionRevision.conclusion_id == conclusion.id,
            ConclusionRevision.action.in_(HUMAN_DECISION_ACTIONS),
        )
        .order_by(
            ConclusionRevision.created_at.desc(),
            literal_column("conclusion_revisions.rowid").desc(),
        )
        .limit(1)
    ).scalar_one()
    metadata = {
        "assessment_id": assessment_id,
        "conclusion_id": conclusion.id,
        "conclusion_version": conclusion.version,
        "conclusion_revision_id": revision.id,
        "framework_id": conclusion.framework_id,
        "requirement_id": conclusion.requirement_id,
        "first_action_id": first_action.id,
    }
    db.add(
        AuditEvent(
            actor=actor,
            action=FINDING_CREATED_EVENT,
            entity_type=FINDING_ENTITY,
            entity_id=finding.id,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    )
    db.flush()
    return finding


def add_action(
    db: Session,
    *,
    assessment_id: str,
    finding_id: str,
    title: str | None,
    owner: str | None,
    target_date: date | None,
    notes: str | None,
    actor: str,
    now: datetime | None = None,
) -> Action:
    finding = _finding(db, assessment_id, finding_id)
    action_title = _title(title, "An action needs a title.")
    action_owner = _owner(owner)
    entry_notes = _notes(notes)
    action = Action(
        finding_id=finding.id,
        title=action_title,
        owner=action_owner,
        target_date=_stored_date(target_date),
        status=NEW_ACTION_STATUS,
        history_json=json.dumps(
            [
                _created_entry(
                    title=action_title,
                    owner=action_owner,
                    target_date=target_date,
                    notes=entry_notes,
                    actor=actor,
                    now=now,
                )
            ]
        ),
    )
    db.add(action)
    db.flush()
    return action


def change_action_status(
    db: Session,
    *,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    status: str,
    expected_history_length: int,
    notes: str | None,
    actor: str,
    now: datetime | None = None,
) -> Action:
    finding = _finding(db, assessment_id, finding_id)
    action = _action(db, finding, action_id)
    def _build():
        current = action.status
        if current in CLOSURE_STATUSES:
            raise InvalidFindingRequest(TERMINAL)
        if status not in ACTION_STATUSES:
            raise InvalidFindingRequest("Unknown action status.")
        if status in CLOSURE_STATUSES:
            raise InvalidFindingRequest(CLOSURE_RESERVED)
        if status not in ACTION_TRANSITIONS.get(current, ()):
            raise InvalidFindingRequest(
                f"An action cannot move from {current} to {status}."
            )
        entry_notes = _notes(notes)
        return (
            _entry(
                actor=actor,
                action="status_changed",
                notes=entry_notes,
                changes={"status": {"from": current, "to": status}},
                now=now,
            ),
            {"status": status},
        )

    return _append(
        db,
        action,
        expected_history_length=expected_history_length,
        build_entry=_build,
    )


def update_action(
    db: Session,
    *,
    assessment_id: str,
    finding_id: str,
    action_id: str,
    title: str | None,
    owner: str | None,
    target_date: date | None,
    expected_history_length: int,
    notes: str | None,
    actor: str,
    now: datetime | None = None,
) -> Action:
    finding = _finding(db, assessment_id, finding_id)
    action = _action(db, finding, action_id)
    def _build():
        if action.status not in ("open", "in_progress"):
            raise InvalidFindingRequest(TERMINAL)
        new_title = _title(title, "An action needs a title.")
        new_owner = _owner(owner)
        entry_notes = _notes(notes)
        current_date = action.target_date.date() if action.target_date else None
        changes = {}
        field_values = {}
        if new_title != action.title:
            changes["title"] = {"from": action.title, "to": new_title}
            field_values["title"] = new_title
        if new_owner != action.owner:
            changes["owner"] = {"from": action.owner, "to": new_owner}
            field_values["owner"] = new_owner
        if target_date != current_date:
            changes["target_date"] = {
                "from": current_date.isoformat() if current_date else None,
                "to": target_date.isoformat() if target_date else None,
            }
            field_values["target_date"] = _stored_date(target_date)
        if not changes:
            raise InvalidFindingRequest(NO_CHANGES)
        return (
            _entry(
                actor=actor,
                action="updated",
                notes=entry_notes,
                changes=changes,
                now=now,
            ),
            field_values,
        )

    return _append(
        db,
        action,
        expected_history_length=expected_history_length,
        build_entry=_build,
    )


def _actor_display(actor: str) -> str:
    return actor.removeprefix(REVIEWER_ACTOR_PREFIX)


def _action_view(action: Action) -> ActionView:
    try:
        raw_history = load_history(action.history_json)
    except InvalidFindingRequest:
        return ActionView(
            action=action,
            history=[],
            history_readable=False,
            history_length=0,
            allowed_statuses=(),
            editable=False,
        )
    history = [
        HistoryEntryView(
            sequence=sequence,
            action=str(entry.get("action", "")),
            label=HISTORY_LABELS.get(
                str(entry.get("action", "")), str(entry.get("action", ""))
            ),
            actor_display=_actor_display(str(entry.get("actor", ""))),
            timestamp=str(entry.get("timestamp", "")),
            notes=entry.get("notes"),
            changes=entry.get("changes") or {},
        )
        for sequence, entry in enumerate(raw_history, start=1)
    ]
    return ActionView(
        action=action,
        history=history,
        history_readable=True,
        history_length=len(history),
        allowed_statuses=ACTION_TRANSITIONS.get(action.status, ()),
        editable=action.status in ("open", "in_progress"),
    )


def findings_page(db: Session, assessment_id: str) -> FindingsPage:
    cards = conclusion_review.conclusion_cards(db, assessment_id)
    finding_rows = db.execute(
        select(Finding)
        .where(Finding.assessment_id == assessment_id)
        .order_by(Finding.created_at, literal_column("findings.rowid"))
    ).scalars().all()
    finding_ids = [finding.id for finding in finding_rows]
    action_rows = (
        db.execute(
            select(Action)
            .where(Action.finding_id.in_(finding_ids))
            .order_by(Action.created_at, literal_column("actions.rowid"))
        ).scalars().all()
        if finding_ids
        else []
    )
    event_rows = (
        db.execute(
            select(AuditEvent).where(
                AuditEvent.entity_type == FINDING_ENTITY,
                AuditEvent.action == FINDING_CREATED_EVENT,
                AuditEvent.entity_id.in_(finding_ids),
            )
        ).scalars().all()
        if finding_ids
        else []
    )
    finding_by_conclusion = {finding.conclusion_id for finding in finding_rows}
    eligible = []
    for card in cards:
        conclusion = card.conclusion
        if (
            card.state not in ELIGIBLE_STATES
            or card.legacy_bulk_approval
            or conclusion.outcome not in GAP_OUTCOMES
            or conclusion.id in finding_by_conclusion
        ):
            continue
        severity = conclusion.risk_level if conclusion.risk_level in RISK_LEVELS else "medium"
        eligible.append(
            EligibleConclusion(
                card=card,
                workpaper_href=(
                    f"/assessments/{assessment_id}/workpaper#"
                    f"{anchor_for(conclusion.framework_id, conclusion.requirement_id)}"
                ),
                prefill={
                    "title": card.requirement_title[:MAX_TITLE],
                    "description": conclusion.gaps_identified,
                    "severity": severity,
                    "priority": PRIORITY_BY_SEVERITY[severity],
                    "action_title": conclusion.recommended_action.strip()[:MAX_TITLE],
                },
            )
        )
    cards_by_id = {card.conclusion.id: card for card in cards}
    actions_by_finding: dict[str, list[Action]] = {finding.id: [] for finding in finding_rows}
    for action in action_rows:
        actions_by_finding[action.finding_id].append(action)
    events_by_finding = {event.entity_id: event for event in event_rows}
    views = []
    for finding in finding_rows:
        card = cards_by_id.get(finding.conclusion_id)
        event = events_by_finding.get(finding.id)
        href = (
            f"/assessments/{assessment_id}/workpaper#"
            f"{anchor_for(card.conclusion.framework_id, card.conclusion.requirement_id)}"
            if card
            else None
        )
        views.append(
            FindingView(
                finding=finding,
                card=card,
                origin="consultant" if event else "migrated",
                created_by=_actor_display(event.actor) if event else None,
                source_approved=card is not None and card.state in ELIGIBLE_STATES,
                workpaper_href=href,
                actions=[_action_view(action) for action in actions_by_finding[finding.id]],
            )
        )
    return FindingsPage(eligible=eligible, findings=views)


def finding_view(db: Session, *, assessment_id: str, finding_id: str) -> FindingView:
    for view in findings_page(db, assessment_id).findings:
        if view.finding.id == finding_id:
            return view
    raise FindingNotFound("Finding not found")
