import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import SupportContactType


class SupportContact(Base):
    """
    A way for learners to reach a real person, shown in the Support deck on the
    phone's Ask tab (app/routers/support_contacts.py). Managed in the admin
    portal; phones cache the active contacts for their audience and download
    only changes (GET /sync/support-contacts?since=).

    `value` is the number (international format, leading +), email address or
    https link, validated per type (app/support/validation.py). `audience` lists
    learner roles; empty means every learner. A delete only sets `deleted_at`,
    so phones that sync "changes since" learn that the contact is gone.
    """

    __tablename__ = "support_contacts"
    __table_args__ = (Index("ix_support_contacts_updated_at", "updated_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[SupportContactType] = mapped_column(SAEnum(SupportContactType, name="support_contact_type"), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    # WHATSAPP only: text placed in the chat box (never personal data).
    whatsapp_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # EMAIL only.
    email_subject: Mapped[str | None] = mapped_column(String(150), nullable=True)
    # WHATSAPP and EMAIL only: add "App version x.y.z" to the pre-filled text.
    include_app_version: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    availability: Mapped[str | None] = mapped_column(String(120), nullable=True)
    languages: Mapped[str | None] = mapped_column(String(120), nullable=True)
    audience: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
