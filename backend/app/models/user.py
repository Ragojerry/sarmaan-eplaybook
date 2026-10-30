import uuid
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import RoleName, UserStatus


class User(Base):
    """Fields per master prompt §6 exactly."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Field team the user belongs to (e.g. "0041"); shown on the phone as "CDD TEAM 0041".
    team_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[RoleName] = mapped_column(SAEnum(RoleName, name="role_name"), nullable=False)
    language_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id"), nullable=True
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status"), nullable=False, default=UserStatus.ACTIVE
    )
    # Where the person works: the deepest boundary is chosen and its ancestors are filled in by the server.
    country_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_boundaries.id"), nullable=True, index=True)
    state_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_boundaries.id"), nullable=True, index=True)
    lga_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_boundaries.id"), nullable=True, index=True)
    ward_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_boundaries.id"), nullable=True, index=True)
    facility_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admin_boundaries.id"), nullable=True, index=True)
    # Training restarts: attempt 1 is the first run; each restart replaces the previous results.
    training_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    training_restarted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    training_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_sessions.id"), nullable=True, index=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    language: Mapped["Language"] = relationship(back_populates="users")  # noqa: F821
    country = relationship("AdminBoundary", foreign_keys=[country_id], lazy="joined")
    state = relationship("AdminBoundary", foreign_keys=[state_id], lazy="joined")
    lga = relationship("AdminBoundary", foreign_keys=[lga_id], lazy="joined")
    ward = relationship("AdminBoundary", foreign_keys=[ward_id], lazy="joined")
    facility = relationship("AdminBoundary", foreign_keys=[facility_id], lazy="joined")

    training_session = relationship("TrainingSession", foreign_keys=[training_session_id], lazy="joined")

    @property
    def session_name(self):
        return self.training_session.name if self.training_session else None

    @property
    def session_start_date(self):
        return self.training_session.start_date if self.training_session else None

    @property
    def session_end_date(self):
        return self.training_session.end_date if self.training_session else None

    @property
    def session_status(self):
        return self.training_session.status if self.training_session else None

    @property
    def country_name(self):
        return self.country.name if self.country else None

    @property
    def state_name(self):
        return self.state.name if self.state else None

    @property
    def lga_name(self):
        return self.lga.name if self.lga else None

    @property
    def ward_name(self):
        return self.ward.name if self.ward else None

    @property
    def facility_name(self):
        return self.facility.name if self.facility else None
