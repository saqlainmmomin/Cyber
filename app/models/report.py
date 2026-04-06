from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class GapReport(Base):
    __tablename__ = "gap_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    overall_score: Mapped[float] = mapped_column(Float)
    chapter_scores: Mapped[str] = mapped_column(Text)  # JSON string
    executive_summary: Mapped[str] = mapped_column(Text)
    raw_ai_response: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class GapItem(Base):
    __tablename__ = "gap_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    report_id: Mapped[str] = mapped_column(String(36), index=True)
    requirement_id: Mapped[str] = mapped_column(String(50))
    chapter: Mapped[str] = mapped_column(String(50))
    requirement_title: Mapped[str] = mapped_column(String(255))
    compliance_status: Mapped[str] = mapped_column(String(30))
    current_state: Mapped[str] = mapped_column(Text)
    gap_description: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(20))
    remediation_action: Mapped[str] = mapped_column(Text)
    remediation_priority: Mapped[int] = mapped_column(Integer)
    remediation_effort: Mapped[str] = mapped_column(String(20))
    timeline_weeks: Mapped[int] = mapped_column(Integer)
    maturity_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    root_cause_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)  # strong|moderate|weak
