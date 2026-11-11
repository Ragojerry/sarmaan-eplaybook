import uuid
from datetime import datetime

from sqlalchemy import Integer, Boolean, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class UserModuleProgress(Base):
    """Fields per master prompt §9. Must work offline: mobile writes this to its
    local Drift DB first, then syncs up via POST /sync/progress when connected
    (docs/architecture.md §3, mobile/lib/sync/sync_engine.dart)."""

    __tablename__ = "user_module_progress"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_progress_user_module"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # When the learner first finished reading (progress reached READING_PERCENT).
    # The post-test is accepted only after it. legacy_reading marks reading
    # recorded before pre/post tests existed, which is kept without a pre-test.
    reading_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    legacy_reading: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Active time in the module (app in front, module on screen), reported by the phone.
    # Only ever grows: the server keeps the larger of stored and uploaded values.
    seconds_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
