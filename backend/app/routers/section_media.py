"""
Audio and video files on a content section, uploaded from the module page.

- AUDIO sections: the file becomes a MediaAsset (type AUDIO) under the media
  root, linked as content.media_asset_id. Release packages carry it, so phones
  download it for offline use like section pictures.
- VIDEO sections: the file goes into a Video record (the same table, storage
  and Range download as the Videos page), linked as content.video_id, which the
  phone's reader already opens. Like any video upload it starts as DRAFT (or
  goes back to DRAFT when replaced) until a content admin publishes it.

Removing detaches the file from the section. The stored file is kept, because
a published release (and the phones on it) may still point to it.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.config import get_settings
from app.content import media_upload
from app.database import get_db
from app.models import ContentSection, MediaAsset, User, Video
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, ContentType, MediaAssetType, RoleName, VideoStatus
from app.routers.media import _media_root
from app.routers.videos import NO_FILE, _video_path, _video_root

router = APIRouter()
settings = get_settings()

CONTENT_EDITORS = (RoleName.CONTENT_ADMIN,)
_MEDIA_KEYS = ("media_asset_id", "video_id", "filename", "mime_type", "size_bytes")


def _section(db: Session, section_id: uuid.UUID) -> ContentSection:
    section = db.get(ContentSection, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    if section.content_type not in (ContentType.AUDIO, ContentType.VIDEO):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Files can only be uploaded to AUDIO or VIDEO sections.",
        )
    return section


def _out(section: ContentSection, video: Video | None = None) -> dict:
    return {
        "id": str(section.id),
        "content_type": section.content_type.value,
        "content": section.content,
        "video_status": video.status.value if video else None,
    }


async def _store_audio(db: Session, section: ContentSection, file: UploadFile) -> dict:
    tmp = _media_root() / "audio" / f".upload-{uuid.uuid4().hex}.part"
    got = await media_upload.receive(file, tmp, settings.max_audio_upload_mb, "Audio")
    try:
        kind = media_upload.check_kind(media_upload.sniff_audio(got.head), settings.audio_upload_formats, "audio")
        asset = db.query(MediaAsset).filter_by(checksum=got.sha256, asset_type=MediaAssetType.AUDIO).first()
        name = media_upload.safe_filename(file.filename, f"audio{kind.ext}")
        if asset is None:
            rel = f"audio/upload-{got.sha256[:16]}{kind.ext}"
            dest = _media_root() / rel
            if dest.exists():
                got.tmp.unlink()
            else:
                got.tmp.replace(dest)
            asset = MediaAsset(asset_type=MediaAssetType.AUDIO, filename=name, storage_path=rel, mime_type=kind.mime,
                               size_bytes=got.size, checksum=got.sha256, asset_metadata={"source": "section_upload"})
            db.add(asset)
            db.flush()
        else:
            got.tmp.unlink()
    except BaseException:
        got.tmp.unlink(missing_ok=True)
        raise
    section.content = {**{k: v for k, v in (section.content or {}).items() if k not in _MEDIA_KEYS},
                       "media_asset_id": str(asset.id), "filename": name, "mime_type": kind.mime,
                       "size_bytes": got.size}
    return {"kind": "AUDIO", "media_asset_id": str(asset.id), "filename": name, "size_bytes": got.size,
            "sha256": got.sha256, "mime_type": kind.mime}


async def _store_video(db: Session, section: ContentSection, file: UploadFile) -> tuple[dict, Video, object]:
    stored = f"{uuid.uuid4().hex}"
    tmp = _video_root() / f".upload-{stored}.part"
    got = await media_upload.receive(file, tmp, settings.max_video_upload_mb, "Video")
    try:
        kind = media_upload.check_kind(media_upload.sniff_video(got.head), settings.video_upload_formats, "video")
        name = media_upload.safe_filename(file.filename, f"video{kind.ext}")
        filename = f"{stored}{kind.ext}"
        path = _video_root() / filename
        got.tmp.replace(path)
    except BaseException:
        got.tmp.unlink(missing_ok=True)
        raise

    try:
        video = db.get(Video, uuid.UUID(str((section.content or {}).get("video_id"))))
    except ValueError:  # no video yet (or a malformed id): start a new Video record
        video = None
    old_path = None
    if video is None:
        video = Video(title=(section.title or name)[:255], module_id=section.module_id, language="en",
                      status=VideoStatus.DRAFT, filename=NO_FILE, storage_path=NO_FILE, mime_type=kind.mime)
        db.add(video)
    elif video.filename != NO_FILE:
        old_path = _video_path(video)
    was_published = video.status == VideoStatus.PUBLISHED
    video.filename = filename
    video.storage_path = f"videos/{filename}"
    video.mime_type = kind.mime
    video.file_size = got.size
    video.checksum = got.sha256
    if was_published:  # same rule as the Videos page: new footage is re-approved before learners get it
        video.status = VideoStatus.DRAFT
        video.offline_available = False
    db.flush()
    content = {k: v for k, v in (section.content or {}).items() if k not in _MEDIA_KEYS}
    content.setdefault("title", section.title or name)
    section.content = {**content, "video_id": str(video.id), "filename": name, "mime_type": kind.mime,
                       "size_bytes": got.size}
    details = {"kind": "VIDEO", "video_id": str(video.id), "filename": name, "size_bytes": got.size,
               "sha256": got.sha256, "mime_type": kind.mime, "replaced_existing": old_path is not None,
               "returned_to_draft": was_published}
    return details, video, (old_path, path)


@router.post("/sections/{section_id}/media")
async def upload_section_media(
    section_id: uuid.UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Uploads (or replaces) the audio or video file of an AUDIO/VIDEO section."""
    section = _section(db, section_id)
    video = None
    paths = None
    if section.content_type == ContentType.AUDIO:
        details = await _store_audio(db, section, file)
    else:
        details, video, paths = await _store_video(db, section, file)
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.MEDIA_UPLOAD, entity_type="content_section",
                    entity_id=section.id, details=details))
    try:
        db.commit()
    except BaseException:
        if paths:
            paths[1].unlink(missing_ok=True)
        raise
    if paths and paths[0] is not None and paths[0] != paths[1]:
        paths[0].unlink(missing_ok=True)  # the replaced footage, only once the new file and row are committed
    db.refresh(section)
    return _out(section, video)


@router.delete("/sections/{section_id}/media")
def remove_section_media(
    section_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CONTENT_EDITORS)),
):
    """Detaches the file from the section. The stored file (and, for video, the Video record on the Videos page) is kept."""
    section = _section(db, section_id)
    content = section.content or {}
    removed = {k: content[k] for k in _MEDIA_KEYS if k in content}
    if not (removed.get("media_asset_id") or removed.get("video_id")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This section has no file to remove.")
    section.content = {k: v for k, v in content.items() if k not in _MEDIA_KEYS}
    db.add(AuditLog(user_id=current_user.id, action=AuditAction.MEDIA_REMOVE, entity_type="content_section",
                    entity_id=section.id, details={"kind": section.content_type.value, **removed}))
    db.commit()
    db.refresh(section)
    return _out(section)
