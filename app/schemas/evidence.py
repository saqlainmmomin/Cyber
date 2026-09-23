from datetime import datetime

from pydantic import BaseModel


class EvidenceVersionOut(BaseModel):
    id: str
    version_number: int
    status: str
    original_filename: str
    mime_type: str
    file_hash_sha256: str
    file_size_bytes: int
    change_reason: str | None
    text_length: int
    created_at: datetime


class EvidenceUseOut(BaseModel):
    id: str
    evidence_id: str
    assessment_id: str
    framework_id: str
    requirement_id: str
    relevance: str
    created_at: datetime


class EvidenceOut(BaseModel):
    id: str
    engagement_id: str
    assessment_id: str | None
    original_filename: str
    mime_type: str
    document_category: str | None
    status: str
    uploaded_by: str
    file_hash_sha256: str
    file_size_bytes: int
    created_at: datetime
    current_version: EvidenceVersionOut | None
    versions: list[EvidenceVersionOut]
    uses: list[EvidenceUseOut]


class EvidenceTransitionIn(BaseModel):
    to_status: str
    reason: str | None = None


class EvidenceUseIn(BaseModel):
    assessment_id: str
    framework_id: str
    requirement_id: str
    relevance: str
