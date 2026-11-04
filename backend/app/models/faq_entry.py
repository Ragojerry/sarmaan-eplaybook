import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import FaqStatus


class FaqEntry(Base):
    """
    Curated answer: a trainer's answer to a question learners actually ask
    (usually one the assistant could not answer, from ai_question_log).
    APPROVED entries are checked before the training passages, both on the
    server and on the phone (app/ai/qa_engine.py <-> qa_engine.dart), and
    travel to phones as extra passages (app/ai/faq.py) with each release.

    `alternates` holds other wordings of the same question, one per line.
    Every entry belongs to a module: it is shipped and cited with it.
    """

    __tablename__ = "faq_entries"
    __table_args__ = (Index("ix_faq_entries_status_language", "status", "language"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    alternates: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[FaqStatus] = mapped_column(
        SAEnum(FaqStatus, name="faq_status"), nullable=False, default=FaqStatus.DRAFT
    )
    source_question: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def phrasings(self) -> list[str]:
        """The question plus each alternate wording, blank lines dropped."""
        extra = [line.strip() for line in (self.alternates or "").splitlines()]
        return [self.question.strip()] + [line for line in extra if line]
