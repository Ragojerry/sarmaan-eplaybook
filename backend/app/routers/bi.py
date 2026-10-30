"""
Power BI / reporting-tool access.

Read-only endpoints authenticated with an API key sent in the `X-API-Key`
header (create keys in the admin portal, Reports -> Power BI access). The data
is the same as the admin reports. Every list endpoint returns a plain JSON array
(or CSV with ?format=csv), which Power BI's Web connector turns into a table.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import ApiKey, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName
from app.reports import activity
from app.reports.activity import Filters
from app.reports.params import report_filters
from app.routers.reports import LEVEL, csv_response

router = APIRouter()
KEY_PREFIX = "sarmaan_bi_"


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def require_api_key(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)) -> ApiKey:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")
    if not x_api_key or not x_api_key.startswith(KEY_PREFIX):
        raise unauthorized
    key = db.query(ApiKey).filter_by(key_hash=_hash(x_api_key)).one_or_none()
    if key is None or key.revoked_at is not None:
        raise unauthorized
    now = datetime.now(timezone.utc)
    if key.last_used_at is None or now - key.last_used_at > timedelta(minutes=1):
        key.last_used_at = now
        db.commit()
    return key


# ---------- key management (SUPER_ADMIN, normal login) ----------
class KeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.post("/keys", status_code=status.HTTP_201_CREATED)
def create_key(payload: KeyCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.SUPER_ADMIN))):
    key = KEY_PREFIX + secrets.token_urlsafe(32)
    row = ApiKey(name=payload.name.strip(), key_prefix=key[:14], key_hash=_hash(key), created_by=user.id)
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=user.id, action=AuditAction.API_KEY_CREATE, entity_type="api_key", entity_id=row.id,
                    details={"name": row.name}))
    db.commit()
    # The only time the key is ever shown.
    return {"id": str(row.id), "name": row.name, "key": key, "key_prefix": row.key_prefix}


@router.get("/keys")
def list_keys(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.SUPER_ADMIN))):
    rows = db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()
    return [
        {
            "id": str(k.id), "name": k.name, "key_prefix": k.key_prefix,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "revoked": k.revoked_at is not None,
        }
        for k in rows
    ]


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(key_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.SUPER_ADMIN))):
    row = db.get(ApiKey, key_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.add(AuditLog(user_id=user.id, action=AuditAction.API_KEY_REVOKE, entity_type="api_key", entity_id=row.id,
                        details={"name": row.name}))
        db.commit()


# ---------- data (API key) ----------
def _out(rows: list[dict], fmt: str, name: str):
    return csv_response(rows, name) if fmt == "csv" else rows


FORMAT = Query(default="json", pattern="^(json|csv)$")


@router.get("/users")
def bi_users(format: str = FORMAT, f: Filters = Depends(report_filters), db: Session = Depends(get_db), key: ApiKey = Depends(require_api_key)):
    """One row per user: area, location, module completion, quiz and activity categories."""
    return _out(activity.user_rows(db, f), format, "user_activity")


@router.get("/boundaries")
def bi_boundaries(level: str = LEVEL, format: str = FORMAT, f: Filters = Depends(report_filters), db: Session = Depends(get_db), key: ApiKey = Depends(require_api_key)):
    """Activity and completion rolled up by country, state, LGA, ward or facility."""
    return _out(activity.boundary_rollup(activity.user_rows(db, f), level), format, f"activity_by_{level}")


@router.get("/sessions")
def bi_sessions(format: str = FORMAT, f: Filters = Depends(report_filters), db: Session = Depends(get_db), key: ApiKey = Depends(require_api_key)):
    """One row per training session: dates, status, enrolment, completion, quizzes, activity categories."""
    return _out(activity.session_rollup(db, activity.user_rows(db, f), not f.narrowed), format, "training_sessions")


@router.get("/modules")
def bi_modules(
    level: str | None = Query(default=None, pattern="^(country|state|lga|ward|facility|session)$"),
    format: str = FORMAT, f: Filters = Depends(report_filters), db: Session = Depends(get_db), key: ApiKey = Depends(require_api_key),
):
    """Completion and quiz results per module; add level=state (etc.) or level=session for module x area / session."""
    return _out(activity.module_rows(db, f, level), format, "module_completion")
