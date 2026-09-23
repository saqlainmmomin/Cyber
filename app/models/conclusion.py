from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class Conclusion(Base):
    __tablename__ = "conclusions"
    __table_args__ = (
        Index(
            "uq_conclusions_assessment_framework_requirement",
            "assessment_id",
            "framework_id",
            "requirement_id",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), index=True
    )
    requirement_id: Mapped[str] = mapped_column(String(100))
    framework_id: Mapped[str] = mapped_column(String(50))
    cluster_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    outcome: Mapped[str] = mapped_column(String(40))
    rationale: Mapped[str] = mapped_column(Text)
    evidence_summary: Mapped[str] = mapped_column(Text)
    gaps_identified: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(20))
    recommended_action: Mapped[str] = mapped_column(Text)
    ai_proposed: Mapped[bool] = mapped_column(Boolean)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class ConclusionRevision(Base):
    __tablename__ = "conclusion_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    conclusion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conclusions.id"), index=True
    )
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(30))
    previous_outcome: Mapped[str | None] = mapped_column(String(40), nullable=True)
    previous_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("analysis_runs.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
