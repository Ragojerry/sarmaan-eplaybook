"""
Revised Phases 10/11: extractive question answering over approved content.
POST /ai/ask answers from the same engine the phone runs offline
(app/ai/qa_engine.py <-> mobile/lib/qa/qa_engine.dart), over the training
modules first and, only when they have no answer, the approved reference
library (server-side only, so phones that are online can reach it). GET
/ai/chunks is how the phone downloads the passages it searches. Every
question is logged to ai_question_log so content admins can see what learners
ask that the materials don't answer (master prompt §42-43).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai import qa_engine
from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import AiQuestionLog, ContentChunk, ReferenceDocument, ReferencePassage, User
from app.models.enums import ReferenceStatus
from app.schemas.ai import AnswerOut, AskRequest, ChunkOut

router = APIRouter()
REFERENCE_CODE = "REF"
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


def _load_reference_chunks(db: Session, language: str) -> list[dict]:
    """Passages of APPROVED reference documents, shaped like content chunks
    (module_code "REF", the document title as source_title)."""
    rows = (
        db.query(ReferencePassage, ReferenceDocument.title)
        .join(ReferenceDocument, ReferencePassage.document_id == ReferenceDocument.id)
        .filter(ReferenceDocument.status == ReferenceStatus.APPROVED, ReferenceDocument.language == language)
        .order_by(ReferenceDocument.title, ReferencePassage.position)
        .all()
    )
    return [
        {
            "id": str(p.id),
            "module_id": None,
            "section_id": None,
            "module_code": REFERENCE_CODE,
            "source_title": title,
            "section_title": p.heading,
            "language": language,
            "chunk_text": p.text,
        }
        for p, title in rows
    ]


def answer(db: Session, question: str, language: str) -> dict:
    """Training modules always win; the reference library is searched only
    when the modules have no answer, and its sources say kind="reference"."""
    result = qa_engine.answer_question(
        question, _load_chunks(db, language), min_coverage_pct=settings.ai_min_coverage_pct
    )
    if result["matched"] or qa_engine.is_greeting(question):
        return result
    references = _load_reference_chunks(db, language)
    if references:
        from_references = qa_engine.answer_question(
            question, references, min_coverage_pct=settings.ai_min_coverage_pct
        )
        if from_references["matched"]:
            for s in from_references["sources"]:
                s["kind"] = "reference"
            return from_references
    return result


@router.get("/chunks", response_model=list[ChunkOut])
def list_chunks(
    language: str = Query("en"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return _load_chunks(db, language)


@router.post("/ask", response_model=AnswerOut)
def ask(payload: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = answer(db, payload.question, payload.language)

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
