import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ContentReviewStatus


class AppString(Base):
    """One piece of the mobile app's interface text (a button, label or message).

    English is the source, seeded from the app (mobile/l10n/app_strings.json via
    app/l10n/seed.py) and never typed in the portal. `english_one` makes the
    string plural (the singular form; `english` is the "other" form).
    `source_version` goes up whenever the English changes, so translations made
    from an older English are flagged "needs update". Strings the app no longer
    uses are retired (kept, with `retired_at`), never deleted."""

    __tablename__ = "app_strings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)  # e.g. "home.title"
    english: Mapped[str] = mapped_column(Text, nullable=False)
    english_one: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")  # where it appears, for translators
    placeholders: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # ["count", "name"]
    source_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    translations: Mapped[list["AppStringTranslation"]] = relationship(back_populates="string")

    @property
    def is_plural(self) -> bool:
        return self.english_one is not None


class AppStringTranslation(Base):
    """One string in one language. Follows the content governance workflow
    (DRAFT -> PROGRAMME_REVIEW -> LOCALISATION_REVIEW -> TECHNICAL_QA -> PUBLISHED).

    `text`/`text_one` are the working copy that moves through review. On
    PUBLISHED it is copied to `published_text`/`published_text_one`, which is
    the only thing phones receive. Editing a published string therefore keeps
    the approved text on phones until the new version is published too.
    `source_version` is the English version the working copy was made from."""

    __tablename__ = "app_string_translations"
    __table_args__ = (UniqueConstraint("string_id", "language_id", name="uq_app_string_translation_lang"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    string_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_strings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_one: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ContentReviewStatus] = mapped_column(
        SAEnum(ContentReviewStatus, name="content_review_status", create_type=False),
        nullable=False,
        default=ContentReviewStatus.DRAFT,
    )
    source_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    edited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_text_one: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_source_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    string: Mapped[AppString] = relationship(back_populates="translations")
    language: Mapped["Language"] = relationship()  # noqa: F821
