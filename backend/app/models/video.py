import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import VideoStatus


class Video(Base):
    """Fields per master prompt §8. `offline_available` matters now that offline
    video download is confirmed in MVP scope (docs/architecture.md §6)."""

    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_releases.id"), nullable=True
    )
    offline_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Master prompt §24: "Allow administrators to define required versus
    # optional videos." Required videos are ones an admin has decided every
    # device must have downloaded (e.g. safety-critical demonstrations);
    # optional ones are download-on-demand. Storage/download-manager logic
    # (Phase 9) reads this to decide what to auto-download vs. leave to the
    # user's choice.
    required_offline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[VideoStatus] = mapped_column(
        SAEnum(VideoStatus, name="video_status"), nullable=False, default=VideoStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    module: Mapped["Module"] = relationship(back_populates="videos")  # noqa: F821
