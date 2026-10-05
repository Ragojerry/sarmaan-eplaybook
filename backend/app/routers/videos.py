"""
Phase 9: real video upload + resumable download, closing the gap Phase 7
flagged (read-only listing only, no upload mechanism). Download supports
HTTP Range requests — required for master prompt §24's "resume" bullet:
a mobile client that got interrupted mid-download can request
`Range: bytes=<offset>-` and receive only the remaining bytes, verifying
the full file's checksum only once every byte has arrived.
"""
import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.auth.dependencies import get_current_user, require_roles
from app.models import User, Video
from app.models.enums import RoleName

router = APIRouter()
settings = get_settings()

CONTENT_EDITORS = (RoleName.CONTENT_ADMIN,)


def _video_root() -> Path:
    root = Path(settings.storage_local_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    video_dir = root.parent / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    return video_dir


def _serialize(video: Video) -> dict:
    return {
        "id": str(video.id),
        "title": video.title,
        "description": video.description,
        "module_id": str(video.module_id) if video.module_id else None,
        "duration_seconds": video.duration_seconds,
        "file_size": video.file_size,
        "checksum": video.checksum,
        "language": video.language,
        "offline_available": video.offline_available,
        "required_offline": video.required_offline,
        "status": video.status.value,
        # Deliberately NOT including storage_path/filename — internal
        # details, not something the client should construct a path from.
        "has_file": video.filename != "NOT_YET_UPLOADED",
    }


@router.get("")
def list_videos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    videos = db.query(Video).order_by(Video.title).all()
    return [_serialize(v) for v in videos]


@router.get("/{video_id}")
def get_video(video_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return _serialize(video)


@router.patch("/{video_id}")
def update_video(
    video_id: uuid.UUID,
    required_offline: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Master prompt §24: "Allow administrators to define required versus
    optional videos." Only field exposed here for now — status transitions
    should go through a proper governance-style endpoint once video review
    workflow is designed; that's future work, not this phase's job."""
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if required_offline is not None:
        video.required_offline = required_offline
    db.commit()
    db.refresh(video)
    return _serialize(video)


@router.post("/{video_id}/file")
async def upload_video_file(
    video_id: uuid.UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    checksum = hashlib.sha256(data).hexdigest()
    filename = f"{video_id}_{file.filename}"
    path = _video_root() / filename
    path.write_bytes(data)

    video.filename = filename
    video.storage_path = f"videos/{filename}"
    video.mime_type = file.content_type or "video/mp4"
    video.file_size = len(data)
    video.checksum = checksum
    db.commit()
    db.refresh(video)
    return _serialize(video)


@router.get("/{video_id}/file")
def download_video_file(
    video_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.filename == "NOT_YET_UPLOADED":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No video file has been uploaded yet")

    root = Path(settings.storage_local_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    path = root.parent / video.storage_path
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video row exists but file missing on disk at {video.storage_path}",
        )

    file_size = path.stat().st_size
    range_header = request.headers.get("range")

    if range_header is None:
        # Full-file response, still advertising range support so a client
        # that starts a fresh download knows resume is available if the
        # connection drops partway through.
        data = path.read_bytes()
        return Response(
            content=data,
            media_type=video.mime_type,
            headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)},
        )

    # Parse "bytes=<start>-<end>" (end is optional — means "to EOF").
    try:
        range_value = range_header.replace("bytes=", "")
        start_str, end_str = range_value.split("-")
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
    except (ValueError, IndexError):
        raise HTTPException(status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE, detail="Invalid Range header")

    if start >= file_size or end >= file_size or start > end:
        raise HTTPException(
            status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
            detail=f"Range not satisfiable for a {file_size}-byte file",
        )

    with open(path, "rb") as f:
        f.seek(start)
        chunk = f.read(end - start + 1)

    return Response(
        content=chunk,
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        media_type=video.mime_type,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(chunk)),
        },
    )
