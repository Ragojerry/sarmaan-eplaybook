import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


def session_status(start: date, end: date, today: date | None = None) -> str:
    today = today or date.today()
    if today < start:
        return "UPCOMING"
    if today > end:
        return "ENDED"
    return "ONGOING"


class TrainingSession(Base):
    """A training cohort with start and end dates. Sessions can run at the same
    time; each user belongs to one, and every report can be filtered to one
    session so it is monitored on its own."""

    __tablename__ = "training_sessions"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="ck_training_sessions_dates"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def status(self) -> str:
        return session_status(self.start_date, self.end_date)
