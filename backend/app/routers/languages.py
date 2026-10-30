import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models import ContentChunk, Language, ModuleTranslation, SectionTranslation, User
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


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_language(
    language_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CONTENT_ADMIN)),
):
    """Removes a language that was added by mistake. Refused for the default
    language, and for any language that people or translations already use, so
    nothing a learner or translator relies on can disappear."""
    language = db.get(Language, language_id)
    if language is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    if language.is_default or language.code == "en":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The default language cannot be deleted.")
    users = db.query(User).filter_by(language_id=language.id).count()
    translations = (
        db.query(ModuleTranslation).filter_by(language_id=language.id).count()
        + db.query(SectionTranslation).filter_by(language_id=language.id).count()
    )
    if users or translations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"In use: {users} user(s) and {translations} translation record(s) use this language.",
        )
    code = language.code
    db.query(ContentChunk).filter_by(language=code).delete()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_EDIT,
            entity_type="language",
            entity_id=language.id,
            details={"deleted": True, "code": code},
        )
    )
    db.delete(language)
    db.commit()
