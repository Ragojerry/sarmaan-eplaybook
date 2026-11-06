"""
Curriculum changeover: the HFW flipbook modules become the FIRST and ONLY content,
and every user starts the training from nothing.

Programme decision (2026-11-06): the app is still being built, so every progress
record and test submission in the database is test data. The changeover keeps no
training history and no trace of the old modules.

One transaction (nothing is half-done):
  1. imports the HFW modules, sections, images, roles, translations and quizzes
     (scripts/import_hfw_content.py) and publishes them;
  2. wipes ALL users' training history: module progress, pre-/post-test attempts,
     Ask (AI) questions and analytics events. Every user's training attempt goes back
     to 1, and their restart time is set to now, so each phone clears its own
     copy at its next sync and anything recorded before now is refused;
  3. deletes the old modules M1-M6 completely: their sections, translations, quiz
     questions, videos, FAQ entries, search passages and the media rows only they used.
     Image files stay on disk, so restoring the backup brings everything back;
  4. rebuilds the search index and publishes a new content release, so every
     phone refreshes at its next sync.
Kept: user accounts, roles, areas and the audit log.

There is no --rollback: deleted data comes back only by restoring the backup
taken just before the run (pg_restore). That is why a verified backup is required.

Guards:
  - CUTOVER_DATE (YYYY-MM-DD) comes from configuration. When ENVIRONMENT=production
    the script refuses to run if it is not set, and refuses a real run before it.
  - A real run against production needs --backup <pg_dump -Fc file>, verified here
    (dump format, the learner/progress/test tables in its table of contents, recent),
    and --confirm-production.

Usage (from backend/):
    python -m scripts.cutover_hfw --dry-run --report ../content/hfw_flipbook/cutover_dry_run_report.md
    python -m scripts.cutover_hfw --backup /backups/pre-cutover.dump --confirm-production   # production
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.indexer import rebuild_all_chunks  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AiQuestionLog,
    AnalyticsEvent,
    AuditLog,
    ContentChunk,
    ContentRelease,
    ContentSection,
    FaqEntry,
    Language,
    MediaAsset,
    Module,
    ModuleTranslation,
    QuizAttempt,
    QuizQuestion,
    SectionTranslation,
    User,
    UserModuleProgress,
    Video,
)
from app.models.enums import AuditAction, ContentReviewStatus, ModuleStatus, ReleaseStatus, RoleName  # noqa: E402
from app.releases.packager import build_package, write_package  # noqa: E402
from app.routers.media import _media_root  # noqa: E402
from scripts import import_hfw_content  # noqa: E402

OLD_CODES = ["M1", "M2", "M3", "M4", "M5", "M6"]
NEW_PREFIX = "HFW-"
REQUIRED_TABLES = (b"users", b"user_module_progress", b"quiz_attempts")
MAX_BACKUP_AGE_HOURS = 12


class Refused(Exception):
    pass


# ---------------------------------------------------------------- guards
def check_cutover_date(env: str, value: str | None, dry_run: bool, today: date | None = None) -> str:
    """Returns a note for the report; raises Refused when production may not run."""
    if not value:
        if env == "production":
            raise Refused("CUTOVER_DATE is not set: refusing to run against production (the programme sets the date).")
        return "CUTOVER_DATE not set (allowed outside production)"
    try:
        when = date.fromisoformat(value)
    except ValueError as exc:
        raise Refused(f"CUTOVER_DATE {value!r} is not a YYYY-MM-DD date") from exc
    today = today or datetime.now(timezone.utc).date()
    if env == "production" and not dry_run and today < when:
        raise Refused(f"CUTOVER_DATE is {when}; refusing a real production run before it (today {today}).")
    return f"CUTOVER_DATE {when}"


def verify_backup(path: Path | None, max_age_hours: float = MAX_BACKUP_AGE_HOURS) -> str:
    """A pg_dump custom-format file that holds the learner, progress and test tables
    and was made recently. Uses pg_restore --list when it is installed."""
    if path is None:
        raise Refused("no --backup given: take a pg_dump (-Fc) first and pass its path")
    if not path.is_file() or path.stat().st_size == 0:
        raise Refused(f"backup {path} does not exist or is empty")
    head = path.read_bytes()[: 4 * 1024 * 1024]
    if not head.startswith(b"PGDMP"):
        raise Refused(f"backup {path} is not a pg_dump custom-format (-Fc) file")
    missing = [t.decode() for t in REQUIRED_TABLES if b"TABLE DATA" not in head or t not in head]
    if missing:
        raise Refused(f"backup {path} does not contain table data for: {', '.join(missing)}")
    age_h = (time.time() - path.stat().st_mtime) / 3600
    if age_h > max_age_hours:
        raise Refused(f"backup {path} is {age_h:.1f} h old; take a fresh one (limit {max_age_hours} h)")
    how = "header and table list checked"
    if shutil.which("pg_restore"):
        out = subprocess.run(["pg_restore", "--list", str(path)], capture_output=True, text=True)
        if out.returncode != 0:
            raise Refused(f"pg_restore --list failed on {path}: {out.stderr.strip()[:200]}")
        for t in REQUIRED_TABLES:
            if f"TABLE DATA public {t.decode()} " not in out.stdout:
                raise Refused(f"pg_restore --list shows no table data for {t.decode()}")
        how = "pg_restore --list checked"
    return f"backup {path.name} verified ({path.stat().st_size // 1024} KB, {age_h:.1f} h old, {how})"


# ---------------------------------------------------------------- counts
def learner_counts(db) -> dict:
    """Read-only: who has training history that will be wiped."""
    learners = {u.id for u in db.query(User.id).filter(User.role == RoleName.CDD)}
    with_history = {p.user_id for p in db.query(UserModuleProgress.user_id)} | {a.user_id for a in db.query(QuizAttempt.user_id)}
    completed = {p.user_id for p in db.query(UserModuleProgress.user_id).filter(UserModuleProgress.completed.is_(True))}
    return {
        "user accounts (all start the training from nothing; accounts are kept)": db.query(User).count(),
        "learner accounts": len(learners),
        "users with any progress or test submission (wiped)": len(with_history),
        "  of whom learners with started but unfinished modules": len((with_history - completed) & learners),
        "  of whom learners who had completed at least one module": len(completed & learners),
    }


# ---------------------------------------------------------------- steps
def wipe_training_history(db, now: datetime) -> dict:
    """Every user's progress, test attempts, Ask questions and analytics: deleted.
    Restart time = now, so phones clear their copies and older uploads are refused."""
    out = {
        "module progress rows deleted": db.query(UserModuleProgress).delete(synchronize_session=False),
        "pre-/post-test attempts deleted": db.query(QuizAttempt).delete(synchronize_session=False),
        "Ask (AI) question logs deleted": db.query(AiQuestionLog).delete(synchronize_session=False),
        "analytics events deleted": db.query(AnalyticsEvent).delete(synchronize_session=False),
    }
    out["users reset to training attempt 1"] = db.query(User).update(
        {User.training_attempt: 1, User.training_restarted_at: now}, synchronize_session=False)
    return out


def delete_old_modules(db) -> dict:
    """M1-M6 and everything that belongs only to them."""
    mods = db.query(Module).filter(Module.module_code.in_(OLD_CODES)).all()
    ids = [m.id for m in mods]
    out = {"old modules deleted": len(mods)}
    if not ids:
        return out
    sec_ids = [s.id for s in db.query(ContentSection.id).filter(ContentSection.module_id.in_(ids))]
    old_media = set()
    for s in db.query(ContentSection).filter(ContentSection.module_id.in_(ids)):
        if (s.content or {}).get("media_asset_id"):
            old_media.add(str(s.content["media_asset_id"]))
    for q in db.query(QuizQuestion).filter(QuizQuestion.module_id.in_(ids)):
        if (q.content or {}).get("media_asset_id"):
            old_media.add(str(q.content["media_asset_id"]))
    if sec_ids:
        out["section translations deleted"] = db.query(SectionTranslation).filter(
            SectionTranslation.section_id.in_(sec_ids)).delete(synchronize_session=False)
        db.query(ContentChunk).filter(ContentChunk.section_id.in_(sec_ids)).delete(synchronize_session=False)
    db.query(ContentChunk).filter(ContentChunk.module_id.in_(ids)).delete(synchronize_session=False)
    out["FAQ entries deleted"] = db.query(FaqEntry).filter(FaqEntry.module_id.in_(ids)).delete(synchronize_session=False)
    out["quiz questions deleted"] = db.query(QuizQuestion).filter(QuizQuestion.module_id.in_(ids)).delete(synchronize_session=False)
    out["module texts deleted"] = db.query(ModuleTranslation).filter(ModuleTranslation.module_id.in_(ids)).delete(synchronize_session=False)
    out["videos deleted"] = db.query(Video).filter(Video.module_id.in_(ids)).delete(synchronize_session=False)
    out["sections deleted"] = db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(Module).filter(Module.id.in_(ids)).delete(synchronize_session=False)
    # media rows that only the old modules used (files stay on disk for a backup restore)
    still_used = set()
    for s in db.query(ContentSection.content):
        if (s.content or {}).get("media_asset_id"):
            still_used.add(str(s.content["media_asset_id"]))
    for q in db.query(QuizQuestion.content):
        if (q.content or {}).get("media_asset_id"):
            still_used.add(str(q.content["media_asset_id"]))
    gone = []
    for m in old_media - still_used:
        try:
            gone.append(uuid.UUID(m))
        except ValueError:
            pass
    out["media rows deleted (files kept on disk)"] = db.query(MediaAsset).filter(
        MediaAsset.id.in_(gone)).delete(synchronize_session=False) if gone else 0
    db.flush()
    return out


def publish_release(db, dry_run: bool, rep: dict) -> None:
    now = datetime.now(timezone.utc)
    release = ContentRelease(release_code=f"HFW-CUTOVER-{now:%Y%m%d%H%M%S}", version=f"{now:%Y.%m.%d}-hfw",
                             description="HFW flipbook modules: first and only curriculum", mandatory=True,
                             status=ReleaseStatus.DRAFT)
    db.add(release)
    db.flush()
    rebuild_all_chunks(db)
    package = build_package(db, release)
    if package["counts"]["modules"] == 0:
        raise Refused("the release would contain no modules (no published module with an approved text)")
    rep["release"] = {"code": release.release_code, "curriculum": package["curriculum"], **package["counts"]}
    if dry_run:
        return
    _, size, checksum = write_package(package, release.release_code)
    release.package_size, release.checksum = size, checksum
    release.status, release.published_at = ReleaseStatus.PUBLISHED, now
    db.add(AuditLog(action=AuditAction.RELEASE_PUBLISH, entity_type="content_release", entity_id=release.id,
                    details={"release_code": release.release_code, "via": "scripts/cutover_hfw.py"}))


def cutover(db, dry_run: bool, content_dir: Path, media_root: Path, rep: dict) -> None:
    imp = import_hfw_content.run(content_dir, dry_run, media_root, db=db, manage_transaction=False)
    rep["import"] = dict(imp.counts)
    if imp.errors:
        raise Refused("import checks failed: " + "; ".join(imp.errors[:5]))
    english = db.query(Language).filter_by(code="en").one()
    published = 0
    for m in db.query(Module).filter(Module.module_code.like(f"{NEW_PREFIX}%")):
        tr = db.query(ModuleTranslation).filter_by(module_id=m.id, language_id=english.id).one()
        if tr.status != ContentReviewStatus.PUBLISHED:
            tr.status, tr.reviewed_at = ContentReviewStatus.PUBLISHED, datetime.now(timezone.utc)
        if m.status != ModuleStatus.PUBLISHED:
            m.status = ModuleStatus.PUBLISHED
            published += 1
    rep["new modules published"] = published
    rep["wiped"] = wipe_training_history(db, datetime.now(timezone.utc))
    rep["deleted"] = delete_old_modules(db)
    rep["modules live after the cutover"] = [m.module_code for m in db.query(Module).filter(
        Module.status == ModuleStatus.PUBLISHED).order_by(Module.sort_order)]
    db.add(AuditLog(action=AuditAction.CONTENT_EDIT, entity_type="curriculum_cutover", entity_id=None,
                    details={"published": published, "wiped": rep["wiped"], "deleted": rep["deleted"]}))
    publish_release(db, dry_run, rep)


def run(*, dry_run: bool, backup: Path | None = None, confirm_production: bool = False,
        content_dir: Path = import_hfw_content.DEFAULT_CONTENT, media_root: Path | None = None, db=None,
        env: str | None = None, cutover_date: str | None = None, today: date | None = None) -> dict:
    settings = get_settings()
    env = env or settings.environment
    cutover_date = cutover_date if cutover_date is not None else (settings.cutover_date or os.environ.get("CUTOVER_DATE"))
    rep = {"mode": "DRY RUN, nothing changed" if dry_run else "real run", "environment": env, "notes": []}
    rep["notes"].append(check_cutover_date(env, cutover_date, dry_run, today))
    if not dry_run:
        if env == "production":
            if not confirm_production:
                raise Refused("refusing a real production run without --confirm-production")
            rep["notes"].append(verify_backup(backup))
        elif backup is not None:
            rep["notes"].append(verify_backup(backup))
        else:
            rep["notes"].append("no backup given (required in production): deleted data cannot be recovered without one")
    own = db is None
    db = db or SessionLocal()
    try:
        rep["users"] = learner_counts(db)  # read-only, before anything changes
        cutover(db, dry_run, content_dir, media_root or _media_root(), rep)
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return rep
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def markdown(rep: dict) -> str:
    out = [f"# Curriculum changeover report ({rep['mode']}, environment {rep['environment']})", "",
           f"Run at {datetime.now(timezone.utc).isoformat(timespec='seconds')}.", "", "## Checks", ""]
    out += [f"- {n}" for n in rep["notes"]] + ["", "## Users (counted before the run)", ""]
    out += [f"- {k}: **{v}**" for k, v in rep.get("users", {}).items()]
    out += ["", "## Training history wiped", ""] + [f"- {k}: {v}" for k, v in rep.get("wiped", {}).items()]
    out += ["", "## Old modules deleted", ""] + [f"- {k}: {v}" for k, v in rep.get("deleted", {}).items()]
    out += ["", "## New curriculum", "", f"- new modules published: {rep.get('new modules published')}",
            f"- modules live after the cutover, in learning order: {', '.join(rep.get('modules live after the cutover', []))}"]
    if "release" in rep:
        r = rep["release"]
        out += ["", "## Content release (devices refresh at their next sync)", "",
                f"- release code: `{r['code']}`; curriculum: `{r['curriculum']}`",
                f"- modules {r['modules']}, sections {r['sections']}, media {r['media']}, quiz questions {r['quiz_questions']}"]
    out += ["", "Rollback: restore the backup taken before the run (`pg_restore`). There is no other way back."]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="change nothing; report what would happen")
    ap.add_argument("--backup", type=Path, help="pg_dump -Fc file taken just before this run (required in production)")
    ap.add_argument("--confirm-production", action="store_true")
    ap.add_argument("--content-dir", type=Path, default=import_hfw_content.DEFAULT_CONTENT)
    ap.add_argument("--media-root", type=Path)
    ap.add_argument("--report", type=Path)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        rep = run(dry_run=a.dry_run, backup=a.backup, confirm_production=a.confirm_production,
                  content_dir=a.content_dir, media_root=a.media_root)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 2
    md = markdown(rep)
    print(md)
    if a.report:
        a.report.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
