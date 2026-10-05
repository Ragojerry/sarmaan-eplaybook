"""
Phase 6: migrates the prototype's actual training content into the real
schema built in Phases 3-5 — 6 modules, 11 images (extracted to real files),
4 video metadata records, and structured (typed, non-HTML) content sections
for each module, per master prompt §16.

Idempotent: safe to re-run — checks for existing rows by their natural key
(module_code, checksum, title) before creating anything.

Usage:
    cd backend && python3 -m scripts.import_prototype_content
"""
import hashlib
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import Module, ModuleTranslation, ContentSection, MediaAsset, Video, Language
from app.models.content_release import ContentRelease
from app.models.audit_log import AuditLog
from app.models.enums import (
    ModuleStatus,
    ContentReviewStatus,
    ContentType,
    MediaAssetType,
    VideoStatus,
    ReleaseStatus,
    AuditAction,
)
from scripts.prototype_content_data import MODULES, VIDEOS

MEDIA_DIR = Path(__file__).resolve().parents[2] / "content" / "media" / "images"
RELEASE_CODE = "AZM-MDA-PROTOTYPE-MIGRATION-1.0"


def import_media_assets(db) -> dict[str, MediaAsset]:
    """Uploads every real image file extracted from the prototype. Returns a
    dict keyed by the prototype's photo key (e.g. "module1-hero") for lookup
    while building content sections."""
    assets: dict[str, MediaAsset] = {}
    image_files = sorted(MEDIA_DIR.glob("*.jpg"))
    if not image_files:
        raise RuntimeError(
            f"No images found in {MEDIA_DIR} — extract them from the prototype HTML first "
            "(see the image-extraction step in this phase's build log)."
        )

    for path in image_files:
        photo_key = path.stem
        data = path.read_bytes()
        checksum = hashlib.sha256(data).hexdigest()

        existing = db.query(MediaAsset).filter_by(checksum=checksum).one_or_none()
        if existing:
            assets[photo_key] = existing
            continue

        from PIL import Image

        with Image.open(path) as img:
            width, height = img.size

        asset = MediaAsset(
            asset_type=MediaAssetType.IMAGE,
            filename=path.name,
            storage_path=f"images/{path.name}",
            mime_type="image/jpeg",
            size_bytes=len(data),
            checksum=checksum,
            asset_metadata={"width": width, "height": height, "source": "prototype_migration", "photo_key": photo_key},
        )
        db.add(asset)
        db.flush()
        assets[photo_key] = asset

    return assets


def import_videos(db) -> dict[int, Video]:
    """Creates Video metadata rows. NO real video files exist anywhere in the
    source materials (the prototype itself never had them — see
    docs/prototype-analysis.md §5) — these rows are honestly incomplete:
    status=DRAFT, offline_available=False, and placeholder storage fields
    that must be replaced with real uploads before these can ever be
    published. Returns a dict keyed by the prototype's video array index
    (0-3) for lookup while building content sections."""
    videos: dict[int, Video] = {}
    for index, v in enumerate(VIDEOS):
        existing = db.query(Video).filter_by(title=v["title"]).one_or_none()
        if existing:
            videos[index] = existing
            continue

        module = db.query(Module).filter_by(module_code=v["module_code"]).one()
        video = Video(
            title=v["title"],
            description=v["description"],
            module_id=module.id,
            filename="NOT_YET_UPLOADED",
            storage_path="NOT_YET_UPLOADED",
            mime_type="video/mp4",
            language="en",
            offline_available=False,
            status=VideoStatus.DRAFT,
        )
        db.add(video)
        db.flush()
        videos[index] = video

    return videos


def import_modules(db, media_assets: dict[str, MediaAsset], videos: dict[int, Video], english: Language):
    for mod_data in MODULES:
        module = db.query(Module).filter_by(module_code=mod_data["module_code"]).one_or_none()
        is_new_module = module is None
        if is_new_module:
            module = Module(
                module_code=mod_data["module_code"],
                module_number=mod_data["module_number"],
                title=mod_data["title"],
                status=ModuleStatus.PUBLISHED,
                sort_order=mod_data["sort_order"],
            )
            db.add(module)
            db.flush()

        translation = (
            db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=english.id).one_or_none()
        )
        if translation is None:
            translation = ModuleTranslation(
                module_id=module.id,
                language_id=english.id,
                title=mod_data["title"],
                audio_text=mod_data["speak"],
                status=ContentReviewStatus.PUBLISHED,
                reviewed_at=datetime.now(timezone.utc),
            )
            db.add(translation)
            db.flush()  # populates translation.id before the audit log references it
            db.add(
                AuditLog(
                    action=AuditAction.CONTENT_CREATE,
                    entity_type="module_translation",
                    entity_id=translation.id,
                    details={
                        "module_code": module.module_code,
                        "note": "Migrated from the SARMAAN e-Playbook prototype's existing content "
                        "(sourced from the AZM Training Flipbook). Marked PUBLISHED as a baseline "
                        "import, not routed through the live governance workflow — this content "
                        "already existed and was not authored fresh through the admin portal.",
                    },
                )
            )
            db.flush()

        existing_sections = db.query(ContentSection).filter_by(module_id=module.id).count()
        if existing_sections > 0:
            continue  # sections already migrated for this module

        for i, section_data in enumerate(mod_data["sections"], start=1):
            content = dict(section_data["content"])
            content_type = ContentType[section_data["content_type"]]

            if content_type == ContentType.IMAGE:
                asset = media_assets[content.pop("photo_key")]
                content["media_asset_id"] = str(asset.id)
                content["storage_path"] = asset.storage_path
            elif content_type == ContentType.VIDEO:
                video = videos[content.pop("video_index")]
                content["video_id"] = str(video.id)

            section = ContentSection(
                module_id=module.id,
                section_number=i,
                title=content.get("heading"),
                content_type=content_type,
                content=content,
                sort_order=i,
            )
            db.add(section)

        db.flush()


def create_migration_release(db):
    existing = db.query(ContentRelease).filter_by(release_code=RELEASE_CODE).one_or_none()
    if existing:
        return existing
    release = ContentRelease(
        release_code=RELEASE_CODE,
        version="1.0.0",
        description=(
            "Baseline content migration: the 6 AZM training modules, 11 images, and 4 video "
            "metadata records migrated out of the sarmaan-eplaybook-prototype_1.html prototype "
            "into the real schema. Video files themselves are NOT included — no real .mp4 assets "
            "exist in the source materials; video rows are metadata-only placeholders pending "
            "real footage."
        ),
        mandatory=False,
        status=ReleaseStatus.PUBLISHED,
        published_at=datetime.now(timezone.utc),
    )
    db.add(release)
    db.flush()
    return release


def run():
    db = SessionLocal()
    try:
        english = db.query(Language).filter_by(code="en").one()

        media_assets = import_media_assets(db)
        print(f"Media assets: {len(media_assets)} images available ({', '.join(sorted(media_assets.keys()))})")

        # Modules must exist before videos (videos FK to module_id), and
        # videos must exist before module content sections (VIDEO-type
        # sections FK-reference them) — so modules are created in two passes:
        # first pass creates bare Module rows only, then videos, then the
        # full import_modules() pass adds translations + sections.
        for mod_data in MODULES:
            if not db.query(Module).filter_by(module_code=mod_data["module_code"]).one_or_none():
                db.add(
                    Module(
                        module_code=mod_data["module_code"],
                        module_number=mod_data["module_number"],
                        title=mod_data["title"],
                        status=ModuleStatus.PUBLISHED,
                        sort_order=mod_data["sort_order"],
                    )
                )
        db.flush()

        videos = import_videos(db)
        print(f"Videos: {len(videos)} metadata records created (no real video files — see docstring)")

        import_modules(db, media_assets, videos, english)
        module_count = db.query(Module).count()
        section_count = db.query(ContentSection).count()
        print(f"Modules: {module_count} total, {section_count} content sections total")

        release = create_migration_release(db)
        print(f"Release: '{release.release_code}' — status {release.status.value}")

        db.commit()
        print("\nPhase 6 content migration complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
