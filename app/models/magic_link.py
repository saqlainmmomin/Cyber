from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.assessment import _new_id, _utcnow


class MagicLink(Base):
    __tablename__ = "magic_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id"), index=True
    )
    token_digest: Mapped[str] = mapped_column(String(64))
    scope_json: Mapped[str] = mapped_column(Text)
    max_uploads: Mapped[int] = mapped_column(Integer)
    max_size_bytes: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Yozora: the client contact the link is for (optional; shown to the consultant, first name in the greeting).
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
