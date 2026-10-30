import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import BoundaryLevel


class AdminBoundary(Base):
    """One node of the administrative hierarchy: Country > State > LGA > Ward > Facility.
    A node's parent is always the level directly above it."""

    __tablename__ = "admin_boundaries"
    __table_args__ = (Index("ix_admin_boundaries_level_parent", "level", "parent_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level: Mapped[BoundaryLevel] = mapped_column(SAEnum(BoundaryLevel, name="boundary_level"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("admin_boundaries.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
