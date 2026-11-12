"""
The mobile app's interface text: translate, review and publish it per language,
the same way module translations are governed (content/governance.py), and let
phones download the published strings.

Who may do what (SUPER_ADMIN may do everything):
  - read the list, stats and files: CONTENT_ADMIN and the three reviewer roles;
  - edit or import translations: CONTENT_ADMIN and LOCALISATION_REVIEWER. Any
    edit returns the string to DRAFT, so it passes every review stage again;
  - move a string to the next stage: the role governance.py assigns to that stage.
    Nobody approves their own edit at a review stage (another person must).
English is the source and is never edited here: it comes from the app
(python -m app.l10n.seed).
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import require_roles
from app.content.governance import advance, reject
from app.database import get_db
from app.l10n import files, rules
from app.models import AppString, AppStringTranslation, Language, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, ContentReviewStatus, RoleName

router = APIRouter()
sync_router = APIRouter()

READERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.LOCALISATION_REVIEWER, RoleName.TECHNICAL_REVIEWER)
EDITORS = (RoleName.CONTENT_ADMIN, RoleName.LOCALISATION_REVIEWER)
IN_REVIEW = (ContentReviewStatus.PROGRAMME_REVIEW, ContentReviewStatus.LOCALISATION_REVIEW, ContentReviewStatus.TECHNICAL_QA)
ENTITY = "app_string_translation"
MAX_FILE = 5 * 1024 * 1024
# Phones ask for changes since their last download; this overlap catches a
# publish whose transaction committed just after that download (re-sending a
# string is harmless: the phone simply stores it again).
SYNC_OVERLAP = timedelta(minutes=5)


class TranslationEdit(BaseModel):
    text: str = Field(..., max_length=4000)
    text_one: str | None = Field(None, max_length=4000)


class RejectBody(BaseModel):
    reason: str | None = Field(None, max_length=500)


class BulkAction(BaseModel):
    action: Literal["submit-review", "approve", "reject"]
    ids: list[uuid.UUID] = Field(..., min_length=1, max_length=1000)
    reason: str | None = Field(None, max_length=500)


def _target_language(db: Session, code: str) -> Language:
    if code == "en":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="English is the source language; choose another language.")
    language = db.query(Language).filter_by(code=code).one_or_none()
    if language is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown language '{code}'")
    return language


def _name(user: User | None) -> str | None:
    return f"{user.first_name} {user.last_name}".strip() or user.username if user else None


def _row(s: AppString, t: AppStringTranslation | None, users: dict) -> dict:
    return {
        "key": s.key,
        "note": s.note,
        "placeholders": list(s.placeholders or []),
        "english": s.english,
        "english_one": s.english_one,
        "plural": s.is_plural,
        "translation_id": str(t.id) if t else None,
        "text": t.text if t else None,
        "text_one": t.text_one if t else None,
        "status": t.status.value if t else None,
        "needs_update": files.needs_update(s, t),
        "published_text": t.published_text if t else None,
        "published_text_one": t.published_text_one if t else None,
        "published_at": t.published_at.isoformat() if t and t.published_at else None,
        "edited_by": _name(users.get(t.edited_by)) if t and t.edited_by else None,
        "edited_by_id": str(t.edited_by) if t and t.edited_by else None,
        "edited_at": t.edited_at.isoformat() if t and t.edited_at else None,
    }


def _users(db: Session, ids) -> dict:
    ids = {i for i in ids if i}
    return {u.id: u for u in db.query(User).filter(User.id.in_(ids)).all()} if ids else {}


def _matches(s: AppString, t: AppStringTranslation | None, show: str, q: str) -> bool:
    if q:
        hay = " ".join([s.key, s.english, s.english_one or "", s.note, (t.text if t else "") or "", (t.text_one or "") if t else ""]).lower()
        if q not in hay:
            return False
    if show == "missing":
        return t is None
    if show == "draft":
        return t is not None and t.status == ContentReviewStatus.DRAFT
    if show == "in_review":
        return t is not None and t.status in IN_REVIEW
    if show == "published":
        return t is not None and t.published_text is not None
    if show == "rejected":
        return t is not None and t.status == ContentReviewStatus.REJECTED
    if show == "needs_update":
        return files.needs_update(s, t)
    return True


@router.get("")
def list_strings(
    language: str = Query(..., description="Target language code, e.g. ha"),
    show: Literal["all", "missing", "draft", "in_review", "published", "rejected", "needs_update"] = "all",
    q: str = Query("", max_length=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*READERS)),
):
    """Every active string with its translation in `language` (or none yet)."""
    lang = _target_language(db, language)
    saved = files.translations_by_string(db, lang)
    strings = files.active_strings(db)
    picked = [(s, saved.get(s.id)) for s in strings if _matches(s, saved.get(s.id), show, q.strip().lower())]
    users = _users(db, [t.edited_by for _, t in picked if t])
    return {"language": lang.code, "total": len(strings), "items": [_row(s, t, users) for s, t in picked]}


@router.get("/stats")
def stats(db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    """Completion per language: translated / total and published / total."""
    strings = {s.id: s for s in files.active_strings(db)}
    total = len(strings)
    out = []
    for lang in db.query(Language).filter(Language.code != "en").order_by(Language.name).all():
        ts = [t for t in db.query(AppStringTranslation).filter_by(language_id=lang.id).all() if t.string_id in strings]
        translated = len(ts)
        published = sum(1 for t in ts if t.published_text is not None)
        out.append({
            "language": lang.code,
            "name": lang.name,
            "total": total,
            "translated": translated,
            "published": published,
            "in_review": sum(1 for t in ts if t.status in IN_REVIEW),
            "needs_update": sum(1 for t in ts if files.needs_update(strings[t.string_id], t)),
            "translated_percent": round(100 * translated / total) if total else 0,
            "published_percent": round(100 * published / total) if total else 0,
        })
    return {"total": total, "languages": out}


@router.put("/{key}/translations/{language}")
def edit_translation(
    key: str,
    language: str,
    payload: TranslationEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*EDITORS)),
):
    """Saves a translation as DRAFT (it must pass every review stage again).
    Refused (422) for an empty text or a placeholder the English does not have;
    a left-out placeholder is returned as a warning."""
    lang = _target_language(db, language)
    s = db.query(AppString).filter_by(key=key).one_or_none()
    if s is None or s.retired_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown app string '{key}'")
    errors, warnings = rules.check(s, payload.text, payload.text_one)
    if errors:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"errors": errors, "warnings": warnings})
    text, text_one = payload.text.strip(), (payload.text_one or "").strip() or None
    t = db.query(AppStringTranslation).filter_by(string_id=s.id, language_id=lang.id).one_or_none()
    unchanged = t is not None and t.text == text and (t.text_one or None) == text_one and t.source_version == s.source_version
    if not unchanged:
        before = t.status.value if t else None
        if t is None:
            t = AppStringTranslation(string_id=s.id, language_id=lang.id, text=text)
            db.add(t)
        files.apply_edit(t, s, text, text_one, current_user, datetime.now(timezone.utc))
        db.flush()
        db.add(AuditLog(user_id=current_user.id, action=AuditAction.CONTENT_EDIT, entity_type=ENTITY, entity_id=t.id,
                        details={"key": key, "language": lang.code, "from": before, "to": "DRAFT"}))
        db.commit()
        db.refresh(t)
    return {"item": _row(s, t, _users(db, [t.edited_by])), "warnings": warnings, "changed": not unchanged}


def _translation(db: Session, translation_id: uuid.UUID) -> AppStringTranslation:
    t = db.query(AppStringTranslation).options(joinedload(AppStringTranslation.string)).filter_by(id=translation_id).one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App string translation not found")
    return t


def _step(db: Session, t: AppStringTranslation, actor: User, action: str, reason: str | None = None) -> None:
    """One workflow step without committing. Raises HTTPException when not allowed."""
    if (t.status in IN_REVIEW and actor.role != RoleName.SUPER_ADMIN and t.edited_by == actor.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You edited this translation, so another reviewer must review it.",
        )
    if action == "reject":
        reject(db, t, actor, reason, entity_type=ENTITY, commit=False)
        return
    if action == "submit-review" and t.status != ContentReviewStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only a DRAFT can be submitted for review.")
    if action == "approve" and t.status not in IN_REVIEW:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"A {t.status.value} translation is not waiting for review.")
    advance(db, t, actor, entity_type=ENTITY, commit=False)
    if t.status == ContentReviewStatus.PUBLISHED:
        # From now on phones show this text (they keep the previous one until here).
        t.published_text = t.text
        t.published_text_one = t.text_one
        t.published_source_version = t.source_version
        t.published_at = datetime.now(timezone.utc)


def _respond(db: Session, t: AppStringTranslation) -> dict:
    return _row(t.string, t, _users(db, [t.edited_by]))


@router.post("/translations/{translation_id}/submit-review")
def submit_for_review(translation_id: uuid.UUID, db: Session = Depends(get_db),
                      current_user: User = Depends(require_roles(*READERS))):
    t = _translation(db, translation_id)
    _step(db, t, current_user, "submit-review")
    db.commit()
    db.refresh(t)
    return _respond(db, t)


@router.post("/translations/{translation_id}/approve")
def approve(translation_id: uuid.UUID, db: Session = Depends(get_db),
            current_user: User = Depends(require_roles(*READERS))):
    t = _translation(db, translation_id)
    _step(db, t, current_user, "approve")
    db.commit()
    db.refresh(t)
    return _respond(db, t)


@router.post("/translations/{translation_id}/reject")
def reject_translation(translation_id: uuid.UUID, payload: RejectBody, db: Session = Depends(get_db),
                       current_user: User = Depends(require_roles(*READERS))):
    t = _translation(db, translation_id)
    _step(db, t, current_user, "reject", payload.reason)
    db.commit()
    db.refresh(t)
    return _respond(db, t)


@router.post("/translations/bulk")
def bulk(payload: BulkAction, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    """The same workflow step for many translations, all or nothing: if any one is
    not allowed, none moves and every problem is listed."""
    rows = (db.query(AppStringTranslation).options(joinedload(AppStringTranslation.string))
            .filter(AppStringTranslation.id.in_(payload.ids)).all())
    found = {t.id: t for t in rows}
    problems = [{"id": str(i), "key": None, "problem": "Not found"} for i in payload.ids if i not in found]
    for t in rows:
        try:
            _step(db, t, current_user, payload.action, payload.reason)
        except HTTPException as exc:
            problems.append({"id": str(t.id), "key": t.string.key, "problem": exc.detail})
    if problems:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail={"message": f"Nothing was changed: {len(problems)} translation(s) cannot be moved.", "problems": problems})
    db.commit()
    return {"moved": len(rows)}


@router.get("/export")
def export(
    language: str = Query(...),
    format: Literal["csv", "json"] = "csv",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*READERS)),
):
    """Every active string with its English, note, placeholders and current translation."""
    lang = _target_language(db, language)
    if format == "json":
        return Response(content=files.export_json(db, lang), media_type="application/json; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="app_text_{lang.code}.json"'})
    return Response(content=files.export_csv(db, lang), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="app_text_{lang.code}.csv"'})


@router.post("/import")
async def import_translations(
    language: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*EDITORS)),
):
    """Loads a translated CSV or JSON file as DRAFT translations, all or nothing.
    A bad file is refused (422) with every problem listed by row."""
    lang = _target_language(db, language)
    raw = await file.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Translation file is larger than 5 MB.")
    try:
        result = files.import_file(db, lang, raw, file.filename or "", current_user)
    except files.ImportRejected as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"message": str(exc), "problems": exc.problems}) from exc
    for t in result.changed:
        db.add(AuditLog(user_id=current_user.id, action=AuditAction.CONTENT_EDIT, entity_type=ENTITY, entity_id=t.id,
                        details={"import": True, "language": lang.code, "key": t.string.key if t.string else None, "to": "DRAFT"}))
    db.commit()
    return {"created": result.created, "updated": result.updated, "unchanged": result.unchanged,
            "skipped_empty": result.skipped_empty, "warnings": result.warnings}


@sync_router.get("/app-strings")
def sync_app_strings(
    language: str = Query(..., min_length=2, max_length=10),
    since: datetime | None = Query(None, description="server_time of the phone's last download"),
    db: Session = Depends(get_db),
):
    """Published interface text for one language, for phones. Public like
    GET /languages: the sign-in and consent screens come before login and should
    already be in the learner's language. Only PUBLISHED text is ever sent.

    Without `since` (or with an unreadable one) everything is sent and `full` is
    true: the phone replaces what it has. With `since`, only strings published or
    changed after it, plus `removed` keys (retired from the app). Safe to repeat."""
    lang = db.query(Language).filter_by(code=language).one_or_none()
    if lang is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown language")
    server_time = datetime.now(timezone.utc)
    if lang.code == "en":
        return {"language": "en", "server_time": server_time.isoformat(), "full": True, "strings": [], "removed": []}
    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    full = since is None
    query = (db.query(AppStringTranslation, AppString)
             .join(AppString, AppString.id == AppStringTranslation.string_id)
             .filter(AppStringTranslation.language_id == lang.id,
                     AppStringTranslation.published_text.isnot(None),
                     AppString.retired_at.is_(None)))
    removed: list[str] = []
    if not full:
        after = since - SYNC_OVERLAP
        query = query.filter(or_(AppStringTranslation.published_at > after, AppString.updated_at > after))
        removed = [k for (k,) in db.query(AppString.key).filter(AppString.retired_at.isnot(None), AppString.retired_at > after).all()]
    strings = [{"key": s.key, "text": t.published_text, "text_one": t.published_text_one if s.is_plural else None}
               for t, s in query.order_by(AppString.key).all()]
    return {"language": lang.code, "server_time": server_time.isoformat(), "full": full, "strings": strings, "removed": removed}
