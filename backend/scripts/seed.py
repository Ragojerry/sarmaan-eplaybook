"""
Phase 3 seed data: minimal reference/lookup rows needed to verify the schema
works end-to-end — languages, a default campaign, and one seed admin user.

Deliberately NOT in scope here: migrating the prototype's 6 modules, photos,
and videos into content_sections/media_assets/videos. That's Phase 6
("Prototype content migration") per the master development prompt's phase
list — doing it here would blur phase boundaries and make Phase 6 redundant.

Usage:
    cd backend && python3 -m scripts.seed
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import User, Language, Campaign
from app.models.enums import RoleName, UserStatus, LanguageStatus, CampaignStatus
from app.auth.security import hash_password


def seed_languages(db):
    languages = [
        # code, name, native_name, status, is_default — matches the prototype's
        # language list exactly (docs/prototype-analysis.md §1): English is
        # full/active, the other three are "Beta" in the prototype UI.
        ("en", "English", "English", LanguageStatus.ACTIVE, True),
        ("ha", "Hausa", "Hausa", LanguageStatus.BETA, False),
        ("ff", "Fulfulde", "Fulfulde", LanguageStatus.BETA, False),
        ("kr", "Kanuri", "Kanuri", LanguageStatus.BETA, False),
    ]
    created = []
    for code, name, native_name, status, is_default in languages:
        existing = db.query(Language).filter_by(code=code).one_or_none()
        if existing:
            created.append(existing)
            continue
        lang = Language(code=code, name=name, native_name=native_name, status=status, is_default=is_default)
        db.add(lang)
        created.append(lang)
    db.flush()
    return created


def seed_campaign(db):
    existing = db.query(Campaign).filter_by(code="AZM-MDA").one_or_none()
    if existing:
        return existing
    campaign = Campaign(
        code="AZM-MDA",
        name="Azithromycin Mass Drug Administration",
        description=(
            "Bi-annual AZM administration to children aged 1-59 months, delivered door-to-door "
            "by trained CDDs under Malaria Consortium's SARMAAN II project."
        ),
        status=CampaignStatus.ACTIVE,
    )
    db.add(campaign)
    db.flush()
    return campaign


def seed_admin_user(db, english: Language):
    existing = db.query(User).filter_by(username="admin").one_or_none()
    if existing:
        return existing
    admin = User(
        username="admin",
        email="admin@sarmaan-eplaybook.app",
        # CHANGE THIS before any shared/staging use — seed-only placeholder.
        password_hash=hash_password("ChangeMe123!"),
        first_name="System",
        last_name="Administrator",
        role=RoleName.SUPER_ADMIN,
        language_id=english.id,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.flush()
    return admin


def run():
    db = SessionLocal()
    try:
        languages = seed_languages(db)
        english = next(l for l in languages if l.code == "en")
        campaign = seed_campaign(db)
        admin = seed_admin_user(db, english)
        db.commit()
        print(f"Seeded {len(languages)} languages, campaign '{campaign.code}', admin user '{admin.username}'.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
