import uuid

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SectionTranslation(Base):
    """A translated copy of one ContentSection's text. The English section stays
    the structural source of truth (type, order, media ids); this row only
    carries the translated title/content for one language. Its review status is
    that of the module's ModuleTranslation for the same language, so a section
    translation is never shown unless the module translation is PUBLISHED."""

    __tablename__ = "section_translations"
    __table_args__ = (UniqueConstraint("section_id", "language_id", name="uq_section_translation_lang"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_sections.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
