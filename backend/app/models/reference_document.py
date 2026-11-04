import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import ReferenceStatus


class ReferenceDocument(Base):
    """
    Reference library: supporting material outside the training modules
    (national guidelines, SOPs, job aids) that the online Ask assistant may
    quote. Uploaded as a DRAFT; only APPROVED documents are searched, and only
    when the training modules have no answer (app/routers/ai.py). Server-side
    only — reference passages are not shipped to phones.

    The original file is kept (`file_data`) so reviewers can check exactly
    what was approved; `passages` hold the text the assistant searches.
    """

    __tablename__ = "reference_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    file_data: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[ReferenceStatus] = mapped_column(
        SAEnum(ReferenceStatus, name="reference_status"), nullable=False, default=ReferenceStatus.DRAFT
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    passages: Mapped[list["ReferencePassage"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="ReferencePassage.position"
    )


class ReferencePassage(Base):
    """One searchable passage of a reference document (a few paragraphs,
    with the page or heading it came from)."""

    __tablename__ = "reference_passages"
    __table_args__ = (Index("ix_reference_passages_document", "document_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reference_documents.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[ReferenceDocument] = relationship(back_populates="passages")
