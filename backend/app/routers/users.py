"""
User administration (SUPER_ADMIN only): list, create and edit accounts,
including the field team code a CDD sees on the phone's Home screen.
Passwords are never returned or editable here, except the ones a bulk import
generates, which are returned once in the import response.
"""
import csv
import io
import secrets
import string
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.auth.security import hash_password
from app.database import get_db
from app.models import AdminBoundary, TrainingSession, User
from app.models.audit_log import AuditLog
from app.models.enums import BOUNDARY_ORDER, AuditAction, RoleName, UserStatus
from app.schemas.auth import UserResponse
from app.routers.boundaries import LEVEL_COLUMN, _find, ancestors
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


IMPORT_MAX_ROWS = 100  # 100 hashes take ~11 s on the t4g.small; CloudFront gives up at 30 s
IMPORT_MAX_ERRORS = 30


def _generated_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(14))


def _area_by_names(db: Session, row: dict, cache: dict) -> tuple[uuid.UUID | None, str | None]:
    """Walks country > state > lga > ward > facility by name. Returns the deepest
    boundary id, or an error message. Unlike the boundary import, nothing is created."""
    parent_id, gap, path = None, False, []
    for level in BOUNDARY_ORDER:
        name = row.get(level.value.lower(), "")
        if not name:
            gap = True
            continue
        if gap:
            return None, f"'{name}' has an empty area column above it"
        path.append(name)
        key = (level, parent_id, name.lower())
        if key not in cache:
            found = _find(db, level, parent_id, name)
            cache[key] = found.id if found else None
        if cache[key] is None:
            return None, f"area '{' > '.join(path)}' does not exist (add it under Administrative areas first)"
        parent_id = cache[key]
    return parent_id, None


@router.post("/import")
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    """CSV with the IMPORT_COLUMNS header. All or nothing: every row is checked
    first and any problem rejects the whole file, listing the bad rows. A blank
    password is generated; generated passwords are returned once, here only."""
    raw = await file.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is larger than 2 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="The file must be UTF-8 (in Excel choose 'CSV UTF-8').")
    reader = csv.DictReader(io.StringIO(text))
    header = {h.strip().lower() for h in (reader.fieldnames or []) if h}
    missing = [c for c in ("first_name", "last_name", "username", "email") if c not in header]
    if missing:
        raise HTTPException(status_code=422, detail=f"The header row is missing: {', '.join(missing)}. Download the template.")

    sessions = {s.name.lower(): s.id for s in db.query(TrainingSession).all()}
    area_cache: dict = {}
    seen_usernames: set[str] = set()
    seen_emails: set[str] = set()
    errors: list[str] = []
    pending: list[tuple[dict, str, bool]] = []  # (user columns, password, generated?)

    for n, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items() if k is not None and isinstance(v, (str, type(None)))}
        if not any(row.values()):
            continue  # blank line
        if len(pending) + len(errors) >= IMPORT_MAX_ROWS:
            raise HTTPException(status_code=422, detail=f"At most {IMPORT_MAX_ROWS} users per file. Split the list into several files.")
        problems = []
        password, generated = row.get("password", ""), False
        if not password:
            password, generated = _generated_password(), True
        try:
            payload = UserCreate(
                username=row.get("username", ""),
                email=row.get("email", ""),
                password=password,
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
                phone=row.get("phone") or None,
                role=(row.get("role") or "CDD").upper(),
                team_code=row.get("team_code") or None,
            )
        except ValidationError as e:
            for err in e.errors():
                field = str(err["loc"][0]) if err["loc"] else "row"
                problems.append(f"{field}: {err['msg']}")
            payload = None
        if payload is not None:
            if payload.role == RoleName.SUPER_ADMIN:
                problems.append("SUPER_ADMIN accounts cannot be bulk-created")
            uname, mail = payload.username.lower(), payload.email.lower()
            if uname in seen_usernames:
                problems.append(f"username '{payload.username}' appears twice in the file")
            if mail in seen_emails:
                problems.append(f"email '{payload.email}' appears twice in the file")
            seen_usernames.add(uname)
            seen_emails.add(mail)
        data = payload.model_dump(exclude={"password", "boundary_id", "training_session_id"}) if payload else {}
        session_name = row.get("session", "")
        if session_name:
            if session_name.lower() in sessions:
                data["training_session_id"] = sessions[session_name.lower()]
            else:
                problems.append(f"session '{session_name}' does not exist (create it under Sessions first)")
        boundary_id, area_error = _area_by_names(db, row, area_cache)
        if area_error:
            problems.append(area_error)
        elif boundary_id:
            data.update(_area_columns(db, boundary_id))
        if problems:
            errors.append(f"Row {n}: " + "; ".join(problems))
            if len(errors) >= IMPORT_MAX_ERRORS:
                break
            continue
        pending.append((data, password, generated))

    if not errors and pending:
        taken = (
            db.query(User.username, User.email)
            .filter(func.lower(User.username).in_(seen_usernames) | func.lower(User.email).in_(seen_emails))
            .all()
        )
        for u, e in taken:
            errors.append(f"'{u}' / '{e}' is already an account (username or email in use)")
    if errors:
        more = " (stopped after the first errors; fix these and upload again)" if len(errors) >= IMPORT_MAX_ERRORS else ""
        raise HTTPException(status_code=422, detail="Nothing was imported. " + " | ".join(errors) + more)
    if not pending:
        raise HTTPException(status_code=422, detail="The file has no user rows under the header.")

    # argon2 releases the GIL, so hashing in threads uses every CPU.
    with ThreadPoolExecutor(max_workers=4) as pool:
        hashes = list(pool.map(hash_password, [p for _, p, _ in pending]))
    created = []
    for (data, password, generated), password_hash in zip(pending, hashes):
        user = User(**data, password_hash=password_hash, status=UserStatus.ACTIVE)
        db.add(user)
        db.flush()
        db.add(AuditLog(
            user_id=current_user.id,
            action=AuditAction.USER_CREATE,
            entity_type="user",
            entity_id=user.id,
            details={"username": user.username, "role": user.role.value, "team_code": user.team_code, "import": True},
        ))
        created.append((user.username, password if generated else None))
    db.commit()
    return {
        "created": len(created),
        "generated_passwords": [{"username": u, "password": p} for u, p in created if p],
    }


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
