"""Consultant-confirmed evidence reuse across the assessments of one engagement (P4-2, PR-025): read-only reuse suggestions with age and scope warnings, and an audited confirmation that creates the EvidenceUse link. Never commits."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.frameworks.registry import FrameworkRegistry
from app.models.assessment import Assessment
from app.models.audit_event import AuditEvent
from app.models.evidence import Evidence, EvidenceUse, EvidenceVersion
from app.services import evidence as evidence_service

REUSE_AGE_WARNING_DAYS = 180
WARNING_AGE = "age"
WARNING_SCOPE = "scope"
WARNING_ORDER = (WARNING_AGE, WARNING_SCOPE)
REUSE_CONFIRMED_ACTION = "evidence_reuse.confirmed"
REUSE_ENTITY_TYPE = "evidence_use"
AUDIT_METADATA_KEYS = (
    "acknowledged_warnings",
    "age_days",
    "evidence_id",
    "evidence_version_id",
    "framework_id",
    "reference_date",
    "requirement_id",
    "sha256",
    "source_assessment_id",
    "source_use_id",
    "warnings",
)

ASSESSMENT_NOT_FOUND = "Assessment not found"
REUSE_NOT_AVAILABLE = (
    "This evidence is no longer available for reuse in this assessment. Reload the page. Nothing was saved."
)
REUSE_ACK_REQUIRED = (
    "Confirm that this evidence still applies despite the warnings shown. Nothing was saved."
)


class ReuseError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ReuseNotFound(ReuseError):
    status_code = 404


class ReuseNotAvailable(ReuseError):
    status_code = 409


class ReuseAcknowledgementRequired(ReuseError):
    status_code = 400


@dataclass(frozen=True)
class ReuseCandidate:
    source_use_id: str
    evidence_id: str
    evidence_version_id: str
    version_number: int
    filename: str
    sha256: str
    evidence_status: str
    source_assessment_id: str
    source_assessment_label: str
    source_framework_ids: tuple[str, ...]
    framework_id: str
    requirement_id: str
    relevance: str
    received_on: date
    reference_date: date
    age_days: int
    warnings: tuple[str, ...]


def _assessment(db: Session, assessment_id: str) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise ReuseNotFound(ASSESSMENT_NOT_FOUND)
    return assessment


def _framework_names(framework_ids: tuple[str, ...]) -> list[str]:
    return [
        (FrameworkRegistry.get_or_none(framework_id).name
         if FrameworkRegistry.get_or_none(framework_id)
         else framework_id.upper())
        for framework_id in framework_ids
    ]


def reuse_candidates(db: Session, assessment_id: str) -> list[ReuseCandidate]:
    target = _assessment(db, assessment_id)
    if target.engagement_id is None:
        return []

    target_frameworks = tuple(target.frameworks)
    target_uses = (
        db.query(EvidenceUse)
        .filter(EvidenceUse.assessment_id == target.id)
        .all()
    )
    existing = {
        (use.evidence_id, use.framework_id, use.requirement_id)
        for use in target_uses
    }

    source_rows = (
        db.query(EvidenceUse, Evidence, Assessment)
        .join(Evidence, Evidence.id == EvidenceUse.evidence_id)
        .join(Assessment, Assessment.id == EvidenceUse.assessment_id)
        .filter(
            Assessment.engagement_id == target.engagement_id,
            Assessment.id != target.id,
            Assessment.status != "archived",
            Evidence.engagement_id == target.engagement_id,
            Evidence.status == "active",
            EvidenceUse.framework_id.in_(target_frameworks),
        )
        .order_by(EvidenceUse.created_at, EvidenceUse.id)
        .all()
    )
    evidence_ids = list({evidence.id for _use, evidence, _source in source_rows})
    versions = (
        db.query(EvidenceVersion)
        .filter(
            EvidenceVersion.evidence_id.in_(evidence_ids),
            EvidenceVersion.status == "active",
        )
        .order_by(EvidenceVersion.evidence_id, EvidenceVersion.version_number.desc())
        .all()
        if evidence_ids
        else []
    )
    current_versions: dict[str, EvidenceVersion] = {}
    for version in versions:
        current_versions.setdefault(version.evidence_id, version)

    deduplicated: dict[tuple[str, str, str], tuple[EvidenceUse, Evidence, Assessment]] = {}
    for use, evidence, source in source_rows:
        key = (evidence.id, use.framework_id, use.requirement_id)
        if key in existing or key in deduplicated:
            continue
        if evidence.id not in current_versions:
            continue
        deduplicated[key] = (use, evidence, source)

    candidates = []
    reference_date = target.created_at.date()
    for use, evidence, source in deduplicated.values():
        version = current_versions[evidence.id]
        received_on = version.created_at.date()
        age_days = (reference_date - received_on).days
        warnings = tuple(
            warning
            for warning in WARNING_ORDER
            if (
                warning == WARNING_AGE and age_days > REUSE_AGE_WARNING_DAYS
            )
            or (warning == WARNING_SCOPE and set(source.frameworks) != set(target_frameworks))
        )
        source_framework_ids = tuple(source.frameworks)
        candidates.append(
            ReuseCandidate(
                source_use_id=use.id,
                evidence_id=evidence.id,
                evidence_version_id=version.id,
                version_number=version.version_number,
                filename=version.original_filename,
                sha256=version.file_hash_sha256,
                evidence_status=evidence.status,
                source_assessment_id=source.id,
                source_assessment_label=(
                    f"{source.description or source.company_name} ({source.created_at:%d %b %Y})"
                ),
                source_framework_ids=source_framework_ids,
                framework_id=use.framework_id,
                requirement_id=use.requirement_id,
                relevance=use.relevance,
                received_on=received_on,
                reference_date=reference_date,
                age_days=age_days,
                warnings=warnings,
            )
        )
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.received_on,
            candidate.filename,
            candidate.framework_id,
            candidate.requirement_id,
            candidate.source_use_id,
        ),
    )


def confirm_reuse(
    db: Session,
    *,
    assessment_id: str,
    source_use_id: str,
    acknowledge_warnings: bool,
    actor: str,
) -> EvidenceUse:
    candidate = next(
        (item for item in reuse_candidates(db, assessment_id) if item.source_use_id == source_use_id),
        None,
    )
    if candidate is None:
        raise ReuseNotAvailable(REUSE_NOT_AVAILABLE)
    if candidate.warnings and not acknowledge_warnings:
        raise ReuseAcknowledgementRequired(REUSE_ACK_REQUIRED)

    use = evidence_service.map_evidence(
        db,
        evidence_id=candidate.evidence_id,
        assessment_id=assessment_id,
        framework_id=candidate.framework_id,
        requirement_id=candidate.requirement_id,
        relevance=candidate.relevance,
        actor=actor,
    )
    metadata = {
        "acknowledged_warnings": bool(acknowledge_warnings),
        "age_days": candidate.age_days,
        "evidence_id": candidate.evidence_id,
        "evidence_version_id": candidate.evidence_version_id,
        "framework_id": candidate.framework_id,
        "reference_date": candidate.reference_date.isoformat(),
        "requirement_id": candidate.requirement_id,
        "sha256": candidate.sha256,
        "source_assessment_id": candidate.source_assessment_id,
        "source_use_id": candidate.source_use_id,
        "warnings": list(candidate.warnings),
    }
    db.add(
        AuditEvent(
            actor=actor,
            action=REUSE_CONFIRMED_ACTION,
            entity_type=REUSE_ENTITY_TYPE,
            entity_id=use.id,
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
    )
    db.flush()
    return use
