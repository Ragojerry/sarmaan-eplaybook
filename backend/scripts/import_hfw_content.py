"""
Imports the HFW flipbook role modules (content/hfw_flipbook). Nothing existing is
replaced or deleted. The changeover itself (archiving M1-M6, publishing the new
modules, a new content release) is scripts/cutover_hfw.py, which calls this.

Order: checks -> 1 modules -> 2 sections (with the UUIDs the CSV keys use) ->
3 images (media assets) -> 4 roles -> 5 translation CSVs -> 6 quiz questions.

Safe to re-run: modules are matched by module_code, sections and quiz questions
by their fixed UUIDs, media assets by checksum. Nothing is ever duplicated.
New modules are created as DRAFT (status never downgraded on a re-run) and go
through the normal review and release steps before phones see them.

Usage (from backend/):
    python -m scripts.import_hfw_content --dry-run --report ../content/hfw_flipbook/import_dry_run_report.md
    python -m scripts.import_hfw_content                  # writes (refused when ENVIRONMENT=production
                                                          #   unless --allow-production is given)
Options: --content-dir PATH  --media-root PATH  --skip-quizzes
"""
import argparse
import csv
import hashlib
import io
import json
import shutil
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.content import translation_io  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    ContentSection,
    Language,
    MediaAsset,
    Module,
    ModuleTranslation,
    QuizQuestion,
)
from app.models.enums import (  # noqa: E402
    AuditAction,
    ContentReviewStatus,
    ContentType,
    LearnerRole,
    MediaAssetType,
    ModuleAudience,
    ModuleStatus,
    QuestionType,
    QuestionUsage,
)
from app.quiz.grading import InvalidQuestion, validate_content  # noqa: E402
from app.routers.media import _media_root  # noqa: E402

DEFAULT_CONTENT = Path(__file__).resolve().parents[2] / "content" / "hfw_flipbook"
CODE_PREFIX = "HFW-"
MODULE_NUMBER_BASE = 100  # after the current M1-M6 (1-6)
SORT_ORDER_BASE = 1000    # learning order: after the current modules
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
LETTERS = "ABCD"


class Report:
    def __init__(self):
        self.errors, self.warnings, self.info = [], [], []
        self.counts = Counter()

    def markdown(self, mode: str) -> str:
        out = [f"# HFW import report ({mode})", "", f"Run at {datetime.now(timezone.utc).isoformat(timespec='seconds')}.", ""]
        out += ["## Blocking problems", ""] + ([f"- {e}" for e in self.errors] or ["- none"]) + [""]
        out += ["## Warnings", ""] + ([f"- {w}" for w in self.warnings] or ["- none"]) + [""]
        out += ["## What the import does / would do", ""] + [f"- {k}: {v}" for k, v in sorted(self.counts.items())] + [""]
        out += ["## Notes", ""] + ([f"- {i}" for i in self.info] or ["- none"]) + [""]
        return "\n".join(out)


def read_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig"))))


def load(content_dir: Path, rep: Report):
    modules = json.loads((content_dir / "content_sections.json").read_text(encoding="utf-8"))
    sections = {s["id"]: (m, s) for m in modules for s in m["sections"]}
    csvs = {}
    for m in modules:
        p = content_dir / "en" / f"module_hfw_{m['module_code'][len(CODE_PREFIX):]}.csv"
        if not p.exists():
            rep.errors.append(f"missing translation source CSV {p.name} for {m['module_code']}")
        else:
            csvs[m["module_code"]] = read_csv(p)
    alt = read_csv(content_dir / "alt_text.csv") if (content_dir / "alt_text.csv").exists() else []
    quiz = read_csv(content_dir / "quizzes.csv") if (content_dir / "quizzes.csv").exists() else []
    return modules, sections, csvs, alt, quiz


def check(db, content_dir: Path, modules, sections, csvs, alt, quiz, rep: Report):
    """Every check the dry run reports. Errors block a real import."""
    roles = {r.value for r in LearnerRole}
    codes = [m["module_code"] for m in modules]
    if len(set(codes)) != len(codes):
        rep.errors.append("duplicate module codes in content_sections.json")
    for m in modules:
        if m["audience"] == "ROLE_SPECIFIC" and not m["learner_roles"]:
            rep.errors.append(f"module with no role assigned: {m['module_code']}")
        for r in m["learner_roles"]:
            if r not in roles:
                rep.errors.append(f"{m['module_code']}: unknown learner role {r}")
    # images and caption/alt
    for sid, (m, s) in sections.items():
        if s["content_type"] != "IMAGE":
            continue
        f = s["content"].get("image_file")
        if not f or not (content_dir / "images" / f).exists():
            rep.errors.append(f"missing image file {f!r} ({m['module_code']} section {s['section_number']})")
        if not (s["content"].get("caption") or "").strip():
            rep.errors.append(f"section with no caption: {m['module_code']} section {s['section_number']} ({sid})")
        if not (s["content"].get("alt") or "").strip():
            rep.errors.append(f"section with no alt text: {m['module_code']} section {s['section_number']} ({sid})")
    # CSV keys must match a section of that module, and a path it really has
    for code, rows in csvs.items():
        mine = {sid: s for sid, (m, s) in sections.items() if m["module_code"] == code}
        for r in rows:
            key = r["key"]
            if key in ("MODULE|title", "MODULE|description"):
                continue
            sid, _, path = key.partition("|")
            s = mine.get(sid)
            if s is None:
                rep.errors.append(f"CSV key with no matching section in {code}: {key}")
                continue
            allowed = {p for p, _ in translation_io.flatten(ContentType[s["content_type"]], s["content"])}
            if s["title"]:
                allowed.add("@title")
            if path not in allowed:
                rep.errors.append(f"CSV key with no matching field in {code}: {key}")
    image_ids = {sid for sid, (m, s) in sections.items() if s["content_type"] == "IMAGE"}
    for r in alt:
        sid, _, path = r["key"].partition("|")
        if path != "alt" or sid not in image_ids:
            rep.errors.append(f"alt_text.csv key with no matching image section: {r['key']}")
    missing_alt = image_ids - {r["key"].partition("|")[0] for r in alt}
    if missing_alt:
        rep.warnings.append(f"{len(missing_alt)} image section(s) have no row in alt_text.csv")
    # UUID collisions with sections that are not part of this import
    ours = set(codes)
    existing = db.query(ContentSection, Module.module_code).join(Module, Module.id == ContentSection.module_id) \
        .filter(ContentSection.id.in_([uuid.UUID(i) for i in sections])).all()
    for sec, code in existing:
        target = sections[str(sec.id)][0]["module_code"]
        if code not in ours:
            rep.errors.append(f"UUID collision: section {sec.id} already exists in module {code} (not an HFW module)")
        elif code != target:
            rep.info.append(f"section {sec.id} moves from {code} to {target}")
    qids = [q["question_id"] for q in quiz]
    for q, code in db.query(QuizQuestion, Module.module_code).join(Module, Module.id == QuizQuestion.module_id) \
            .filter(QuizQuestion.id.in_([uuid.UUID(i) for i in qids])).all():
        if code not in ours:
            rep.errors.append(f"UUID collision: quiz question {q.id} already exists in module {code}")
    for mod in db.query(Module).filter(Module.module_code.in_(codes)):
        rep.info.append(f"module {mod.module_code} already exists (status {mod.status.value}): it will be updated, not duplicated")
    per = Counter(q["module"] for q in quiz)
    for code in codes:
        if per[code] == 0:
            rep.warnings.append(f"{code} has no quiz questions: it would have no pre-/post-test")


def upsert_modules(db, modules, english, rep):
    out = {}
    for order, m in enumerate(modules, 1):
        mod = db.query(Module).filter_by(module_code=m["module_code"]).one_or_none()
        if mod is None:
            mod = Module(module_code=m["module_code"], status=ModuleStatus.DRAFT, module_number=0, title=m["title"])
            db.add(mod)
            rep.counts["modules created"] += 1
        else:
            rep.counts["modules updated"] += 1
        mod.module_number = MODULE_NUMBER_BASE + m.get("learning_order", order)
        mod.sort_order = SORT_ORDER_BASE + 10 * m.get("learning_order", order)
        mod.title = m["title"]
        mod.description = m["description"]
        db.flush()
        tr = db.query(ModuleTranslation).filter_by(module_id=mod.id, language_id=english.id).one_or_none()
        if tr is None:
            db.add(ModuleTranslation(module_id=mod.id, language_id=english.id, title=m["title"],
                                     description=m["description"], status=ContentReviewStatus.DRAFT))
            rep.counts["English module texts created (DRAFT)"] += 1
        elif (tr.title, tr.description) != (m["title"], m["description"]):
            tr.title, tr.description = m["title"], m["description"]
            if tr.status != ContentReviewStatus.DRAFT:
                tr.status, tr.reviewed_by, tr.reviewed_at = ContentReviewStatus.DRAFT, None, None
                rep.warnings.append(f"{m['module_code']}: English title/description changed; its review went back to DRAFT")
        out[m["module_code"]] = mod
    db.flush()
    return out


def upsert_sections(db, modules, mods, rep):
    for m in modules:
        mod = mods[m["module_code"]]
        for s in m["sections"]:
            content = {k: v for k, v in s["content"].items()}
            sec = db.get(ContentSection, uuid.UUID(s["id"]))
            if sec is None:
                sec = ContentSection(id=uuid.UUID(s["id"]), module_id=mod.id, section_number=s["section_number"],
                                     content_type=ContentType[s["content_type"]], content=content, sort_order=s["section_number"])
                db.add(sec)
                rep.counts["sections created"] += 1
            else:
                old = sec.content or {}
                for keep in ("media_asset_id", "storage_path"):  # filled by the image step
                    if keep in old and keep not in content:
                        content[keep] = old[keep]
                if (sec.module_id, sec.section_number, sec.content, sec.title) != (mod.id, s["section_number"], content, s["title"]):
                    rep.counts["sections updated"] += 1
                else:
                    rep.counts["sections unchanged"] += 1
                sec.module_id, sec.section_number, sec.sort_order = mod.id, s["section_number"], s["section_number"]
                sec.content_type = ContentType[s["content_type"]]
                sec.content = content
            sec.title = s["title"]
        wanted = {s["id"] for s in m["sections"]}
        for extra in db.query(ContentSection).filter_by(module_id=mod.id):
            if str(extra.id) not in wanted:
                rep.warnings.append(f"{m['module_code']}: section {extra.id} is in the database but not in the content; left in place (not deleted)")
    db.flush()


def image_sizes(content_dir):
    """{file: (width, height)} from images_manifest.csv, so the server needs no Pillow."""
    path = content_dir / "images_manifest.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {r["file"]: tuple(int(v) for v in r["pixel_size"].split("x")) for r in csv.DictReader(f)
                if r.get("pixel_size")}


def image_size(path, sizes):
    if path.name in sizes:
        return sizes[path.name]
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def upload_images(db, content_dir, modules, media_root, dry_run, rep):
    """-> {image file name: MediaAsset}."""
    assets, by_file = {}, {}
    sizes = image_sizes(content_dir)
    for m in modules:
        for s in m["sections"]:
            if s["content_type"] != "IMAGE":
                continue
            path = content_dir / "images" / s["content"]["image_file"]
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            asset = assets.get(digest) or db.query(MediaAsset).filter_by(checksum=digest).one_or_none()
            if asset is None:
                rel = f"images/hfw/{path.name}"
                dest = media_root / rel
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists():
                        shutil.copyfile(path, dest)
                w, h = image_size(path, sizes)
                asset = MediaAsset(asset_type=MediaAssetType.IMAGE, filename=path.name, storage_path=rel,
                                   mime_type=MIME[path.suffix.lower()], size_bytes=len(data), checksum=digest,
                                   asset_metadata={"width": w, "height": h, "source": "hfw_flipbook",
                                                   "alt": s["content"]["alt"][:300]})
                db.add(asset)
                db.flush()
                rep.counts["images uploaded" + (" (dry run: not copied)" if dry_run else "")] += 1
            else:
                rep.counts["images already present (reused)"] += 1
            assets[digest] = by_file[path.name] = asset
            sec = db.get(ContentSection, uuid.UUID(s["id"]))
            content = dict(sec.content)
            content["media_asset_id"], content["storage_path"] = str(asset.id), asset.storage_path
            sec.content = content
    db.flush()
    return by_file


def assign_roles(db, modules, mods, rep):
    for m in modules:
        mod = mods[m["module_code"]]
        mod.audience = ModuleAudience[m["audience"]]
        mod.learner_roles = list(m["learner_roles"])  # one module, every role that needs it
        mod.audience_needs_review = False
        rep.counts[f"roles: {m['module_code']} -> {'GENERAL (all roles)' if m['audience'] == 'GENERAL' else ', '.join(m['learner_roles'])}"] += 1
    db.flush()


def load_translations(db, content_dir, mods, rep):
    alt_supported = any(p == "alt" for p, _ in translation_io.flatten(ContentType.IMAGE, {"caption": "c", "alt": "a"}))
    langs = [d for d in sorted(content_dir.iterdir()) if d.is_dir() and d.name not in ("en", "images", "assets", "_build")]
    if not langs:
        rep.info.append("no translated CSVs yet (content/hfw_flipbook/<language>/ folders); English is the source and is stored in the sections")
    for d in langs:
        lang = db.query(Language).filter_by(code=d.name).one_or_none()
        if lang is None:
            rep.warnings.append(f"folder {d.name}/ is not a known language code; skipped")
            continue
        alt_rows = read_csv(d / "alt_text.csv") if (d / "alt_text.csv").exists() else []
        alt_by_section = {r["key"].partition("|")[0]: r for r in alt_rows if (r.get("translation") or "").strip()}
        for code, mod in mods.items():
            p = d / f"module_hfw_{code[len(CODE_PREFIX):]}.csv"
            if not p.exists():
                continue
            raw = p.read_bytes()
            ids = {str(s.id) for s in db.query(ContentSection.id).filter_by(module_id=mod.id)}
            extra = [r for sid, r in alt_by_section.items() if sid in ids]
            if extra and alt_supported:
                text = raw.decode("utf-8-sig").rstrip("\r\n") + "\r\n"
                buf = io.StringIO()
                csv.writer(buf).writerows([[r["key"], "alt", r["english"], r["translation"]] for r in extra])
                raw = ("﻿" + text + buf.getvalue()).encode("utf-8")
            elif extra:
                rep.warnings.append(f"{d.name} {code}: {len(extra)} alt-text translation(s) skipped: the importer does not accept |alt keys yet")
            try:
                res = translation_io.import_csv(db, mod, lang, raw)
                rep.counts[f"translations loaded ({d.name})"] += res["strings"]
            except translation_io.ImportError_ as exc:
                rep.warnings.append(f"{d.name} {code}: {exc}")


def upsert_quizzes(db, content_dir, mods, image_assets, rep):
    rows = read_csv(content_dir / "quizzes.csv")
    for r in rows:
        mod = mods[r["module"]]
        options = [r[f"option_{c.lower()}"] for c in LETTERS]
        content = {"options": options, "correct": LETTERS.index(r["correct_option"])}
        qtype = QuestionType.MULTIPLE_CHOICE
        if r["image_file"]:
            asset = image_assets.get(r["image_file"])
            if asset is None:
                rep.errors.append(f"quiz {r['question_id']}: image {r['image_file']} is not a lesson image")
                continue
            qtype = QuestionType.IMAGE_CHOICE
            content.update(media_asset_id=str(asset.id), alt=(asset.asset_metadata or {}).get("alt", ""))
        try:
            content = validate_content(qtype, content)
        except InvalidQuestion as exc:
            rep.errors.append(f"quiz {r['question_id']}: {exc}")
            continue
        q = db.get(QuizQuestion, uuid.UUID(r["question_id"]))
        if q is None:
            q = QuizQuestion(id=uuid.UUID(r["question_id"]), module_id=mod.id, question_type=qtype, prompt=r["question"], content=content)
            db.add(q)
            rep.counts["quiz questions created"] += 1
        else:
            rep.counts["quiz questions updated"] += 1
        q.module_id, q.question_type, q.prompt, q.content = mod.id, qtype, r["question"], content
        q.explanation, q.sort_order, q.usage, q.is_active = r["explanation"], int(r["order"]), QuestionUsage.BOTH, True
    db.flush()


def run(content_dir: Path, dry_run: bool, media_root: Path, skip_quizzes: bool = False, db=None,
        manage_transaction: bool = True) -> Report:
    """manage_transaction=False: the caller (the cutover) commits or rolls back; dry_run
    then only stops image files being copied."""
    rep = Report()
    own = db is None
    db = db or SessionLocal()
    try:
        modules, sections, csvs, alt, quiz = load(content_dir, rep)
        check(db, content_dir, modules, sections, csvs, alt, quiz, rep)
        if rep.errors and (not dry_run or not manage_transaction):
            return rep  # nothing written
        english = db.query(Language).filter_by(code="en").one()
        mods = upsert_modules(db, modules, english, rep)                    # 1
        upsert_sections(db, modules, mods, rep)                              # 2
        image_assets = upload_images(db, content_dir, modules, media_root, dry_run, rep)  # 3
        assign_roles(db, modules, mods, rep)                                 # 4
        load_translations(db, content_dir, mods, rep)                        # 5
        if skip_quizzes:
            rep.info.append("quiz questions skipped (--skip-quizzes)")
        else:
            upsert_quizzes(db, content_dir, mods, image_assets, rep)         # 6
        if not manage_transaction:
            return rep
        if rep.errors or dry_run:
            db.rollback()
            if not dry_run:
                rep.info.append("rolled back: nothing was written")
        else:
            db.add(AuditLog(action=AuditAction.CONTENT_CREATE, entity_type="hfw_import", entity_id=None,
                            details={k: v for k, v in rep.counts.items()}))
            db.commit()
        return rep
    except Exception:
        if manage_transaction:
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
    ap.add_argument("--skip-quizzes", action="store_true")
    ap.add_argument("--report", type=Path, help="also write the report to this markdown file")
    ap.add_argument("--allow-production", action="store_true", help="required when ENVIRONMENT=production")
    a = ap.parse_args(argv)
    env = get_settings().environment
    if env == "production" and not a.allow_production:
        print("Refusing to run against ENVIRONMENT=production without --allow-production (import to staging first).")
        return 2
    rep = run(a.content_dir, a.dry_run, a.media_root or _media_root(), a.skip_quizzes)
    md = rep.markdown(("DRY RUN, nothing changed" if a.dry_run else "real import") + f", environment {env}")
    sys.stdout.reconfigure(encoding="utf-8")
    print(md)
    if a.report:
        a.report.write_text(md, encoding="utf-8")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
