import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import MediaAssetType


class MediaAsset(Base):
    """Fields per master prompt §7. Real files on disk/object storage —
    never large binaries embedded in source code (the prototype's mistake;
    see docs/prototype-analysis.md §1, §5)."""

    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_type: Mapped[MediaAssetType] = mapped_column(
        SAEnum(MediaAssetType, name="media_asset_type"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)  # sha256
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)  # for AUDIO/VIDEO
    asset_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
