"""Models for the desk review pipeline (Call 0 — pre-questionnaire document analysis)."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeskReviewSummary(Base):
    __tablename__ = "desk_review_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    document_catalog: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    coverage_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    raw_ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|analyzing|completed|error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DeskReviewFinding(Base):
    __tablename__ = "desk_review_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(36), index=True)
    finding_type: Mapped[str] = mapped_column(String(20))  # evidence|absence|signal
    requirement_id: Mapped[str | None] = mapped_column(String(30), nullable=True)  # nullable for cross-cutting signals
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # FK to assessment_documents
    content: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # info|low|medium|high|critical
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_location: Mapped[str | None] = mapped_column(String(200), nullable=True)  # page/section ref
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
