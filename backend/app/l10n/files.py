"""
App-string translation files for translators.

CSV (recommended: opens in Excel, the same workflow as module translations):
    key, where, placeholders, english, english_singular, translation, translation_singular, status, needs_update
JSON (for translation tools): {"format": "sarmaan-app-strings", "version": 1, "language": "ha",
    "strings": [{"key", "note", "placeholders", "english", "english_one", "translation", "translation_one", ...}]}

Only `key`, `translation` and `translation_singular` (JSON: `translation_one`) are read
back; the other columns are there to help the translator. Empty translations are
skipped (the string keeps whatever it had, or shows English). Import is
all-or-nothing: any unknown key or broken placeholder rejects the whole file with
a report of every problem, so there is never a silent partial import.
"""
import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.l10n import rules
from app.models import AppString, AppStringTranslation, Language, User
from app.models.enums import ContentReviewStatus

CSV_COLUMNS = ["key", "where", "placeholders", "english", "english_singular",
               "translation", "translation_singular", "status", "needs_update"]
FORMAT = "sarmaan-app-strings"


def _csv_safe(value) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def _unsafe(value: str) -> str:
    return value[1:] if len(value) > 1 and value[0] == "'" and value[1] in ("=", "+", "-", "@", "\t", "\r") else value


def active_strings(db: Session) -> list[AppString]:
    return db.query(AppString).filter(AppString.retired_at.is_(None)).order_by(AppString.key).all()


def translations_by_string(db: Session, language: Language) -> dict:
    return {t.string_id: t for t in db.query(AppStringTranslation).filter_by(language_id=language.id).all()}


def needs_update(string: AppString, t: AppStringTranslation | None) -> bool:
    return t is not None and t.source_version < string.source_version


def _rows(db: Session, language: Language):
    saved = translations_by_string(db, language)
    for s in active_strings(db):
        t = saved.get(s.id)
        yield s, t


def export_csv(db: Session, language: Language) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    for s, t in _rows(db, language):
        w.writerow([
            s.key, _csv_safe(s.note), " ".join("{" + p + "}" for p in s.placeholders or []),
            _csv_safe(s.english), _csv_safe(s.english_one or ""),
            _csv_safe(t.text if t else ""), _csv_safe((t.text_one or "") if t else ""),
            t.status.value if t else "", "yes" if needs_update(s, t) else "",
        ])
    return "﻿" + buf.getvalue()  # BOM so Excel shows Hausa/Fulfulde/Kanuri letters correctly


def export_json(db: Session, language: Language) -> str:
    return json.dumps({
        "format": FORMAT,
        "version": 1,
        "language": language.code,
        "strings": [{
            "key": s.key,
            "note": s.note,
            "placeholders": list(s.placeholders or []),
            "english": s.english,
            "english_one": s.english_one,
            "translation": t.text if t else "",
            "translation_one": (t.text_one or "") if t else "",
            "status": t.status.value if t else None,
            "needs_update": needs_update(s, t),
        } for s, t in _rows(db, language)],
    }, ensure_ascii=False, indent=2)


class ImportRejected(ValueError):
    """The file was not applied. `problems` lists every row that is wrong."""

    def __init__(self, message: str, problems: list[dict] | None = None):
        super().__init__(message)
        self.problems = problems or []


@dataclass
class ImportResult:
    changed: list[AppStringTranslation] = field(default_factory=list)
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped_empty: int = 0
    warnings: list[dict] = field(default_factory=list)


def _parse(raw: bytes, filename: str) -> list[tuple[int, str, str, str]]:
    """-> [(row number, key, translation, translation_one)]"""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportRejected("The file must be UTF-8 encoded (in Excel: Save As -> CSV UTF-8).") from exc
    if filename.lower().endswith(".json") or text.lstrip().startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ImportRejected(f"The JSON file cannot be read: {exc.msg} (line {exc.lineno}).") from exc
        if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("strings"), list):
            raise ImportRejected("This is not a SARMAAN app-text file (export one from the portal to see the format).")
        out = []
        for i, item in enumerate(data["strings"], start=1):
            if not isinstance(item, dict):
                raise ImportRejected(f"Entry {i} is not an object.")
            out.append((i, str(item.get("key") or "").strip(), str(item.get("translation") or ""), str(item.get("translation_one") or "")))
        return out
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or not {"key", "translation"} <= set(rows[0].keys()):
        raise ImportRejected("This does not look like a SARMAAN app-text file (needs 'key' and 'translation' columns).")
    return [
        (i, (r.get("key") or "").strip(), _unsafe((r.get("translation") or "").strip()),
         _unsafe((r.get("translation_singular") or "").strip()))
        for i, r in enumerate(rows, start=2)  # row 1 is the header
    ]


def import_file(db: Session, language: Language, raw: bytes, filename: str, actor: User) -> ImportResult:
    """Checks the whole file, then applies it as DRAFT translations. Raises
    ImportRejected (and writes nothing) on any problem. The caller commits."""
    entries = _parse(raw, filename)
    strings = {s.key: s for s in db.query(AppString).all()}
    saved = translations_by_string(db, language)
    problems: list[dict] = []
    result = ImportResult()
    seen: set[str] = set()
    todo: list[tuple[AppString, str, str | None]] = []

    for row, key, text, text_one in entries:
        if not key:
            continue
        s = strings.get(key)
        if s is None or s.retired_at is not None:
            problems.append({"row": row, "key": key, "problem": "Unknown key (not in the app). Do not edit the 'key' column."})
            continue
        if key in seen:
            problems.append({"row": row, "key": key, "problem": "This key appears more than once in the file."})
            continue
        seen.add(key)
        if not text.strip() and not text_one.strip():
            result.skipped_empty += 1
            continue
        errors, warnings = rules.check(s, text, text_one)
        problems += [{"row": row, "key": key, "problem": e} for e in errors]
        result.warnings += [{"row": row, "key": key, "problem": w} for w in warnings]
        if not errors:
            todo.append((s, text.strip(), text_one.strip() or None))

    if problems:
        raise ImportRejected(f"Nothing was imported: {len(problems)} problem(s) in the file. Fix them and upload again.", problems)
    if not todo:
        raise ImportRejected("The translation column is empty; nothing to import.")

    now = datetime.now(timezone.utc)
    for s, text, text_one in todo:
        t = saved.get(s.id)
        if t is not None and t.text == text and (t.text_one or None) == text_one and t.source_version == s.source_version:
            result.unchanged += 1
            continue
        if t is None:
            t = AppStringTranslation(string_id=s.id, language_id=language.id, text=text)
            db.add(t)
            result.created += 1
        else:
            result.updated += 1
        apply_edit(t, s, text, text_one, actor, now)
        result.changed.append(t)
    db.flush()
    return result


def apply_edit(t: AppStringTranslation, s: AppString, text: str, text_one: str | None, actor: User, now: datetime) -> None:
    """A new working copy: back to DRAFT so it passes every review step again.
    The last published text stays on phones until this one is published."""
    t.text = text
    t.text_one = text_one
    t.status = ContentReviewStatus.DRAFT
    t.source_version = s.source_version
    t.edited_by = actor.id
    t.edited_at = now
    t.reviewed_by = None
    t.reviewed_at = None
