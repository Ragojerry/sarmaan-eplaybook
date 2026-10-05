import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models import User, Language
from app.models.audit_log import AuditLog
from app.models.enums import RoleName, AuditAction
from app.schemas.language import LanguageCreate, LanguageUpdate, LanguageResponse

router = APIRouter()


@router.get("", response_model=list[LanguageResponse])
def list_languages(db: Session = Depends(get_db)):
    """Deliberately public (no auth dependency) — the mobile app's first-run
    flow shows the language picker BEFORE login (per master prompt Phase 7's
    screen order: splash, language, consent, login...), so a not-yet-
    authenticated user must be able to fetch this list. The language list
    isn't sensitive data; nothing here justifies gating it behind a login
    a first-time user hasn't had the chance to complete yet."""
    return db.query(Language).order_by(Language.is_default.desc(), Language.name).all()


@router.post("", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED)
def create_language(
    payload: LanguageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CONTENT_ADMIN)),
):
    if db.query(Language).filter_by(code=payload.code).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Language code already exists")
    language = Language(**payload.model_dump())
    db.add(language)
    db.commit()
    db.refresh(language)
    return language


@router.patch("/{language_id}", response_model=LanguageResponse)
def update_language(
    language_id: uuid.UUID,
    payload: LanguageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CONTENT_ADMIN, RoleName.LOCALISATION_REVIEWER)),
):
    language = db.get(Language, language_id)
    if language is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(language, field, value)

    if "status" in changes and changes["status"] == "ACTIVE":
        db.add(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.LANGUAGE_APPROVE,
                entity_type="language",
                entity_id=language.id,
                details={"code": language.code},
            )
        )
    db.commit()
    db.refresh(language)
    return language
