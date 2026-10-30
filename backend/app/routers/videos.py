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
from typing import Iterator

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.auth.dependencies import get_current_user, require_roles
from app.models import User, Video
from app.models.audit_log import AuditLog
from app.models import Module
from app.models.enums import AuditAction, RoleName, VideoStatus

router = APIRouter()
settings = get_settings()

CONTENT_EDITORS = (RoleName.CONTENT_ADMIN,)
# Roles that may see videos that are not published yet (drafts, archived).
DRAFT_VIEWERS = (
    RoleName.SUPER_ADMIN,
    RoleName.CONTENT_ADMIN,
    RoleName.PROGRAM_REVIEWER,
    RoleName.LOCALISATION_REVIEWER,
    RoleName.TECHNICAL_REVIEWER,
)
NO_FILE = "NOT_YET_UPLOADED"
ALLOWED_MIME = {"video/mp4", "video/webm"}
CHUNK = 1024 * 1024


class VideoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    module_id: uuid.UUID | None = None
    language: str = Field(default="en", max_length=10)
    duration_seconds: int | None = Field(default=None, ge=0)
    required_offline: bool = False


class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    module_id: uuid.UUID | None = None
    language: str | None = Field(default=None, max_length=10)
    duration_seconds: int | None = Field(default=None, ge=0)
    required_offline: bool | None = None
    status: VideoStatus | None = None


def _can_see_drafts(user: User) -> bool:
    return user.role in DRAFT_VIEWERS


def _sniff_ok(head: bytes) -> bool:
    """Checks the file really is an MP4 (`ftyp` box) or WebM/Matroska (EBML header), whatever its name or declared type."""
    return head[4:8] == b"ftyp" or head[:4] == b"\x1a\x45\xdf\xa3"


def _video_path(video: Video) -> Path:
    root = Path(settings.storage_local_path)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    return root.parent / video.storage_path


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
    q = db.query(Video)
    if not _can_see_drafts(current_user):
        q = q.filter(Video.status == VideoStatus.PUBLISHED)  # learners only ever see approved videos
    return [_serialize(v) for v in q.order_by(Video.title).all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_video(
    payload: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Creates the video's record (DRAFT, no file). The footage is attached with POST /videos/{id}/file."""
    if payload.module_id and db.get(Module, payload.module_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown module_id")
    video = Video(
        title=payload.title.strip(),
        description=payload.description,
        module_id=payload.module_id,
        filename=NO_FILE,
        storage_path=NO_FILE,
        mime_type="video/mp4",
        language=payload.language,
        duration_seconds=payload.duration_seconds,
        required_offline=payload.required_offline,
        offline_available=False,
        status=VideoStatus.DRAFT,
    )
    db.add(video)
    db.flush()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONTENT_CREATE,
            entity_type="video",
            entity_id=video.id,
            details={"title": video.title},
        )
    )
    db.commit()
    db.refresh(video)
    return _serialize(video)


@router.get("/{video_id}")
def get_video(video_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    video = db.get(Video, video_id)
    if video is None or (video.status != VideoStatus.PUBLISHED and not _can_see_drafts(current_user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return _serialize(video)


@router.patch("/{video_id}")
def update_video(
    video_id: uuid.UUID,
    required_offline: bool | None = None,
    payload: VideoUpdate | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Edits metadata and moves a video between DRAFT / PUBLISHED / ARCHIVED.
    `required_offline` is also accepted as a query parameter (Phase 9 callers).
    A video can only be PUBLISHED once real footage has been uploaded."""
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    changes = payload.model_dump(exclude_unset=True) if payload else {}
    if required_offline is not None:
        changes["required_offline"] = required_offline

    if "module_id" in changes and changes["module_id"] and db.get(Module, changes["module_id"]) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown module_id")
    has_file = video.filename != NO_FILE
    if changes.get("status") == VideoStatus.PUBLISHED and not has_file:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Upload the video file before publishing it.")

    for field, value in changes.items():
        setattr(video, field, value)
    video.offline_available = has_file and video.status == VideoStatus.PUBLISHED

    if changes:
        db.add(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.VIDEO_UPDATE,
                entity_type="video",
                entity_id=video.id,
                details={k: (v.value if hasattr(v, "value") else str(v)) for k, v in changes.items()},
            )
        )
    db.commit()
    db.refresh(video)
    return _serialize(video)


@router.post("/{video_id}/file")
async def upload_video_file(
    video_id: uuid.UUID,
    file: UploadFile,
    duration_seconds: int | None = Form(default=None, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Streams the upload to disk (never holding the whole file in memory),
    enforces a size cap, checks it really is MP4/WebM, and records its SHA-256.
    Replacing the footage of a PUBLISHED video sends it back to DRAFT so the
    new footage is re-approved before learners get it."""
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if (file.content_type or "") not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only MP4 (H.264) or WebM video is accepted."
        )

    max_bytes = settings.max_video_upload_mb * 1024 * 1024
    safe_name = "".join(ch for ch in (file.filename or "video.mp4") if ch.isalnum() or ch in "._-") or "video.mp4"
    filename = f"{video_id}_{uuid.uuid4().hex[:8]}_{safe_name}"
    path = _video_root() / filename
    tmp = path.with_suffix(path.suffix + ".part")

    digest = hashlib.sha256()
    size = 0
    head = b""
    try:
        with open(tmp, "wb") as out:
            while True:
                chunk = await file.read(CHUNK)
                if not chunk:
                    break
                if size == 0:
                    head = chunk[:16]
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Video is larger than the {settings.max_video_upload_mb} MB limit.",
                    )
                digest.update(chunk)
                out.write(chunk)
        if size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        if not _sniff_ok(head):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="The file is not a valid MP4 or WebM video."
            )
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    old = None if video.filename == NO_FILE else _video_path(video)
    was_published = video.status == VideoStatus.PUBLISHED
    checksum = digest.hexdigest()

    video.filename = filename
    video.storage_path = f"videos/{filename}"
    video.mime_type = file.content_type
    video.file_size = size
    video.checksum = checksum
    if duration_seconds is not None:
        video.duration_seconds = duration_seconds
    if was_published:
        video.status = VideoStatus.DRAFT
        video.offline_available = False
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.VIDEO_UPLOAD,
            entity_type="video",
            entity_id=video.id,
            details={
                "filename": file.filename,
                "size_bytes": size,
                "sha256": checksum,
                "replaced_existing": old is not None,
                "returned_to_draft": was_published,
            },
        )
    )
    db.commit()
    db.refresh(video)
    if old is not None and old != path:
        old.unlink(missing_ok=True)  # only after the new file and row are safely committed
    return _serialize(video)


@router.get("/{video_id}/file")
def download_video_file(
    video_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    video = db.get(Video, video_id)
    if video is None or (video.status != VideoStatus.PUBLISHED and not _can_see_drafts(current_user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if video.filename == NO_FILE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No video file has been uploaded yet")

    path = _video_path(video)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video row exists but file missing on disk at {video.storage_path}",
        )

    file_size = path.stat().st_size
    range_header = request.headers.get("range")

    if range_header is None:
        # Whole file, streamed from disk; still advertises range support so an
        # interrupted download can resume.
        return FileResponse(path, media_type=video.mime_type, headers={"Accept-Ranges": "bytes"})

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

    length = end - start + 1

    def _stream() -> Iterator[bytes]:
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                data = f.read(min(CHUNK, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data

    return StreamingResponse(
        _stream(),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        media_type=video.mime_type,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        },
    )
