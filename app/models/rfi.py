"""Model for Request for Information (RFI) documents."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class RFIDocument(Base):
    __tablename__ = "rfi_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    introduction: Mapped[str] = mapped_column(Text)
    evidence_items: Mapped[str] = mapped_column(Text)  # JSON list of evidence request items
    response_instructions: Mapped[str] = mapped_column(Text)
    appendix: Mapped[str] = mapped_column(Text, nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    critical_items: Mapped[int] = mapped_column(Integer, default=0)
    raw_ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
