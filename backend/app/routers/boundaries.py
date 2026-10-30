"""
Administrative boundaries: Country > State > LGA > Ward > Facility.
Anyone on the programme team can read them (the user form and report filters
need the lists); only SUPER_ADMIN changes them.
"""
import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import AdminBoundary, User
from app.models.audit_log import AuditLog
from app.models.enums import BOUNDARY_ORDER, AuditAction, BoundaryLevel, RoleName
from app.schemas.boundaries import BoundaryCreate, BoundaryResponse, BoundaryUpdate

router = APIRouter()
ADMINS = (RoleName.SUPER_ADMIN,)
READERS = tuple(r for r in RoleName if r != RoleName.CDD)
LEVEL_COLUMN = {
    BoundaryLevel.COUNTRY: "country_id",
    BoundaryLevel.STATE: "state_id",
    BoundaryLevel.LGA: "lga_id",
    BoundaryLevel.WARD: "ward_id",
    BoundaryLevel.FACILITY: "facility_id",
}


def parent_level(level: BoundaryLevel) -> BoundaryLevel | None:
    i = BOUNDARY_ORDER.index(level)
    return BOUNDARY_ORDER[i - 1] if i else None


def _conflict(msg: str):
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)


def _unprocessable(msg: str):
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


def _find(db: Session, level, parent_id, name):
    q = db.query(AdminBoundary).filter(AdminBoundary.level == level, AdminBoundary.name.ilike(name))
    q = q.filter(AdminBoundary.parent_id.is_(None)) if parent_id is None else q.filter(AdminBoundary.parent_id == parent_id)
    return q.first()


def ancestors(db: Session, node: AdminBoundary) -> dict[str, uuid.UUID]:
    """{'country_id': .., 'state_id': .., ...} for a node and everything above it."""
    out, cur = {}, node
    while cur is not None:
        out[LEVEL_COLUMN[cur.level]] = cur.id
        cur = db.get(AdminBoundary, cur.parent_id) if cur.parent_id else None
    return out


@router.get("", response_model=list[BoundaryResponse])
def list_boundaries(
    level: BoundaryLevel | None = Query(default=None),
    parent_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*READERS)),
):
    query = db.query(AdminBoundary)
    if level:
        query = query.filter(AdminBoundary.level == level)
    if parent_id:
        query = query.filter(AdminBoundary.parent_id == parent_id)
    if q:
        query = query.filter(AdminBoundary.name.ilike(f"%{q}%"))
    return query.order_by(AdminBoundary.name).limit(limit).all()


@router.post("", response_model=BoundaryResponse, status_code=status.HTTP_201_CREATED)
def create_boundary(
    payload: BoundaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    expected = parent_level(payload.level)
    if expected is None:
        if payload.parent_id is not None:
            raise _unprocessable("A country has no parent.")
    else:
        parent = db.get(AdminBoundary, payload.parent_id) if payload.parent_id else None
        if parent is None or parent.level != expected:
            raise _unprocessable(f"A {payload.level.value.lower()} must sit under a {expected.value.lower()}.")
    if _find(db, payload.level, payload.parent_id, payload.name):
        raise _conflict("That name already exists here.")
    row = AdminBoundary(**payload.model_dump())
    db.add(row)
    db.flush()
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.BOUNDARY_CHANGE, entity_type="boundary",
                    entity_id=row.id, details={"created": row.name, "level": row.level.value}))
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{boundary_id}", response_model=BoundaryResponse)
def update_boundary(
    boundary_id: uuid.UUID,
    payload: BoundaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    row = db.get(AdminBoundary, boundary_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boundary not found")
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"].lower() != row.name.lower() and _find(db, row.level, row.parent_id, changes["name"]):
        raise _conflict("That name already exists here.")
    for k, v in changes.items():
        setattr(row, k, v)
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.BOUNDARY_CHANGE, entity_type="boundary",
                    entity_id=row.id, details={"fields": sorted(changes)}))
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{boundary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_boundary(
    boundary_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    row = db.get(AdminBoundary, boundary_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boundary not found")
    children = db.query(AdminBoundary).filter_by(parent_id=row.id).count()
    users = db.query(User).filter(getattr(User, LEVEL_COLUMN[row.level]) == row.id).count()
    if children or users:
        raise _conflict(f"In use: {children} child area(s) and {users} user(s) belong to it.")
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.BOUNDARY_CHANGE, entity_type="boundary",
                    entity_id=row.id, details={"deleted": row.name, "level": row.level.value}))
    db.delete(row)
    db.commit()


@router.post("/import")
async def import_boundaries(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMINS)),
):
    """CSV with columns country,state,lga,ward,facility (a row may stop at any
    depth). Existing names are reused, so the file can be re-imported safely.
    All or nothing: one bad row rejects the whole file."""
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is larger than 5 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise _unprocessable("The file must be UTF-8 (in Excel choose 'CSV UTF-8').")
    reader = csv.DictReader(io.StringIO(text))
    names = [h.strip().lower() for h in (reader.fieldnames or [])]
    if "country" not in names:
        raise _unprocessable("The first row must be a header containing at least: country, state, lga, ward, facility.")
    created = 0
    cache: dict[tuple, uuid.UUID] = {}
    try:
        for n, raw_row in enumerate(reader, start=2):
            row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items() if k is not None and isinstance(v, (str, type(None)))}
            parent_id, gap = None, False
            for level in BOUNDARY_ORDER:
                name = row.get(level.value.lower(), "")
                if not name:
                    gap = True
                    continue
                if gap:
                    raise _unprocessable(f"Row {n}: '{name}' has an empty level above it.")
                if len(name) > 200:
                    raise _unprocessable(f"Row {n}: a name is longer than 200 characters.")
                key = (level, parent_id, name.lower())
                if key not in cache:
                    existing = _find(db, level, parent_id, name)
                    if existing is None:
                        existing = AdminBoundary(level=level, name=name, parent_id=parent_id)
                        db.add(existing)
                        db.flush()
                        created += 1
                    cache[key] = existing.id
                parent_id = cache[key]
        db.add(AuditLog(user_id=current_user.id, action=AuditAction.BOUNDARY_CHANGE, entity_type="boundary",
                        entity_id=current_user.id, details={"import": True, "created": created}))
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    return {"created": created}
