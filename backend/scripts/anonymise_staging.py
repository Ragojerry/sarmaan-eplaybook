"""
Anonymises a COPY of the production database for staging. Run it on the staging
database right after the restore, before anyone signs in or any phone connects.

Replaces personal data, never deletes a row:
  users            first and last name, username, email and phone; every password
                   is replaced with STAGING_PASSWORD so testers can sign in as any
                   (now anonymous) account and real passwords cannot be reused
  ai_question_logs the free-text question and answer (may contain names)
  audit_logs       username/email values inside the details JSON
Learner roles, areas, teams, progress and test records are kept as they are, so
the changeover can be rehearsed on realistic data.

Refuses unless ENVIRONMENT=staging. Usage (from backend/, on the staging server):
    STAGING_PASSWORD='...' python -m scripts.anonymise_staging            # --dry-run to count only
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.auth.security import hash_password  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import AiQuestionLog, User  # noqa: E402

REMOVED = "[removed for staging]"


def anonymise(db, staging_password: str) -> dict:
    """Changes the session only; the caller commits (or rolls back for a dry run)."""
    pw = hash_password(staging_password)
    users = db.query(User).order_by(User.created_at, User.id).all()
    for n, u in enumerate(users, 1):
        u.first_name = u.role.value.replace("_", " ").title()
        u.last_name = f"{n:05d}"
        u.username = f"user{n:05d}"
        u.email = f"user{n:05d}@staging.invalid"
        u.phone = None
        u.password_hash = pw
    q = db.query(AiQuestionLog).update({AiQuestionLog.question: REMOVED, AiQuestionLog.answer: None}, synchronize_session=False)
    a = db.execute(text(
        "UPDATE audit_logs SET details = (details - 'username' - 'email' - 'full_name') "
        "WHERE details ?| array['username','email','full_name']")).rowcount
    db.flush()
    return {"users anonymised": len(users), "question texts removed": q, "audit entries cleaned": a}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    env = get_settings().environment
    if env != "staging":
        print(f"REFUSED: ENVIRONMENT is {env!r}; this only runs on a staging copy (ENVIRONMENT=staging).")
        return 2
    pw = os.environ.get("STAGING_PASSWORD", "")
    if len(pw) < 10:
        print("REFUSED: set STAGING_PASSWORD (10 characters or more) for the anonymised accounts.")
        return 2
    db = SessionLocal()
    try:
        counts = anonymise(db, pw)
        db.rollback() if a.dry_run else db.commit()
        print(("DRY RUN, nothing changed: " if a.dry_run else "Done: ") + str(counts))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
