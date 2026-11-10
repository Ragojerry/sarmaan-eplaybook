"""
Audio/video upload helpers for content sections (app/routers/section_media.py).

The file type is decided from the file's first bytes, never from its name or
the browser's declared Content-Type, and only formats listed in settings
(AUDIO_UPLOAD_FORMATS / VIDEO_UPLOAD_FORMATS) are accepted. Uploads are
streamed to disk in chunks with a size cap, so a large video is never held in
memory.
"""
import hashlib
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

CHUNK = 1024 * 1024

# MPEG-4 brands that mean "audio file" (an .m4a). Generic brands such as isom/mp42
# are also used by .mp4 video, so they are treated as video, never as audio.
_M4A_BRANDS = {b"M4A ", b"M4B ", b"M4P "}


@dataclass(frozen=True)
class Kind:
    fmt: str  # the name used in settings, e.g. "mp3"
    mime: str
    ext: str


def sniff_audio(head: bytes) -> Kind | None:
    if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return Kind("mp3", "audio/mpeg", ".mp3")
    if head[4:8] == b"ftyp" and head[8:12] in _M4A_BRANDS:
        return Kind("m4a", "audio/mp4", ".m4a")
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return Kind("wav", "audio/wav", ".wav")
    return None


def sniff_video(head: bytes) -> Kind | None:
    if head[4:8] == b"ftyp" and head[8:12] not in _M4A_BRANDS:
        return Kind("mp4", "video/mp4", ".mp4")
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return Kind("webm", "video/webm", ".webm")
    return None


def safe_filename(name: str | None, default: str) -> str:
    cleaned = "".join(ch for ch in (name or "") if ch.isalnum() or ch in "-_. ").strip()[:120]
    return cleaned or default


@dataclass
class Received:
    tmp: Path
    size: int
    sha256: str
    head: bytes


async def receive(file: UploadFile, tmp: Path, max_mb: int, label: str) -> Received:
    """Streams the upload into `tmp`, enforcing the size cap. Deletes `tmp` on any failure."""
    max_bytes = max_mb * 1024 * 1024
    digest = hashlib.sha256()
    size = 0
    head = b""
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(tmp, "wb") as out:
            while chunk := await file.read(CHUNK):
                if size == 0:
                    head = chunk[:16]
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"{label} is larger than the {max_mb} MB limit.",
                    )
                digest.update(chunk)
                out.write(chunk)
        if size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return Received(tmp, size, digest.hexdigest(), head)


def check_kind(kind: Kind | None, allowed: list[str], label: str) -> Kind:
    allowed = [a.lower() for a in allowed]
    if kind is None or kind.fmt not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Please upload {label} in one of these formats: {', '.join(allowed)}.",
        )
    return kind
