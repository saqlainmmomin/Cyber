"""Append-only evidence requests added from consultant requirement cards."""

from __future__ import annotations

import hashlib
import json
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.conclusion import Conclusion
from app.services.rfi_examples import DOCUMENT_EXAMPLES, artifact_name

REQUESTED_ACTION = "rfi.evidence_requested"
WITHDRAWN_ACTION = "rfi.evidence_request_withdrawn"
AUDIT_ENTITY_TYPE = "conclusion"
ITEM_KIND = "evidence_request"
OTHER_DOCUMENT_TYPE = "other"
RFI_REQUESTED_GROUP = "Additional evidence requested"
RFI_OTHER_TITLE = "Additional evidence"
RFI_EVIDENCE_REQUEST_STATUS = "Specific evidence requested for the requirements listed"
REQUEST_DETAIL_FALLBACK = "Provide this document."
REQUEST_TEXT_FORMAT = "{detail} Requested for {framework_name} {requirement_id}: {requirement_title}."
STATE_REQUESTED_LABEL = "Added to the draft RFI. Generate a new RFI version to send it."
STATE_ISSUED_LABEL = "Sent in RFI {version_label} as {item_id}."
OTHER_REQUESTS_LABEL = "Also on the draft RFI for this conclusion"
ADDED_TOAST = "Added to the draft RFI"
ALREADY_TOAST = "Already on the draft RFI"
WITHDRAWN_TOAST = "Removed from the draft RFI"
ALREADY_WITHDRAWN_TOAST = "Not on the draft RFI"
RFI_REQUEST_STALE_MESSAGE = "The missing-evidence list changed since you loaded it. Reload the card and try again."
RFI_REQUEST_NOT_FOUND_MESSAGE = "Evidence request not found."
RFI_PAGE_REQUESTS_NOTE = "Evidence requests you added from requirement cards are included."
CONCLUSION_NOT_FOUND_MESSAGE = "Conclusion not found"


class RfiRequestError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class ActiveRequest:
    conclusion_id: str
    request_key: str
    framework_id: str
    requirement_id: str
    document_type: str
    title: str
    request: str
    requested_by: str
    requested_at: datetime
    event_id: str


@dataclass(frozen=True)
class RequestState:
    request: ActiveRequest
    state: str
    item_id: str | None
    version_label: str | None
    status_label: str


def _normalise(value: str | None) -> str:
    return " ".join((value or "").split())


def _evidence_request(framework_id: str, document_type: str):
    framework = FrameworkRegistry.get_or_none(framework_id)
    if framework is None:
        return None
    return next(
        (item for item in framework.evidence_requests if item.document_type == document_type),
        None,
    )


def _framework_name(framework_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    return framework.name if framework is not None else framework_id.upper()


def _requirement_title(framework_id: str, requirement_id: str) -> str:
    framework = FrameworkRegistry.get_or_none(framework_id)
    control = framework.get_control(requirement_id) if framework is not None else None
    return control.title if control is not None else requirement_id


def request_key(
    framework_id: str,
    requirement_id: str,
    document_type: str,
    detail: str,
) -> str:
    raw = "\x1f".join(
        (framework_id, requirement_id, document_type, _normalise(detail))
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def request_title(framework_id: str, document_type: str) -> str:
    if document_type == OTHER_DOCUMENT_TYPE:
        return RFI_OTHER_TITLE
    evidence_request = _evidence_request(framework_id, document_type)
    if evidence_request is not None and evidence_request.label:
        return evidence_request.label
    return document_type.replace("_", " ").capitalize()


def request_text(
    framework_id: str,
    requirement_id: str,
    document_type: str,
    detail: str,
) -> str:
    cleaned = _normalise(detail)
    if not cleaned:
        evidence_request = _evidence_request(framework_id, document_type)
        cleaned = _normalise(evidence_request.reason if evidence_request else "")
    if not cleaned:
        cleaned = REQUEST_DETAIL_FALLBACK
    if not cleaned.endswith((".", "?", "!")):
        cleaned += "."
    return REQUEST_TEXT_FORMAT.format(
        detail=cleaned,
        framework_name=_framework_name(framework_id),
        requirement_id=requirement_id,
        requirement_title=_requirement_title(framework_id, requirement_id),
    )


def _split_hint(hint: str) -> list[str]:
    """Split an evidence hint on ';' outside parentheses."""
    parts, current, depth = [], [], 0
    for char in hint:
        if char == ";" and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        current.append(char)
    parts.append("".join(current).strip())
    return [part for part in parts if part]


def display_hint(hint: str) -> str:
    """Readable form of a signed evidence hint: internal ids become plain names.

    `access_control_policy (user access review records); HR leaver list` becomes
    `Access control policy (user access review records); HR leaver list`.
    """
    readable = []
    for part in _split_hint(hint):
        match = re.fullmatch(r"(.*?)\s*\((.*)\)", part)
        if match:
            readable.append(f"{artifact_name(match[1].strip())} ({match[2].strip()})")
        else:
            readable.append(artifact_name(part))
    return "; ".join(readable)


def document_request_guidance(requirements: list[list[str]]) -> tuple[list[dict], list[dict]]:
    """Group signed evidence hints and retain the checks in requirement order."""
    groups: dict[str, dict] = {}
    rows = []
    for framework_id, requirement_id in requirements:
        framework = FrameworkRegistry.get_or_none(framework_id)
        control = framework.get_control(requirement_id) if framework else None
        if control is None or not control.test_criteria:
            continue
        rows.append({
            "framework_id": framework_id,
            "requirement_id": requirement_id,
            "title": control.title,
            "criteria": [{
                "kind": criterion.kind,
                "statement": criterion.statement,
                "evidence_hint": criterion.evidence_hint,
                "evidence_hint_label": display_hint(criterion.evidence_hint),
                "source_basis": criterion.source_basis,
            } for criterion in control.test_criteria],
        })
        for criterion in control.test_criteria:
            parts = []
            current = []
            depth = 0
            for char in criterion.evidence_hint:
                if char == ";" and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                    continue
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                current.append("," if char == ";" else char)
            parts.append("".join(current).strip())
            for part in parts:
                if not part:
                    continue
                match = re.fullmatch(r"(.*?)\s*\((.*)\)", part)
                base, detail = (match[1].strip(), match[2].strip()) if match else (part, None)
                group = groups.setdefault(base.casefold(), {
                    "name": artifact_name(base), "bare": [], "details": {},
                })
                ids = group["bare"] if detail is None else group["details"].setdefault(detail, [])
                if requirement_id not in ids:
                    ids.append(requirement_id)

    order = {requirement_id: index for index, (_framework_id, requirement_id) in enumerate(requirements)}
    artifacts = [{
        "name": group["name"],
        "controls": sorted(group["bare"], key=order.get),
        "specifics": [{
            "text": detail,
            "controls": sorted(ids, key=order.get),
        } for detail, ids in group["details"].items()],
    } for group in groups.values()]
    return artifacts, rows


def _wrapped(text: str, *, initial_indent: str = "", subsequent_indent: str = "") -> str:
    return textwrap.fill(
        text, width=100, initial_indent=initial_indent,
        subsequent_indent=subsequent_indent, break_long_words=False,
        break_on_hyphens=False,
    )


def document_request_fields(
    original: str,
    document_type: str,
    requirements: list[list[str]],
) -> dict:
    """Build the structured request and its plain-text compatibility rendering."""
    artifacts, rows = document_request_guidance(requirements)
    example = DOCUMENT_EXAMPLES.get(document_type) or DOCUMENT_EXAMPLES["other"]
    sections = [_wrapped(original)]
    if artifacts:
        lines = ["What to send"]
        for artifact in artifacts:
            lines.append(_wrapped(artifact["name"], initial_indent="- ", subsequent_indent="  "))
            if artifact["controls"]:
                lines.append(_wrapped(
                    "supports: " + ", ".join(artifact["controls"]),
                    initial_indent="    ", subsequent_indent="    ",
                ))
            for specific in artifact["specifics"]:
                lines.append(_wrapped(
                    specific["text"] + " (" + ", ".join(specific["controls"]) + ")",
                    initial_indent="    - ", subsequent_indent="      ",
                ))
        sections.append("\n".join(lines))
    sections.extend((
        _wrapped("Example of what to send: " + example["example_artifacts"])
        + "\n" + _wrapped("Good looks like: " + example["good_looks_like"]),
        "Period (auditor): __________\nSample size (auditor): __________",
    ))
    fields = {
        "summary": original,
        "what_to_send": artifacts,
        "example": example["example_artifacts"],
        "good_looks_like": example["good_looks_like"],
        "request": "\n\n".join(sections),
    }
    if rows:
        fields["why_we_ask"] = rows
    return fields


def document_request_text(
    original: str,
    document_type: str,
    requirements: list[list[str]],
) -> str:
    """Render grouped artifacts and document examples without analysis."""
    return document_request_fields(original, document_type, requirements)["request"]


def _metadata(event: AuditEvent) -> dict:
    try:
        value = json.loads(event.metadata_json or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def latest_events(
    db: Session,
    assessment_id: str,
    conclusion_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[tuple[str, str], AuditEvent]:
    if conclusion_ids is not None and not conclusion_ids:
        return {}
    query = (
        select(AuditEvent)
        .join(Conclusion, AuditEvent.entity_id == Conclusion.id)
        .where(
            Conclusion.assessment_id == assessment_id,
            AuditEvent.entity_type == AUDIT_ENTITY_TYPE,
            AuditEvent.action.in_((REQUESTED_ACTION, WITHDRAWN_ACTION)),
        )
        .order_by(AuditEvent.created_at, literal_column("audit_events.rowid"))
    )
    if conclusion_ids is not None:
        query = query.where(AuditEvent.entity_id.in_(conclusion_ids))

    latest: dict[tuple[str, str], AuditEvent] = {}
    for event in db.execute(query).scalars().all():
        key = _metadata(event).get("request_key")
        if not isinstance(key, str):
            continue
        pair = (event.entity_id, key)
        latest.pop(pair, None)
        latest[pair] = event
    return latest


def _active_request(event: AuditEvent) -> ActiveRequest | None:
    metadata = _metadata(event)
    values = (
        metadata.get("framework_id"),
        metadata.get("requirement_id"),
        metadata.get("document_type"),
        metadata.get("title"),
        metadata.get("request"),
    )
    if not all(isinstance(value, str) for value in values):
        return None
    return ActiveRequest(
        conclusion_id=event.entity_id,
        request_key=metadata["request_key"],
        framework_id=metadata["framework_id"],
        requirement_id=metadata["requirement_id"],
        document_type=metadata["document_type"],
        title=metadata["title"],
        request=metadata["request"],
        requested_by=event.actor.removeprefix("consultant:"),
        requested_at=event.created_at,
        event_id=event.id,
    )


def active_requests(
    db: Session,
    assessment_id: str,
    conclusion_ids: list[str] | tuple[str, ...] | None = None,
) -> list[ActiveRequest]:
    requests = []
    for event in latest_events(db, assessment_id, conclusion_ids).values():
        if event.action != REQUESTED_ACTION:
            continue
        request = _active_request(event)
        if request is not None:
            requests.append(request)
    return requests


def issued_refs(
    db: Session,
    assessment: Assessment,
) -> dict[tuple[str, str], tuple[str, str]]:
    from app.services import report_snapshots

    try:
        snapshot = report_snapshots.current_rfi_issue(db, assessment)
        if snapshot is None:
            return {}
        document = report_snapshots.read_rfi_document(db, snapshot)
        rows = report_snapshots.rfi_snapshot_rows(
            db,
            assessment,
            current_source=None,
        )
        row = next((candidate for candidate in rows if candidate.snapshot.id == snapshot.id), None)
        if row is None:
            return {}
        refs = {}
        for item in document.get("items", []):
            for reference in item.get("request_refs", []):
                if isinstance(reference, list) and len(reference) == 2:
                    refs[(reference[0], reference[1])] = (
                        item.get("item_id"),
                        f"v{row.sequence}",
                    )
        return refs
    except report_snapshots.SnapshotError:
        return {}


def request_states(
    db: Session,
    assessment: Assessment,
    conclusion_ids: list[str] | tuple[str, ...],
) -> dict[str, dict[str, RequestState]]:
    requests = active_requests(db, assessment.id, conclusion_ids)
    if not requests:
        return {}
    issued = issued_refs(db, assessment)
    states: dict[str, dict[str, RequestState]] = {}
    for request in requests:
        item_id, version_label = issued.get((request.conclusion_id, request.request_key), (None, None))
        state = "issued" if item_id is not None else "requested"
        status_label = (
            STATE_ISSUED_LABEL.format(version_label=version_label, item_id=item_id)
            if state == "issued"
            else STATE_REQUESTED_LABEL
        )
        states.setdefault(request.conclusion_id, {})[request.request_key] = RequestState(
            request=request,
            state=state,
            item_id=item_id,
            version_label=version_label,
            status_label=status_label,
        )
    return states


def record_request(
    db: Session,
    *,
    conclusion: Conclusion,
    request_key_value: str,
    document_type: str,
    title: str,
    request: str,
    analysis_run_id: str | None,
    actor: str,
) -> tuple[AuditEvent, bool]:
    existing = latest_events(db, conclusion.assessment_id, [conclusion.id]).get(
        (conclusion.id, request_key_value)
    )
    if existing is not None and existing.action == REQUESTED_ACTION:
        return existing, False

    event = AuditEvent(
        actor=actor,
        action=REQUESTED_ACTION,
        entity_type=AUDIT_ENTITY_TYPE,
        entity_id=conclusion.id,
        metadata_json=json.dumps(
            {
                "request_key": request_key_value,
                "framework_id": conclusion.framework_id,
                "requirement_id": conclusion.requirement_id,
                "document_type": document_type,
                "title": title,
                "request": request,
                "analysis_run_id": analysis_run_id,
            },
            sort_keys=True,
        ),
    )
    db.add(event)
    db.flush()
    return event, True


def withdraw_request(
    db: Session,
    *,
    assessment_id: str,
    conclusion_id: str,
    request_key_value: str,
    actor: str,
) -> tuple[AuditEvent | None, bool]:
    conclusion = db.get(Conclusion, conclusion_id)
    if conclusion is None or conclusion.assessment_id != assessment_id:
        raise RfiRequestError(CONCLUSION_NOT_FOUND_MESSAGE, 404)
    existing = latest_events(db, assessment_id, [conclusion_id]).get(
        (conclusion_id, request_key_value)
    )
    if existing is None:
        raise RfiRequestError(RFI_REQUEST_NOT_FOUND_MESSAGE, 404)
    if existing.action == WITHDRAWN_ACTION:
        return None, False

    metadata = _metadata(existing)
    event = AuditEvent(
        actor=actor,
        action=WITHDRAWN_ACTION,
        entity_type=AUDIT_ENTITY_TYPE,
        entity_id=conclusion_id,
        metadata_json=json.dumps(
            {
                "request_key": request_key_value,
                "document_type": metadata.get("document_type", ""),
            },
            sort_keys=True,
        ),
    )
    db.add(event)
    db.flush()
    return event, True


def rfi_items(requests: list[ActiveRequest]) -> list[dict]:
    grouped: dict[str, list[ActiveRequest]] = {}
    for request in requests:
        grouped.setdefault(request.document_type, []).append(request)

    items = []
    for document_type, grouped_requests in grouped.items():
        first = grouped_requests[0]
        request_texts = []
        requirements = []
        refs = []
        for request in grouped_requests:
            if request.request not in request_texts:
                request_texts.append(request.request)
            pair = [request.framework_id, request.requirement_id]
            if pair not in requirements:
                requirements.append(pair)
            reference = [request.conclusion_id, request.request_key]
            if reference not in refs:
                refs.append(reference)
        items.append(
            {
                "kind": ITEM_KIND,
                "title": first.title,
                "request": " ".join(request_texts),
                "required": True,
                "requirements": requirements,
                "document_type": document_type,
                "control_reference": None,
                "conclusion_id": None,
                "conclusion_version": None,
                "group": RFI_REQUESTED_GROUP,
                "request_refs": refs,
            }
        )
    return items
