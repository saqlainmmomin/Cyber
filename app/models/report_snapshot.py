from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assessments.id"), nullable=True, index=True
    )
    engagement_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("engagements.id"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(30))
    format: Mapped[str] = mapped_column(String(10))
    storage_path: Mapped[str] = mapped_column(String(500))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    is_issued: Mapped[bool] = mapped_column(Boolean, default=False)
