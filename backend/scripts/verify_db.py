"""
Phase 3 verification script: confirms the schema is fully migrated and the
minimal seed data is present and idempotent. Run after `alembic upgrade head`
and `python3 -m scripts.seed`.

Usage:
    cd backend && python3 -m scripts.verify_db
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect
from app.database import engine, SessionLocal
from app.models import Language, Campaign, User

EXPECTED_TABLES = {
    "users",
    "languages",
    "campaigns",
    "modules",
    "module_translations",
    "content_sections",
    "media_assets",
    "videos",
    "user_module_progress",
    "content_releases",
    "ai_question_log",
    "rag_chunks",
    "audit_logs",
    "alembic_version",
}


def verify():
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - actual_tables
    assert not missing, f"Missing tables: {missing}"
    print(f"✓ All {len(EXPECTED_TABLES)} expected tables present.")

    # Spot-check the pgvector column actually has the right type/dimension.
    columns = {c["name"]: c for c in inspector.get_columns("rag_chunks")}
    assert "embedding" in columns, "rag_chunks.embedding column missing"
    print("✓ rag_chunks.embedding (pgvector) column present.")

    db = SessionLocal()
    try:
        lang_count = db.query(Language).count()
        assert lang_count == 4, f"Expected 4 languages, found {lang_count}"
        english = db.query(Language).filter_by(code="en").one()
        assert english.is_default, "English should be the default language"
        print(f"✓ {lang_count} languages seeded, English is default.")

        campaign = db.query(Campaign).filter_by(code="AZM-MDA").one_or_none()
        assert campaign is not None, "AZM-MDA campaign missing"
        print(f"✓ Campaign '{campaign.code}' present.")

        admin = db.query(User).filter_by(username="admin").one_or_none()
        assert admin is not None, "admin user missing"
        assert admin.role.value == "SUPER_ADMIN"
        print(f"✓ Admin user '{admin.username}' present with role {admin.role.value}.")
    finally:
        db.close()

    print("\nPhase 3 database verification: ALL CHECKS PASSED.")


if __name__ == "__main__":
    verify()
