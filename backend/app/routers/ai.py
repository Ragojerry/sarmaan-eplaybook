"""
Revised Phases 10/11: extractive question answering over approved content.
POST /ai/ask answers from the same engine the phone runs offline
(app/ai/qa_engine.py <-> mobile/lib/qa/qa_engine.dart); GET /ai/chunks is how
the phone downloads the passages it searches. Every question is logged to
ai_question_log so content admins can see what learners ask that the
materials don't answer (master prompt §42-43).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai import qa_engine
from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import AiQuestionLog, ContentChunk, User
from app.schemas.ai import AnswerOut, AskRequest, ChunkOut

router = APIRouter()
settings = get_settings()


def _load_chunks(db: Session, language: str) -> list[dict]:
    rows = (
        db.query(ContentChunk)
        .filter_by(language=language)
        .order_by(ContentChunk.module_code, ContentChunk.created_at)
        .all()
    )
    return [
        {
            "id": str(c.id),
            "module_id": str(c.module_id),
            "section_id": str(c.section_id) if c.section_id else None,
            "module_code": c.module_code,
            "source_title": c.source_title,
            "section_title": c.section_title,
            "language": c.language,
            "chunk_text": c.chunk_text,
        }
        for c in rows
    ]


@router.get("/chunks", response_model=list[ChunkOut])
def list_chunks(
    language: str = Query("en"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return _load_chunks(db, language)


@router.post("/ask", response_model=AnswerOut)
def ask(payload: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chunks = _load_chunks(db, payload.language)
    result = qa_engine.answer_question(payload.question, chunks, min_coverage_pct=settings.ai_min_coverage_pct)

    top = result["sources"][0] if result["sources"] else None
    now = datetime.now(timezone.utc)
    db.add(
        AiQuestionLog(
            question=payload.question.strip(),
            answer=result["answer"] if result["matched"] else None,
            matched=result["matched"],
            confidence=result["confidence"],
            source_module_id=uuid.UUID(top["module_id"]) if top and top.get("module_id") else None,
            source_section_id=uuid.UUID(top["section_id"]) if top and top.get("section_id") else None,
            language=payload.language,
            user_id=current_user.id,
            asked_at=now,
            synced_at=now,
        )
    )
    db.commit()
    return result
