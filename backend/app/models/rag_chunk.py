import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database import Base

# Embedding dimension is a placeholder pending the embedding-model decision
# (master prompt §29 — still open, see docs/architecture.md §6). 384 matches
# common lightweight multilingual sentence-embedding models (e.g. MiniLM-based)
# as a reasonable default; changing models later requires an Alembic migration
# to alter this column's dimension, since pgvector fixes it at column-creation time.
EMBEDDING_DIM = 384


class RagChunk(Base):
    """Server-side pgvector index for the online RAG pipeline (master prompt
    §26-27). Every chunk carries the full metadata set §27 requires, so
    answers can always be traced back to approved, versioned content."""

    __tablename__ = "rag_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    module_code: Mapped[str] = mapped_column(String(20), nullable=False)
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_sections.id"), nullable=True
    )
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    release_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_releases.id"), nullable=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False)  # mirrors ContentReviewStatus
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
