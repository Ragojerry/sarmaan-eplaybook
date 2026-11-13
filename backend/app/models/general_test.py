import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import TestType


class GeneralTestQuestion(Base):
    """One multiple-choice question of the General test, which every learner takes
    once before any module (PRE) and once after finishing all their modules (POST).
    `options` keeps the printed order; `correct_index` (0-3) is empty until the
    programme supplies the answer key, and an inactive question is never served."""

    __tablename__ = "general_test_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)  # 1-25, as printed
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    correct_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Mentions CDDs (shown to every learner; flagged for the content reviewers).
    cdd_specific: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GeneralTestAttempt(Base):
    """One General pre- or post-test taken on a phone. The server grades it from the
    chosen options (`answers`), so the score never depends on the phone. Every upload
    is kept; only `valid` ones count, and the first valid one of each type is the
    learner's result (each test is taken once)."""

    __tablename__ = "general_test_attempts"
    __table_args__ = (UniqueConstraint("user_id", "client_id", name="uq_general_test_attempt_client"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(80), nullable=False)
    test_type: Mapped[TestType] = mapped_column(SAEnum(TestType, name="test_type", create_type=False), nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    score_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # [{question_id, choice, correct}]
    valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    invalid_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # The learner's pass mark (%) when the attempt reached the server; NULL for attempts
    # from before 2026-11-13 (never recalculated). app/learning/settings.py.
    pass_mark: Mapped[int | None] = mapped_column(Integer, nullable=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlatformSetting(Base):
    """A training rule an administrator can change in the portal without a redeploy
    (app/learning/settings.py lists the keys, their defaults and limits)."""

    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
