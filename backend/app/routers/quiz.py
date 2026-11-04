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
from app.models import MediaAsset, Module, QuizAttempt, QuizQuestion, User, UserModuleProgress
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, QuestionType, QuestionUsage, RoleName, TestType
from app.learning.state import test_question_counts
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
    usages = [u for (u,) in db.query(QuizQuestion.usage).filter_by(module_id=module_id, is_active=True)]
    n = len(usages)
    pre_n, post_n = test_question_counts(db, module_id)
    warning = None
    if n and QuestionUsage.BOTH not in usages and len(set(usages)) == 1:
        only = "pre-test" if usages[0] == QuestionUsage.PRE else "post-test"
        other = "post-test" if only == "pre-test" else "pre-test"
        warning = f"Every question is tagged {only} only, so the {other} uses all of them too."
    counts = dict(
        db.query(QuizAttempt.test_type, func.count(QuizAttempt.id))
        .filter_by(module_id=module_id, valid=True)
        .group_by(QuizAttempt.test_type)
        .all()
    )
    attempts = db.query(func.count(QuizAttempt.id)).filter_by(module_id=module_id).scalar() or 0
    completed = (
        db.query(func.count(func.distinct(QuizAttempt.user_id)))
        .join(UserModuleProgress, (UserModuleProgress.user_id == QuizAttempt.user_id)
              & (UserModuleProgress.module_id == QuizAttempt.module_id))
        .filter(QuizAttempt.module_id == module_id, QuizAttempt.test_type == TestType.POST,
                QuizAttempt.valid.is_(True), UserModuleProgress.completed.is_(True))
        .scalar() or 0
    )
    return QuizSummary(
        module_id=module_id, questions=n, pass_mark=PASS_MARK, attempts=attempts, learners_passed=completed,
        pre_test_questions=pre_n, post_test_questions=post_n,
        pre_test_attempts=counts.get(TestType.PRE, 0), post_test_attempts=counts.get(TestType.POST, 0),
        warning=warning,
    )


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
        usage=payload.usage,
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
