"""
Builds the extractive-search passages (content_chunks) from PUBLISHED content.
One chunk per heading group — a heading plus every block under it until the
next heading — mirroring how the flipbook is organised. Content before a
module's first heading is folded into that first heading's chunk.

Importable so that publishing a release can rebuild the index in the same
transaction (app/routers/releases.py). `rebuild_chunks` flushes but never
commits: the caller owns the transaction.
"""
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.models import ContentChunk, ContentSection, Language, Module, ModuleTranslation, SectionTranslation
from app.models.enums import ContentReviewStatus, ContentType, ModuleStatus


def extract_text(section):
    """Human-readable text of one section — the same fields the admin portal
    and mobile reader render per ContentType."""
    c = section.content or {}
    t = section.content_type
    if t in (ContentType.TEXT, ContentType.HEADING):
        return c.get("text")
    if t == ContentType.LIST:
        items = c.get("items")
        return ". ".join(str(i).rstrip(".") for i in items) + "." if isinstance(items, list) and items else None
    if t in (ContentType.CALLOUT, ContentType.WARNING, ContentType.JOB_AID):
        heading = (c.get("heading") or "").strip()
        text = (c.get("text") or "").strip()
        if heading and text:
            return f"{heading}: {text}"
        return heading or text or None
    if t == ContentType.TABLE:
        headers = [str(h) for h in (c.get("headers") or [])]
        rows = c.get("rows") or []
        sentences = []
        for row in rows:
            cells = []
            for i, cell in enumerate(row):
                label = headers[i] if i < len(headers) else ""
                cells.append(f"{label}: {cell}" if label else str(cell))
            sentences.append("; ".join(cells) + ".")
        return " ".join(sentences) if sentences else None
    if t == ContentType.IMAGE:
        return c.get("caption")
    # VIDEO/AUDIO carry no indexable body text; TRUE_FALSE quiz statements are left out on
    # purpose, so Ask never answers with a quiz statement (half of them are false).
    return None


def build_groups(module, sections):
    """-> list of (section_title, first_section_id, [text parts])"""
    groups = []
    prefix = []
    current = None
    for s in sections:
        text = extract_text(s)
        if s.content_type == ContentType.HEADING:
            if current is not None:
                groups.append(current)
            current = [text.strip() if text else module.title, s.id, prefix[:]]
            prefix = []
            continue
        if not text or not text.strip():
            continue
        if current is None:
            prefix.append(text.strip())
        else:
            current[2].append(text.strip())
    if current is not None:
        groups.append(current)
    elif prefix:
        groups.append([module.title, None, prefix])
    return groups


def rebuild_chunks(db: Session, language_code: str = "en") -> int:
    """Rebuild chunks for every module. Published modules (with a PUBLISHED
    translation) get fresh chunks; chunks of anything else are removed so an
    unpublished/rolled-back module can never be answered from. Returns the
    number of chunks written."""
    language = db.query(Language).filter_by(code=language_code).one_or_none()
    if language is None:
        return 0
    total = 0
    for module in db.query(Module).all():
        db.query(ContentChunk).filter_by(module_id=module.id, language=language_code).delete()
        if module.status != ModuleStatus.PUBLISHED:
            continue
        published = (
            db.query(ModuleTranslation)
            .filter_by(module_id=module.id, language_id=language.id, status=ContentReviewStatus.PUBLISHED)
            .one_or_none()
        )
        if published is None:
            continue
        sections = db.query(ContentSection).filter_by(module_id=module.id).order_by(ContentSection.sort_order).all()
        source_title = module.title
        if language_code != "en":
            # Translated text where it exists; any untranslated section falls
            # back to English so a partial translation still has full coverage.
            overlay = {
                st.section_id: st
                for st in db.query(SectionTranslation).filter_by(language_id=language.id).all()
            }
            sections = [
                SimpleNamespace(id=s.id, content_type=s.content_type,
                                content=overlay[s.id].content if s.id in overlay else s.content)
                for s in sections
            ]
            module = SimpleNamespace(id=module.id, module_code=module.module_code, title=published.title)
            source_title = published.title
        for title, section_id, parts in build_groups(module, sections):
            body = " ".join(p for p in parts if p).strip()
            if not body:
                continue
            db.add(
                ContentChunk(
                    module_id=module.id,
                    module_code=module.module_code,
                    section_id=section_id,
                    section_title=title,
                    language=language_code,
                    source_title=source_title,
                    chunk_text=body,
                )
            )
            total += 1
    db.flush()
    return total


def rebuild_all_chunks(db: Session) -> int:
    """English plus every other language that has data. A language whose
    translations are no longer published has its chunks removed."""
    total = 0
    for language in db.query(Language).all():
        total += rebuild_chunks(db, language.code)
    return total
