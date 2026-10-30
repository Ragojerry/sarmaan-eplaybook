"""
Phase 5: real module + content CRUD, per master prompt §16 (admin content
management) and §15 (governance workflow). Structured section editing only —
admins build content from typed blocks (ContentType), never raw HTML,
per §16 ("Do not require administrators to edit raw HTML").
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.content import translation_io
from app.content.governance import advance, reject
from app.models import User, Module, ModuleTranslation, ContentSection, Language
from app.models.audit_log import AuditLog
from app.models.enums import RoleName, AuditAction
from app.schemas.content import (
    ModuleCreate,
    ModuleUpdate,
    ModuleReorder,
    ModuleResponse,
    ModuleTranslationCreate,
    ModuleTranslationUpdate,
    ModuleTranslationResponse,
    ContentSectionCreate,
    ContentSectionUpdate,
    ContentSectionResponse,
    RejectRequest,
)

router = APIRouter()

CONTENT_EDITORS = (RoleName.CONTENT_ADMIN,)


def _get_module_or_404(db: Session, module_id: uuid.UUID) -> Module:
    module = db.get(Module, module_id)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module


def _get_translation_or_404(db: Session, translation_id: uuid.UUID) -> ModuleTranslation:
    translation = db.get(ModuleTranslation, translation_id)
    if translation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module translation not found")
    return translation


# ---------- Modules ----------

@router.get("", response_model=list[ModuleResponse])
def list_modules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Module).order_by(Module.sort_order).all()


@router.get("/{module_id}", response_model=ModuleResponse)
def get_module(module_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_module_or_404(db, module_id)


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(
    payload: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    if db.query(Module).filter_by(module_code=payload.module_code).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="module_code already exists")
    module = Module(**payload.model_dump())
    db.add(module)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_CREATE,
            entity_type="module",
            entity_id=module.id,
            details={"module_code": module.module_code},
        )
    )
    db.commit()
    db.refresh(module)
    return module


@router.patch("/{module_id}", response_model=ModuleResponse)
def update_module(
    module_id: uuid.UUID,
    payload: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    module = _get_module_or_404(db, module_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_EDIT,
            entity_type="module",
            entity_id=module.id,
            details=payload.model_dump(exclude_unset=True, mode="json"),
        )
    )
    db.commit()
    db.refresh(module)
    return module


@router.post("/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_modules(
    payload: list[ModuleReorder],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    for item in payload:
        module = _get_module_or_404(db, item.module_id)
        module.sort_order = item.sort_order
    db.commit()
    return None


# ---------- Translations (per-language content + governance workflow) ----------

@router.get("/{module_id}/translations", response_model=list[ModuleTranslationResponse])
def list_translations(
    module_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    _get_module_or_404(db, module_id)
    return db.query(ModuleTranslation).filter_by(module_id=module_id).all()


@router.post(
    "/{module_id}/translations",
    response_model=ModuleTranslationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_translation(
    module_id: uuid.UUID,
    payload: ModuleTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    _get_module_or_404(db, module_id)
    existing = (
        db.query(ModuleTranslation)
        .filter_by(module_id=module_id, language_id=payload.language_id)
        .one_or_none()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Translation for this language already exists")

    translation = ModuleTranslation(module_id=module_id, **payload.model_dump())
    db.add(translation)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_CREATE,
            entity_type="module_translation",
            entity_id=translation.id,
        )
    )
    db.commit()
    db.refresh(translation)
    return translation


def _target_language(db: Session, code: str) -> Language:
    if code == "en":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="English is the source language; choose another language.")
    language = db.query(Language).filter_by(code=code).one_or_none()
    if language is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown language '{code}'")
    return language


@router.get("/{module_id}/translations/export.csv")
def export_translation_csv(
    module_id: uuid.UUID,
    language: str = Query(..., description="Target language code, e.g. ha, ff, kr"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """English source (plus any existing translation) as a CSV for translators."""
    module = _get_module_or_404(db, module_id)
    lang = _target_language(db, language)
    body = translation_io.export_csv(db, module, lang)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{module.module_code}_{language}.csv"'},
    )


@router.post("/{module_id}/translations/import")
async def import_translation_csv(
    module_id: uuid.UUID,
    language: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Loads a translated CSV as a DRAFT. It must then pass the normal review
    steps, including LOCALISATION_REVIEW, before it can be published."""
    module = _get_module_or_404(db, module_id)
    lang = _target_language(db, language)
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Translation file is larger than 5 MB.")
    try:
        summary = translation_io.import_csv(db, module, lang, raw)
    except translation_io.ImportError_ as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_EDIT,
            entity_type="module_translation",
            entity_id=uuid.UUID(summary["translation_id"]),
            details={"import": True, "language": language, "strings": summary["strings"]},
        )
    )
    db.commit()
    return summary


@router.patch("/translations/{translation_id}", response_model=ModuleTranslationResponse)
def update_translation(
    translation_id: uuid.UUID,
    payload: ModuleTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    translation = _get_translation_or_404(db, translation_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(translation, field, value)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_EDIT,
            entity_type="module_translation",
            entity_id=translation.id,
        )
    )
    db.commit()
    db.refresh(translation)
    return translation


@router.post("/translations/{translation_id}/submit-review", response_model=ModuleTranslationResponse)
def submit_for_review(
    translation_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """First workflow step: DRAFT -> PROGRAMME_REVIEW. Uses the same
    governance.advance() as every later step, so the same rules apply."""
    translation = _get_translation_or_404(db, translation_id)
    return advance(db, translation, current_user)


@router.post("/translations/{translation_id}/approve", response_model=ModuleTranslationResponse)
def approve_translation(
    translation_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    translation = _get_translation_or_404(db, translation_id)
    return advance(db, translation, current_user)


@router.post("/translations/{translation_id}/reject", response_model=ModuleTranslationResponse)
def reject_translation(
    translation_id: uuid.UUID,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    translation = _get_translation_or_404(db, translation_id)
    return reject(db, translation, current_user, payload.reason)


# ---------- Content sections ----------

@router.get("/{module_id}/sections", response_model=list[ContentSectionResponse])
def list_sections(module_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_module_or_404(db, module_id)
    return db.query(ContentSection).filter_by(module_id=module_id).order_by(ContentSection.sort_order).all()


@router.post(
    "/{module_id}/sections", response_model=ContentSectionResponse, status_code=status.HTTP_201_CREATED
)
def create_section(
    module_id: uuid.UUID,
    payload: ContentSectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    _get_module_or_404(db, module_id)
    section = ContentSection(module_id=module_id, **payload.model_dump())
    db.add(section)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_CREATE,
            entity_type="content_section",
            entity_id=section.id,
        )
    )
    db.commit()
    db.refresh(section)
    return section


@router.patch("/sections/{section_id}", response_model=ContentSectionResponse)
def update_section(
    section_id: uuid.UUID,
    payload: ContentSectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    section = db.get(ContentSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_EDIT,
            entity_type="content_section",
            entity_id=section.id,
        )
    )
    db.commit()
    db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    section_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    section = db.get(ContentSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    db.delete(section)
    db.commit()
    return None
