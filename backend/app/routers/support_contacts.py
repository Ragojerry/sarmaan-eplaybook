"""
Support contacts: the people learners can reach from the Support deck on the
phone's Ask tab (call, SMS, email, WhatsApp or a web link).

Admin portal (prefix /support-contacts):
  GET    ""                 every contact that is not deleted, in display order
  POST   ""                 add a contact (goes to the end of the list)
  PUT    /{id}              edit a contact
  PUT    /{id}/active       activate or deactivate
  POST   /reorder           new display order (every contact, once)
  DELETE /{id}              delete (kept as a tombstone so phones remove it)
  GET    /settings          the deck's optional note (empty = hidden)
  PUT    /settings          change the note
Managing: CONTENT_ADMIN (and SUPER_ADMIN); every other portal role reads.
Every change is audited with the before and after values.

Phones (prefix /sync):
  GET /sync/support-contacts?since=   the active contacts for this account's
      audience. Without `since`: all of them and `full` = true (the phone
      replaces its copy). With `since`: only contacts changed after it, plus
      the ids to remove (deactivated, deleted, or no longer for this audience).
Old app versions never call it, so nothing changes for them.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.learning.access import is_learner
from app.models import PlatformSetting, SupportContact, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, LearnerRole, RoleName, SupportContactType
from app.support.validation import ContactValueError, normalise_value

router = APIRouter()
sync_router = APIRouter()

MANAGERS = (RoleName.CONTENT_ADMIN,)
READERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.LOCALISATION_REVIEWER,
           RoleName.TECHNICAL_REVIEWER, RoleName.SUPERVISOR, RoleName.READ_ONLY)
ENTITY = "support_contact"
NOTE_KEY = "support_deck_note"
NOTE_MAX = 200
# Phones ask for changes since their last download; this overlap catches a
# change committed while the previous download was being answered.
SYNC_OVERLAP = timedelta(minutes=5)
FIELDS = ("type", "label", "value", "whatsapp_message", "email_subject", "include_app_version",
          "availability", "languages", "audience")


class ContactIn(BaseModel):
    type: SupportContactType
    label: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=500)
    whatsapp_message: str | None = Field(None, max_length=500)
    email_subject: str | None = Field(None, max_length=150)
    include_app_version: bool = False
    availability: str | None = Field(None, max_length=120)
    languages: str | None = Field(None, max_length=120)
    audience: list[LearnerRole] = Field(default_factory=list, description="Learner roles; empty = every learner")
    is_active: bool = True


class ActiveIn(BaseModel):
    active: bool


class ReorderIn(BaseModel):
    ids: list[uuid.UUID]


class SettingsIn(BaseModel):
    note: str = Field("", max_length=NOTE_MAX)


def _blank(s: str | None) -> str | None:
    s = (s or "").strip()
    return s or None


def _clean(payload: ContactIn) -> dict:
    """The stored fields: value checked for its type, text trimmed, and the
    fields that do not apply to the type cleared."""
    try:
        value = normalise_value(payload.type, payload.value)
    except ContactValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    label = payload.label.strip()
    if not label:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Enter a label.")
    t = payload.type
    return {
        "type": t,
        "label": label,
        "value": value,
        "whatsapp_message": _blank(payload.whatsapp_message) if t == SupportContactType.WHATSAPP else None,
        "email_subject": _blank(payload.email_subject) if t == SupportContactType.EMAIL else None,
        "include_app_version": payload.include_app_version and t in (SupportContactType.WHATSAPP, SupportContactType.EMAIL),
        "availability": _blank(payload.availability),
        "languages": _blank(payload.languages),
        "audience": sorted({r.value for r in payload.audience}),
    }


def _snapshot(c: SupportContact) -> dict:
    out = {f: getattr(c, f) for f in FIELDS}
    out["type"] = c.type.value
    out["is_active"] = c.is_active
    return out


def _name(user: User | None) -> str | None:
    return f"{user.first_name} {user.last_name}".strip() if user else None


def _admin_row(c: SupportContact, users: dict) -> dict:
    return {
        "id": str(c.id),
        **_snapshot(c),
        "display_order": c.display_order,
        "created_by": _name(users.get(c.created_by)),
        "updated_by": _name(users.get(c.updated_by)),
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _phone_row(c: SupportContact) -> dict:
    return {
        "id": str(c.id),
        "type": c.type.value,
        "label": c.label,
        "value": c.value,
        "whatsapp_message": c.whatsapp_message,
        "email_subject": c.email_subject,
        "include_app_version": c.include_app_version,
        "availability": c.availability,
        "languages": c.languages,
        "display_order": c.display_order,
    }


def _live(db: Session):
    return db.query(SupportContact).filter(SupportContact.deleted_at.is_(None))


def _get(db: Session, contact_id: uuid.UUID) -> SupportContact:
    c = _live(db).filter(SupportContact.id == contact_id).one_or_none()
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support contact not found")
    return c


def _audit(db: Session, user: User, action: AuditAction, contact_id: uuid.UUID | None, details: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=action, entity_type=ENTITY, entity_id=contact_id, details=details))


def _touch(c: SupportContact, user: User) -> None:
    c.updated_by = user.id
    c.updated_at = datetime.now(timezone.utc)


def _respond(db: Session, c: SupportContact) -> dict:
    db.refresh(c)
    ids = {i for i in (c.created_by, c.updated_by) if i}
    users = {u.id: u for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return _admin_row(c, users)


def _note(db: Session) -> str:
    row = db.get(PlatformSetting, NOTE_KEY)
    return row.value if row and isinstance(row.value, str) else ""


# ---------- admin portal ----------

@router.get("")
def list_contacts(db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    rows = _live(db).order_by(SupportContact.display_order, SupportContact.created_at).all()
    ids = {i for c in rows for i in (c.created_by, c.updated_by) if i}
    users = {u.id: u for u in db.query(User).filter(User.id.in_(ids))} if ids else {}
    return [_admin_row(c, users) for c in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactIn, db: Session = Depends(get_db),
                   current_user: User = Depends(require_roles(*MANAGERS))):
    fields = _clean(payload)
    last = _live(db).order_by(SupportContact.display_order.desc()).first()
    c = SupportContact(**fields, is_active=payload.is_active, display_order=(last.display_order + 1) if last else 0,
                       created_by=current_user.id)
    _touch(c, current_user)
    db.add(c)
    db.flush()
    _audit(db, current_user, AuditAction.SUPPORT_CONTACT_CREATE, c.id, {"new": _snapshot(c)})
    db.commit()
    return _respond(db, c)


# Declared before /{contact_id} so "settings" and "reorder" are never read as an id.
@router.get("/settings")
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    return {"note": _note(db), "note_max": NOTE_MAX}


@router.put("/settings")
def save_settings(payload: SettingsIn, db: Session = Depends(get_db),
                  current_user: User = Depends(require_roles(*MANAGERS))):
    note = payload.note.strip()
    before = _note(db)
    if note != before:
        row = db.get(PlatformSetting, NOTE_KEY)
        if row is None:
            row = PlatformSetting(key=NOTE_KEY, value=note,
                                  note="Optional line under the Support deck on the Ask tab; empty = hidden")
            db.add(row)
        row.value, row.updated_by = note, current_user.id
        db.add(AuditLog(user_id=current_user.id, action=AuditAction.SETTING_CHANGE, entity_type="platform_setting",
                        details={"key": NOTE_KEY, "before": before, "after": note}))
        db.commit()
    return {"note": note, "note_max": NOTE_MAX}


@router.post("/reorder")
def reorder(payload: ReorderIn, db: Session = Depends(get_db),
            current_user: User = Depends(require_roles(*MANAGERS))):
    rows = _live(db).order_by(SupportContact.display_order, SupportContact.created_at).all()
    if len(payload.ids) != len(set(payload.ids)) or set(payload.ids) != {c.id for c in rows}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Send every support contact exactly once, in the new order.")
    before = [str(c.id) for c in rows]
    by_id = {c.id: c for c in rows}
    for position, contact_id in enumerate(payload.ids):
        c = by_id[contact_id]
        if c.display_order != position:
            c.display_order = position
            _touch(c, current_user)  # phones download the new position
    after = [str(i) for i in payload.ids]
    if after != before:
        _audit(db, current_user, AuditAction.SUPPORT_CONTACT_REORDER, None, {"before": before, "after": after})
    db.commit()
    return list_contacts(db, current_user)


@router.put("/{contact_id}")
def update_contact(contact_id: uuid.UUID, payload: ContactIn, db: Session = Depends(get_db),
                   current_user: User = Depends(require_roles(*MANAGERS))):
    c = _get(db, contact_id)
    fields = _clean(payload)
    before = _snapshot(c)
    for f, v in fields.items():
        setattr(c, f, v)
    if payload.is_active != c.is_active:
        c.is_active = payload.is_active
    after = _snapshot(c)
    if after != before:
        _touch(c, current_user)
        _audit(db, current_user, AuditAction.SUPPORT_CONTACT_UPDATE, c.id, {"before": before, "after": after})
        db.commit()
    return _respond(db, c)


@router.put("/{contact_id}/active")
def set_active(contact_id: uuid.UUID, payload: ActiveIn, db: Session = Depends(get_db),
               current_user: User = Depends(require_roles(*MANAGERS))):
    c = _get(db, contact_id)
    if c.is_active != payload.active:
        c.is_active = payload.active
        _touch(c, current_user)
        action = AuditAction.SUPPORT_CONTACT_ACTIVATE if payload.active else AuditAction.SUPPORT_CONTACT_DEACTIVATE
        _audit(db, current_user, action, c.id, {"label": c.label, "type": c.type.value})
        db.commit()
    return _respond(db, c)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: uuid.UUID, db: Session = Depends(get_db),
                   current_user: User = Depends(require_roles(*MANAGERS))):
    c = _get(db, contact_id)
    _audit(db, current_user, AuditAction.SUPPORT_CONTACT_DELETE, c.id, {"previous": _snapshot(c)})
    c.is_active = False
    c.deleted_at = datetime.now(timezone.utc)
    _touch(c, current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- phones ----------

def visible_to(c: SupportContact, user: User) -> bool:
    """Active, not deleted, and for this account. Learners see contacts for
    every learner plus those listing their learner role; staff see them all."""
    if c.deleted_at is not None or not c.is_active:
        return False
    if not c.audience or not is_learner(user):
        return True
    return user.learner_role is not None and user.learner_role.value in c.audience


@sync_router.get("/support-contacts")
def sync_support_contacts(
    since: datetime | None = Query(None, description="server_time of the phone's last download"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server_time = datetime.now(timezone.utc)
    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    full = since is None
    query = db.query(SupportContact)
    if full:
        query = query.filter(SupportContact.deleted_at.is_(None), SupportContact.is_active.is_(True))
    else:
        query = query.filter(SupportContact.updated_at > since - SYNC_OVERLAP)
    contacts, removed = [], []
    for c in query.order_by(SupportContact.display_order, SupportContact.created_at).all():
        if visible_to(c, current_user):
            contacts.append(_phone_row(c))
        elif not full:
            removed.append(str(c.id))
    return {"server_time": server_time.isoformat(), "full": full, "contacts": contacts, "removed": removed, "note": _note(db) or None}
