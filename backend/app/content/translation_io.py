"""
Translation workflow: export the English source as a CSV for translators and
import the finished CSV back as a DRAFT translation.

The CSV has one row per translatable string:
    key, where, english, translation
`key` is "<section_id>|<path>" (or "MODULE|title"), and it is the only thing
the importer trusts, so translators must not edit it. Empty `translation`
cells are ignored and fall back to English on the phone. Imported text always
lands as DRAFT and must pass the normal review steps (including
LOCALISATION_REVIEW) before it can ship.
"""
import copy
import csv
import io
import uuid

from app.models import ContentSection, Module, ModuleTranslation, SectionTranslation
from app.models.enums import ContentReviewStatus, ContentType

MODULE_ID = "MODULE"
TEXT_ONLY = (ContentType.TEXT, ContentType.HEADING)
HEADED = (ContentType.CALLOUT, ContentType.WARNING, ContentType.JOB_AID)


def flatten(content_type, content):
    """-> [(path, english_text)] for the strings of one section a translator edits."""
    c = content or {}
    out = []
    if content_type in TEXT_ONLY:
        if isinstance(c.get("text"), str):
            out.append(("text", c["text"]))
    elif content_type == ContentType.LIST:
        for i, item in enumerate(c.get("items") or []):
            out.append((f"items.{i}", str(item)))
    elif content_type in HEADED:
        for k in ("heading", "text"):
            if isinstance(c.get(k), str) and c[k].strip():
                out.append((k, c[k]))
    elif content_type == ContentType.TABLE:
        for i, h in enumerate(c.get("headers") or []):
            out.append((f"headers.{i}", str(h)))
        for r, row in enumerate(c.get("rows") or []):
            for col, cell in enumerate(row):
                out.append((f"rows.{r}.{col}", str(cell)))
    elif content_type == ContentType.IMAGE:
        if isinstance(c.get("caption"), str) and c["caption"].strip():
            out.append(("caption", c["caption"]))
    return out


def _set_path(content, path, value):
    parts = path.split(".")
    node = content
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    last = parts[-1]
    if isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value


def _get_path(content, path):
    node = content
    for part in path.split("."):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def _csv_safe(value):
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def _unsafe(value):
    """Undo _csv_safe (only when the apostrophe guards a formula character)."""
    return value[1:] if len(value) > 1 and value[0] == "'" and value[1] in ("=", "+", "-", "@", "\t", "\r") else value


def _sections(db, module):
    return db.query(ContentSection).filter_by(module_id=module.id).order_by(ContentSection.sort_order).all()


def export_csv(db, module: Module, language) -> str:
    existing = (
        db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=language.id).one_or_none()
    )
    saved = {
        st.section_id: st
        for st in db.query(SectionTranslation).filter_by(language_id=language.id).all()
    }
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["key", "where", "english", "translation"])
    w.writerow([f"{MODULE_ID}|title", "Module title", _csv_safe(module.title), _csv_safe(existing.title if existing else "")])
    w.writerow([f"{MODULE_ID}|description", "Module description", _csv_safe(module.description or ""), _csv_safe(existing.description if existing and existing.description else "")])
    for s in _sections(db, module):
        st = saved.get(s.id)
        label = f"Section {s.section_number} ({s.content_type.value})"
        if s.title:
            w.writerow([f"{s.id}|@title", label + " title", _csv_safe(s.title), _csv_safe(st.title if st and st.title else "")])
        for path, text in flatten(s.content_type, s.content):
            done = ""
            if st:
                try:
                    done = str(_get_path(st.content, path))
                    if done == text:
                        done = ""
                except (KeyError, IndexError, ValueError, TypeError):
                    done = ""
            w.writerow([f"{s.id}|{path}", f"{label} {path}", _csv_safe(text), _csv_safe(done)])
    return "﻿" + buf.getvalue()  # BOM so Excel opens Hausa/Fulfulde/Kanuri letters correctly


class ImportError_(ValueError):
    pass


def import_csv(db, module: Module, language, raw: bytes) -> dict:
    """Applies a translated CSV. Raises ImportError_ on a bad file, and writes
    nothing in that case (caller commits). Returns a summary dict."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportError_("The file must be UTF-8 encoded (in Excel: Save As -> CSV UTF-8).") from exc
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or not {"key", "translation"} <= set(rows[0].keys()):
        raise ImportError_("This does not look like a SARMAAN translation file (needs 'key' and 'translation' columns).")

    sections = {str(s.id): s for s in _sections(db, module)}
    allowed = {f"{MODULE_ID}|title", f"{MODULE_ID}|description"}
    for sid, s in sections.items():
        if s.title:
            allowed.add(f"{sid}|@title")
        allowed.update(f"{sid}|{p}" for p, _ in flatten(s.content_type, s.content))

    values: dict[str, str] = {}
    unknown = []
    for r in rows:
        key = (r.get("key") or "").strip()
        value = _unsafe((r.get("translation") or "").strip())
        if not key:
            continue
        if key not in allowed:
            unknown.append(key)
            continue
        if value:
            values[key] = value
    if unknown:
        raise ImportError_(
            f"{len(unknown)} row(s) do not belong to this module (first: {unknown[0]}). "
            "Export the file again from this module and do not edit the 'key' column."
        )
    if not values:
        raise ImportError_("The 'translation' column is empty; nothing to import.")

    mt = db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=language.id).one_or_none()
    created = mt is None
    if mt is None:
        mt = ModuleTranslation(module_id=module.id, language_id=language.id, title=module.title, description=module.description)
        db.add(mt)
    was = mt.status
    if f"{MODULE_ID}|title" in values:
        mt.title = values[f"{MODULE_ID}|title"][:255]
    if f"{MODULE_ID}|description" in values:
        mt.description = values[f"{MODULE_ID}|description"]
    mt.status = ContentReviewStatus.DRAFT  # any change needs review again
    mt.reviewed_by = None
    mt.reviewed_at = None

    touched = 0
    for sid, s in sections.items():
        mine = {k.split("|", 1)[1]: v for k, v in values.items() if k.startswith(sid + "|")}
        if not mine:
            continue
        st = db.query(SectionTranslation).filter_by(section_id=s.id, language_id=language.id).one_or_none()
        if st is None:
            st = SectionTranslation(section_id=s.id, language_id=language.id, content=copy.deepcopy(s.content or {}))
            db.add(st)
        content = copy.deepcopy(st.content or s.content or {})
        for path, value in mine.items():
            if path == "@title":
                st.title = value[:255]
            else:
                _set_path(content, path, value)
        st.content = content  # reassign so JSONB change is detected
        touched += 1
    db.flush()
    return {
        "translation_id": str(mt.id),
        "created": created,
        "reset_to_draft": (not created) and was != ContentReviewStatus.DRAFT,
        "strings": len(values),
        "sections": touched,
    }
