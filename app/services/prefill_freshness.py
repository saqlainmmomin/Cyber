"""Pre-fill freshness (Yozora): how many documents a questionnaire pre-fill (desk review) would read
now, and how many of them arrived after the last completed one. Feeds "5 documents ready to
pre-fill" and "3 new documents since the last pre-fill". Read-only; never calls a model.

Available documents are exactly what desk review reads: app.services.evidence.analysis_documents
(active evidence uploaded to or mapped into the assessment, plus unmigrated legacy documents).
A document counts as new when its active version, or its mapping into this assessment, is newer
than the completion time of the last completed desk review. With no completed desk review, every
available document is new.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, AssessmentDocument
from app.models.desk_review import DeskReviewSummary
from app.models.evidence import EvidenceUse
from app.services import evidence as evidence_service


@dataclass(frozen=True)
class PrefillFreshness:
    available: int
    new_since_last_prefill: int
    last_prefill_at: datetime | None


def _as_utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def last_prefill_at(db: Session, assessment: Assessment) -> datetime | None:
    summary = db.execute(
        select(DeskReviewSummary).where(DeskReviewSummary.assessment_id == assessment.id)
    ).scalars().first()
    if summary is None or summary.status != "completed" or summary.completed_at is None:
        return None
    return _as_utc(summary.completed_at)


def freshness(db: Session, assessment: Assessment) -> PrefillFreshness:
    documents = evidence_service.analysis_documents(db, assessment.id)
    cutoff = last_prefill_at(db, assessment)
    if cutoff is None:
        return PrefillFreshness(len(documents), len(documents), None)

    arrived: dict[str, datetime] = {}
    for evidence, version in evidence_service.active_versions_in_scope(db, assessment.id):
        arrived[evidence.id] = _as_utc(version.created_at)
    if arrived:
        for evidence_id, mapped_at in db.execute(
            select(EvidenceUse.evidence_id, EvidenceUse.created_at).where(
                EvidenceUse.assessment_id == assessment.id,
                EvidenceUse.evidence_id.in_(list(arrived)),
            )
        ).all():
            arrived[evidence_id] = max(arrived[evidence_id], _as_utc(mapped_at))
    legacy_ids = [doc["id"] for doc in documents if doc["source"] == "legacy"]
    if legacy_ids:
        for document_id, uploaded_at in db.execute(
            select(AssessmentDocument.id, AssessmentDocument.uploaded_at).where(
                AssessmentDocument.id.in_(legacy_ids)
            )
        ).all():
            arrived[document_id] = _as_utc(uploaded_at)
    new = sum(1 for doc in documents if doc["id"] in arrived and arrived[doc["id"]] > cutoff)
    return PrefillFreshness(len(documents), new, cutoff)
