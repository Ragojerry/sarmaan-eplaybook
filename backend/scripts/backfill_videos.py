"""One-off: fills in each video's size and SHA-256 and, with VIDEO_STORAGE=s3,
copies files still on the server's disk to S3. Safe to run any number of times:
a video that already has its size, hash and S3 file is left alone.

    docker compose ... exec -T -w /app backend python -m scripts.backfill_videos [--dry-run]

Needs s3:PutObject on the videos/ prefix for the copy (reading is enough for a
dry run). Nothing is deleted: local files stay where they are.
"""
import argparse
import hashlib
import sys
import uuid
from pathlib import Path

from app import video_storage
from app.routers.videos import NO_FILE, _video_path

CHUNK = 1024 * 1024


def local_path(video) -> Path:
    return _video_path(video)


def _hash(path: Path) -> tuple[int, str]:
    digest, size = hashlib.sha256(), 0
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def run(session_factory, only: list[uuid.UUID] | None = None, dry_run: bool = False) -> dict[str, int]:
    from app.models import Video

    store = video_storage.current()
    counts = {"checked": 0, "hashed": 0, "uploaded": 0, "missing": 0}
    db = session_factory()
    try:
        q = db.query(Video).filter(Video.filename != NO_FILE)
        if only:
            q = q.filter(Video.id.in_(only))
        for video in q.order_by(Video.created_at).all():
            counts["checked"] += 1
            done = video.file_size and video.checksum and (store is None or video.storage_key)
            if done:
                continue
            path = local_path(video)
            if not path.is_file():
                counts["missing"] += 1
                print(f"missing on disk: {video.id} {video.storage_path}")
                continue
            size, sha = _hash(path)
            if (video.file_size, video.checksum) != (size, sha):
                counts["hashed"] += 1
                if not dry_run:
                    video.file_size, video.checksum = size, sha
            if store is not None and not video.storage_key:
                key = store.key_for(video.id, sha, video.mime_type)
                found = store.stat(key)
                if found is None or found.sha256 != sha:
                    counts["uploaded"] += 1
                    if not dry_run:
                        store.put_file(path, key, video.mime_type, sha)
                if not dry_run:
                    video.storage_key = key
            if not dry_run:
                db.commit()
        return counts
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report what would change, change nothing")
    args = parser.parse_args()
    from app.database import SessionLocal

    counts = run(SessionLocal, dry_run=args.dry_run)
    print(("DRY RUN " if args.dry_run else "") + " ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if counts["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
