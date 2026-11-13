import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ModuleAudience, ToolItemType


class ToolModule(Base):
    """
    A Tools repository (resource library) assigned to learner roles: links to
    documents, forms, images and websites that learners open online. Separate
    from training on purpose: no table that computes completion, the General
    test gate or unlock, the time rule, progress, restart, reports, releases or
    the question index ever reads these tables (app/routers/tools.py).

    Role assignment works exactly like a training module's: GENERAL = every
    learner role, ROLE_SPECIFIC = only `learner_roles`; staff accounts see all.
    """

    __tablename__ = "tool_modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[ModuleAudience] = mapped_column(
        SAEnum(ModuleAudience, name="module_audience"), nullable=False, default=ModuleAudience.GENERAL,
    )
    learner_roles: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    # A delete only sets this, so phones that sync "changes since" remove it.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ToolItem(Base):
    """
    One link in a Tools module. Only the link and its description are stored;
    the file itself is never downloaded, copied or fetched (not even to check
    it). `host` labels well-known services (Google Drive, OneDrive, ...) from
    the address alone, so the app can show the right icon. `audience` narrows
    the module's roles further; empty = everyone the module is assigned to.
    """

    __tablename__ = "tool_items"
    __table_args__ = (
        Index("ix_tool_items_tool_module_id", "tool_module_id"),
        Index("ix_tool_items_updated_at", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tool_modules.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[ToolItemType] = mapped_column(SAEnum(ToolItemType, name="tool_item_type"), nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    host: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    languages: Mapped[str | None] = mapped_column(String(120), nullable=True)
    audience: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    last_reviewed: Mapped[date | None] = mapped_column(Date, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
