"""
Quiz authoring (CONTENT_ADMIN edits; any staff role reads) and a small
per-module summary. Questions ship to phones inside the next published release.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import MediaAsset, Module, QuizAttempt, QuizQuestion, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, QuestionType, RoleName
from app.quiz.grading import PASS_MARK, InvalidQuestion, validate_content
from app.schemas.quiz import QuestionCreate, QuestionResponse, QuestionUpdate, QuizSummary

router = APIRouter()
EDITORS = (RoleName.CONTENT_ADMIN,)


def _require_staff(user: User = Depends(get_current_user)) -> User:
    if user.role == RoleName.CDD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quiz answers are not available to learners")
    return user


def _module(db: Session, module_id: uuid.UUID) -> Module:
    m = db.get(Module, module_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return m


def _clean(db: Session, qtype: QuestionType, content: dict) -> dict:
    try:
        cleaned = validate_content(qtype, content)
    except InvalidQuestion as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if qtype == QuestionType.IMAGE_CHOICE:
        asset = db.get(MediaAsset, uuid.UUID(cleaned["media_asset_id"]))
        if asset is None or asset.asset_type.value != "IMAGE":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Picture not found in the media library")
    return cleaned


@router.get("/modules/{module_id}/questions", response_model=list[QuestionResponse])
def list_questions(module_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(_require_staff)):
    _module(db, module_id)
    return (
        db.query(QuizQuestion).filter_by(module_id=module_id).order_by(QuizQuestion.sort_order, QuizQuestion.created_at).all()
    )


@router.get("/modules/{module_id}/summary", response_model=QuizSummary)
def quiz_summary(module_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(_require_staff)):
    _module(db, module_id)
    n = db.query(func.count(QuizQuestion.id)).filter_by(module_id=module_id, is_active=True).scalar() or 0
    attempts = db.query(func.count(QuizAttempt.id)).filter_by(module_id=module_id).scalar() or 0
    passed = (
        db.query(func.count(func.distinct(QuizAttempt.user_id))).filter_by(module_id=module_id, passed=True).scalar() or 0
    )
    return QuizSummary(module_id=module_id, questions=n, pass_mark=PASS_MARK, attempts=attempts, learners_passed=passed)


@router.post("/modules/{module_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    module_id: uuid.UUID,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*EDITORS)),
):
    _module(db, module_id)
    content = _clean(db, payload.question_type, payload.content)
    order = payload.sort_order
    if order is None:
        order = (db.query(func.max(QuizQuestion.sort_order)).filter_by(module_id=module_id).scalar() or 0) + 1
    q = QuizQuestion(
        module_id=module_id, question_type=payload.question_type, prompt=payload.prompt.strip(),
        content=content, explanation=(payload.explanation or "").strip() or None, sort_order=order,
    )
    db.add(q)
    db.flush()
    db.add(AuditLog(user_id=user.id, action=AuditAction.CONTENT_CREATE, entity_type="quiz_question", entity_id=q.id,
                    details={"module_id": str(module_id), "type": q.question_type.value}))
    db.commit()
    db.refresh(q)
    return q


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*EDITORS)),
):
    q = db.get(QuizQuestion, question_id)
    if q is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    changes = payload.model_dump(exclude_unset=True)
    if "content" in changes:
        q.content = _clean(db, q.question_type, changes.pop("content"))
    if "prompt" in changes:
        q.prompt = changes.pop("prompt").strip()
    if "explanation" in changes:
        q.explanation = (changes.pop("explanation") or "").strip() or None
    for k, v in changes.items():
        setattr(q, k, v)
    db.add(AuditLog(user_id=user.id, action=AuditAction.CONTENT_EDIT, entity_type="quiz_question", entity_id=q.id,
                    details={"module_id": str(q.module_id)}))
    db.commit()
    db.refresh(q)
    return q


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(*EDITORS))):
    q = db.get(QuizQuestion, question_id)
    if q is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    db.add(AuditLog(user_id=user.id, action=AuditAction.CONTENT_EDIT, entity_type="quiz_question", entity_id=q.id,
                    details={"module_id": str(q.module_id), "deleted": True}))
    db.delete(q)
    db.commit()
