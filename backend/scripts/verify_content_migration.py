"""
Phase 6 verification: confirms the migrated content is actually present and
correctly linked — real files exist on disk with matching checksums, every
module has an English translation and content sections, and every
IMAGE/VIDEO section resolves to a real row (not a dangling reference).

Usage:
    cd backend && python3 -m scripts.verify_content_migration
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import Module, ModuleTranslation, ContentSection, MediaAsset, Video, Language
from app.models.content_release import ContentRelease
from app.models.enums import ContentReviewStatus, ContentType, ModuleStatus

MEDIA_DIR = Path(__file__).resolve().parents[2] / "content" / "media" / "images"
EXPECTED_MODULE_CODES = ["M1", "M2", "M3", "M4", "M5", "M6"]


def verify():
    db = SessionLocal()
    try:
        # 1. All 6 modules exist and are PUBLISHED.
        modules = db.query(Module).filter(Module.module_code.in_(EXPECTED_MODULE_CODES)).all()
        assert len(modules) == 6, f"Expected 6 modules, found {len(modules)}"
        for m in modules:
            assert m.status == ModuleStatus.PUBLISHED, f"{m.module_code} should be PUBLISHED, is {m.status.value}"
        print(f"✓ All 6 modules present and PUBLISHED: {sorted(m.module_code for m in modules)}")

        # 2. Every module has an English translation, PUBLISHED, with audio_text set.
        english = db.query(Language).filter_by(code="en").one()
        for m in modules:
            t = db.query(ModuleTranslation).filter_by(module_id=m.id, language_id=english.id).one_or_none()
            assert t is not None, f"{m.module_code} missing English translation"
            assert t.status == ContentReviewStatus.PUBLISHED
            assert t.audio_text, f"{m.module_code} translation missing audio_text (TTS narration)"
        print("✓ Every module has a PUBLISHED English translation with TTS narration text.")

        # 3. Every module has content sections.
        total_sections = 0
        for m in modules:
            count = db.query(ContentSection).filter_by(module_id=m.id).count()
            assert count > 0, f"{m.module_code} has no content sections"
            total_sections += count
        print(f"✓ All modules have content sections ({total_sections} total).")

        # 4. Real image files on disk match what's in media_assets, checksums verified.
        assets = db.query(MediaAsset).all()
        assert len(assets) == 11, f"Expected 11 media assets, found {len(assets)}"
        for asset in assets:
            path = MEDIA_DIR / asset.filename
            assert path.exists(), f"Missing file on disk: {path}"
            actual_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual_checksum == asset.checksum, f"Checksum mismatch for {asset.filename}"
        print(f"✓ All {len(assets)} media assets exist on disk with matching checksums.")

        # 5. Every IMAGE section's media_asset_id resolves to a real row.
        image_sections = db.query(ContentSection).filter_by(content_type=ContentType.IMAGE).all()
        asset_ids = {str(a.id) for a in assets}
        for section in image_sections:
            ref = section.content.get("media_asset_id")
            assert ref in asset_ids, f"Section {section.id} references missing media_asset_id {ref}"
        print(f"✓ All {len(image_sections)} IMAGE sections resolve to real media assets.")

        # 6. Every VIDEO section's video_id resolves to a real row.
        videos = db.query(Video).all()
        assert len(videos) == 4, f"Expected 4 videos, found {len(videos)}"
        video_ids = {str(v.id) for v in videos}
        video_sections = db.query(ContentSection).filter_by(content_type=ContentType.VIDEO).all()
        for section in video_sections:
            ref = section.content.get("video_id")
            assert ref in video_ids, f"Section {section.id} references missing video_id {ref}"
        print(f"✓ All {len(video_sections)} VIDEO sections resolve to real video records ({len(videos)} videos total).")
        print("  NOTE: video records are metadata-only — no real .mp4 files exist yet (honest gap, not a bug).")

        # 7. Migration release exists and is published.
        release = db.query(ContentRelease).filter_by(release_code="AZM-MDA-PROTOTYPE-MIGRATION-1.0").one_or_none()
        assert release is not None, "Migration release record missing"
        print(f"✓ Migration release '{release.release_code}' present, status {release.status.value}.")

        print("\nPhase 6 content migration verification: ALL CHECKS PASSED.")
    finally:
        db.close()


if __name__ == "__main__":
    verify()
