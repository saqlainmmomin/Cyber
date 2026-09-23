from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id"), index=True
    )
    assessment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=True, index=True
    )
    document_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # original_filename, storage_path, file_hash_sha256, file_size_bytes and mime_type record the FIRST receipt (v1) and are frozen at creation. Never read them to get current content: use app.services.evidence.current_version().
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    file_hash_sha256: Mapped[str] = mapped_column(String(64))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    uploaded_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvidenceVersion(Base):
    __tablename__ = "evidence_versions"
    __table_args__ = (
        UniqueConstraint(
            "evidence_id",
            "version_number",
            name="uq_evidence_versions_evidence_id_version_number",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))
    file_hash_sha256: Mapped[str] = mapped_column(String(64), index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="quarantined")
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvidenceUse(Base):
    __tablename__ = "evidence_uses"
    __table_args__ = (
        UniqueConstraint(
            "evidence_id",
            "assessment_id",
            "framework_id",
            "requirement_id",
            name="uq_evidence_uses_mapping",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence.id"), index=True)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), index=True
    )
    requirement_id: Mapped[str] = mapped_column(String(100))
    framework_id: Mapped[str] = mapped_column(String(50))
    relevance: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
