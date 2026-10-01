from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class InitiativeMetadata(Base):
    __tablename__ = "initiative_metadata"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "group_id",
            name="uq_initiative_metadata_assessment_group",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="RESTRICT"), index=True
    )
    group_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    complexity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    benefit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
