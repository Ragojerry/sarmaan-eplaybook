"""
Tools repository (resource library): Tools modules assigned to learner roles,
each holding links to documents, forms, images and websites that learners open
online. Only links and descriptions are stored; the server never fetches them.

Separate from training by design: completion, the General test gate and
unlock, the time rule, progress, restart, releases, training reports and the
question index never read these tables. No governance workflow: an active
flag and the audit log (decision 2026-11-13).

Admin portal (prefix /tools), managing: CONTENT_ADMIN (and SUPER_ADMIN);
every other portal role reads. Every change is audited (entity_type
"tool_module" or "tool_item").
  GET    /modules                    Tools modules (not deleted), in order
  POST   /modules                    add       PUT /modules/{id}   edit
  PUT    /modules/{id}/active        activate / deactivate
  POST   /modules/reorder            new order (every module, once)
  DELETE /modules/{id}               delete (its items go with it)
  GET    /items                      every item (not deleted), with duplicate-link flags
  POST   /items                      add       PUT /items/{id}     edit
  PUT    /items/{id}/active          activate / deactivate
  POST   /modules/{id}/items/reorder new order of one module's items
  DELETE /items/{id}                 delete
  POST   /modules/{id}/items/import  CSV (title, description, type, url, category[, languages]):
                                     all rows or none; every invalid row is reported
  GET    /opens?date_from=&date_to=  "Most opened tools": open counts per item, no people
                                     (dates inclusive; default the last 90 days; no dates = all time
                                     only when all_time=true)

Phones (prefix /sync):
  GET /sync/tools?since=   the active Tools modules for this account (always all of
      them; there are few) and their active items for this account. Without
      `since`: every item and `full` = true. With `since`: items changed after it
      (or whose module changed), plus the ids to remove. Older apps never call it.
"""
import csv
import io
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.learning.access import is_learner
from app.models import AnalyticsEvent, ToolItem, ToolModule, User
from app.models.audit_log import AuditLog
from app.models.enums import AnalyticsEventType, AuditAction, LearnerRole, ModuleAudience, RoleName, ToolItemType
from app.tools.links import LinkError, check_url, host_label, same_link

router = APIRouter()
sync_router = APIRouter()

MANAGERS = (RoleName.CONTENT_ADMIN,)
READERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.LOCALISATION_REVIEWER,
           RoleName.TECHNICAL_REVIEWER, RoleName.SUPERVISOR, RoleName.READ_ONLY)
SYNC_OVERLAP = timedelta(minutes=5)
MAX_IMPORT = 1024 * 1024
MAX_IMPORT_ROWS = 1000
MODULE_FIELDS = ("title", "description", "audience", "learner_roles", "is_active")
ITEM_FIELDS = ("title", "description", "type", "url", "category", "languages", "audience", "is_active", "last_reviewed")


class ModuleIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(None, max_length=2000)
    audience: ModuleAudience = ModuleAudience.GENERAL
    learner_roles: list[LearnerRole] = Field(default_factory=list)
    is_active: bool = True


class ItemIn(BaseModel):
    tool_module_id: uuid.UUID
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    type: ToolItemType
    url: str = Field(min_length=1, max_length=2000)
    category: str | None = Field(None, max_length=80)
    languages: str | None = Field(None, max_length=120)
    audience: list[LearnerRole] = Field(default_factory=list, description="Learner roles; empty = everyone the module is for")
    is_active: bool = True
    last_reviewed: date | None = None


class ActiveIn(BaseModel):
    active: bool


class ReorderIn(BaseModel):
    ids: list[uuid.UUID]


def _blank(s: str | None) -> str | None:
    s = (s or "").strip()
    return s or None


def _unprocessable(detail) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _module_fields(p: ModuleIn) -> dict:
    title = p.title.strip()
    if not title:
        raise _unprocessable("Enter a title.")
    roles = sorted({r.value for r in p.learner_roles})
    if p.audience == ModuleAudience.ROLE_SPECIFIC and not roles:
        raise _unprocessable("Choose at least one learner role, or make the Tools module General.")
    return {"title": title, "description": _blank(p.description), "audience": p.audience,
            "learner_roles": roles if p.audience == ModuleAudience.ROLE_SPECIFIC else [], "is_active": p.is_active}


def _item_fields(p: ItemIn) -> dict:
    title = p.title.strip()
    if not title:
        raise _unprocessable("Enter a title.")
    try:
        url = check_url(p.url)
    except LinkError as e:
        raise _unprocessable(str(e))
    return {"title": title, "description": _blank(p.description), "type": p.type, "url": url, "host": host_label(url),
            "category": _blank(p.category), "languages": _blank(p.languages),
            "audience": sorted({r.value for r in p.audience}), "is_active": p.is_active, "last_reviewed": p.last_reviewed}


def _snap(row, fields) -> dict:
    out = {}
    for f in fields:
        v = getattr(row, f)
        out[f] = v.value if hasattr(v, "value") else (v.isoformat() if isinstance(v, date) else v)
    return out


def _name(user: User | None) -> str | None:
    return f"{user.first_name} {user.last_name}".strip() if user else None


def _users(db: Session, rows) -> dict:
    ids = {i for r in rows for i in (r.created_by, r.updated_by) if i}
    return {u.id: u for u in db.query(User).filter(User.id.in_(ids))} if ids else {}


def _touch(row, user: User) -> None:
    row.updated_by = user.id
    row.updated_at = datetime.now(timezone.utc)


def _audit(db: Session, user: User, action: AuditAction, entity: str, entity_id, details: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=action, entity_type=entity, entity_id=entity_id, details=details))


def _live_modules(db: Session):
    return db.query(ToolModule).filter(ToolModule.deleted_at.is_(None))


def _live_items(db: Session):
    return db.query(ToolItem).filter(ToolItem.deleted_at.is_(None))


def _module(db: Session, module_id: uuid.UUID) -> ToolModule:
    m = _live_modules(db).filter(ToolModule.id == module_id).one_or_none()
    if m is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tools module not found")
    return m


def _item(db: Session, item_id: uuid.UUID) -> ToolItem:
    i = _live_items(db).filter(ToolItem.id == item_id).one_or_none()
    if i is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tools item not found")
    return i


def _module_row(m: ToolModule, users: dict, item_count: int = 0) -> dict:
    return {"id": str(m.id), **_snap(m, MODULE_FIELDS), "display_order": m.display_order, "item_count": item_count,
            "updated_by": _name(users.get(m.updated_by)), "updated_at": m.updated_at.isoformat() if m.updated_at else None}


def _duplicates(db: Session) -> dict[str, list[ToolItem]]:
    by_link = defaultdict(list)
    for i in _live_items(db):
        by_link[same_link(i.url)].append(i)
    return by_link


def _item_row(i: ToolItem, users: dict, dups: dict) -> dict:
    others = [o for o in dups.get(same_link(i.url), []) if o.id != i.id]
    return {"id": str(i.id), "tool_module_id": str(i.tool_module_id), **_snap(i, ITEM_FIELDS), "host": i.host,
            "display_order": i.display_order, "duplicates": [{"id": str(o.id), "title": o.title} for o in others],
            "created_by": _name(users.get(i.created_by)), "updated_by": _name(users.get(i.updated_by)),
            "updated_at": i.updated_at.isoformat() if i.updated_at else None}


def _respond_item(db: Session, i: ToolItem) -> dict:
    db.refresh(i)
    return _item_row(i, _users(db, [i]), _duplicates(db))


def _set_order(db: Session, rows: list, ids: list[uuid.UUID], user: User, entity: str, scope: dict) -> None:
    if len(ids) != len(set(ids)) or set(ids) != {r.id for r in rows}:
        raise _unprocessable("Send every entry exactly once, in the new order.")
    before = [str(r.id) for r in rows]
    by_id = {r.id: r for r in rows}
    for position, rid in enumerate(ids):
        r = by_id[rid]
        if r.display_order != position:
            r.display_order = position
            _touch(r, user)
    after = [str(i) for i in ids]
    if after != before:
        _audit(db, user, AuditAction.TOOL_REORDER, entity, None, {**scope, "before": before, "after": after})


# ---------- Tools modules ----------

@router.get("/modules")
def list_modules(db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    rows = _live_modules(db).order_by(ToolModule.display_order, ToolModule.created_at).all()
    counts = dict(db.query(ToolItem.tool_module_id, func.count()).filter(ToolItem.deleted_at.is_(None))
                  .group_by(ToolItem.tool_module_id).all())
    users = _users(db, rows)
    return [_module_row(m, users, counts.get(m.id, 0)) for m in rows]


@router.post("/modules", status_code=status.HTTP_201_CREATED)
def create_module(payload: ModuleIn, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*MANAGERS))):
    last = _live_modules(db).order_by(ToolModule.display_order.desc()).first()
    m = ToolModule(**_module_fields(payload), display_order=(last.display_order + 1) if last else 0, created_by=current_user.id)
    _touch(m, current_user)
    db.add(m)
    db.flush()
    _audit(db, current_user, AuditAction.TOOL_CREATE, "tool_module", m.id, {"new": _snap(m, MODULE_FIELDS)})
    db.commit()
    db.refresh(m)
    return _module_row(m, _users(db, [m]))


@router.post("/modules/reorder")
def reorder_modules(payload: ReorderIn, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*MANAGERS))):
    rows = _live_modules(db).order_by(ToolModule.display_order, ToolModule.created_at).all()
    _set_order(db, rows, payload.ids, current_user, "tool_module", {})
    db.commit()
    return list_modules(db, current_user)


@router.put("/modules/{module_id}")
def update_module(module_id: uuid.UUID, payload: ModuleIn, db: Session = Depends(get_db),
                  current_user: User = Depends(require_roles(*MANAGERS))):
    m = _module(db, module_id)
    before = _snap(m, MODULE_FIELDS)
    for f, v in _module_fields(payload).items():
        setattr(m, f, v)
    after = _snap(m, MODULE_FIELDS)
    if after != before:
        _touch(m, current_user)
        _audit(db, current_user, AuditAction.TOOL_UPDATE, "tool_module", m.id, {"before": before, "after": after})
        db.commit()
    db.refresh(m)
    return _module_row(m, _users(db, [m]))


@router.put("/modules/{module_id}/active")
def set_module_active(module_id: uuid.UUID, payload: ActiveIn, db: Session = Depends(get_db),
                      current_user: User = Depends(require_roles(*MANAGERS))):
    m = _module(db, module_id)
    if m.is_active != payload.active:
        m.is_active = payload.active
        _touch(m, current_user)
        _audit(db, current_user, AuditAction.TOOL_ACTIVATE if payload.active else AuditAction.TOOL_DEACTIVATE,
               "tool_module", m.id, {"title": m.title})
        db.commit()
    db.refresh(m)
    return _module_row(m, _users(db, [m]))


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(module_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*MANAGERS))):
    m = _module(db, module_id)
    now = datetime.now(timezone.utc)
    items = _live_items(db).filter(ToolItem.tool_module_id == m.id).all()
    _audit(db, current_user, AuditAction.TOOL_DELETE, "tool_module", m.id,
           {"previous": _snap(m, MODULE_FIELDS), "items_deleted": [str(i.id) for i in items]})
    for row in [m, *items]:
        row.is_active = False
        row.deleted_at = now
        _touch(row, current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- items ----------

@router.get("/items")
def list_items(db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    rows = (_live_items(db).join(ToolModule, ToolModule.id == ToolItem.tool_module_id)
            .filter(ToolModule.deleted_at.is_(None))
            .order_by(ToolModule.display_order, ToolItem.display_order, ToolItem.created_at).all())
    users, dups = _users(db, rows), _duplicates(db)
    return [_item_row(i, users, dups) for i in rows]


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemIn, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*MANAGERS))):
    m = _module(db, payload.tool_module_id)
    fields = _item_fields(payload)
    last = _live_items(db).filter(ToolItem.tool_module_id == m.id).order_by(ToolItem.display_order.desc()).first()
    i = ToolItem(tool_module_id=m.id, **fields, display_order=(last.display_order + 1) if last else 0, created_by=current_user.id)
    _touch(i, current_user)
    db.add(i)
    db.flush()
    _audit(db, current_user, AuditAction.TOOL_CREATE, "tool_item", i.id, {"tool_module_id": str(m.id), "new": _snap(i, ITEM_FIELDS)})
    db.commit()
    return _respond_item(db, i)


@router.put("/items/{item_id}")
def update_item(item_id: uuid.UUID, payload: ItemIn, db: Session = Depends(get_db),
                current_user: User = Depends(require_roles(*MANAGERS))):
    i = _item(db, item_id)
    target = _module(db, payload.tool_module_id)
    before = {**_snap(i, ITEM_FIELDS), "tool_module_id": str(i.tool_module_id)}
    for f, v in _item_fields(payload).items():
        setattr(i, f, v)
    if target.id != i.tool_module_id:
        last = _live_items(db).filter(ToolItem.tool_module_id == target.id).order_by(ToolItem.display_order.desc()).first()
        i.tool_module_id, i.display_order = target.id, (last.display_order + 1) if last else 0
    after = {**_snap(i, ITEM_FIELDS), "tool_module_id": str(i.tool_module_id)}
    if after != before:
        _touch(i, current_user)
        _audit(db, current_user, AuditAction.TOOL_UPDATE, "tool_item", i.id, {"before": before, "after": after})
        db.commit()
    return _respond_item(db, i)


@router.put("/items/{item_id}/active")
def set_item_active(item_id: uuid.UUID, payload: ActiveIn, db: Session = Depends(get_db),
                    current_user: User = Depends(require_roles(*MANAGERS))):
    i = _item(db, item_id)
    if i.is_active != payload.active:
        i.is_active = payload.active
        _touch(i, current_user)
        _audit(db, current_user, AuditAction.TOOL_ACTIVATE if payload.active else AuditAction.TOOL_DEACTIVATE,
               "tool_item", i.id, {"title": i.title})
        db.commit()
    return _respond_item(db, i)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*MANAGERS))):
    i = _item(db, item_id)
    _audit(db, current_user, AuditAction.TOOL_DELETE, "tool_item", i.id, {"previous": _snap(i, ITEM_FIELDS)})
    i.is_active = False
    i.deleted_at = datetime.now(timezone.utc)
    _touch(i, current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/modules/{module_id}/items/reorder")
def reorder_items(module_id: uuid.UUID, payload: ReorderIn, db: Session = Depends(get_db),
                  current_user: User = Depends(require_roles(*MANAGERS))):
    m = _module(db, module_id)
    rows = (_live_items(db).filter(ToolItem.tool_module_id == m.id)
            .order_by(ToolItem.display_order, ToolItem.created_at).all())
    _set_order(db, rows, payload.ids, current_user, "tool_item", {"tool_module_id": str(m.id)})
    db.commit()
    return list_items(db, current_user)


@router.post("/modules/{module_id}/items/import")
async def import_items(module_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db),
                       current_user: User = Depends(require_roles(*MANAGERS))):
    """CSV with a header row: title, description, type, url, category (languages optional).
    Every row is checked first; if any row is invalid nothing is imported and every
    problem is listed with its line number."""
    m = _module(db, module_id)
    raw = await file.read(MAX_IMPORT + 1)
    if len(raw) > MAX_IMPORT:
        raise _unprocessable("The file is larger than 1 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise _unprocessable("Save the file as CSV UTF-8 and try again.")
    reader = csv.DictReader(io.StringIO(text))
    header = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
    missing = [c for c in ("title", "type", "url") if c not in header]
    if missing:
        raise _unprocessable({"message": f"Missing column(s): {', '.join(missing)}. Expected: title, description, type, url, category.",
                              "errors": []})
    reader.fieldnames = header
    errors, parsed = [], []
    for n, row in enumerate(reader, start=2):
        if n - 1 > MAX_IMPORT_ROWS:
            errors.append({"row": n, "error": f"More than {MAX_IMPORT_ROWS} rows: split the file."})
            break
        row = {k: (v or "").strip() for k, v in row.items() if k}
        if not any(row.values()):
            continue
        problems = []
        title = row.get("title", "")
        if not title:
            problems.append("title is empty")
        elif len(title) > 150:
            problems.append("title is longer than 150 characters")
        if len(row.get("description", "")) > 500:
            problems.append("description is longer than 500 characters")
        if len(row.get("category", "")) > 80:
            problems.append("category is longer than 80 characters")
        if len(row.get("languages", "")) > 120:
            problems.append("languages is longer than 120 characters")
        kind = row.get("type", "").upper().replace(" ", "_")
        if kind not in ToolItemType.__members__:
            problems.append(f"type \"{row.get('type', '')}\" is not one of {', '.join(ToolItemType.__members__)}")
        try:
            url = check_url(row.get("url", ""))
        except LinkError as e:
            problems.append(f"url: {e}")
            url = None
        if problems:
            errors.append({"row": n, "title": title or None, "error": "; ".join(problems)})
        else:
            parsed.append((n, title, kind, url, row))
    if errors:
        raise _unprocessable({"message": f"Nothing was imported: {len(errors)} row(s) need fixing.", "errors": errors})
    if not parsed:
        raise _unprocessable({"message": "The file has no rows to import.", "errors": []})
    last = _live_items(db).filter(ToolItem.tool_module_id == m.id).order_by(ToolItem.display_order.desc()).first()
    order = (last.display_order + 1) if last else 0
    created = []
    for offset, (_n, title, kind, url, row) in enumerate(parsed):
        i = ToolItem(tool_module_id=m.id, title=title, description=_blank(row.get("description")), type=ToolItemType(kind),
                     url=url, host=host_label(url), category=_blank(row.get("category")), languages=_blank(row.get("languages")),
                     audience=[], display_order=order + offset, created_by=current_user.id)
        _touch(i, current_user)
        db.add(i)
        created.append(i)
    db.flush()
    _audit(db, current_user, AuditAction.TOOL_IMPORT, "tool_module", m.id,
           {"file": (file.filename or "")[:200], "created": [str(i.id) for i in created]})
    db.commit()
    dups = _duplicates(db)
    return {"created": len(created),
            "duplicates": [{"title": i.title, "url": i.url} for i in created if len(dups.get(same_link(i.url), [])) > 1]}


DEFAULT_OPENS_DAYS = 90


@router.get("/opens")
def most_opened(
    date_from: date | None = Query(None, description="first day counted (UTC), inclusive"),
    date_to: date | None = Query(None, description="last day counted (UTC), inclusive"),
    all_time: bool = Query(False, description="ignore the dates and count every open"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*READERS)),
):
    """How often each item was opened on phones whose users opted in to usage
    statistics, in a date range. Counts only: no names, no devices."""
    if not all_time and date_from is None and date_to is None:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=DEFAULT_OPENS_DAYS - 1)
    if not all_time and date_from and date_to and date_from > date_to:
        raise _unprocessable("The start date is after the end date.")
    item_col = AnalyticsEvent.payload["item_id"].astext
    query = db.query(item_col, func.count()).filter(AnalyticsEvent.event_type == AnalyticsEventType.TOOL_OPEN)
    if not all_time:
        if date_from:
            query = query.filter(AnalyticsEvent.occurred_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
        if date_to:
            query = query.filter(AnalyticsEvent.occurred_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time(), timezone.utc))
    counts = dict(query.group_by(item_col).all())
    ids = []
    for k in counts:
        try:
            ids.append(uuid.UUID(k))
        except (TypeError, ValueError):
            pass
    items = {str(i.id): i for i in db.query(ToolItem).filter(ToolItem.id.in_(ids))} if ids else {}
    rows = [{"item_id": k, "title": items[k].title if k in items else None, "deleted": k in items and items[k].deleted_at is not None,
             "opens": n} for k, n in counts.items() if k in items]
    return {"date_from": None if all_time or not date_from else date_from.isoformat(),
            "date_to": None if all_time or not date_to else date_to.isoformat(),
            "all_time": all_time, "items": sorted(rows, key=lambda r: (-r["opens"], r["title"] or ""))}


# ---------- phones ----------

def module_visible_to(m: ToolModule, user: User) -> bool:
    """Same rule as training modules (app/learning/access.py): learners see General
    Tools modules and those listing their learner role; staff see them all."""
    if m.deleted_at is not None or not m.is_active:
        return False
    if not is_learner(user) or m.audience == ModuleAudience.GENERAL:
        return True
    return user.learner_role is not None and user.learner_role.value in (m.learner_roles or [])


def item_visible_to(i: ToolItem, m: ToolModule, user: User) -> bool:
    if i.deleted_at is not None or not i.is_active or not module_visible_to(m, user):
        return False
    if not i.audience or not is_learner(user):
        return True
    return user.learner_role is not None and user.learner_role.value in i.audience


def _phone_item(i: ToolItem) -> dict:
    return {"id": str(i.id), "tool_module_id": str(i.tool_module_id), "title": i.title, "description": i.description,
            "type": i.type.value, "url": i.url, "host": i.host, "category": i.category, "languages": i.languages,
            "display_order": i.display_order}


@sync_router.get("/tools")
def sync_tools(
    since: datetime | None = Query(None, description="server_time of the phone's last download"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server_time = datetime.now(timezone.utc)
    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    full = since is None
    modules = {m.id: m for m in db.query(ToolModule)}
    visible_modules = sorted((m for m in modules.values() if module_visible_to(m, current_user)),
                             key=lambda m: (m.display_order, m.created_at or server_time))
    query = db.query(ToolItem)
    if full:
        query = query.filter(ToolItem.deleted_at.is_(None), ToolItem.is_active.is_(True),
                             ToolItem.tool_module_id.in_([m.id for m in visible_modules]))
    else:
        after = since - SYNC_OVERLAP
        changed_modules = [m.id for m in modules.values() if m.updated_at and m.updated_at > after]
        query = query.filter((ToolItem.updated_at > after) | ToolItem.tool_module_id.in_(changed_modules))
    items, removed = [], []
    for i in query.order_by(ToolItem.display_order, ToolItem.created_at).all():
        if item_visible_to(i, modules[i.tool_module_id], current_user):
            items.append(_phone_item(i))
        elif not full:
            removed.append(str(i.id))
    return {
        "server_time": server_time.isoformat(),
        "full": full,
        "modules": [{"id": str(m.id), "title": m.title, "description": m.description, "display_order": m.display_order}
                    for m in visible_modules],
        "items": items,
        "removed": removed,
    }
