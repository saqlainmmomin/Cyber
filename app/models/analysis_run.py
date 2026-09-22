from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id"), index=True
    )
    framework_id: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50))
    claims_json: Mapped[str] = mapped_column(Text)
    model_id: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
