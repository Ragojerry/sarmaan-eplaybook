import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ConsentText(Base):
    """
    The "Before you start" consent screen shown on first launch, one row per
    language (English always exists). Served without login (the screen comes
    before it) and cached on the phone, which falls back to English, then to
    the copy built into the app.

    `version` goes up on every change, so the phone can record exactly which
    text a person agreed to. A translation records the English version it was
    made from (`source_version`), so the admin portal can flag translations
    that are behind the English text.
    """

    __tablename__ = "consent_texts"

    language: Mapped[str] = mapped_column(String(10), primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    usage_label: Mapped[str] = mapped_column(String(255), nullable=False)
    button_label: Mapped[str] = mapped_column(String(60), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
