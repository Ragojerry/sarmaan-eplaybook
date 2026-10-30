import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ContentChunk(Base):
    """
    Revised Phases 10/11 (product-owner direction, superseding the master
    prompt's embeddings + pgvector + local-LLM design): a deterministic,
    offline-first EXTRACTIVE search index. No embedding model, no vector
    database, no LLM — so none of the decisions that blocked the original
    design (which model, which runtime) apply.

    One row per module *section group* (a heading plus the content under
    it), built by scripts/build_content_index.py from real published
    content. Ranking is BM25 implemented in app/ai/qa_engine.py — and
    mirrored line-for-line in mobile/lib/qa/qa_engine.dart — so the phone
    gives the same answer with or without a connection.
    """

    __tablename__ = "content_chunks"
    __table_args__ = (Index("ix_content_chunks_module_language", "module_id", "language"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id"), nullable=False)
    module_code: Mapped[str] = mapped_column(String(20), nullable=False)
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_sections.id"), nullable=True
    )
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)  # the module's title
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
