"""
Adds the CDD flipbook (content/cdd_flipbook, built from content/source/CDD-flipbook.pdf)
as six CDD-only modules, CDD-01 .. CDD-06, and stops CDD learners seeing the HFW modules.
Programme decisions of 2026-11-10:
  - CDD learners see only the CDD modules; every other learner role keeps the HFW modules.
  - HFW-03 and HFW-07 (CDD-only today) go to Health Worker instead.
  - No quiz questions yet: the CDD modules are completed with "Mark as complete".

One transaction, in this order:
  1. HFW fingerprint: row counts and SHA-256 of every HFW module, text, section,
     translation, quiz question, video, FAQ entry, picture (row and file on disk), search
     passage, plus all users, progress, test attempts and audit rows.
  2. CDD modules, English texts and sections (fixed section ids), PUBLISHED directly,
     one CONTENT_CREATE audit entry per module that was created or changed.
  3. Pictures as media assets (matched by SHA-256, never duplicated), copied to
     <media root>/images/cdd/.
  4. HFW audience tags only: CDD is removed from every HFW module (GENERAL ones become
     role-specific for the other four roles; a module left with no role goes to
     HEALTH_WORKER). One AUDIENCE_CHANGE audit entry per module changed.
  5. Search index rebuilt (all modules; HFW passages come back with the same text).
  6. The fingerprint again: everything must be identical except the HFW audience tags,
     otherwise the whole run is rolled back.
No content release is made: phones see the change after the next release is published.

Safe to re-run: a second run changes nothing and adds no audit entries.

Usage (from backend/):
    python -m scripts.migrate_cdd_content --dry-run
    python -m scripts.migrate_cdd_content --baseline-out ../content/cdd_flipbook/hfw_baseline_local.json
    python -m scripts.migrate_cdd_content --backup /opt/sarmaan/backups/pre-cdd.dump --allow-production   # production
Options: --content-dir PATH  --media-root PATH  --report FILE.md
"""
import argparse
import hashlib
import json
import shutil
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.ai.indexer import rebuild_all_chunks  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import AuditLog, ContentSection, Language, MediaAsset, Module, ModuleTranslation, User  # noqa: E402
from app.models.enums import (  # noqa: E402
    AuditAction,
    ContentReviewStatus,
    ContentType,
    LearnerRole,
    MediaAssetType,
    ModuleAudience,
    ModuleStatus,
    RoleName,
)
from app.routers.media import _media_root  # noqa: E402
from scripts.cutover_hfw import Refused, verify_backup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT = ROOT / "content" / "cdd_flipbook"
SOURCE_PDF = ROOT / "content" / "source" / "CDD-flipbook.pdf"
CODE_PREFIX = "CDD-"
HFW_PREFIX = "HFW-"
MODULE_NUMBER_BASE = 200  # HFW modules are 100+
SORT_ORDER_BASE = 2000    # HFW modules are 1000+
CDD = LearnerRole.CDD.value
OTHER_ROLES = [r.value for r in LearnerRole if r != LearnerRole.CDD]
NO_ROLE_LEFT = [LearnerRole.HEALTH_WORKER.value]  # programme decision for HFW-03 and HFW-07
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
AUDIENCE_COLUMNS = ["audience", "learner_roles", "audience_needs_review", "updated_at"]

HFW_MODULES = f"(select id from modules where module_code like '{HFW_PREFIX}%')"
HFW_SECTIONS = f"(select id from content_sections where module_id in {HFW_MODULES})"
HFW_MEDIA = (f"(select (content->>'media_asset_id')::uuid from content_sections where module_id in {HFW_MODULES} "
             f"and content ? 'media_asset_id' union select (content->>'media_asset_id')::uuid from quiz_questions "
             f"where module_id in {HFW_MODULES} and content ? 'media_asset_id')")
# table, rows that belong to the fingerprint, columns left out
FINGERPRINT = [
    ("modules", f"module_code like '{HFW_PREFIX}%'", AUDIENCE_COLUMNS),
    ("module_translations", f"module_id in {HFW_MODULES}", []),
    ("content_sections", f"module_id in {HFW_MODULES}", []),
    ("section_translations", f"section_id in {HFW_SECTIONS}", []),
    ("quiz_questions", f"module_id in {HFW_MODULES}", []),
    ("videos", f"module_id in {HFW_MODULES}", []),
    ("faq_entries", f"module_id in {HFW_MODULES}", []),
    ("media_assets", f"id in {HFW_MEDIA}", []),
    ("content_chunks", f"module_id in {HFW_MODULES}", ["id", "created_at"]),  # rebuilt: compare the text
    ("users", "true", ["last_login_at", "updated_at"]),
    ("user_module_progress", "true", []),
    ("quiz_attempts", "true", []),
    ("audit_logs", "created_at < :started", []),
]


class Report:
    def __init__(self):
        self.counts, self.warnings, self.info = Counter(), [], []
        self.audience, self.fingerprint = [], {}

    def markdown(self, mode: str) -> str:
        out = [f"# CDD content migration ({mode})", "", f"Run at {datetime.now(timezone.utc).isoformat(timespec='seconds')}.", ""]
        out += ["## What the migration does / would do", ""] + [f"- {k}: {v}" for k, v in sorted(self.counts.items())] + [""]
        out += ["## HFW audience tags (only these change on HFW modules)", ""]
        out += [f"- {c}: {b} -> {a}" for c, b, a in self.audience] or ["- no change (already done)"]
        out += ["", "## HFW and user data: before and after (must be identical)", "",
                "| Table | Rows before | Rows after | Identical |", "|---|---|---|---|"]
        for t, (b, a) in self.fingerprint.items():
            out.append(f"| {t} | {b['rows']} | {a['rows']} | {'yes' if b == a else '**NO**'} |")
        out += ["", "## Warnings", ""] + ([f"- {w}" for w in self.warnings] or ["- none"])
        out += ["", "## Notes", ""] + ([f"- {i}" for i in self.info] or ["- none"]) + [""]
        return "\n".join(out)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(db, media_root: Path, started: datetime) -> dict:
    """{table: {rows, sha256}} plus the HFW picture files on disk. Read-only."""
    out = {}
    for table, where, leave_out in FINGERPRINT:
        drop = "".join(f" - '{c}'" for c in leave_out)
        rows = db.execute(text(f"select (to_jsonb(t){drop})::text from {table} t where {where}"),
                          {"started": started}).scalars().all()
        # jsonb text is canonical (sorted keys), so sorting the rows gives a stable digest
        out[table] = {"rows": len(rows), "sha256": _sha("\n".join(sorted(rows)).encode())}
    files = db.execute(text(f"select storage_path from media_assets where id in {HFW_MEDIA}")).scalars().all()
    digests = []
    for rel in sorted(files):
        p = media_root / rel
        digests.append(f"{rel} {_sha(p.read_bytes()) if p.is_file() else 'MISSING'}")
    out["HFW picture files on disk"] = {"rows": len(files), "sha256": _sha("\n".join(digests).encode()),
                                        "missing": sum(d.endswith("MISSING") for d in digests)}
    return out


def hfw_audiences(db) -> dict:
    return {m.module_code: (m.audience.value, sorted(m.learner_roles or []))
            for m in db.query(Module).filter(Module.module_code.like(f"{HFW_PREFIX}%")).order_by(Module.sort_order)}


def load(content_dir: Path) -> list[dict]:
    modules = json.loads((content_dir / "content_sections.json").read_text(encoding="utf-8"))
    problems = []
    for m in modules:
        if not m["module_code"].startswith(CODE_PREFIX):
            problems.append(f"{m['module_code']}: not a {CODE_PREFIX} code")
        if m["learner_roles"] != [CDD] or m["audience"] != "ROLE_SPECIFIC":
            problems.append(f"{m['module_code']}: must be ROLE_SPECIFIC for CDD only")
        for s in m["sections"]:
            ContentType[s["content_type"]]
            if s["content_type"] == "IMAGE" and not (content_dir / "images" / s["content"]["image_file"]).is_file():
                problems.append(f"{m['module_code']}: missing image {s['content']['image_file']}")
    if problems:
        raise Refused("; ".join(problems))
    return modules


def upsert_modules(db, modules, english, rep) -> dict:
    pdf_sha = _sha(SOURCE_PDF.read_bytes()) if SOURCE_PDF.is_file() else None
    out = {}
    for m in modules:
        mod = db.query(Module).filter_by(module_code=m["module_code"]).one_or_none()
        created = mod is None
        if created:
            mod = Module(module_code=m["module_code"], module_number=0, title=m["title"], status=ModuleStatus.PUBLISHED)
            db.add(mod)
        before = (mod.module_number, mod.sort_order, mod.title, mod.description, mod.status,
                  mod.audience, sorted(mod.learner_roles or []))
        mod.module_number = MODULE_NUMBER_BASE + m["learning_order"]
        mod.sort_order = SORT_ORDER_BASE + 10 * m["learning_order"]
        mod.title, mod.description = m["title"], m["description"]
        mod.status = ModuleStatus.PUBLISHED
        mod.audience, mod.learner_roles, mod.audience_needs_review = ModuleAudience.ROLE_SPECIFIC, [CDD], False
        db.flush()
        changed = created or before != (mod.module_number, mod.sort_order, mod.title, mod.description, mod.status,
                                        mod.audience, sorted(mod.learner_roles))
        tr = db.query(ModuleTranslation).filter_by(module_id=mod.id, language_id=english.id).one_or_none()
        if tr is None:
            tr = ModuleTranslation(module_id=mod.id, language_id=english.id, title=m["title"], description=m["description"])
            db.add(tr)
        if (tr.title, tr.description, tr.status) != (m["title"], m["description"], ContentReviewStatus.PUBLISHED):
            tr.title, tr.description = m["title"], m["description"]
            tr.status, tr.reviewed_at = ContentReviewStatus.PUBLISHED, datetime.now(timezone.utc)
            changed = True
        out[m["module_code"]] = (mod, changed, created, pdf_sha)
        rep.counts["modules created (PUBLISHED)" if created else "modules already present"] += 1
    db.flush()
    return out


def upsert_sections(db, modules, mods, rep) -> None:
    for m in modules:
        mod, changed, created, pdf_sha = mods[m["module_code"]]
        for s in m["sections"]:
            content = dict(s["content"])
            sec = db.get(ContentSection, uuid.UUID(s["id"]))
            if sec is None:
                sec = ContentSection(id=uuid.UUID(s["id"]), module_id=mod.id)
                db.add(sec)
                rep.counts["sections created"] += 1
                changed = True
            else:
                old = sec.content or {}
                for keep in ("media_asset_id", "storage_path"):  # filled by the picture step
                    if keep in old and keep not in content:
                        content[keep] = old[keep]
                if (sec.module_id, sec.section_number, sec.content_type.value, sec.title, sec.content) == \
                        (mod.id, s["section_number"], s["content_type"], s["title"], content):
                    rep.counts["sections unchanged"] += 1
                else:
                    rep.counts["sections updated"] += 1
                    changed = True
            sec.module_id, sec.section_number, sec.sort_order = mod.id, s["section_number"], s["section_number"]
            sec.content_type, sec.title, sec.content = ContentType[s["content_type"]], s["title"], content
        wanted = {s["id"] for s in m["sections"]}
        for extra in db.query(ContentSection).filter_by(module_id=mod.id):
            if str(extra.id) not in wanted:
                rep.warnings.append(f"{m['module_code']}: section {extra.id} is not in the content; left in place (not deleted)")
        mods[m["module_code"]] = (mod, changed, created, pdf_sha)
    db.flush()


def upload_images(db, content_dir, modules, mods, media_root, dry_run, rep) -> None:
    sizes = {r["file"]: r["px"] for r in json.loads((content_dir / "images_build.json").read_text(encoding="utf-8"))}
    for m in modules:
        mod, changed, created, pdf_sha = mods[m["module_code"]]
        for s in m["sections"]:
            if s["content_type"] != "IMAGE":
                continue
            path = content_dir / "images" / s["content"]["image_file"]
            data = path.read_bytes()
            digest = _sha(data)
            asset = db.query(MediaAsset).filter_by(checksum=digest).first()
            if asset is None:
                rel = f"images/cdd/{path.name}"
                if not dry_run:
                    dest = media_root / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists() or _sha(dest.read_bytes()) != digest:
                        shutil.copyfile(path, dest)
                w, h = sizes.get(path.name, (None, None))
                asset = MediaAsset(asset_type=MediaAssetType.IMAGE, filename=path.name, storage_path=rel,
                                   mime_type=MIME[path.suffix.lower()], size_bytes=len(data), checksum=digest,
                                   asset_metadata={"width": w, "height": h, "source": "cdd_flipbook",
                                                   "pdf_pages": s["pdf_pages"], "alt": s["content"]["alt"][:300]})
                db.add(asset)
                db.flush()
                rep.counts["pictures added" + (" (dry run: files not copied)" if dry_run else "")] += 1
                changed = True
            else:
                rep.counts["pictures already present (matched by SHA-256)"] += 1
            sec = db.get(ContentSection, uuid.UUID(s["id"]))
            content = dict(sec.content)
            if (content.get("media_asset_id"), content.get("storage_path")) != (str(asset.id), asset.storage_path):
                content["media_asset_id"], content["storage_path"] = str(asset.id), asset.storage_path
                sec.content = content
                changed = True
        mods[m["module_code"]] = (mod, changed, created, pdf_sha)
    db.flush()


def audit_modules(db, modules, mods, rep) -> None:
    for m in modules:
        mod, changed, created, pdf_sha = mods[m["module_code"]]
        if not changed:
            continue
        db.add(AuditLog(action=AuditAction.CONTENT_CREATE if created else AuditAction.CONTENT_EDIT,
                        entity_type="module", entity_id=mod.id,
                        details={"module_code": mod.module_code, "source": "content/source/CDD-flipbook.pdf",
                                 "source_sha256": pdf_sha, "title": "Azithromycin Drug Administration Training Flipbook, CDDs",
                                 "sections": len(m["sections"]), "status": "PUBLISHED", "via": "scripts/migrate_cdd_content.py"}))
        rep.counts["audit entries for CDD modules"] += 1


def retag_hfw(db, rep) -> None:
    """Only the audience columns of HFW modules change."""
    for mod in db.query(Module).filter(Module.module_code.like(f"{HFW_PREFIX}%")).order_by(Module.sort_order):
        before = (mod.audience.value, sorted(mod.learner_roles or []))
        if mod.audience == ModuleAudience.GENERAL:
            roles = list(OTHER_ROLES)
        else:
            roles = sorted(r for r in (mod.learner_roles or []) if r != CDD) or list(NO_ROLE_LEFT)
        after = (ModuleAudience.ROLE_SPECIFIC.value, sorted(roles))
        if after == before:
            continue
        mod.audience, mod.learner_roles, mod.audience_needs_review = ModuleAudience.ROLE_SPECIFIC, sorted(roles), False
        db.add(AuditLog(action=AuditAction.AUDIENCE_CHANGE, entity_type="module", entity_id=mod.id,
                        details={"module_code": mod.module_code,
                                 "before": {"audience": before[0], "learner_roles": before[1]},
                                 "after": {"audience": after[0], "learner_roles": after[1]},
                                 "reason": "CDD learners see only the CDD flipbook modules (programme decision 2026-11-10)",
                                 "via": "scripts/migrate_cdd_content.py"}))
        rep.audience.append((mod.module_code, f"{before[0]} {before[1]}", f"{after[0]} {after[1]}"))
        rep.counts["HFW modules re-tagged (audience only)"] += 1
    db.flush()


def run(content_dir: Path, dry_run: bool, media_root: Path, db=None, baseline_out: Path | None = None) -> Report:
    rep = Report()
    own = db is None
    db = db or SessionLocal()
    try:
        if own:  # one consistent view for both fingerprints (a caller's session has already begun)
            db.execute(text("set transaction isolation level repeatable read"))
        # now() is the transaction start, which is also the created_at of every audit row this run adds,
        # so "created_at < started" is exactly the audit rows that existed before
        started = db.execute(text("select now()")).scalar()
        modules = load(content_dir)
        before = fingerprint(db, media_root, started)
        if baseline_out:
            baseline_out.write_text(json.dumps({"taken_at": started.isoformat(), "fingerprint": before,
                                                "hfw_audience": hfw_audiences(db)}, indent=1), encoding="utf-8")
        english = db.query(Language).filter_by(code="en").one()
        mods = upsert_modules(db, modules, english, rep)                                   # 2
        upsert_sections(db, modules, mods, rep)
        upload_images(db, content_dir, modules, mods, media_root, dry_run, rep)            # 3
        audit_modules(db, modules, mods, rep)
        retag_hfw(db, rep)                                                                 # 4
        rep.counts["search passages after rebuild"] = rebuild_all_chunks(db)               # 5
        after = fingerprint(db, media_root, started)                                       # 6
        rep.fingerprint = {t: (before[t], after[t]) for t in before}
        changed = [t for t in before if before[t] != after[t]]
        if before["HFW picture files on disk"].get("missing"):
            rep.warnings.append(f"{before['HFW picture files on disk']['missing']} HFW picture file(s) are missing on disk "
                                "(this was already so before the run; nothing here touches them)")
        no_role = db.query(User).filter(User.role == RoleName.CDD, User.learner_role.is_(None)).count()
        general_left = db.query(Module).filter(Module.status == ModuleStatus.PUBLISHED,
                                               Module.audience == ModuleAudience.GENERAL).count()
        if no_role and not general_left:
            rep.warnings.append(f"{no_role} learner account(s) have no learner role; with no GENERAL module left they see "
                                "no modules until a role is set in the admin portal")
        rep.counts["CDD modules published"] = db.query(Module).filter(Module.module_code.like(f"{CODE_PREFIX}%"),
                                                                      Module.status == ModuleStatus.PUBLISHED).count()
        if changed:
            db.rollback()
            raise Refused("HFW or user data would change, so nothing was written: " + ", ".join(changed))
        if dry_run:
            db.rollback()
            rep.info.append("dry run: rolled back, nothing written, no files copied")
        else:
            db.commit()
            rep.info.append("committed. No content release was made: phones get the change with the next release")
        return rep
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="change nothing; report what would happen")
    ap.add_argument("--content-dir", type=Path, default=DEFAULT_CONTENT)
    ap.add_argument("--media-root", type=Path, default=None, help="default: the backend's media storage folder")
    ap.add_argument("--baseline-out", type=Path, help="write the HFW fingerprint taken before any change to this JSON file")
    ap.add_argument("--report", type=Path, help="also write the report to this markdown file")
    ap.add_argument("--backup", type=Path, help="pg_dump -Fc file taken just before; required with --allow-production")
    ap.add_argument("--allow-production", action="store_true", help="required when ENVIRONMENT=production")
    a = ap.parse_args(argv)
    env = get_settings().environment
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        if env == "production" and not a.dry_run:
            if not a.allow_production:
                raise Refused("ENVIRONMENT=production: add --allow-production and --backup <fresh pg_dump -Fc file>")
            print(verify_backup(a.backup))
        rep = run(a.content_dir, a.dry_run, a.media_root or _media_root(), baseline_out=a.baseline_out)
    except Refused as exc:
        print(f"Refused: {exc}")
        return 2
    md = rep.markdown(("DRY RUN, nothing changed" if a.dry_run else "real run") + f", environment {env}")
    print(md)
    if a.report:
        a.report.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
