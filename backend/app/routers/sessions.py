"""
Training sessions: a cohort with start and end dates. Several can run at once;
each user belongs to at most one, and reports can be limited to one session so
it is monitored on its own. Everyone except field staff can read sessions;
SUPER_ADMIN creates and changes them.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import TrainingSession, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName
from app.schemas.sessions import MemberBatch, SessionCreate, SessionResponse, SessionUpdate

router = APIRouter()
ADMINS = (RoleName.SUPER_ADMIN,)
READERS = tuple(r for r in RoleName if r != RoleName.CDD)


def _out(db: Session, row: TrainingSession) -> dict:
    count = db.query(func.count(User.id)).filter(User.training_session_id == row.id).scalar() or 0
    return {
        "id": row.id, "name": row.name, "description": row.description, "start_date": row.start_date,
        "end_date": row.end_date, "status": row.status, "user_count": count, "created_at": row.created_at,
    }


def _get(db: Session, session_id: uuid.UUID) -> TrainingSession:
    row = db.get(TrainingSession, session_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found")
    return row


def _name_taken(db: Session, name: str, except_id=None) -> bool:
    q = db.query(TrainingSession.id).filter(func.lower(TrainingSession.name) == name.lower())
    if except_id:
        q = q.filter(TrainingSession.id != except_id)
    return q.first() is not None


def _audit(db, user, row, details):
    db.add(AuditLog(user_id=user.id, action=AuditAction.SESSION_CHANGE, entity_type="training_session",
                    entity_id=row.id, details=details))


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    state: str | None = Query(default=None, pattern="^(UPCOMING|ONGOING|ENDED)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*READERS)),
):
    rows = db.query(TrainingSession).order_by(TrainingSession.start_date.desc(), TrainingSession.name).all()
    out = [_out(db, r) for r in rows]
    return [r for r in out if not state or r["status"] == state]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*READERS))):
    return _out(db, _get(db, session_id))


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ADMINS))):
    if _name_taken(db, payload.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A session with that name already exists.")
    row = TrainingSession(**payload.model_dump(), created_by=current_user.id)
    db.add(row)
    db.flush()
    _audit(db, current_user, row, {"created": row.name})
    db.commit()
    db.refresh(row)
    return _out(db, row)


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(session_id: uuid.UUID, payload: SessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ADMINS))):
    row = _get(db, session_id)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and _name_taken(db, changes["name"], row.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A session with that name already exists.")
    start = changes.get("start_date", row.start_date)
    end = changes.get("end_date", row.end_date)
    if end < start:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The end date cannot be before the start date.")
    for k, v in changes.items():
        setattr(row, k, v)
    _audit(db, current_user, row, {"fields": sorted(changes)})
    db.commit()
    db.refresh(row)
    return _out(db, row)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ADMINS))):
    row = _get(db, session_id)
    members = db.query(func.count(User.id)).filter(User.training_session_id == row.id).scalar() or 0
    if members:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"In use: {members} user(s) belong to this session. Move them first.")
    _audit(db, current_user, row, {"deleted": row.name})
    db.delete(row)
    db.commit()


@router.post("/{session_id}/assign")
def assign_users(session_id: uuid.UUID, payload: MemberBatch, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ADMINS))):
    """Puts the users in this session, moving them out of any other one."""
    row = _get(db, session_id)
    users = db.query(User).filter(User.id.in_(payload.user_ids)).all()
    moved = sum(1 for u in users if u.training_session_id not in (None, row.id))
    for u in users:
        u.training_session_id = row.id
    _audit(db, current_user, row, {"assigned": len(users), "moved_from_other_session": moved})
    db.commit()
    return {"assigned": len(users), "not_found": len(payload.user_ids) - len(users), "moved_from_other_session": moved}


@router.post("/{session_id}/unassign")
def unassign_users(session_id: uuid.UUID, payload: MemberBatch, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*ADMINS))):
    row = _get(db, session_id)
    users = db.query(User).filter(User.id.in_(payload.user_ids), User.training_session_id == row.id).all()
    for u in users:
        u.training_session_id = None
    _audit(db, current_user, row, {"unassigned": len(users)})
    db.commit()
    return {"unassigned": len(users)}
