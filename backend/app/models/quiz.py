import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import QuestionType, QuestionUsage, TestType


class QuizQuestion(Base):
    """One question of a module's end-of-module quiz. `content` holds the
    type-specific options/answer (see app/quiz/grading.py for the shapes)."""

    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType, name="question_type"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usage: Mapped[QuestionUsage] = mapped_column(
        SAEnum(QuestionUsage, name="question_usage"), nullable=False, default=QuestionUsage.BOTH,
        server_default=QuestionUsage.BOTH.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Set when the per-module pre/post tests were retired (2026-11): the row is kept for
    # history and old attempts, but never served again.
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class QuizAttempt(Base):
    """One completed attempt by one learner. Uploaded by the phone (which grades
    offline); `client_id` makes re-uploads idempotent. Every upload is kept as
    history; only `valid` attempts count (app/learning/state.py), and
    `invalid_reason` says why one doesn't."""

    __tablename__ = "quiz_attempts"
    __table_args__ = (UniqueConstraint("user_id", "client_id", name="uq_quiz_attempt_client"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(80), nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    test_type: Mapped[TestType] = mapped_column(
        SAEnum(TestType, name="test_type"), nullable=False, default=TestType.POST, server_default=TestType.POST.value
    )
    valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    invalid_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    results: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # [{question_id, correct}]
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

