import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Device(Base):
    """
    One app install used by one account (app/devices/registry.py). `install_id` is
    the random id the app creates on first run (never a hardware identifier, IMEI,
    advertising id or phone number). A phone shared by two people is two rows.
    Refreshed at every login and sync by app 0.1.16 and later; older apps simply
    have no row. "Active" = seen within settings.active_device_days.
    """

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("user_id", "install_id", name="uq_devices_user_install"),
        Index("ix_devices_last_seen_at", "last_seen_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    install_id: Mapped[str] = mapped_column(String(64), nullable=False)
    os: Mapped[str | None] = mapped_column(String(20), nullable=True)  # android, ios
    os_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
