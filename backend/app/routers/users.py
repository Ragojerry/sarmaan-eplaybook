"""
User administration (SUPER_ADMIN only): list, create and edit accounts,
including the field team code a CDD sees on the phone's Home screen.
Passwords are never returned or editable here.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.security import hash_password
from app.database import get_db
from app.models import AdminBoundary, TrainingSession, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, RoleName, UserStatus
from app.schemas.auth import UserResponse
from app.routers.boundaries import LEVEL_COLUMN, ancestors
from app.training.restart import restart_training
from app.schemas.users import UserCreate, UserUpdate

router = APIRouter()
ADMINS = (RoleName.SUPER_ADMIN,)


def _check_session(db: Session, session_id) -> None:
    if db.get(TrainingSession, session_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown training session")


def _area_columns(db: Session, boundary_id) -> dict:
    node = db.get(AdminBoundary, boundary_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown area")
    found = ancestors(db, node)
    return {col: found.get(col) for col in LEVEL_COLUMN.values()}


@router.get("", response_model=list[UserResponse])
def list_users(
    team_code: str | None = Query(default=None),
    state_id: uuid.UUID | None = Query(default=None),
    lga_id: uuid.UUID | None = Query(default=None),
    session_id: uuid.UUID | None = Query(default=None),
    role: RoleName | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    q = db.query(User)
    if state_id:
        q = q.filter(User.state_id == state_id)
    if lga_id:
        q = q.filter(User.lga_id == lga_id)
    if session_id:
        q = q.filter(User.training_session_id == session_id)
    if team_code:
        q = q.filter(User.team_code == team_code)
    if role:
        q = q.filter(User.role == role)
    return q.order_by(User.created_at.desc()).limit(500).all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already in use")
    data = payload.model_dump(exclude={"password", "boundary_id"})
    if payload.boundary_id:
        data.update(_area_columns(db, payload.boundary_id))
    if payload.training_session_id:
        _check_session(db, payload.training_session_id)
    user = User(**data, password_hash=hash_password(payload.password), status=UserStatus.ACTIVE)
    db.add(user)
    db.flush()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.USER_CREATE,
            entity_type="user",
            entity_id=user.id,
            details={"username": user.username, "role": user.role.value, "team_code": user.team_code},
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-training", response_model=UserResponse)
def reset_training(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    """Admin starts this person's training over (e.g. they asked for a fresh start
    or the phone is lost). Same effect as the learner's own restart."""
    from datetime import datetime, timezone

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    restart_training(db, user, datetime.now(timezone.utc), current_user, via="admin")
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    changes = payload.model_dump(exclude_unset=True)
    if user.id == current_user.id and (
        changes.get("role", user.role) != user.role or changes.get("status", user.status) != user.status
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role or status")
    if "team_code" in changes and changes["team_code"] == "":
        changes["team_code"] = None
    boundary_id = changes.pop("boundary_id", None)
    clear_boundary = changes.pop("clear_boundary", False)
    clear_session = changes.pop("clear_session", False)
    if boundary_id:
        changes.update(_area_columns(db, boundary_id))
    elif clear_boundary:
        changes.update({col: None for col in LEVEL_COLUMN.values()})
    if changes.get("training_session_id"):
        _check_session(db, changes["training_session_id"])
    elif clear_session:
        changes["training_session_id"] = None
    else:
        changes.pop("training_session_id", None)
    before = {k: (getattr(user, k).value if hasattr(getattr(user, k), "value") else getattr(user, k)) for k in changes}
    changed_area = any(k in changes for k in LEVEL_COLUMN.values())
    for k, v in changes.items():
        setattr(user, k, v)
    role_changed = "role" in changes and changes["role"].value != before["role"]
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.ROLE_CHANGE if role_changed else AuditAction.USER_UPDATE,
            entity_type="user",
            entity_id=user.id,
            details={"fields": sorted(k for k in changes if k not in LEVEL_COLUMN.values()) + (["area"] if changed_area else []), "team_code": user.team_code},
        )
    )
    db.commit()
    db.refresh(user)
    return user
