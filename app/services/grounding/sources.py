"""Immutable source-document inputs for the grounding pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.assessment import AssessmentDocument
from app.services.evidence import (
    FILE_TYPE_TO_MIME,
    active_versions_in_scope,
    analysis_documents,
)


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    evidence_id: str | None
    evidence_version_id: str | None
    legacy_document_id: str | None
    filename: str
    category: str
    mime_type: str | None
    text: str

    @property
    def text_sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @property
    def derived_from_image(self) -> bool:
        return self.mime_type is not None and self.mime_type.startswith("image/")


def load_source_documents(db: Session, assessment_id: str) -> list[SourceDocument]:
    """Load the same ordered, active documents used by the analysis reader."""
    active_by_evidence = {
        evidence.id: version
        for evidence, version in active_versions_in_scope(db, assessment_id)
    }
    result: list[SourceDocument] = []
    for document in analysis_documents(db, assessment_id):
        if document["source"] == "evidence":
            version = active_by_evidence[document["id"]]
            result.append(
                SourceDocument(
                    source_id=f"ev:{version.id}",
                    evidence_id=document["id"],
                    evidence_version_id=version.id,
                    legacy_document_id=None,
                    filename=document["filename"],
                    category=document["category"],
                    mime_type=version.mime_type,
                    text=version.extracted_text or "",
                )
            )
            continue

        legacy = db.get(AssessmentDocument, document["id"])
        file_type = (legacy.file_type or "").lower().lstrip(".") if legacy else ""
        result.append(
            SourceDocument(
                source_id=f"legacy:{document['id']}",
                evidence_id=None,
                evidence_version_id=None,
                legacy_document_id=document["id"],
                filename=document["filename"],
                category=document["category"],
                mime_type=FILE_TYPE_TO_MIME.get(file_type),
                text=(legacy.extracted_text if legacy else None) or "",
            )
        )
    return result
