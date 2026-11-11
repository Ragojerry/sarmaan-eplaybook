"""
Loads the General test and the HFW inline module quizzes (content/learning_tests, built by
content/learning_tests/build.py from the programme's two Word files).

  1. General test: the 25 questions, added by number. A new question is INACTIVE with no
     answer. Existing questions are left as they are (admins may have edited them).
  2. Answer key (only with --answer-key or --answer-key-file): sets the correct option of
     the listed questions and makes them active. It never switches the test on: that is
     the setting general_test_active, changed in the admin portal once the key is confirmed.
  3. HFW module quizzes: one TRUE_FALSE section per statement (fixed ids), placed right
     after the section that teaches it; the module's sections are renumbered in that
     order. HFW modules that are not in the database are skipped.
     The CDD statements are part of the CDD flipbook content and arrive with
     scripts/migrate_cdd_content.py.
  4. Rebuilds the search index (quiz statements are never indexed).

Safe to re-run: nothing is duplicated, and a second run changes nothing.

Usage (from backend/):
    python -m scripts.load_learning_tests --dry-run
    python -m scripts.load_learning_tests
    python -m scripts.load_learning_tests --answer-key "1-B, 2-B, 3-C, ..."
    python -m scripts.load_learning_tests --answer-key-file ../content/learning_tests/general_test_answer_key.csv
    (ENVIRONMENT=production also needs --allow-production)
"""
import argparse
import csv
import io
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.indexer import rebuild_all_chunks  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.content.true_false import clean_true_false  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import AuditLog, ContentSection, GeneralTestQuestion, Module  # noqa: E402
from app.models.enums import AuditAction, ContentType  # noqa: E402
from app.routers.general_test import LETTERS, parse_key  # noqa: E402

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "content" / "learning_tests"


def load_general(db, questions: list[dict], rep: Counter) -> None:
    present = {q.number for q in db.query(GeneralTestQuestion.number)}
    for q in questions:
        if q["number"] in present:
            rep["General test questions already present (left as they are)"] += 1
            continue
        db.add(GeneralTestQuestion(number=q["number"], prompt=q["prompt"], options=q["options"], correct_index=None,
                                   cdd_specific=q["cdd_specific"], is_active=False))
        rep["General test questions added (inactive, no answer yet)"] += 1
    db.flush()


def key_from_csv(path: Path) -> str:
    rows = csv.DictReader(io.StringIO(path.read_bytes().decode("utf-8-sig")))
    parts = [f"{r['number'].strip()}-{r['correct_option'].strip()}" for r in rows if (r.get("correct_option") or "").strip()]
    return ", ".join(parts)


def load_key(db, key_text: str, rep: Counter) -> None:
    key = parse_key(key_text)
    questions = {q.number: q for q in db.query(GeneralTestQuestion)}
    unknown = sorted(set(key) - set(questions))
    if unknown:
        raise ValueError(f"no question numbered {', '.join(map(str, unknown))}")
    for n, index in sorted(key.items()):
        q = questions[n]
        if index >= len(q.options):
            raise ValueError(f"question {n}: answer {LETTERS[index]} is not one of its {len(q.options)} options")
        if (q.correct_index, q.is_active) != (index, True):
            q.correct_index, q.is_active = index, True
            rep["answers set (question activated)"] += 1
        else:
            rep["answers already set"] += 1
    missing = sorted(set(questions) - set(key))
    if missing:
        rep[f"questions still without an answer: {', '.join(map(str, missing))}"] += 1
    db.add(AuditLog(action=AuditAction.GENERAL_TEST_UPDATE, entity_type="general_test_answer_key",
                    details={"answer_key": {n: LETTERS[i] for n, i in sorted(key.items())},
                             "via": "scripts/load_learning_tests.py"}))
    db.flush()


def load_hfw_quizzes(db, statements: list[dict], rep: Counter, warnings: list[str]) -> None:
    by_module: dict[str, list[tuple[dict, dict]]] = {}
    for s in statements:
        for p in s["placements"]:
            if p["audience"] == "HFW":
                by_module.setdefault(p["module_code"], []).append((s, p))
    for code, items in by_module.items():
        module = db.query(Module).filter_by(module_code=code).one_or_none()
        if module is None:
            warnings.append(f"{code} is not in the database: its {len(items)} statement(s) were skipped")
            continue
        changed = False
        for s, p in items:
            content = clean_true_false({"statement": s["statement"], "answer": s["answer"], "explanation": None,
                                        "audience": "HFW", "quiz_ref": s["ref"]})
            sec = db.get(ContentSection, uuid.UUID(p["section_id"]))
            if sec is None:
                db.add(ContentSection(id=uuid.UUID(p["section_id"]), module_id=module.id, section_number=0,
                                      sort_order=0, content_type=ContentType.TRUE_FALSE, title=None, content=content))
                rep["HFW quiz statements added"] += 1
                changed = True
            else:
                rep["HFW quiz statements already present"] += 1
        db.flush()
        changed |= _place(db, module, items, warnings)
        if changed:
            db.add(AuditLog(action=AuditAction.CONTENT_EDIT, entity_type="module", entity_id=module.id,
                            details={"module_code": code, "quiz_statements": [s["ref"] for s, _ in items],
                                     "source": "content/source/Module_Quiz_aa_rev_10.11.26.docx",
                                     "via": "scripts/load_learning_tests.py"}))
            rep["HFW modules with their quiz placed"] += 1


def _place(db, module: Module, items, warnings: list[str]) -> bool:
    """Each statement right after its teaching section; all sections numbered 1..n in that order."""
    sections = db.query(ContentSection).filter_by(module_id=module.id).order_by(
        ContentSection.sort_order, ContentSection.section_number).all()
    ours = {uuid.UUID(p["section_id"]): p for _, p in items}
    reading = [s for s in sections if s.id not in ours]
    quiz = {s.id: s for s in sections if s.id in ours}
    after: dict[uuid.UUID, list[ContentSection]] = {}
    for _, p in items:  # statement order within one anchor follows the quiz table
        anchor = uuid.UUID(p["after_section_id"])
        if not any(r.id == anchor for r in reading):
            warnings.append(f"{module.module_code}: section {anchor} not found; statement {p['section_id']} goes last")
            anchor = reading[-1].id
        after.setdefault(anchor, []).append(quiz[uuid.UUID(p["section_id"])])
    ordered = []
    for r in reading:
        ordered.append(r)
        ordered.extend(after.get(r.id, []))
    changed = False
    for n, s in enumerate(ordered, 1):
        if (s.section_number, s.sort_order) != (n, n):
            s.section_number, s.sort_order = n, n
            changed = True
    db.flush()
    return changed


def run(content_dir: Path, dry_run: bool, key_text: str | None = None, db=None):
    rep, warnings = Counter(), []
    own = db is None
    db = db or SessionLocal()
    try:
        general = json.loads((content_dir / "general_test.json").read_text(encoding="utf-8"))
        statements = json.loads((content_dir / "module_quiz.json").read_text(encoding="utf-8"))
        load_general(db, general, rep)
        if key_text:
            load_key(db, key_text, rep)
        load_hfw_quizzes(db, statements, rep, warnings)
        rep["search passages after rebuild"] = rebuild_all_chunks(db)
        cdd = db.query(Module).filter(Module.module_code.like("CDD-%")).count()
        cdd_statements = (db.query(ContentSection).join(Module, Module.id == ContentSection.module_id)
                          .filter(Module.module_code.like("CDD-%"), ContentSection.content_type == ContentType.TRUE_FALSE).count())
        rep[f"CDD modules in the database: {cdd}, with {cdd_statements} quiz statements (they come with migrate_cdd_content)"] += 1
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return rep, warnings
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--content-dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--answer-key", help='e.g. "1-B, 2-B, 3-C"')
    ap.add_argument("--answer-key-file", type=Path, help="the filled-in general_test_answer_key template (CSV)")
    ap.add_argument("--allow-production", action="store_true")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    env = get_settings().environment
    if env == "production" and not a.allow_production and not a.dry_run:
        print("Refused: ENVIRONMENT=production needs --allow-production (take a pg_dump first).")
        return 2
    key = a.answer_key or (key_from_csv(a.answer_key_file) if a.answer_key_file else None)
    try:
        rep, warnings = run(a.content_dir, a.dry_run, key)
    except ValueError as exc:
        print(f"Refused: {exc}")
        return 2
    print(f"# Learning tests ({'DRY RUN, nothing changed' if a.dry_run else 'real run'}, environment {env})")
    for k, v in sorted(rep.items()):
        print(f"- {k}: {v}")
    for w in warnings:
        print(f"- WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
