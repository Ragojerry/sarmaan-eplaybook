"""
Curated answers: trainers answer the questions learners actually ask
(GET /analytics/questions lists the unanswered ones). Create -> DRAFT -> a
reviewer approves -> APPROVED (checked first by the Ask assistant, online at
once and offline from the next release) -> ARCHIVED. Editing the wording or
answer of an approved entry sends it back to DRAFT for re-approval. Every
change lands in the audit log.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai import qa_engine
from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import FaqEntry, Module, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, FaqStatus, RoleName

router = APIRouter()

EDITORS = (RoleName.CONTENT_ADMIN,)
# As for content and the reference library, reviewers may approve too;
# SUPER_ADMIN always passes require_roles.
APPROVERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.TECHNICAL_REVIEWER)
VIEWERS = APPROVERS + (RoleName.LOCALISATION_REVIEWER,)
CONTENT_FIELDS = ("question", "alternates", "answer", "module_id", "language")


class FaqCreate(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    alternates: str | None = Field(default=None, max_length=5000)
    answer: str = Field(min_length=3, max_length=5000)
    module_id: uuid.UUID
    language: str = Field(default="en", min_length=2, max_length=10)
    source_question: str | None = Field(default=None, max_length=500)


class FaqUpdate(BaseModel):
    question: str | None = Field(default=None, min_length=3, max_length=500)
    alternates: str | None = Field(default=None, max_length=5000)
    answer: str | None = Field(default=None, min_length=3, max_length=5000)
    module_id: uuid.UUID | None = None
    language: str | None = Field(default=None, min_length=2, max_length=10)
    status: FaqStatus | None = None


def _serialize(f: FaqEntry, module: Module | None) -> dict:
    return {
        "id": str(f.id),
        "question": f.question,
        "alternates": f.alternates,
        "answer": f.answer,
        "module_id": str(f.module_id),
        "module_code": module.module_code if module else None,
        "module_title": module.title if module else None,
        "language": f.language,
        "status": f.status.value,
        "source_question": f.source_question,
        "created_by": str(f.created_by) if f.created_by else None,
        "approved_by": str(f.approved_by) if f.approved_by else None,
        "approved_at": f.approved_at.isoformat() if f.approved_at else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }


def _get(db: Session, faq_id: uuid.UUID) -> FaqEntry:
    f = db.get(FaqEntry, faq_id)
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    return f


def _module(db: Session, module_id: uuid.UUID) -> Module:
    m = db.get(Module, module_id)
    if m is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown module_id")
    return m


def _check_question(text: str) -> None:
    if not qa_engine.build_concepts(text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"“{text}” has no words the assistant can match on. Write the question in full.",
        )


def _audit(db: Session, user: User, action: AuditAction, f: FaqEntry, details: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=action, entity_type="faq_entry", entity_id=f.id,
                    details={"question": f.question, **details}))


@router.get("")
def list_faqs(
    status_filter: FaqStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*VIEWERS)),
):
    q = db.query(FaqEntry, Module).join(Module, FaqEntry.module_id == Module.id)
    if status_filter is not None:
        q = q.filter(FaqEntry.status == status_filter)
    return [_serialize(f, m) for f, m in q.order_by(FaqEntry.updated_at.desc()).all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_faq(payload: FaqCreate, db: Session = Depends(get_db),
               current_user: User = Depends(require_roles(*EDITORS))):
    module = _module(db, payload.module_id)
    f = FaqEntry(
        question=payload.question.strip(),
        alternates=(payload.alternates or "").strip() or None,
        answer=payload.answer.strip(),
        module_id=module.id,
        language=payload.language,
        source_question=(payload.source_question or "").strip() or None,
        status=FaqStatus.DRAFT,
        created_by=current_user.id,
    )
    for phrasing in f.phrasings():
        _check_question(phrasing)
    db.add(f)
    db.flush()
    _audit(db, current_user, AuditAction.FAQ_CREATE, f, {"module": module.module_code})
    db.commit()
    db.refresh(f)
    return _serialize(f, module)


@router.patch("/{faq_id}")
def update_faq(faq_id: uuid.UUID, payload: FaqUpdate, db: Session = Depends(get_db),
               current_user: User = Depends(require_roles(*APPROVERS))):
    f = _get(db, faq_id)
    changes = payload.model_dump(exclude_unset=True)
    content = {k: v for k, v in changes.items() if k in CONTENT_FIELDS}
    if content and current_user.role not in (RoleName.CONTENT_ADMIN, RoleName.SUPER_ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only content admins can edit answers.")
    for key in ("question", "answer"):
        if content.get(key) is not None:
            setattr(f, key, content[key].strip())
    if "alternates" in content:
        f.alternates = (content["alternates"] or "").strip() or None
    if content.get("module_id") is not None:
        f.module_id = _module(db, content["module_id"]).id
    if content.get("language") is not None:
        f.language = content["language"]
    for phrasing in f.phrasings():
        _check_question(phrasing)

    new_status = changes.get("status")
    if new_status is not None and new_status != f.status:
        f.status = new_status
        if new_status == FaqStatus.APPROVED:
            f.approved_by = current_user.id
            f.approved_at = datetime.now(timezone.utc)
    elif content and f.status == FaqStatus.APPROVED:
        # A changed answer has not been reviewed: take it out of use until it is.
        f.status = FaqStatus.DRAFT
        changes["status"] = FaqStatus.DRAFT
    f.updated_at = datetime.now(timezone.utc)
    _audit(db, current_user, AuditAction.FAQ_UPDATE, f,
           {k: (v.value if isinstance(v, FaqStatus) else str(v) if isinstance(v, uuid.UUID) else v)
            for k, v in changes.items()})
    db.commit()
    db.refresh(f)
    return _serialize(f, db.get(Module, f.module_id))


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(faq_id: uuid.UUID, db: Session = Depends(get_db),
               current_user: User = Depends(require_roles(*EDITORS))):
    f = _get(db, faq_id)
    if f.status == FaqStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Archive the answer before deleting it.")
    _audit(db, current_user, AuditAction.FAQ_UPDATE, f, {"deleted": True, "answer": f.answer})
    db.delete(f)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
