"""
Real file-serving for media_assets, closing the loop opened by Phase 6's
content migration: content_sections reference real media_asset_id values,
but nothing could actually deliver the bytes until now. Matches the
/api/media group in master prompt §53.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.auth.dependencies import get_current_user
from app.models import User, MediaAsset

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


@router.get("/{media_id}")
def get_media_metadata(
    media_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    asset = db.get(MediaAsset, media_id)
    if asset is None:
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
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    path = _media_root() / asset.storage_path
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media file missing on disk at {asset.storage_path} (asset row exists, file does not)",
        )
    return FileResponse(path, media_type=asset.mime_type, filename=asset.filename)
