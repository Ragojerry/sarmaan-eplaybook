"""
Real file-serving for media_assets, closing the loop opened by Phase 6's
content migration: content_sections reference real media_asset_id values,
but nothing could actually deliver the bytes until now. Matches the
/api/media group in master prompt §53.
"""
import uuid
from pathlib import Path

import hashlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.auth.dependencies import get_current_user, require_roles
from app.learning.access import is_learner, visible_module_ids
from app.models import User, MediaAsset
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, MediaAssetType, RoleName

router = APIRouter()
settings = get_settings()


def _media_root() -> Path:
    # STORAGE_LOCAL_PATH is relative to backend/ in .env.example
    # (../content/media) — resolved here so it works regardless of the
    # process's current working directory.
    root = Path(settings.storage_local_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    return root.resolve()


MAX_IMAGE_BYTES = 5 * 1024 * 1024
_IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
)


def _sniff_image(head: bytes):
    for sig, mime, ext in _IMAGE_SIGNATURES:
        if head.startswith(sig):
            return mime, ext
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


@router.get("")
def list_media(
    asset_type: MediaAssetType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER,
                                               RoleName.LOCALISATION_REVIEWER, RoleName.TECHNICAL_REVIEWER)),
):
    """Media library listing for authoring screens (e.g. choosing a quiz picture)."""
    q = db.query(MediaAsset)
    if asset_type:
        q = q.filter(MediaAsset.asset_type == asset_type)
    return [
        {"id": str(a.id), "asset_type": a.asset_type.value, "filename": a.filename, "mime_type": a.mime_type,
         "alt": (a.asset_metadata or {}).get("alt")}
        for a in q.order_by(MediaAsset.filename).limit(500).all()
    ]


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    alt: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CONTENT_ADMIN)),
):
    """Adds a JPEG/PNG/WebP (max 5 MB) to the media library. The file type is
    checked from the bytes, not the filename."""
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is larger than 5 MB.")
    kind = _sniff_image(data[:16]) if data else None
    if kind is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Please upload a JPEG, PNG or WebP picture.")
    mime, ext = kind
    digest = hashlib.sha256(data).hexdigest()
    rel = f"images/upload-{digest[:16]}{ext}"
    dest = _media_root() / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(data)
    safe_name = "".join(ch for ch in (file.filename or "picture") if ch.isalnum() or ch in "-_. ")[:120] or f"picture{ext}"
    asset = MediaAsset(
        asset_type=MediaAssetType.IMAGE, filename=safe_name, storage_path=rel, mime_type=mime,
        size_bytes=len(data), checksum=digest, asset_metadata={"alt": (alt or "").strip()[:300]} if alt else {},
    )
    db.add(asset)
    db.flush()
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.CONTENT_CREATE, entity_type="media_asset",
                    entity_id=asset.id, details={"filename": safe_name, "size": len(data)}))
    db.commit()
    return {"id": str(asset.id), "filename": asset.filename, "mime_type": mime}


def _learner_may_see(db: Session, asset_id: uuid.UUID, user: User) -> bool:
    """Pictures used in a module's sections or quiz follow that module's
    audience: a learner may fetch one if at least one module using it is
    visible to them. Pictures no module uses are not restricted."""
    if not is_learner(user):
        return True
    from app.models import ContentSection, QuizQuestion

    key = str(asset_id)
    used_by = {m for (m,) in db.query(ContentSection.module_id).filter(ContentSection.content["media_asset_id"].astext == key)}
    used_by |= {m for (m,) in db.query(QuizQuestion.module_id).filter(QuizQuestion.content["media_asset_id"].astext == key)}
    return not used_by or bool(used_by & visible_module_ids(db, user))


@router.get("/{media_id}")
def get_media_metadata(
    media_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    asset = db.get(MediaAsset, media_id)
    if asset is None or not _learner_may_see(db, asset.id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    return {
        "id": str(asset.id),
        "asset_type": asset.asset_type.value,
        "filename": asset.filename,
        "mime_type": asset.mime_type,
        "size_bytes": asset.size_bytes,
        "checksum": asset.checksum,
        "metadata": asset.asset_metadata,
    }


@router.get("/{media_id}/file")
def get_media_file(
    media_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    asset = db.get(MediaAsset, media_id)
    if asset is None or not _learner_may_see(db, asset.id, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    path = _media_root() / asset.storage_path
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media file missing on disk at {asset.storage_path} (asset row exists, file does not)",
        )
    return FileResponse(path, media_type=asset.mime_type, filename=asset.filename)
