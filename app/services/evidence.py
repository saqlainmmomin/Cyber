"""Evidence ingestion, lifecycle, storage, and read-time compatibility."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment, AssessmentDocument, _new_id
from app.models.audit_event import AuditEvent
from app.models.engagement import Engagement
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.services.document_processor import detect_file_type, extract_text

logger = logging.getLogger(__name__)

EVIDENCE_STATUSES = ("quarantined", "active", "rejected", "invalidated", "archived")
VERSION_STATUSES = ("quarantined", "active", "superseded", "rejected")
BLOCKING_DUPLICATE_STATUSES = ("quarantined", "active", "invalidated")
RELEVANCE_VALUES = ("primary", "supporting", "contextual")
CONSULTANT_ACTOR = "consultant"
SYSTEM_ACTOR = "system"
SCAN_ACTOR = "system:scan-placeholder"
SCAN_REJECTED_MESSAGE = "File failed the malware scan and was not released from quarantine."

FILE_TYPE_TO_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "txt": "text/plain",
}


class TransitionRule(NamedTuple):
    actor_kind: str
    requires_reason: bool


EVIDENCE_TRANSITIONS = {
    ("quarantined", "active"): TransitionRule("system", False),
    ("quarantined", "rejected"): TransitionRule("system", False),
    ("active", "invalidated"): TransitionRule("consultant", True),
    ("invalidated", "active"): TransitionRule("consultant", True),
    ("active", "archived"): TransitionRule("consultant", False),
    ("invalidated", "archived"): TransitionRule("consultant", False),
    ("rejected", "archived"): TransitionRule("consultant", False),
    ("archived", "active"): TransitionRule("consultant", True),
}
VERSION_TRANSITIONS = frozenset(
    {
        ("quarantined", "active"),
        ("quarantined", "rejected"),
        ("active", "superseded"),
    }
)


class EvidenceError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EvidenceNotFound(EvidenceError):
    status_code = 404


class EvidenceValidationError(EvidenceError):
    status_code = 422


class UnsupportedFileType(EvidenceValidationError):
    status_code = 400


class EvidenceConflict(EvidenceError):
    status_code = 409


class InvalidTransition(EvidenceConflict):
    pass


class DuplicateMapping(EvidenceConflict):
    pass


class EngagementRequired(EvidenceConflict):
    pass


class DuplicateEvidence(EvidenceConflict):
    def __init__(self, message: str, existing_evidence_id: str):
        self.existing_evidence_id = existing_evidence_id
        super().__init__(message)


class TransitionNotPermitted(EvidenceError):
    status_code = 403


@dataclass(frozen=True)
class IngestResult:
    evidence: Evidence
    version: EvidenceVersion
    released: bool


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def evidence_root() -> Path:
    return Path(settings.upload_dir) / "evidence"


def blob_path(storage_path: str) -> Path:
    return Path(settings.upload_dir) / storage_path


def scan_blob(path: Path) -> bool:
    logger.warning(
        "Malware scanning is not configured; auto-releasing %s from quarantine (P2-1 placeholder).",
        path.name,
    )
    return True


def _display_filename(name: str | None) -> str:
    return (name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()[:255] or "document"


def _file_type(filename: str, supplied: str | None) -> str:
    file_type = detect_file_type(filename) if supplied is None else supplied.lower()
    if file_type not in FILE_TYPE_TO_MIME:
        raise UnsupportedFileType(
            "Unsupported file type. Upload PDF, DOCX, PNG, JPG, JPEG, or WEBP files."
        )
    return file_type


def _write_blob(storage_path: str, content: bytes) -> Path:
    path = blob_path(storage_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)
    return path


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


def _audit_version_status(
    db: Session,
    version: EvidenceVersion,
    *,
    from_status: str,
    to_status: str,
    actor: str,
) -> None:
    _audit(
        db,
        actor=actor,
        action="evidence_version.status_changed",
        entity_type="evidence_version",
        entity_id=version.id,
        metadata={"evidence_id": version.evidence_id, "from": from_status, "to": to_status},
    )


def _audit_evidence_status(
    db: Session,
    evidence: Evidence,
    *,
    from_status: str,
    to_status: str,
    reason: str | None,
    actor: str,
) -> None:
    _audit(
        db,
        actor=actor,
        action="evidence.status_changed",
        entity_type="evidence",
        entity_id=evidence.id,
        metadata={"from": from_status, "reason": reason, "to": to_status},
    )


def check_evidence_transition(
    from_status: str, to_status: str, *, actor_kind: str
) -> TransitionRule:
    if to_status not in EVIDENCE_STATUSES:
        raise EvidenceValidationError(f"Unknown evidence status '{to_status}'.")
    rule = EVIDENCE_TRANSITIONS.get((from_status, to_status))
    if rule is None:
        raise InvalidTransition(f"Invalid evidence transition: {from_status} -> {to_status}.")
    if rule.actor_kind != actor_kind:
        if rule.actor_kind == "system":
            raise TransitionNotPermitted(
                f"Transition {from_status} -> {to_status} is system-driven and cannot be requested directly."
            )
        raise TransitionNotPermitted(
            f"Transition {from_status} -> {to_status} requires a consultant."
        )
    return rule


def check_version_transition(from_status: str, to_status: str) -> None:
    if (from_status, to_status) not in VERSION_TRANSITIONS:
        raise InvalidTransition(
            f"Invalid evidence version transition: {from_status} -> {to_status}."
        )


def _duplicate_candidate(
    db: Session,
    *,
    engagement_id: str,
    assessment_id: str | None,
    digest: str,
) -> Evidence | None:
    assessment_filter = (
        Evidence.assessment_id.is_(None)
        if assessment_id is None
        else Evidence.assessment_id == assessment_id
    )
    return (
        db.query(Evidence)
        .join(EvidenceVersion, EvidenceVersion.evidence_id == Evidence.id)
        .filter(
            Evidence.engagement_id == engagement_id,
            assessment_filter,
            Evidence.status.in_(BLOCKING_DUPLICATE_STATUSES),
            EvidenceVersion.file_hash_sha256 == digest,
        )
        .order_by(Evidence.created_at, Evidence.id)
        .first()
    )


def receive_evidence(
    db: Session,
    *,
    engagement_id: str,
    assessment_id: str | None,
    filename: str,
    content: bytes,
    category: str | None,
    uploaded_by: str,
    actor: str,
    file_type: str | None = None,
    evidence_id: str | None = None,
    created_at: datetime | None = None,
    change_reason: str | None = None,
    allow_duplicate: bool = False,
) -> tuple[Evidence, EvidenceVersion]:
    resolved_type = _file_type(filename, file_type)
    if len(content) == 0:
        raise EvidenceValidationError("The uploaded file is empty.")
    digest = sha256_hex(content)
    if not allow_duplicate:
        existing = _duplicate_candidate(
            db,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            digest=digest,
        )
        if existing is not None:
            raise DuplicateEvidence(
                f"This file is identical to '{existing.original_filename}' already in this engagement's evidence.",
                existing.id,
            )

    evidence_id = evidence_id or _new_id()
    version_id = _new_id()
    display_name = _display_filename(filename)
    storage_path = f"evidence/{engagement_id}/{evidence_id}/v1.{resolved_type}"
    written_path = _write_blob(storage_path, content)
    try:
        evidence = Evidence(
            id=evidence_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            document_category=category or None,
            original_filename=display_name,
            storage_path=storage_path,
            file_hash_sha256=digest,
            file_size_bytes=len(content),
            mime_type=FILE_TYPE_TO_MIME[resolved_type],
            status="quarantined",
            uploaded_by=uploaded_by,
        )
        version = EvidenceVersion(
            id=version_id,
            evidence_id=evidence_id,
            version_number=1,
            storage_path=storage_path,
            file_hash_sha256=digest,
            file_size_bytes=len(content),
            change_reason=change_reason,
            status="quarantined",
            original_filename=display_name,
            mime_type=FILE_TYPE_TO_MIME[resolved_type],
        )
        if created_at is not None:
            evidence.created_at = created_at
            version.created_at = created_at
        db.add_all([evidence, version])
        _audit(
            db,
            actor=actor,
            action="evidence.created",
            entity_type="evidence",
            entity_id=evidence.id,
            metadata={
                "assessment_id": assessment_id,
                "sha256": digest,
                "size_bytes": len(content),
                "uploaded_by": uploaded_by,
                "version_id": version.id,
            },
        )
        _audit(
            db,
            actor=actor,
            action="evidence_version.created",
            entity_type="evidence_version",
            entity_id=version.id,
            metadata={
                "change_reason": change_reason,
                "evidence_id": evidence.id,
                "sha256": digest,
                "size_bytes": len(content),
                "version_number": 1,
            },
        )
        db.flush()
        return evidence, version
    except Exception:
        db.rollback()
        written_path.unlink(missing_ok=True)
        raise


def receive_version(
    db: Session,
    *,
    evidence_id: str,
    filename: str,
    content: bytes,
    change_reason: str,
    actor: str,
    file_type: str | None = None,
) -> EvidenceVersion:
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise EvidenceNotFound("Evidence not found")
    if evidence.status not in ("active", "invalidated"):
        raise InvalidTransition(f"Cannot add a version to evidence in status '{evidence.status}'.")
    if (
        db.query(EvidenceVersion)
        .filter(
            EvidenceVersion.evidence_id == evidence_id,
            EvidenceVersion.status == "quarantined",
        )
        .first()
        is not None
    ):
        raise InvalidTransition("A new version is already awaiting release from quarantine.")
    if not (change_reason or "").strip():
        raise EvidenceValidationError("A change reason is required when uploading a new version.")
    resolved_type = _file_type(filename, file_type)
    if len(content) == 0:
        raise EvidenceValidationError("The uploaded file is empty.")
    digest = sha256_hex(content)
    current = current_version(db, evidence_id)
    if current is not None and current.file_hash_sha256 == digest:
        raise DuplicateEvidence(
            f"This file is identical to the current version (v{current.version_number}).",
            evidence_id,
        )

    version_number = (
        db.query(func.max(EvidenceVersion.version_number))
        .filter(EvidenceVersion.evidence_id == evidence_id)
        .scalar()
        or 0
    ) + 1
    storage_path = f"evidence/{evidence.engagement_id}/{evidence.id}/v{version_number}.{resolved_type}"
    written_path = _write_blob(storage_path, content)
    try:
        version = EvidenceVersion(
            id=_new_id(),
            evidence_id=evidence.id,
            version_number=version_number,
            storage_path=storage_path,
            file_hash_sha256=digest,
            file_size_bytes=len(content),
            change_reason=change_reason.strip(),
            status="quarantined",
            original_filename=_display_filename(filename),
            mime_type=FILE_TYPE_TO_MIME[resolved_type],
        )
        db.add(version)
        _audit(
            db,
            actor=actor,
            action="evidence_version.created",
            entity_type="evidence_version",
            entity_id=version.id,
            metadata={
                "change_reason": version.change_reason,
                "evidence_id": evidence.id,
                "sha256": digest,
                "size_bytes": len(content),
                "version_number": version_number,
            },
        )
        db.flush()
        return version
    except Exception:
        db.rollback()
        written_path.unlink(missing_ok=True)
        raise


def release_from_quarantine(
    db: Session, *, version_id: str, actor: str = SCAN_ACTOR
) -> EvidenceVersion:
    version = db.get(EvidenceVersion, version_id)
    if version is None:
        raise EvidenceNotFound("Evidence version not found")
    check_version_transition(version.status, "active")
    evidence = db.get(Evidence, version.evidence_id)
    if evidence is None:
        raise EvidenceNotFound("Evidence not found")

    passed = scan_blob(blob_path(version.storage_path))
    if not passed:
        from_status = version.status
        check_version_transition(from_status, "rejected")
        version.status = "rejected"
        _audit_version_status(
            db, version, from_status=from_status, to_status="rejected", actor=actor
        )
        if evidence.status == "quarantined":
            evidence_from = evidence.status
            check_evidence_transition(evidence_from, "rejected", actor_kind="system")
            evidence.status = "rejected"
            _audit_evidence_status(
                db,
                evidence,
                from_status=evidence_from,
                to_status="rejected",
                reason=None,
                actor=actor,
            )
        db.flush()
        return version

    active_versions = (
        db.query(EvidenceVersion)
        .filter(
            EvidenceVersion.evidence_id == evidence.id,
            EvidenceVersion.status == "active",
            EvidenceVersion.id != version.id,
        )
        .order_by(EvidenceVersion.version_number)
        .all()
    )
    for prior in active_versions:
        check_version_transition(prior.status, "superseded")
        prior_from = prior.status
        prior.status = "superseded"
        _audit_version_status(
            db, prior, from_status=prior_from, to_status="superseded", actor=actor
        )

    version_from = version.status
    version.status = "active"
    _audit_version_status(
        db, version, from_status=version_from, to_status="active", actor=actor
    )
    if evidence.status == "quarantined":
        evidence_from = evidence.status
        check_evidence_transition(evidence_from, "active", actor_kind="system")
        evidence.status = "active"
        _audit_evidence_status(
            db,
            evidence,
            from_status=evidence_from,
            to_status="active",
            reason=None,
            actor=actor,
        )
    db.flush()
    return version


def transition_evidence(
    db: Session,
    *,
    evidence_id: str,
    to_status: str,
    actor: str,
    reason: str | None = None,
) -> Evidence:
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise EvidenceNotFound("Evidence not found")
    rule = check_evidence_transition(evidence.status, to_status, actor_kind="consultant")
    clean_reason = reason.strip() if isinstance(reason, str) else None
    if rule.requires_reason and not clean_reason:
        raise EvidenceValidationError("A reason is required for this transition.")
    if to_status == "active":
        active = current_version(db, evidence.id)
        if active is None:
            raise InvalidTransition("Evidence has no active version to restore.")
    from_status = evidence.status
    evidence.status = to_status
    _audit_evidence_status(
        db,
        evidence,
        from_status=from_status,
        to_status=to_status,
        reason=clean_reason,
        actor=actor,
    )
    db.flush()
    return evidence


def map_evidence(
    db: Session,
    *,
    evidence_id: str,
    assessment_id: str,
    framework_id: str,
    requirement_id: str,
    relevance: str,
    actor: str,
) -> EvidenceUse:
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise EvidenceNotFound("Evidence not found")
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise EvidenceNotFound("Assessment not found")
    if evidence.engagement_id != assessment.engagement_id:
        raise EvidenceValidationError("Evidence and assessment belong to different engagements.")
    if evidence.status != "active":
        raise EvidenceConflict("Only active evidence can be mapped to a requirement.")
    if framework_id not in assessment.frameworks:
        raise EvidenceValidationError(
            f"Framework '{framework_id}' is not selected for this assessment."
        )
    try:
        controls = FrameworkRegistry.get_all_controls(framework_id)
    except KeyError:
        controls = []
    if requirement_id not in {control.id for control in controls}:
        raise EvidenceValidationError(
            f"Unknown requirement '{requirement_id}' for framework '{framework_id}'."
        )
    if relevance not in RELEVANCE_VALUES:
        raise EvidenceValidationError(
            "Relevance must be one of: primary, supporting, contextual."
        )
    duplicate = (
        db.query(EvidenceUse)
        .filter(
            EvidenceUse.evidence_id == evidence_id,
            EvidenceUse.assessment_id == assessment_id,
            EvidenceUse.framework_id == framework_id,
            EvidenceUse.requirement_id == requirement_id,
        )
        .first()
    )
    if duplicate is not None:
        raise DuplicateMapping("This evidence is already mapped to that requirement.")
    use = EvidenceUse(
        id=_new_id(),
        evidence_id=evidence_id,
        assessment_id=assessment_id,
        framework_id=framework_id,
        requirement_id=requirement_id,
        relevance=relevance,
    )
    db.add(use)
    metadata = {
        "assessment_id": assessment_id,
        "evidence_id": evidence_id,
        "framework_id": framework_id,
        "relevance": relevance,
        "requirement_id": requirement_id,
    }
    _audit(
        db,
        actor=actor,
        action="evidence_use.created",
        entity_type="evidence_use",
        entity_id=use.id,
        metadata=metadata,
    )
    db.flush()
    return use


def unmap_evidence(db: Session, *, evidence_id: str, use_id: str, actor: str) -> None:
    use = db.get(EvidenceUse, use_id)
    if use is None or use.evidence_id != evidence_id:
        raise EvidenceNotFound("Evidence use not found")
    metadata = {
        "assessment_id": use.assessment_id,
        "evidence_id": use.evidence_id,
        "framework_id": use.framework_id,
        "relevance": use.relevance,
        "requirement_id": use.requirement_id,
    }
    _audit(
        db,
        actor=actor,
        action="evidence_use.deleted",
        entity_type="evidence_use",
        entity_id=use.id,
        metadata=metadata,
    )
    db.delete(use)
    db.flush()


def ingest_upload(
    db: Session,
    *,
    assessment_id: str,
    filename: str,
    content: bytes,
    category: str | None,
    uploaded_by: str = CONSULTANT_ACTOR,
) -> IngestResult:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise EvidenceNotFound("Assessment not found")
    if assessment.engagement_id is None:
        raise EngagementRequired(
            "This assessment is not linked to an engagement. Run scripts/migrate_legacy.py before uploading evidence."
        )
    written_paths: list[Path] = []
    try:
        evidence, version = receive_evidence(
            db,
            engagement_id=assessment.engagement_id,
            assessment_id=assessment.id,
            filename=filename,
            content=content,
            category=category,
            uploaded_by=uploaded_by,
            actor=uploaded_by,
        )
        written_paths.append(blob_path(version.storage_path))
        released_version = release_from_quarantine(db, version_id=version.id)
        if released_version.status != "active":
            db.commit()
            return IngestResult(evidence, released_version, False)
        extracted = extract_text(
            blob_path(released_version.storage_path),
            Path(released_version.storage_path).suffix.removeprefix("."),
        )
        if not extracted.strip():
            raise EvidenceValidationError(
                "Could not extract text from this document. If it is a scanned PDF, try uploading it as a PNG or JPEG screenshot instead."
            )
        released_version.extracted_text = extracted
        if assessment.status == "created":
            assessment.status = "documents_uploaded"
        db.commit()
        return IngestResult(evidence, released_version, True)
    except Exception:
        db.rollback()
        for path in written_paths:
            path.unlink(missing_ok=True)
        raise


def ingest_engagement_upload(
    db: Session,
    *,
    engagement_id: str,
    filename: str,
    content: bytes,
    category: str | None,
    uploaded_by: str,
    change_reason: str | None = None,
    evidence_id: str | None = None,
    allow_duplicate: bool = False,
) -> IngestResult:
    """Ingest an engagement-level receipt without changing an assessment."""
    engagement = db.get(Engagement, engagement_id)
    if engagement is None:
        raise EvidenceNotFound("Engagement not found")

    written_paths: list[Path] = []
    try:
        evidence, version = receive_evidence(
            db,
            engagement_id=engagement.id,
            assessment_id=None,
            filename=filename,
            content=content,
            category=category,
            uploaded_by=uploaded_by,
            actor=uploaded_by,
            evidence_id=evidence_id,
            change_reason=change_reason,
            allow_duplicate=allow_duplicate,
        )
        written_paths.append(blob_path(version.storage_path))
        released_version = release_from_quarantine(db, version_id=version.id)
        if released_version.status != "active":
            db.commit()
            return IngestResult(evidence, released_version, False)

        extracted = extract_text(
            blob_path(released_version.storage_path),
            Path(released_version.storage_path).suffix.removeprefix("."),
        )
        if not extracted.strip():
            raise EvidenceValidationError(
                "Could not extract text from this document. If it is a scanned PDF, "
                "try uploading it as a PNG or JPEG screenshot instead."
            )
        released_version.extracted_text = extracted
        db.commit()
        return IngestResult(evidence, released_version, True)
    except Exception:
        db.rollback()
        for path in written_paths:
            path.unlink(missing_ok=True)
        raise


def ingest_new_version(
    db: Session,
    *,
    evidence_id: str,
    filename: str,
    content: bytes,
    change_reason: str,
    actor: str = CONSULTANT_ACTOR,
) -> IngestResult:
    written_paths: list[Path] = []
    try:
        version = receive_version(
            db,
            evidence_id=evidence_id,
            filename=filename,
            content=content,
            change_reason=change_reason,
            actor=actor,
        )
        written_paths.append(blob_path(version.storage_path))
        released_version = release_from_quarantine(db, version_id=version.id)
        evidence = db.get(Evidence, evidence_id)
        if released_version.status != "active":
            db.commit()
            return IngestResult(evidence, released_version, False)
        extracted = extract_text(
            blob_path(released_version.storage_path),
            Path(released_version.storage_path).suffix.removeprefix("."),
        )
        if not extracted.strip():
            raise EvidenceValidationError(
                "Could not extract text from this document. If it is a scanned PDF, try uploading it as a PNG or JPEG screenshot instead."
            )
        released_version.extracted_text = extracted
        db.commit()
        return IngestResult(evidence, released_version, True)
    except Exception:
        db.rollback()
        for path in written_paths:
            path.unlink(missing_ok=True)
        raise


def current_version(db: Session, evidence_id: str) -> EvidenceVersion | None:
    return (
        db.query(EvidenceVersion)
        .filter(
            EvidenceVersion.evidence_id == evidence_id,
            EvidenceVersion.status == "active",
        )
        .order_by(EvidenceVersion.version_number.desc())
        .first()
    )


def verify_version(db: Session, version_id: str) -> bool:
    version = db.get(EvidenceVersion, version_id)
    if version is None:
        return False
    path = blob_path(version.storage_path)
    if not path.is_file():
        return False
    return sha256_hex(path.read_bytes()) == version.file_hash_sha256


def active_versions_in_scope(
    db: Session, assessment_id: str
) -> list[tuple[Evidence, EvidenceVersion]]:
    """Return active Evidence and its active version when in assessment scope."""
    used = select(EvidenceUse.evidence_id).where(EvidenceUse.assessment_id == assessment_id)
    evidence_rows = (
        db.query(Evidence)
        .filter(
            Evidence.status == "active",
            or_(Evidence.assessment_id == assessment_id, Evidence.id.in_(used)),
        )
        .order_by(Evidence.created_at, Evidence.id)
        .all()
    )
    evidence_ids = [row.id for row in evidence_rows]
    if not evidence_ids:
        return []
    versions = (
        db.query(EvidenceVersion)
        .filter(
            EvidenceVersion.evidence_id.in_(evidence_ids),
            EvidenceVersion.status == "active",
        )
        .order_by(EvidenceVersion.evidence_id, EvidenceVersion.version_number.desc())
        .all()
    )
    active_by_evidence: dict[str, EvidenceVersion] = {}
    for version in versions:
        active_by_evidence.setdefault(version.evidence_id, version)
    return [
        (evidence, active_by_evidence[evidence.id])
        for evidence in evidence_rows
        if evidence.id in active_by_evidence
    ]


def analysis_documents(db: Session, assessment_id: str) -> list[dict]:
    active_pairs = active_versions_in_scope(db, assessment_id)
    legacy_pairs = (
        db.query(AssessmentDocument, Evidence.id)
        .outerjoin(Evidence, Evidence.id == AssessmentDocument.id)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .order_by(AssessmentDocument.uploaded_at, AssessmentDocument.id)
        .all()
    )
    legacy_rows = [row for row, _evidence_id in legacy_pairs]
    migrated_ids = {evidence_id for _row, evidence_id in legacy_pairs if evidence_id is not None}

    documents = []
    for evidence, version in active_pairs:
        documents.append(
            {
                "id": evidence.id,
                "filename": version.original_filename,
                "category": evidence.document_category or "other",
                "text": version.extracted_text or "",
                "legacy_document_id": evidence.id if evidence.id in migrated_ids else None,
                "source": "evidence",
            }
        )
    documents.extend(
        {
            "id": row.id,
            "filename": row.filename,
            "category": row.document_category,
            "text": row.extracted_text or "",
            "legacy_document_id": row.id,
            "source": "legacy",
        }
        for row in legacy_rows
        if row.id not in migrated_ids
    )
    return documents


def evidence_panel_rows(db: Session, assessment_id: str) -> list[dict]:
    used = select(EvidenceUse.evidence_id).where(EvidenceUse.assessment_id == assessment_id)
    evidence_rows = (
        db.query(Evidence)
        .filter(
            Evidence.status != "archived",
            or_(Evidence.assessment_id == assessment_id, Evidence.id.in_(used)),
        )
        .all()
    )
    evidence_ids = [row.id for row in evidence_rows]
    versions = (
        db.query(EvidenceVersion)
        .filter(EvidenceVersion.evidence_id.in_(evidence_ids))
        .order_by(EvidenceVersion.version_number)
        .all()
        if evidence_ids
        else []
    )
    versions_by_evidence: dict[str, list[EvidenceVersion]] = {}
    for version in versions:
        versions_by_evidence.setdefault(version.evidence_id, []).append(version)
    legacy_pairs = (
        db.query(AssessmentDocument, Evidence.id)
        .outerjoin(Evidence, Evidence.id == AssessmentDocument.id)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .all()
    )
    legacy_rows = [row for row, _evidence_id in legacy_pairs]
    migrated_ids = {evidence_id for _row, evidence_id in legacy_pairs if evidence_id is not None}

    rows = []
    for evidence in evidence_rows:
        evidence_versions = versions_by_evidence.get(evidence.id, [])
        active = next((version for version in evidence_versions if version.status == "active"), None)
        displayed = active or (evidence_versions[-1] if evidence_versions else None)
        mapped_in = evidence.assessment_id != assessment_id
        rows.append(
            {
                "id": evidence.id,
                "source": "evidence",
                "filename": displayed.original_filename if displayed else evidence.original_filename,
                "category": evidence.document_category or "other",
                "file_type": (
                    Path(displayed.storage_path).suffix.removeprefix(".")
                    if displayed
                    else Path(evidence.storage_path).suffix.removeprefix(".")
                ),
                "status": evidence.status,
                "version_count": len(evidence_versions),
                "current_version_number": active.version_number if active else None,
                "sha256_prefix": displayed.file_hash_sha256[:12] if displayed else None,
                "text_length": len(displayed.extracted_text or "") if displayed else 0,
                "uploaded_at": evidence.created_at,
                "mapped_in": mapped_in,
                "can_archive": not mapped_in
                and evidence.status in {"active", "invalidated", "rejected"},
                "can_add_version": not mapped_in
                and evidence.status in {"active", "invalidated"}
                and not any(version.status == "quarantined" for version in evidence_versions),
            }
        )
    rows.extend(
        {
            "id": row.id,
            "source": "legacy",
            "filename": row.filename,
            "category": row.document_category,
            "file_type": row.file_type,
            "status": "legacy",
            "version_count": 1,
            "current_version_number": None,
            "sha256_prefix": None,
            "text_length": len(row.extracted_text or ""),
            "uploaded_at": row.uploaded_at,
            "mapped_in": False,
            "can_archive": False,
            "can_add_version": False,
        }
        for row in legacy_rows
        if row.id not in migrated_ids
    )
    rows.sort(key=lambda row: (row["uploaded_at"], row["id"]), reverse=True)
    return rows


def _version_detail(version: EvidenceVersion) -> dict:
    return {
        "id": version.id,
        "version_number": version.version_number,
        "status": version.status,
        "original_filename": version.original_filename,
        "mime_type": version.mime_type,
        "file_hash_sha256": version.file_hash_sha256,
        "file_size_bytes": version.file_size_bytes,
        "change_reason": version.change_reason,
        "text_length": len(version.extracted_text or ""),
        "created_at": version.created_at,
    }


def evidence_detail(db: Session, evidence_id: str) -> dict:
    evidence = db.get(Evidence, evidence_id)
    if evidence is None:
        raise EvidenceNotFound("Evidence not found")
    versions = (
        db.query(EvidenceVersion)
        .filter(EvidenceVersion.evidence_id == evidence_id)
        .order_by(EvidenceVersion.version_number)
        .all()
    )
    uses = (
        db.query(EvidenceUse)
        .filter(EvidenceUse.evidence_id == evidence_id)
        .order_by(EvidenceUse.created_at, EvidenceUse.id)
        .all()
    )
    version_details = [_version_detail(version) for version in versions]
    active = next((version for version in versions if version.status == "active"), None)
    return {
        "id": evidence.id,
        "engagement_id": evidence.engagement_id,
        "assessment_id": evidence.assessment_id,
        "original_filename": evidence.original_filename,
        "mime_type": evidence.mime_type,
        "document_category": evidence.document_category,
        "status": evidence.status,
        "uploaded_by": evidence.uploaded_by,
        "file_hash_sha256": evidence.file_hash_sha256,
        "file_size_bytes": evidence.file_size_bytes,
        "created_at": evidence.created_at,
        "current_version": _version_detail(active) if active else None,
        "versions": version_details,
        "uses": [
            {
                "id": use.id,
                "evidence_id": use.evidence_id,
                "assessment_id": use.assessment_id,
                "framework_id": use.framework_id,
                "requirement_id": use.requirement_id,
                "relevance": use.relevance,
                "created_at": use.created_at,
            }
            for use in uses
        ],
    }
