"""
Curated answers as Q&A passages. An APPROVED FaqEntry of a PUBLISHED module
becomes a chunk like the module's own, plus "faq_questions" (its wordings),
which the engine checks first (qa_engine.match_faq). The same chunks are
served by GET /ai/chunks, searched by POST /ai/ask, and frozen into each
release package, so a curated answer works online as soon as it is approved
and offline once phones have the next release or content sync.
"""
from sqlalchemy.orm import Session

from app.models import FaqEntry, Module
from app.models.enums import FaqStatus, ModuleStatus


def faq_chunks(db: Session, language: str | None = None) -> list[dict]:
    q = (
        db.query(FaqEntry, Module)
        .join(Module, FaqEntry.module_id == Module.id)
        .filter(FaqEntry.status == FaqStatus.APPROVED, Module.status == ModuleStatus.PUBLISHED)
    )
    if language is not None:
        q = q.filter(FaqEntry.language == language)
    return [
        {
            "id": str(f.id),
            "module_id": str(m.id),
            "section_id": None,
            "module_code": m.module_code,
            "source_title": m.title,
            "section_title": f.question,
            "language": f.language,
            "chunk_text": f.answer,
            "faq_questions": f.phrasings(),
        }
        for f, m in q.order_by(Module.module_code, FaqEntry.created_at).all()
    ]
