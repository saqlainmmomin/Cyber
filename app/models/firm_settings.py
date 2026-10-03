from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _utcnow

FIRM_SETTINGS_ID = 1


class FirmSettings(Base):
    """The firm's own settings: a single row (id 1). Read through app.services.firm_settings.get()."""

    __tablename__ = "firm_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_firm_settings_singleton"),
        CheckConstraint(
            "archived_retention_years BETWEEN 1 AND 50",
            name="ck_firm_settings_retention_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=FIRM_SETTINGS_ID)
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    archived_retention_years: Mapped[int] = mapped_column(Integer, default=7)
    accent_theme: Mapped[str] = mapped_column(String(20), default="midnight")
    accent_custom_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
