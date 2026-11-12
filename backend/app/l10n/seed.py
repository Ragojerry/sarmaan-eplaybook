"""
Fills the app-string registry from the mobile app's English catalogue.

    cd backend && python -m app.l10n.seed            # uses app/l10n/app_strings.json

The catalogue is mobile/l10n/app_strings.json, copied here by
scripts/l10n_sync.py. Safe to run any number of times:
  - new keys are added (English only; no translations are created);
  - changed English bumps the string's source_version, so existing
    translations show "needs update" (they stay published until re-done);
  - keys the app no longer uses are retired (kept with their translations,
    and removed from phones on their next sync); a key that comes back is restored;
  - an unchanged catalogue changes nothing.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.l10n.rules import placeholders_of
from app.models import AppString
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction

CATALOG = Path(__file__).with_name("app_strings.json")


def load_catalog(path: Path = CATALOG) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))["strings"]


def seed(db: Session, catalog: dict[str, dict] | None = None, only_prefix: str | None = None) -> dict:
    """Applies the catalogue and commits. Returns what changed. `only_prefix`
    limits it to keys starting with that prefix (tests use their own keys, so a
    test catalogue never retires the app's real strings)."""
    catalog = load_catalog() if catalog is None else catalog
    now = datetime.now(timezone.utc)
    existing = {s.key: s for s in db.query(AppString).all() if only_prefix is None or s.key.startswith(only_prefix)}
    summary = {"created": [], "updated": [], "retired": [], "restored": [], "unchanged": 0}

    for key, entry in catalog.items():
        english, english_one = entry["en"], entry.get("en_one")
        note = entry.get("note", "")
        placeholders = sorted(placeholders_of(english) | placeholders_of(english_one))
        row = existing.get(key)
        if row is None:
            db.add(AppString(key=key, english=english, english_one=english_one, note=note,
                             placeholders=placeholders, source_version=1))
            summary["created"].append(key)
            continue
        changed = False
        if row.english != english or row.english_one != english_one:
            row.english, row.english_one = english, english_one
            row.source_version += 1  # translations made from the old English now "need update"
            summary["updated"].append(key)
            changed = True
        if row.note != note or list(row.placeholders or []) != placeholders:
            row.note, row.placeholders = note, placeholders
            changed = True
        if row.retired_at is not None:
            row.retired_at = None
            summary["restored"].append(key)
            changed = True
        if changed:
            row.updated_at = now
        else:
            summary["unchanged"] += 1

    for key, row in existing.items():
        if key not in catalog and row.retired_at is None:
            row.retired_at = now
            row.updated_at = now
            summary["retired"].append(key)

    if summary["created"] or summary["updated"] or summary["retired"] or summary["restored"]:
        db.add(AuditLog(
            user_id=None,
            action=AuditAction.CONTENT_EDIT,
            entity_type="app_string_registry",
            details={k: (v[:50] if isinstance(v, list) else v) for k, v in summary.items()}
            | {"counts": {k: len(v) for k, v in summary.items() if isinstance(v, list)}},
        ))
    db.commit()
    return summary


def main(argv=None) -> int:
    from app.database import SessionLocal

    path = Path(argv[0]) if argv else CATALOG
    db = SessionLocal()
    try:
        summary = seed(db, load_catalog(path))
    finally:
        db.close()
    print(
        f"app strings: {len(summary['created'])} added, {len(summary['updated'])} English changed, "
        f"{len(summary['retired'])} retired, {len(summary['restored'])} restored, {summary['unchanged']} unchanged"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
