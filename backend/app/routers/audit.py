"""
Phase 13: read access to the audit trail (master prompt §61). Entries are
written next to the action itself (auth, content governance, releases, videos);
this router only reads them. Append-only by design: there is no update or
delete endpoint.
"""
import csv
import io
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import AuditLog, User
from app.models.enums import AuditAction, RoleName
from app.schemas.audit import AuditEntry, AuditPage

router = APIRouter()

# SUPER_ADMIN always passes (see require_roles).
AUDIT_VIEWERS = (RoleName.CONTENT_ADMIN, RoleName.TECHNICAL_REVIEWER)
EXPORT_LIMIT = 10_000


def _query(
    db: Session,
    action: AuditAction | None,
    user_id: uuid.UUID | None,
    entity_type: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
):
    q = db.query(AuditLog, User.username, User.role).outerjoin(User, User.id == AuditLog.user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)
    return q


def _entry(row) -> AuditEntry:
    log, username, role = row
    return AuditEntry(
        id=log.id,
        created_at=log.created_at,
        action=log.action.value,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        details=log.details or {},
        ip_address=log.ip_address,
        user_id=log.user_id,
        username=username,
        user_role=role.value if role else None,
    )


@router.get("/actions", response_model=list[str])
def list_actions(current_user: User = Depends(require_roles(*AUDIT_VIEWERS))):
    return [a.value for a in AuditAction]


@router.get("", response_model=AuditPage)
def list_audit(
    action: AuditAction | None = None,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*AUDIT_VIEWERS)),
):
    q = _query(db, action, user_id, entity_type, date_from, date_to)
    total = q.count()
    rows = q.order_by(AuditLog.created_at.desc(), AuditLog.id).offset(offset).limit(limit).all()
    return AuditPage(total=total, limit=limit, offset=offset, items=[_entry(r) for r in rows])


def _csv_safe(value) -> str:
    """Spreadsheet apps execute cells beginning with = + - @ as formulas; audit
    details contain user-supplied text (e.g. attempted usernames)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@router.get("/export.csv")
def export_csv(
    action: AuditAction | None = None,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*AUDIT_VIEWERS)),
):
    q = _query(db, action, user_id, entity_type, date_from, date_to)
    rows = q.order_by(AuditLog.created_at.desc(), AuditLog.id).limit(EXPORT_LIMIT).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["time_utc", "action", "user", "role", "entity_type", "entity_id", "ip_address", "details"])
    for r in rows:
        e = _entry(r)
        w.writerow(
            [
                e.created_at.isoformat(),
                e.action,
                _csv_safe(e.username),
                e.user_role or "",
                _csv_safe(e.entity_type),
                e.entity_id or "",
                _csv_safe(e.ip_address),
                _csv_safe(json.dumps(e.details, sort_keys=True)),
            ]
        )
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-log.csv"'},
    )
