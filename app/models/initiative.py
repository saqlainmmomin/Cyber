from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id


class Initiative(Base):
    __tablename__ = "initiatives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    report_id: Mapped[str] = mapped_column(String(36), index=True)
    initiative_id: Mapped[str] = mapped_column(String(20))  # e.g., "INIT-001"
    title: Mapped[str] = mapped_column(String(255))
    root_cause: Mapped[str] = mapped_column(Text)
    root_cause_category: Mapped[str] = mapped_column(String(30))
    requirements_addressed: Mapped[str] = mapped_column(Text)  # JSON list
    combined_effort: Mapped[str] = mapped_column(String(20))
    combined_timeline_weeks: Mapped[int] = mapped_column(Integer)
    priority: Mapped[int] = mapped_column(Integer)
    budget_estimate_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    suggested_approach: Mapped[str] = mapped_column(Text)
