import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ReleaseStatus  # noqa: F401  (kept for reviewers; release_id below is a plain FK)


class AiQuestionLog(Base):
    """Fields per master prompt §41-42. Mirrors the mobile app's local
    `local_ai_questions` queue once synced (§41: local queue -> FastAPI -> PostgreSQL).
    Admin uses this to see matched/unmatched questions and spot frequently
    unanswered ones (§42, §43) — replacing the prototype's non-persisted
    in-memory chat log (docs/prototype-analysis.md §6)."""

    __tablename__ = "ai_question_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id"), nullable=True
    )
    source_section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_sections.id"), nullable=True
    )
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_releases.id"), nullable=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
