"""Where training video files live.

Production (VIDEO_STORAGE=s3): S3 under `videos/`, served by CloudFront. The admin
browser uploads straight to S3 with a signed PUT that carries the file's SHA-256,
so S3 itself rejects a corrupted upload, and video bytes never pass through the
API. Object names hold the hash (videos/<video id>/<sha256[:16]>.mp4), so a
replaced video gets a new URL and every copy can be cached for a year.

Development and tests (VIDEO_STORAGE=local): current() is None and the older
disk storage in app/routers/videos.py is used.
"""
import base64
import uuid
from functools import lru_cache
from typing import NamedTuple

from app.config import get_settings

EXTENSIONS = {"video/mp4": ".mp4", "video/webm": ".webm"}
CACHE_CONTROL = "public, max-age=31536000, immutable"
UPLOAD_LINK_SECONDS = 3600


class Stat(NamedTuple):
    size: int
    sha256: str  # hex
    content_type: str | None
    head: bytes  # first 16 bytes, to check it really is a video


def object_key(prefix: str, video_id: uuid.UUID | str, sha256: str, mime: str) -> str:
    return f"{prefix}/{video_id}/{sha256[:16]}{EXTENSIONS.get(mime, '.mp4')}"


def sha256_b64(sha256_hex: str) -> str:
    return base64.b64encode(bytes.fromhex(sha256_hex)).decode()


def upload_headers(mime: str, sha256_hex: str) -> dict[str, str]:
    """Headers the browser must send with the signed PUT (they are part of the signature)."""
    return {"Content-Type": mime, "Cache-Control": CACHE_CONTROL, "x-amz-checksum-sha256": sha256_b64(sha256_hex)}


class S3VideoStorage:
    def __init__(self, bucket: str, prefix: str, cdn_base_url: str, region: str, credentials: dict | None = None):
        import boto3
        from botocore.config import Config

        self.bucket, self.prefix, self.cdn = bucket, prefix.strip("/"), cdn_base_url.rstrip("/")
        # "when_required": sign only the SHA-256 we pass, not an extra default CRC32 the browser would not send.
        config = Config(signature_version="s3v4", s3={"addressing_style": "virtual"},
                        request_checksum_calculation="when_required", response_checksum_validation="when_required")
        self._s3 = boto3.client("s3", region_name=region, config=config, **(credentials or {}))

    def key_for(self, video_id, sha256: str, mime: str) -> str:
        return object_key(self.prefix, video_id, sha256, mime)

    def url(self, key: str) -> str:
        return f"{self.cdn}/{key}"

    def upload_target(self, key: str, mime: str, size: int, sha256: str) -> dict:
        url = self._s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": mime, "CacheControl": CACHE_CONTROL,
                    "ChecksumSHA256": sha256_b64(sha256)},
            ExpiresIn=UPLOAD_LINK_SECONDS,
            HttpMethod="PUT",
        )
        return {"url": url, "method": "PUT", "headers": upload_headers(mime, sha256)}

    def stat(self, key: str) -> Stat | None:
        from botocore.exceptions import ClientError

        try:
            head = self._s3.head_object(Bucket=self.bucket, Key=key, ChecksumMode="ENABLED")
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return None  # not uploaded (yet)
            raise
        checksum = head.get("ChecksumSHA256") or ""
        sha = base64.b64decode(checksum).hex() if checksum and "-" not in checksum else ""
        with self._s3.get_object(Bucket=self.bucket, Key=key, Range="bytes=0-15")["Body"] as body:
            first = body.read()
        return Stat(size=head["ContentLength"], sha256=sha, content_type=head.get("ContentType"), head=first)

    def put_file(self, path, key: str, mime: str, sha256: str) -> None:
        """One PUT (videos are at most a few hundred MB) so S3 keeps a whole-file SHA-256."""
        with open(path, "rb") as f:
            self._s3.put_object(Bucket=self.bucket, Key=key, Body=f, ContentType=mime, CacheControl=CACHE_CONTROL,
                                ChecksumSHA256=sha256_b64(sha256))


@lru_cache
def _s3() -> S3VideoStorage:
    s = get_settings()
    if not (s.video_s3_bucket and s.video_cdn_base_url):
        raise RuntimeError("VIDEO_STORAGE=s3 needs VIDEO_S3_BUCKET and VIDEO_CDN_BASE_URL")
    return S3VideoStorage(s.video_s3_bucket, s.video_s3_prefix, s.video_cdn_base_url, s.aws_region)


def current() -> S3VideoStorage | None:
    """The S3 storage, or None when videos are kept on local disk (development)."""
    return _s3() if get_settings().video_storage == "s3" else None
