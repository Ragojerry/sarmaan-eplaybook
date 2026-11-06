"""
Curriculum changeover: the HFW flipbook modules become the only curriculum and
the old modules M1-M6 are archived (hidden, never deleted).

Cutover (one transaction; nothing is half-done):
  1. imports the HFW modules, sections, images, roles, translations and quizzes
     (scripts/import_hfw_content.py);
  2. publishes the HFW modules and their English text;
  3. archives M1-M6 (status ARCHIVED): gone from learner lists, the unlock chain,
     search and downloads; every progress and test record stays in the database;
  4. rebuilds the search index and publishes a new content release, so every
     phone refreshes at its next sync.
--rollback: M1-M6 back to PUBLISHED, the HFW modules back to DRAFT (hidden), and
a new release. No record is deleted either way. Learner, progress and test
tables are only ever read.

Guards:
  - CUTOVER_DATE (YYYY-MM-DD) comes from configuration. When ENVIRONMENT=production
    the script refuses to run if it is not set, and refuses a real run before it.
  - A real run against production needs --backup <pg_dump -Fc file>, verified here
    (dump format, the learner/progress/test tables in its table of contents, recent),
    and --confirm-production.

Usage (from backend/):
    python -m scripts.cutover_hfw --dry-run --report ../content/hfw_flipbook/cutover_dry_run_report.md
    python -m scripts.cutover_hfw --backup /backups/pre-cutover.dump
    python -m scripts.cutover_hfw --rollback --backup /backups/pre-rollback.dump
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.indexer import rebuild_all_chunks  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    ContentRelease,
    Language,
    Module,
    ModuleTranslation,
    QuizAttempt,
    User,
    UserModuleProgress,
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
        listing = out.stdout
        for t in REQUIRED_TABLES:
            if f"TABLE DATA public {t.decode()} " not in listing:
                raise Refused(f"pg_restore --list shows no table data for {t.decode()}")
        how = "pg_restore --list checked"
    return f"backup {path.name} verified ({path.stat().st_size // 1024} KB, {age_h:.1f} h old, {how})"


# ---------------------------------------------------------------- counts
def learner_counts(db) -> dict:
    """Read-only counts of learner accounts and their old-module records."""
    learners = {u.id for u in db.query(User.id).filter(User.role == RoleName.CDD)}
    old = {m.id: m.module_code for m in db.query(Module).filter(Module.module_code.in_(OLD_CODES))}
    started, done = Counter(), Counter()
    for p in db.query(UserModuleProgress).filter(UserModuleProgress.module_id.in_(list(old))):
        if p.user_id not in learners:
            continue
        if p.completed:
            done[p.user_id] += 1
        elif p.progress_percent > 0 or p.reading_completed_at is not None:
            started[p.user_id] += 1
    attempted = {a.user_id for a in db.query(QuizAttempt.user_id).filter(QuizAttempt.module_id.in_(list(old)))} & learners
    with_records = set(started) | set(done) | attempted
    in_progress = {u for u in with_records if done[u] < len(old) and (started[u] or u in attempted or done[u])}
    return {
        "learner accounts (all affected: their list becomes the new curriculum)": len(learners),
        "learners with any old-module record (kept as Legacy)": len(with_records),
        "in-progress learners who lose visible progress (started or part-completed M1-M6)": len(in_progress),
        "learners who completed all M1-M6 (completion kept as Legacy)": sum(1 for u in learners if done[u] == len(old) and old),
        "learners who completed at least one of M1-M6": sum(1 for u in learners if done[u]),
    }


# ---------------------------------------------------------------- release
def publish_release(db, kind: str, dry_run: bool, rep: dict) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    release = ContentRelease(release_code=f"HFW-{kind}-{stamp}", version=f"{datetime.now(timezone.utc):%Y.%m.%d}-{kind.lower()}"[:30],
                             description=("Curriculum changeover: HFW flipbook modules replace M1-M6"
                                          if kind == "CUTOVER" else "Curriculum changeover rolled back: M1-M6 restored"),
                             mandatory=True, status=ReleaseStatus.DRAFT)
    db.add(release)
    db.flush()
    rebuild_all_chunks(db)  # search index: archived modules drop out
    package = build_package(db, release)
    if package["counts"]["modules"] == 0:
        raise Refused("the release would contain no modules (no published module with an approved text)")
    rep["release"] = {"code": release.release_code, "curriculum": package["curriculum"], **package["counts"]}
    if dry_run:
        return
    _, size, checksum = write_package(package, release.release_code)
    release.package_size, release.checksum = size, checksum
    release.status, release.published_at = ReleaseStatus.PUBLISHED, datetime.now(timezone.utc)
    db.add(AuditLog(action=AuditAction.RELEASE_PUBLISH, entity_type="content_release", entity_id=release.id,
                    details={"release_code": release.release_code, "via": "scripts/cutover_hfw.py"}))


# ---------------------------------------------------------------- steps
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
    archived, before = 0, {}
    for m in db.query(Module).filter(Module.module_code.in_(OLD_CODES)):
        before[m.module_code] = m.status.value
        if m.status != ModuleStatus.ARCHIVED:
            m.status = ModuleStatus.ARCHIVED
            archived += 1
    db.flush()
    rep["new modules published"] = published
    rep["new modules live after the cutover"] = db.query(Module).filter(
        Module.module_code.like(f"{NEW_PREFIX}%"), Module.status == ModuleStatus.PUBLISHED).count()
    rep["modules archived"] = archived
    rep["old module status before"] = before
    db.add(AuditLog(action=AuditAction.CONTENT_EDIT, entity_type="curriculum_cutover", entity_id=None,
                    details={"step": "cutover", "archived": archived, "published": published, "before": before}))
    publish_release(db, "CUTOVER", dry_run, rep)


def rollback(db, dry_run: bool, rep: dict) -> None:
    restored = hidden = 0
    for m in db.query(Module).filter(Module.module_code.in_(OLD_CODES)):
        if m.status == ModuleStatus.ARCHIVED:
            m.status = ModuleStatus.PUBLISHED
            restored += 1
    for m in db.query(Module).filter(Module.module_code.like(f"{NEW_PREFIX}%")):
        if m.status == ModuleStatus.PUBLISHED:
            m.status = ModuleStatus.DRAFT  # hidden from phones; content and any new progress kept
            hidden += 1
    db.flush()
    rep["old modules restored (archived = false)"] = restored
    rep["new modules hidden (back to DRAFT)"] = hidden
    db.add(AuditLog(action=AuditAction.CONTENT_EDIT, entity_type="curriculum_cutover", entity_id=None,
                    details={"step": "rollback", "restored": restored, "hidden": hidden}))
    publish_release(db, "ROLLBACK", dry_run, rep)


def run(*, dry_run: bool, do_rollback: bool = False, backup: Path | None = None, confirm_production: bool = False,
        content_dir: Path = import_hfw_content.DEFAULT_CONTENT, media_root: Path | None = None, db=None,
        env: str | None = None, cutover_date: str | None = None, today: date | None = None) -> dict:
    settings = get_settings()
    env = env or settings.environment
    cutover_date = cutover_date if cutover_date is not None else (settings.cutover_date or os.environ.get("CUTOVER_DATE"))
    rep = {"mode": ("DRY RUN, nothing changed" if dry_run else "real run") + (" - ROLLBACK" if do_rollback else " - CUTOVER"),
           "environment": env, "notes": []}
    rep["notes"].append(check_cutover_date(env, cutover_date, dry_run, today))
    if not dry_run:
        if env == "production":
            if not confirm_production:
                raise Refused("refusing a real production run without --confirm-production")
            rep["notes"].append(verify_backup(backup))
        elif backup is not None:
            rep["notes"].append(verify_backup(backup))
        else:
            rep["notes"].append("no backup given (required in production; recommended on staging)")
    own = db is None
    db = db or SessionLocal()
    try:
        rep["learners"] = learner_counts(db)  # read-only
        if do_rollback:
            rollback(db, dry_run, rep)
        else:
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
    out += [f"- {n}" for n in rep["notes"]] + ["", "## Learners (read-only counts)", ""]
    out += [f"- {k}: **{v}**" for k, v in rep.get("learners", {}).items()] + ["", "## Modules", ""]
    for k, v in rep.items():
        if k in ("mode", "environment", "notes", "learners", "import", "release"):
            continue
        out.append(f"- {k}: {v}")
    if "release" in rep:
        r = rep["release"]
        out += ["", "## Content release (devices refresh at their next sync)", "",
                f"- release code: `{r['code']}`; curriculum: `{r['curriculum']}`",
                f"- modules {r['modules']}, sections {r['sections']}, media {r['media']}, quiz questions {r['quiz_questions']}"]
    if rep.get("import"):
        out += ["", "## Import", ""] + [f"- {k}: {v}" for k, v in sorted(rep["import"].items()) if not k.startswith("roles:")]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="change nothing; report what would happen")
    ap.add_argument("--rollback", action="store_true", help="restore M1-M6 and hide the HFW modules")
    ap.add_argument("--backup", type=Path, help="pg_dump -Fc file taken just before this run (required in production)")
    ap.add_argument("--confirm-production", action="store_true")
    ap.add_argument("--content-dir", type=Path, default=import_hfw_content.DEFAULT_CONTENT)
    ap.add_argument("--media-root", type=Path)
    ap.add_argument("--report", type=Path)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        rep = run(dry_run=a.dry_run, do_rollback=a.rollback, backup=a.backup, confirm_production=a.confirm_production,
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
