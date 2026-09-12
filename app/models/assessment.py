import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    company_name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(100))
    company_size: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created")
    # Phase 0 — scope
    scope_answers: Mapped[str | None] = mapped_column(Text, nullable=True)          # JSON: {SCP.1: ..., ...}
    applicable_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: [req_id, ...]
    # Phase 1 — context
    context_answers: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    desk_review_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # pending|analyzing|completed|error
    # Phase 3 — domain-level screening pass
    screening_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # not_started|completed
    screening_results: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: {req_id: {status, confidence}}
    # Multi-framework support
    selected_frameworks: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: ["dpdpa", "iso27001", ...]
    review_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    @property
    def frameworks(self) -> list[str]:
        """Return the selected framework ids, including the legacy DPDPA default."""
        if not self.selected_frameworks:
            return ["dpdpa"]
        try:
            frameworks = json.loads(self.selected_frameworks)
        except (json.JSONDecodeError, TypeError):
            return ["dpdpa"]
        return frameworks if isinstance(frameworks, list) and frameworks else ["dpdpa"]

    @validates("selected_frameworks")
    def validate_selected_frameworks(self, _key: str, value: str | None) -> str | None:
        """Reject explicit empty selections while allowing historical NULL rows."""
        if value is None:
            return value
        try:
            frameworks = json.loads(value)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("selected_frameworks must be a JSON list") from exc
        if not isinstance(frameworks, list) or not frameworks:
            raise ValueError("At least one framework must be selected")
        if not all(isinstance(framework, str) and framework for framework in frameworks):
            raise ValueError("Framework ids must be non-empty strings")
        return value

    @property
    def is_multi_framework(self) -> bool:
        return len(self.frameworks) > 1


class AssessmentDocument(Base):
    __tablename__ = "assessment_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str] = mapped_column(String(36), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(10))
    document_category: Mapped[str] = mapped_column(String(50))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
