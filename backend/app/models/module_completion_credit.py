import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ModuleCompletionCredit(Base):
    """A completion GIVEN for a module because the learner completed an older
    module that taught the same content (scripts/credit_hfw_modules.py), not
    earned in the module itself. The learner's progress row for the module is
    marked completed so the phone and the lock order treat it as done; this row
    says where that completion came from, so reports can tell credited
    completions apart from earned ones. The old module's own progress and test
    rows are never touched; source_* copies what the credit was based on."""

    __tablename__ = "module_completion_credits"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_credit_user_module"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    source_module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    source_module_code: Mapped[str] = mapped_column(String(20), nullable=False)
    # Copied from the old module: when it was completed, and the score of the
    # post-test that completed it (None when it was completed without a test).
    source_completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_score_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_id: Mapped[str] = mapped_column(String(40), nullable=False)  # which credit run created it
    # The learner's progress row for the NEW module before the credit (for --undo):
    # whether it existed, and how far along it was.
    progress_existed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    previous_progress_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def label(self) -> str:
        return f"credited from {self.source_module_code}"
