"""
The first-launch consent screen's text, editable in the admin portal and
translatable per language. GET is public (the screen comes before login,
like GET /languages); the phone caches every language and shows the chosen
one, falling back to English. Saving goes live at once; each save bumps the
version and is audited with the previous text.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import ConsentText, Language, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName

router = APIRouter()

SOURCE_LANGUAGE = "en"
FIELDS = ("title", "body", "usage_label", "button_label")
# English is the source text; translators may only write the other languages.
SOURCE_EDITORS = (RoleName.CONTENT_ADMIN,)
TRANSLATORS = (RoleName.CONTENT_ADMIN, RoleName.LOCALISATION_REVIEWER)


class ConsentIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    # Holds the full privacy notice (content/privacy_notice/, about 21,000 characters in English).
    body: str = Field(min_length=20, max_length=40000)
    usage_label: str = Field(min_length=1, max_length=255)
    button_label: str = Field(min_length=1, max_length=60)


def _serialize(c: ConsentText, source_version: int | None) -> dict:
    out = {f: getattr(c, f) for f in FIELDS}
    out.update(
        language=c.language,
        version=c.version,
        updated_at=c.updated_at.isoformat() if c.updated_at else None,
        # A translation made from an older English text than the current one.
        outdated=c.language != SOURCE_LANGUAGE and (c.source_version or 0) < (source_version or 0),
    )
    return out


@router.get("")
def list_consent(db: Session = Depends(get_db)):
    """Every language's consent text. Deliberately public: shown before login."""
    rows = db.query(ConsentText).order_by(ConsentText.language).all()
    source = next((c.version for c in rows if c.language == SOURCE_LANGUAGE), None)
    return [_serialize(c, source) for c in rows]


@router.put("/{language}")
def save_consent(
    language: str,
    payload: ConsentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*TRANSLATORS)),
):
    if language == SOURCE_LANGUAGE and current_user.role not in SOURCE_EDITORS + (RoleName.SUPER_ADMIN,):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only content admins can change the English consent text.")
    if db.query(Language).filter_by(code=language).one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown language")

    new = {f: getattr(payload, f).strip() for f in FIELDS}
    row = db.get(ConsentText, language)
    previous = {f: getattr(row, f) for f in FIELDS} if row else None
    source = db.get(ConsentText, SOURCE_LANGUAGE)
    if row is None:
        row = ConsentText(language=language, version=0, **new)
        db.add(row)
    elif previous == new:
        return _serialize(row, source.version if source else None)
    for f, v in new.items():
        setattr(row, f, v)
    row.version += 1
    if language != SOURCE_LANGUAGE:
        row.source_version = source.version if source else None
    row.updated_by = current_user.id
    row.updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.CONSENT_UPDATE, entity_type="consent_text",
                    details={"language": language, "version": row.version, "previous": previous, "new": new}))
    db.commit()
    db.refresh(row)
    source_version = row.version if language == SOURCE_LANGUAGE else (source.version if source else None)
    return _serialize(row, source_version)


@router.delete("/{language}", status_code=status.HTTP_204_NO_CONTENT)
def delete_translation(
    language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*TRANSLATORS)),
):
    """Removes a translation; phones then show the English text."""
    if language == SOURCE_LANGUAGE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The English text cannot be deleted.")
    row = db.get(ConsentText, language)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No translation for this language")
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.CONSENT_UPDATE, entity_type="consent_text",
                    details={"language": language, "deleted": True,
                             "previous": {f: getattr(row, f) for f in FIELDS}}))
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
