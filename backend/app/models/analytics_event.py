import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import AnalyticsEventType


class AnalyticsEvent(Base):
    """Backs the admin dashboard (master prompt §49-50) with real, queryable
    data instead of the prototype's hardcoded numbers. Mobile syncs these up
    via POST /sync/analytics (same pattern as ai_question_log and
    user_module_progress) whenever connected. Deliberately generic/wide
    rather than one table per event type — the event types list will grow
    (§50 lists ~15 distinct metrics) and a single table with `event_type` +
    JSONB `payload` avoids a migration for every new metric added later."""

    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[AnalyticsEventType] = mapped_column(
        SAEnum(AnalyticsEventType, name="analytics_event_type"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    module_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=True)
    video_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
