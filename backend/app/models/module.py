import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ModuleStatus, ContentReviewStatus


class Module(Base):
    """Fields per master prompt §6. The 6 AZM training modules."""

    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # "M1".."M6"
    module_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ModuleStatus] = mapped_column(
        SAEnum(ModuleStatus, name="module_status"), nullable=False, default=ModuleStatus.DRAFT
    )
    current_release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_releases.id"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    translations: Mapped[list["ModuleTranslation"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )
    content_sections: Mapped[list["ContentSection"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="ContentSection.sort_order"
    )
    videos: Mapped[list["Video"]] = relationship(back_populates="module")  # noqa: F821


class ModuleTranslation(Base):
    """Fields per master prompt §6. One row per (module, language)."""

    __tablename__ = "module_translations"
    __table_args__ = (UniqueConstraint("module_id", "language_id", name="uq_module_translation_lang"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # for on-device TTS (read-aloud)
    status: Mapped[ContentReviewStatus] = mapped_column(
        SAEnum(ContentReviewStatus, name="content_review_status"),
        nullable=False,
        default=ContentReviewStatus.DRAFT,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    module: Mapped["Module"] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship()  # noqa: F821
