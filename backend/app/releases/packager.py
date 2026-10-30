"""
Phase 12: builds the downloadable release package.

A package is ONE self-contained JSON document holding a frozen snapshot of
everything the phone needs for offline use: published modules (with their
published translations and typed sections), the media manifest (id + sha256 per
image), and the extractive-search passages. Publishing freezes it, so a phone
that installs release R gets exactly what was approved at publish time even if
admins keep editing drafts afterwards.

The file's SHA-256 is stored on the release (`checksum`, `package_size`); the
phone verifies the downloaded bytes against it before touching its local DB.
Per-module `checksum`s let the phone tell which modules actually changed.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.quiz.grading import PASS_MARK
from app.models import (
    SectionTranslation,
    ContentChunk,
    ContentRelease,
    ContentSection,
    Language,
    MediaAsset,
    Module,
    ModuleTranslation,
    QuizQuestion,
)
from app.models.enums import ContentReviewStatus, ContentType, ModuleStatus

SCHEMA_VERSION = 1


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_package(db: Session, release: ContentRelease) -> dict:
    languages = {l.id: l.code for l in db.query(Language).all()}
    modules_out: list[dict] = []
    media_ids: set[str] = set()

    modules = db.query(Module).filter(Module.status == ModuleStatus.PUBLISHED).order_by(Module.sort_order).all()
    for m in modules:
        translations = (
            db.query(ModuleTranslation)
            .filter_by(module_id=m.id, status=ContentReviewStatus.PUBLISHED)
            .order_by(ModuleTranslation.language_id)
            .all()
        )
        if not translations:
            continue  # a module with no approved translation is not shippable
        sections = db.query(ContentSection).filter_by(module_id=m.id).order_by(ContentSection.sort_order).all()
        published_lang_ids = [t.language_id for t in translations if languages.get(t.language_id, "en") != "en"]
        section_translations = (
            db.query(SectionTranslation)
            .filter(
                SectionTranslation.section_id.in_([s.id for s in sections]),
                SectionTranslation.language_id.in_(published_lang_ids),
            )
            .order_by(SectionTranslation.language_id, SectionTranslation.section_id)
            .all()
            if sections and published_lang_ids
            else []
        )
        for s in sections:
            if s.content_type == ContentType.IMAGE and (s.content or {}).get("media_asset_id"):
                media_ids.add(str(s.content["media_asset_id"]))
        quiz = (
            db.query(QuizQuestion)
            .filter_by(module_id=m.id, is_active=True)
            .order_by(QuizQuestion.sort_order, QuizQuestion.created_at)
            .all()
        )
        for qq in quiz:
            if qq.content.get("media_asset_id"):
                media_ids.add(str(qq.content["media_asset_id"]))
        entry = {
            "id": str(m.id),
            "module_code": m.module_code,
            "module_number": m.module_number,
            "title": m.title,
            "description": m.description,
            "status": m.status.value,
            "sort_order": m.sort_order,
            "translations": [
                {
                    "id": str(t.id),
                    "language_id": str(t.language_id),
                    "language_code": languages.get(t.language_id, "en"),
                    "title": t.title,
                    "description": t.description,
                    "body": t.body,
                    "audio_text": t.audio_text,
                    "status": t.status.value,
                }
                for t in translations
            ],
            "quiz_questions": [
                {
                    "id": str(qq.id),
                    "question_type": qq.question_type.value,
                    "prompt": qq.prompt,
                    "content": qq.content,
                    "explanation": qq.explanation,
                    "sort_order": qq.sort_order,
                }
                for qq in quiz
            ],
            "section_translations": [
                {
                    "section_id": str(st.section_id),
                    "language_code": languages.get(st.language_id, "en"),
                    "title": st.title,
                    "content": st.content,
                }
                for st in section_translations
            ],
            "sections": [
                {
                    "id": str(s.id),
                    "section_number": s.section_number,
                    "title": s.title,
                    "content_type": s.content_type.value,
                    "content": s.content,
                    "sort_order": s.sort_order,
                }
                for s in sections
            ],
        }
        entry["checksum"] = _sha256(_canonical(entry))
        modules_out.append(entry)

    media_out = []
    if media_ids:
        import uuid as _uuid

        for a in db.query(MediaAsset).filter(MediaAsset.id.in_([_uuid.UUID(i) for i in media_ids])).all():
            media_out.append(
                {
                    "id": str(a.id),
                    "asset_type": a.asset_type.value,
                    "filename": a.filename,
                    "mime_type": a.mime_type,
                    "size_bytes": a.size_bytes,
                    "checksum": a.checksum,
                }
            )
        media_out.sort(key=lambda x: x["id"])

    published_module_ids = {m["id"] for m in modules_out}
    chunk_rows = db.query(ContentChunk).order_by(ContentChunk.module_code, ContentChunk.created_at).all()
    chunks_out = [
        {
            "id": str(c.id),
            "module_id": str(c.module_id),
            "section_id": str(c.section_id) if c.section_id else None,
            "module_code": c.module_code,
            "source_title": c.source_title,
            "section_title": c.section_title,
            "language": c.language,
            "chunk_text": c.chunk_text,
        }
        for c in chunk_rows
        if str(c.module_id) in published_module_ids
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "release": {
            "release_code": release.release_code,
            "version": release.version,
            "mandatory": release.mandatory,
            "description": release.description,
            "built_at": datetime.now(timezone.utc).isoformat(),
        },
        "quiz_pass_mark": PASS_MARK,
        "languages": sorted({t["language_code"] for m in modules_out for t in m["translations"]}),
        "modules": modules_out,
        "media": media_out,
        "chunks": chunks_out,
        "counts": {
            "modules": len(modules_out),
            "sections": sum(len(m["sections"]) for m in modules_out),
            "media": len(media_out),
            "chunks": len(chunks_out),
            "quiz_questions": sum(len(m["quiz_questions"]) for m in modules_out),
        },
    }


def package_path(release_code: str) -> Path:
    safe = "".join(ch for ch in release_code if ch.isalnum() or ch in "-_.")
    root = Path(get_settings().release_storage_path)
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{safe}.package.json"


def write_package(package: dict, release_code: str) -> tuple[Path, int, str]:
    """Writes atomically (temp file + rename) so a crash can never leave a half-written package."""
    data = _canonical(package)
    path = package_path(release_code)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path, len(data), _sha256(data)
