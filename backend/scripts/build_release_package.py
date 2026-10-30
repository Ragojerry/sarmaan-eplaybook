"""
Phase 12: (re)build the downloadable package for a PUBLISHED release that has
none yet — e.g. the migration release created by the Phase 6 import script
before packaging existed. Normal releases get their package automatically when
published via the API (POST /releases/{id}/publish).

Usage:  cd backend && python3 -m scripts.build_release_package [RELEASE_CODE]
        (default: every PUBLISHED release without a checksum)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.indexer import rebuild_chunks
from app.database import SessionLocal
from app.models import ContentRelease
from app.models.enums import ReleaseStatus
from app.releases.packager import build_package, write_package


def run(only_code: str | None = None) -> int:
    db = SessionLocal()
    built = 0
    try:
        q = db.query(ContentRelease).filter(ContentRelease.status == ReleaseStatus.PUBLISHED)
        q = q.filter_by(release_code=only_code) if only_code else q.filter(ContentRelease.checksum.is_(None))
        releases = q.all()
        if releases:
            rebuild_chunks(db)
        for rel in releases:
            pkg = build_package(db, rel)
            _, size, checksum = write_package(pkg, rel.release_code)
            rel.package_size, rel.checksum = size, checksum
            c = pkg["counts"]
            print(f"{rel.release_code}: {c['modules']} modules, {c['sections']} sections, {c['media']} media, "
                  f"{c['chunks']} chunks -> {size} bytes sha256 {checksum[:12]}…")
            built += 1
        db.commit()
        if not built:
            print("Nothing to build.")
        return built
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
