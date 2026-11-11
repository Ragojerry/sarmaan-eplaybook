"""
Permanently deletes the retired per-module pre/post tests (programme decision 2026-11-11):

  - every quiz question archived by migration e7b2c4d91a35 (archived_at set), and
  - every attempt at those tests: quiz_attempts with test_type PRE or POST
    (including ones older apps uploaded afterwards, stored as not counted).

Kept: module-quiz attempts (MODULE_QUIZ), General test results, progress, users and the
audit log. One audit entry records the counts. Refused unless every archived question is
inactive, so an active question can never be deleted by mistake.

Usage (from backend/):
    python -m scripts.purge_retired_tests --dry-run
    python -m scripts.purge_retired_tests --backup /content/hfw_backups/<fresh>.dump --allow-production
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import AuditLog, GeneralTestAttempt, QuizAttempt, QuizQuestion, UserModuleProgress  # noqa: E402
from app.models.enums import AuditAction, TestType  # noqa: E402
from scripts.cutover_hfw import Refused, verify_backup  # noqa: E402

RETIRED_TYPES = (TestType.PRE, TestType.POST)


def counts(db) -> dict:
    return {
        "archived per-module questions": db.query(QuizQuestion).filter(QuizQuestion.archived_at.isnot(None)).count(),
        "active per-module questions": db.query(QuizQuestion).filter(QuizQuestion.archived_at.is_(None)).count(),
        "pre/post test attempts": db.query(QuizAttempt).filter(QuizAttempt.test_type.in_(RETIRED_TYPES)).count(),
        "module quiz attempts (kept)": db.query(QuizAttempt).filter(QuizAttempt.test_type == TestType.MODULE_QUIZ).count(),
        "General test attempts (kept)": db.query(GeneralTestAttempt).count(),
        "progress rows (kept)": db.query(UserModuleProgress).count(),
        "audit entries (kept)": db.query(AuditLog).count(),
    }


def run(dry_run: bool, db=None) -> tuple[dict, dict]:
    own = db is None
    db = db or SessionLocal()
    try:
        before = counts(db)
        if db.query(QuizQuestion).filter(QuizQuestion.archived_at.isnot(None), QuizQuestion.is_active.is_(True)).count():
            raise Refused("an archived question is active; nothing deleted")
        attempts = db.query(QuizAttempt).filter(QuizAttempt.test_type.in_(RETIRED_TYPES)).delete(synchronize_session=False)
        questions = db.query(QuizQuestion).filter(QuizQuestion.archived_at.isnot(None)).delete(synchronize_session=False)
        db.add(AuditLog(action=AuditAction.CONTENT_EDIT, entity_type="retired_tests_purged",
                        details={"questions_deleted": questions, "pre_post_attempts_deleted": attempts,
                                 "reason": "programme decision 2026-11-11: delete the archived per-module pre/post tests",
                                 "via": "scripts/purge_retired_tests.py"}))
        db.flush()
        after = counts(db)
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return before, after
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", type=Path, help="pg_dump -Fc file taken just before; required with --allow-production")
    ap.add_argument("--allow-production", action="store_true")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        if get_settings().environment == "production" and not a.dry_run:
            if not a.allow_production:
                raise Refused("ENVIRONMENT=production: add --allow-production and --backup <fresh pg_dump -Fc file>")
            print(verify_backup(a.backup))
        before, after = run(a.dry_run)
    except Refused as exc:
        print(f"Refused: {exc}")
        return 2
    print(f"# Purge of the retired per-module tests ({'DRY RUN, nothing deleted' if a.dry_run else 'real run'})")
    print("| | before | after |\n|---|---|---|")
    for k in before:
        print(f"| {k} | {before[k]} | {after[k]} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
