"""Versioned, consultant-approved evidence requests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import literal_column, select
from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.evidence import Evidence, EvidenceUse
from app.models.magic_link import MagicLink
from app.models.report import GapReport
from app.models.report_snapshot import ReportSnapshot
from app.services import approved_report, magic_links, report_snapshots, scope_profiler
from app.utils import rfi_export

RFI_DOCUMENT_SCHEMA_VERSION = 1
RFI_ITEM_ID_FORMAT = "RFI-{n:03d}"
RFI_DOCUMENTS_GROUP = "Documents requested"
RFI_DOCUMENT_STATUS = "Document requested for this assessment"
RFI_REQUIREMENT_STATUS = "Evidence needed before this requirement can be concluded"
RFI_REQUIREMENT_FALLBACK = "Provide evidence showing how this requirement is met."
DEADLINE_WEEKS = {"Required": 2, "Recommended": 4}
RFI_INTRODUCTION = (
    "This Request for Information has been prepared as part of the {framework_label} compliance "
    "assessment for {company_name}. It lists the documents and evidence needed to complete the "
    "assessment. Items marked Required are needed before the related requirements can be concluded; "
    "items marked Recommended help confirm the assessment where they exist. Where one document is "
    "requested for several requirements, it only needs to be provided once."
)
RFI_RESPONSE_INSTRUCTIONS = (
    "Please provide each item and quote its RFI item number (for example, RFI-001) when you send it. "
    "If your consultant has given you a secure upload link, upload each file against the matching item. "
    "Documents may be provided in PDF, DOCX or image format. If an item does not apply to your "
    "organisation, reply with a short written explanation instead of a document."
)

RFI_SCOPE_REQUIRED_MESSAGE = "Record the assessment scope before preparing an RFI."
RFI_EMPTY_MESSAGE = (
    "Nothing to request: every evidence request item is omitted and no approved conclusion is marked "
    "insufficient evidence."
)
RFI_UNKNOWN_OMISSION_MESSAGE = (
    "One of the omitted items is not in the current evidence request. Reload the page and try again."
)
RFI_STALE_MESSAGE = (
    "This RFI version no longer matches the current scope, evidence request or approved conclusions. "
    "Generate a new version, then issue it."
)
RFI_NOT_FOUND_MESSAGE = "RFI version not found."
RFI_WRONG_ROUTE_MESSAGE = "RFI versions are generated and issued from the RFI page."
RFI_LINK_NOT_CURRENT_MESSAGE = "Client links can only be created from the current issued RFI version."
RFI_NO_ENGAGEMENT_MESSAGE = (
    "This assessment is not part of an engagement, so a client link cannot be created."
)
RFI_UNKNOWN_ITEM_MESSAGE = "Choose requested items from this RFI version."
LEGACY_RFI_RETIRED = (
    "The previous RFI generator has been retired. Prepare a versioned RFI from the RFI page."
)


class RfiError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class RfiLinkRow:
    link_id: str
    id_prefix: str
    status: str
    created_at: datetime
    expires_at: datetime
    snapshot_id: str
    sequence: int
    items: tuple[tuple[str, str], ...]
    uploads_used: int
    max_uploads: int


def _framework_label(assessment: Assessment) -> str:
    names = []
    for framework_id in assessment.frameworks:
        framework = FrameworkRegistry.get_or_none(framework_id)
        names.append(framework.name if framework else framework_id.upper())
    return ", ".join(names)


def _checklist(db: Session, assessment: Assessment) -> list[dict]:
    answers = json.loads(assessment.scope_answers or "{}")
    return scope_profiler.compute_scope_multi(answers, assessment.frameworks)[
        "evidence_checklist"
    ]


def included_rows(db: Session, assessment: Assessment) -> list[approved_report.ApprovedRow]:
    report_id = (
        db.query(GapReport.id)
        .filter_by(assessment_id=assessment.id)
        .first()
    )
    if report_id is None:
        return []
    approved = approved_report.build_approved_report(db, assessment)
    return [
        row
        for row in approved.rows
        if row.compliance_status == "insufficient_evidence"
    ]


def _requirement_pairs(item: dict) -> list[list[str]]:
    pairs: list[list[str]] = []
    for control_id in item["maps_to"]:
        framework_id = next(
            (
                framework_id
                for framework_id in item["frameworks"]
                if FrameworkRegistry.get(framework_id).get_control(control_id) is not None
            ),
            None,
        )
        if framework_id is None:
            raise ValueError(
                f"Evidence request {item['document_type']} maps to unknown control {control_id}"
            )
        pairs.append([framework_id, control_id])
    return pairs


def current_source(db: Session, assessment: Assessment) -> dict:
    checklist = _checklist(db, assessment)
    checklist_bytes = json.dumps(
        checklist,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    rows = included_rows(db, assessment)
    return {
        "schema_version": RFI_DOCUMENT_SCHEMA_VERSION,
        "framework_ids": list(assessment.frameworks),
        "checklist_sha256": hashlib.sha256(checklist_bytes).hexdigest(),
        "conclusion_versions": [
            [row.conclusion_id, row.conclusion_version]
            for row in sorted(rows, key=lambda item: item.conclusion_id)
        ],
    }


def build_rfi_document(
    db: Session,
    assessment: Assessment,
    *,
    omitted: Sequence[str] = (),
) -> dict:
    checklist = _checklist(db, assessment)
    omitted_document_types = sorted(set(omitted))
    available_document_types = {item["document_type"] for item in checklist}
    if any(item not in available_document_types for item in omitted_document_types):
        raise RfiError(RFI_UNKNOWN_OMISSION_MESSAGE, 400)

    framework_label = _framework_label(assessment)
    items: list[dict] = []
    next_number = 1
    for checklist_item in checklist:
        if checklist_item["document_type"] in omitted_document_types:
            continue
        items.append(
            {
                "item_id": RFI_ITEM_ID_FORMAT.format(n=next_number),
                "kind": "document",
                "title": checklist_item["label"],
                "request": checklist_item["reason"],
                "required": checklist_item["required"],
                "requirements": _requirement_pairs(checklist_item),
                "document_type": checklist_item["document_type"],
                "control_reference": None,
                "conclusion_id": None,
                "conclusion_version": None,
                "group": RFI_DOCUMENTS_GROUP,
            }
        )
        next_number += 1

    for row in included_rows(db, assessment):
        items.append(
            {
                "item_id": RFI_ITEM_ID_FORMAT.format(n=next_number),
                "kind": "requirement",
                "title": row.requirement_title,
                "request": row.gap_description.strip() or RFI_REQUIREMENT_FALLBACK,
                "required": True,
                "requirements": [[row.framework_id, row.requirement_id]],
                "document_type": None,
                "control_reference": row.control_reference,
                "conclusion_id": row.conclusion_id,
                "conclusion_version": row.conclusion_version,
                "group": row.chapter_title,
            }
        )
        next_number += 1

    documents = sum(item["kind"] == "document" for item in items)
    requirements = len(items) - documents
    return {
        "schema_version": RFI_DOCUMENT_SCHEMA_VERSION,
        "assessment_id": assessment.id,
        "company_name": assessment.company_name,
        "framework_ids": list(assessment.frameworks),
        "framework_label": framework_label,
        "title": f"{framework_label} Compliance - Request for Information: {assessment.company_name}",
        "introduction": RFI_INTRODUCTION.format(
            framework_label=framework_label,
            company_name=assessment.company_name,
        ),
        "response_instructions": RFI_RESPONSE_INSTRUCTIONS,
        "omitted_document_types": omitted_document_types,
        "items": items,
        "totals": {
            "items": len(items),
            "documents": documents,
            "requirements": requirements,
            "required": sum(item["required"] for item in items),
        },
        "source": current_source(db, assessment),
    }


def canonical_bytes(document: dict) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def render_items(document: dict) -> list[dict]:
    rendered = []
    for item in document["items"]:
        priority = "Required" if item["required"] else "Recommended"
        ids = [requirement_id for _framework_id, requirement_id in item["requirements"]]
        base = {
            "item_id": item["item_id"],
            "priority": priority,
            "requirement_title": item["title"],
            "evidence_requested": item["request"],
            "deadline_weeks": DEADLINE_WEEKS[priority],
            "chapter": item["group"],
        }
        if item["kind"] == "document":
            rendered.append(
                base
                | {
                    "requirement_id": "",
                    "section_ref": "",
                    "current_status": RFI_DOCUMENT_STATUS,
                    "requirements": ids,
                }
            )
        else:
            rendered.append(
                base
                | {
                    "requirement_id": ids[0],
                    "section_ref": item["control_reference"] or "",
                    "current_status": RFI_REQUIREMENT_STATUS,
                    "requirements": [],
                }
            )
    return rendered


def render_pdf(
    document: dict,
    *,
    generated_at: datetime | None = None,
    version_label: str = "",
) -> bytes:
    return rfi_export.generate_rfi_pdf(
        title=document["title"],
        company_name=document["company_name"],
        introduction=document["introduction"],
        evidence_items=render_items(document),
        response_instructions=document["response_instructions"],
        generated_at=generated_at,
        framework_label=document["framework_label"],
        version_label=version_label,
    )


def render_docx(
    document: dict,
    *,
    generated_at: datetime | None = None,
    version_label: str = "",
) -> bytes:
    return rfi_export.generate_rfi_docx(
        title=document["title"],
        company_name=document["company_name"],
        introduction=document["introduction"],
        evidence_items=render_items(document),
        response_instructions=document["response_instructions"],
        generated_at=generated_at,
        framework_label=document["framework_label"],
        version_label=version_label,
    )


def generate_version(
    db: Session,
    assessment: Assessment,
    *,
    omitted: Sequence[str],
    actor: str,
) -> ReportSnapshot:
    if assessment.scope_answers is None:
        raise RfiError(RFI_SCOPE_REQUIRED_MESSAGE, 409)
    document = build_rfi_document(db, assessment, omitted=omitted)
    if not document["items"]:
        raise RfiError(RFI_EMPTY_MESSAGE, 409)
    sequence = len(
        report_snapshots.rfi_snapshot_rows(
            db,
            assessment,
            current_source=None,
        )
    ) + 1
    generated_at = datetime.now(timezone.utc)
    pdf_content = render_pdf(
        document,
        generated_at=generated_at,
        version_label=f"v{sequence}",
    )
    return report_snapshots.create_rfi_snapshot(
        db,
        assessment=assessment,
        pdf_content=pdf_content,
        document_content=canonical_bytes(document),
        source=document["source"],
        omitted_document_types=document["omitted_document_types"],
        actor=actor,
    )


def issue_version(
    db: Session,
    assessment: Assessment,
    snapshot_id: str,
    *,
    actor: str,
) -> ReportSnapshot:
    try:
        snapshot = report_snapshots.load_snapshot(
            db,
            assessment_id=assessment.id,
            snapshot_id=snapshot_id,
        )
    except report_snapshots.SnapshotNotFound:
        raise RfiError(RFI_NOT_FOUND_MESSAGE, 404) from None
    if snapshot.type != report_snapshots.RFI_SNAPSHOT_TYPE:
        raise RfiError(RFI_NOT_FOUND_MESSAGE, 404)
    report_snapshots.read_rfi_document(db, snapshot)
    metadata = report_snapshots.generated_event(db, snapshot.id)
    if metadata.get("source") != current_source(db, assessment):
        raise RfiError(RFI_STALE_MESSAGE, 409)
    return report_snapshots.issue_snapshot(db, snapshot, actor=actor)


def create_client_link(
    db: Session,
    assessment: Assessment,
    snapshot_id: str,
    *,
    item_ids: Sequence[str],
    expires_in_days: int,
    max_uploads: int,
    max_total_mb: int,
    actor: str,
) -> magic_links.CreatedLink:
    if assessment.engagement_id is None:
        raise RfiError(RFI_NO_ENGAGEMENT_MESSAGE, 409)
    try:
        snapshot = report_snapshots.load_snapshot(
            db,
            assessment_id=assessment.id,
            snapshot_id=snapshot_id,
        )
    except report_snapshots.SnapshotNotFound:
        raise RfiError(RFI_NOT_FOUND_MESSAGE, 404) from None
    if snapshot.type != report_snapshots.RFI_SNAPSHOT_TYPE:
        raise RfiError(RFI_NOT_FOUND_MESSAGE, 404)
    current_issue = report_snapshots.current_rfi_issue(db, assessment)
    if current_issue is None or current_issue.id != snapshot.id:
        raise RfiError(RFI_LINK_NOT_CURRENT_MESSAGE, 409)
    document = report_snapshots.read_rfi_document(db, snapshot)
    selected_ids = list(dict.fromkeys(item_ids))
    by_id = {item["item_id"]: item for item in document["items"]}
    if any(item_id not in by_id for item_id in selected_ids):
        raise RfiError(RFI_UNKNOWN_ITEM_MESSAGE, 422)
    rfi_items = []
    for item_id in selected_ids:
        title = f"{item_id}: {by_id[item_id]['title']}"
        if len(title) > magic_links.MAX_ITEM_TITLE_CHARS:
            title = title[: magic_links.MAX_ITEM_TITLE_CHARS - 1] + "…"
        rfi_items.append((item_id, title))
    try:
        return magic_links.create_rfi_link(
            db,
            engagement_id=assessment.engagement_id,
            assessment_id=assessment.id,
            snapshot_id=snapshot.id,
            rfi_items=rfi_items,
            expires_in_days=expires_in_days,
            max_uploads=max_uploads,
            max_total_mb=max_total_mb,
            actor=actor,
        )
    except magic_links.MagicLinkError:
        raise


def _link_rows(
    db: Session,
    assessment: Assessment,
) -> tuple[list[RfiLinkRow], dict[str, dict[str, str]]]:
    if assessment.engagement_id is None:
        return [], {}
    links = (
        db.query(MagicLink)
        .filter(MagicLink.engagement_id == assessment.engagement_id)
        .order_by(MagicLink.created_at.desc(), MagicLink.id.desc())
        .all()
    )
    rows = []
    link_items: dict[str, dict[str, str]] = {}
    snapshot_sequences = {
        row.snapshot.id: row.sequence
        for row in report_snapshots.rfi_snapshot_rows(
            db,
            assessment,
            current_source=None,
        )
    }
    for link in links:
        try:
            scope = json.loads(link.scope_json)
        except (json.JSONDecodeError, TypeError):
            continue
        rfi = scope.get("rfi")
        if scope.get("version") != magic_links.RFI_SCOPE_VERSION or not isinstance(rfi, dict):
            continue
        if rfi.get("assessment_id") != assessment.id:
            continue
        items = tuple(
            (item.get("rfi_item_id"), item.get("title"))
            for item in scope.get("items", [])
            if isinstance(item, dict)
            and isinstance(item.get("rfi_item_id"), str)
            and isinstance(item.get("title"), str)
        )
        usage = magic_links.link_usage(db, link)
        rows.append(
            RfiLinkRow(
                link_id=link.id,
                id_prefix=link.id[:8],
                status=magic_links.link_status(link),
                created_at=link.created_at,
                expires_at=link.expires_at,
                snapshot_id=rfi.get("snapshot_id", ""),
                sequence=snapshot_sequences.get(rfi.get("snapshot_id"), 0),
                items=items,
                uploads_used=usage.uploads_total,
                max_uploads=link.max_uploads,
            )
        )
        link_items[link.id] = {
            item["key"]: item["rfi_item_id"]
            for item in scope.get("items", [])
            if isinstance(item, dict)
            and isinstance(item.get("key"), str)
            and isinstance(item.get("rfi_item_id"), str)
        }
    return rows, link_items


def page_context(db: Session, assessment: Assessment) -> dict:
    scope_recorded = assessment.scope_answers is not None
    preview = build_rfi_document(db, assessment) if scope_recorded else None
    mapped_hints: dict[str, tuple[int, int]] = {}
    if preview is not None:
        mapped_keys = {
            (use.framework_id, use.requirement_id)
            for use in db.query(EvidenceUse).filter(
                EvidenceUse.assessment_id == assessment.id
            )
        }
        mapped_hints = {
            item["document_type"]: (
                sum(tuple(requirement) in mapped_keys for requirement in item["requirements"]),
                len(item["requirements"]),
            )
            for item in preview["items"]
            if item["kind"] == "document"
        }

    versions = (
        report_snapshots.rfi_snapshot_rows(
            db,
            assessment,
            current_source=current_source(db, assessment),
        )
        if scope_recorded
        else []
    )
    current_issue = report_snapshots.current_rfi_issue(db, assessment)
    current_document = (
        report_snapshots.read_rfi_document(db, current_issue)
        if current_issue is not None
        else None
    )
    links, link_items = _link_rows(db, assessment)
    current_items = current_document["items"] if current_document else []
    coverage: dict[str, list[str]] = {item["item_id"]: [] for item in current_items}
    for row in links:
        if row.snapshot_id != (current_issue.id if current_issue else None):
            continue
        if row.status != "active":
            continue
        for item_id, _title in row.items:
            coverage.setdefault(item_id, []).append(row.id_prefix)

    received: dict[tuple[str, str], list[dict]] = {}
    link_ids = list(link_items)
    if link_ids:
        events = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.entity_type == "magic_link",
                AuditEvent.action == "magic_link.upload_received",
                AuditEvent.entity_id.in_(link_ids),
            )
            .order_by(literal_column("audit_events.rowid"))
            .all()
        )
        for event in events:
            try:
                metadata = json.loads(event.metadata_json or "{}")
            except (json.JSONDecodeError, TypeError):
                continue
            item_id = link_items.get(event.entity_id, {}).get(metadata.get("item_key"))
            evidence_id = metadata.get("evidence_id")
            evidence = db.get(Evidence, evidence_id) if evidence_id else None
            if item_id is None or evidence is None:
                continue
            snapshot_id = next(
                row.snapshot_id for row in links if row.link_id == event.entity_id
            )
            received.setdefault((snapshot_id, item_id), []).append(
                {
                    "evidence_id": evidence.id,
                    "filename": evidence.original_filename,
                    "status": evidence.status,
                    "uploaded_at": evidence.created_at,
                }
            )

    latest = (
        db.query(AuditEvent)
        .join(ReportSnapshot, AuditEvent.entity_id == ReportSnapshot.id)
        .filter(
            ReportSnapshot.assessment_id == assessment.id,
            ReportSnapshot.type == report_snapshots.RFI_SNAPSHOT_TYPE,
            AuditEvent.entity_type == report_snapshots.AUDIT_ENTITY_TYPE,
            AuditEvent.action.startswith("report_snapshot."),
            AuditEvent.actor.startswith("consultant:"),
        )
        .order_by(
            AuditEvent.created_at.desc(),
            literal_column("audit_events.rowid").desc(),
        )
        .first()
    )
    reviewer_name = latest.actor.removeprefix("consultant:") if latest else ""
    return {
        "assessment": assessment,
        "scope_recorded": scope_recorded,
        "preview": preview,
        "mapped_hints": mapped_hints,
        "versions": versions,
        "current_issue": current_issue,
        "current_items": current_items,
        "links": links,
        "coverage": coverage,
        "received": received,
        "reviewer_name": reviewer_name,
    }
