import uuid

from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ContentType


class ContentSection(Base):
    """Fields per master prompt §6. `content` is JSONB (structured, per §6's rule against
    dumping the whole app into JSONB — this is the one place flexible content actually
    belongs, since section content shape varies by content_type)."""

    __tablename__ = "content_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    section_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[ContentType] = mapped_column(SAEnum(ContentType, name="content_type"), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    module: Mapped["Module"] = relationship(back_populates="content_sections")  # noqa: F821
