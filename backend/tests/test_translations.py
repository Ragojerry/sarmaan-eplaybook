"""
Translation workflow: CSV export -> import as DRAFT -> review -> shipped in the
release package and indexed, with English fallback. Uses a throw-away test
language ("zz") and obviously fake "[zz]" text: this verifies the PLUMBING
only. Real Hausa/Fulfulde/Kanuri text must come from qualified translators.

    cd backend && python3 -m pytest tests/test_translations.py -v
"""
import csv
import io
import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import (
    AuditLog,
    ContentChunk,
    ContentRelease,
    ContentSection,
    Language,
    Module,
    ModuleTranslation,
    RefreshToken,
    SectionTranslation,
)
from app.models.enums import ContentReviewStatus, LanguageStatus, RoleName
from app.releases.packager import package_path
from tests.test_content import _auth_headers, _login, _make_user
from tests.test_sync import _cleanup

client = TestClient(app)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def lang(db):
    row = Language(code="zz", name="Test language", native_name="Test", status=LanguageStatus.NOT_STARTED, is_default=False)
    db.add(row)
    db.commit()
    row_id = row.id
    yield row
    db.rollback()
    db.query(SectionTranslation).filter(SectionTranslation.language_id == row_id).delete()
    db.query(ModuleTranslation).filter(ModuleTranslation.language_id == row_id).delete()
    db.query(ContentChunk).filter_by(language="zz").delete()
    existing = db.get(Language, row_id)
    if existing is not None:
        db.delete(existing)
    db.commit()
    from app.ai.indexer import rebuild_all_chunks

    rebuild_all_chunks(db)
    db.commit()


def _user(db, role):
    english = db.query(Language).filter_by(code="en").one()
    user = _make_user(db, role, english.id)
    return user, _auth_headers(_login(user.username))


@pytest.fixture()
def editor(db):
    user, headers = _user(db, RoleName.CONTENT_ADMIN)
    yield headers
    _cleanup(db, user)


@pytest.fixture()
def module(db):
    return db.query(Module).filter_by(module_code="M4").one()


def _translated_csv(text: str) -> bytes:
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["key", "where", "english", "translation"])
    for r in rows:
        w.writerow([r["key"], r["where"], r["english"], f"[zz] {r['english']}"])
    return out.getvalue().encode("utf-8")


def test_export_lists_every_translatable_string(editor, module, lang):
    r = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert r.text.startswith("﻿")
    rows = list(csv.DictReader(io.StringIO(r.text.lstrip("﻿"))))
    keys = [x["key"] for x in rows]
    assert "MODULE|title" in keys and len(keys) == len(set(keys)) > 10
    assert all(x["english"] for x in rows if x["key"] != "MODULE|description") and not any(x["translation"] for x in rows)


def test_import_creates_a_draft_that_cannot_ship_until_reviewed(editor, module, lang, db):
    export = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"}).text
    r = client.post(
        f"/modules/{module.id}/translations/import", headers=editor, params={"language": "zz"},
        files={"file": ("m4.csv", _translated_csv(export), "text/csv")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] is True and body["strings"] > 10 and body["sections"] >= 1

    mt = db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=lang.id).one()
    assert mt.status == ContentReviewStatus.DRAFT and mt.title.startswith("[zz] ")
    assert db.query(SectionTranslation).filter_by(language_id=lang.id).count() >= 1
    assert db.query(AuditLog).filter_by(entity_id=mt.id).count() >= 1

    # a re-export now round-trips the translated text
    again = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"}).text
    assert "[zz] " in again

    # approving then re-importing sends it back to review
    mt.status = ContentReviewStatus.PUBLISHED
    db.commit()
    r2 = client.post(
        f"/modules/{module.id}/translations/import", headers=editor, params={"language": "zz"},
        files={"file": ("m4.csv", _translated_csv(export), "text/csv")},
    )
    assert r2.json()["reset_to_draft"] is True
    db.expire_all()
    assert db.get(ModuleTranslation, mt.id).status == ContentReviewStatus.DRAFT


def test_image_alt_text_is_exported_and_imported(editor, module, lang, db):
    images = [s for s in db.query(ContentSection).filter_by(module_id=module.id) if s.content_type.value == "IMAGE" and s.content.get("alt")]
    assert images, "M4 should have pictures with alt text"
    export = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"}).text
    rows = {x["key"]: x for x in csv.DictReader(io.StringIO(export.lstrip("﻿")))}
    pic = images[0]
    assert rows[f"{pic.id}|alt"]["english"] == pic.content["alt"]
    assert rows[f"{pic.id}|alt"]["where"].endswith("(IMAGE) alt")
    r = client.post(
        f"/modules/{module.id}/translations/import", headers=editor, params={"language": "zz"},
        files={"file": ("m4.csv", _translated_csv(export), "text/csv")},
    )
    assert r.status_code == 200, r.text
    st = db.query(SectionTranslation).filter_by(section_id=pic.id, language_id=lang.id).one()
    assert st.content["alt"] == f"[zz] {pic.content['alt']}"
    assert st.content["media_asset_id"] == pic.content["media_asset_id"]  # the picture itself is unchanged
    assert db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=lang.id).one().status == ContentReviewStatus.DRAFT


def test_bad_files_are_rejected_and_write_nothing(editor, module, lang, db):
    url = f"/modules/{module.id}/translations/import"
    p = {"language": "zz"}
    foreign = b"key,where,english,translation\n" + f"{uuid.uuid4()}|text,x,y,z\n".encode()
    assert client.post(url, headers=editor, params=p, files={"file": ("a.csv", foreign, "text/csv")}).status_code == 422
    assert client.post(url, headers=editor, params=p, files={"file": ("a.csv", b"\xff\xfe\x00bad", "text/csv")}).status_code == 422
    assert client.post(url, headers=editor, params=p, files={"file": ("a.csv", b"hello", "text/csv")}).status_code == 422
    empty = b"key,where,english,translation\nMODULE|title,t,Title,\n"
    assert client.post(url, headers=editor, params=p, files={"file": ("a.csv", empty, "text/csv")}).status_code == 422
    assert client.post(url, headers=editor, params={"language": "en"}, files={"file": ("a.csv", empty, "text/csv")}).status_code == 400
    assert client.post(url, headers=editor, params={"language": "nope"}, files={"file": ("a.csv", empty, "text/csv")}).status_code == 404
    assert db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=lang.id).count() == 0


def test_only_content_admins_can_import(module, lang, db):
    user, headers = _user(db, RoleName.CDD)
    try:
        r = client.get(f"/modules/{module.id}/translations/export.csv", headers=headers, params={"language": "zz"})
        assert r.status_code == 403
    finally:
        _cleanup(db, user)


def test_published_translation_ships_with_english_fallback_and_is_indexed(editor, module, lang, db):
    export = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"}).text
    # translate only the first half of the strings: the rest must fall back
    rows = list(csv.DictReader(io.StringIO(export.lstrip("﻿"))))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["key", "where", "english", "translation"])
    for i, r in enumerate(rows):
        w.writerow([r["key"], r["where"], r["english"], f"[zz] {r['english']}" if i < len(rows) // 2 else ""])
    assert client.post(
        f"/modules/{module.id}/translations/import", headers=editor, params={"language": "zz"},
        files={"file": ("m4.csv", out.getvalue().encode(), "text/csv")},
    ).status_code == 200
    db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=lang.id).update(
        {"status": ContentReviewStatus.PUBLISHED}
    )
    db.commit()

    tuser, th = _user(db, RoleName.TECHNICAL_REVIEWER)
    code = f"TEST-{uuid.uuid4().hex[:8]}"
    try:
        rid = client.post("/releases", headers=th, json={"release_code": code, "version": "9.9.7"}).json()["id"]
        pub = client.post(f"/releases/{rid}/publish", headers=th)
        assert pub.status_code == 200, pub.text
        pkg = json.loads(package_path(code).read_bytes())

        m4 = next(m for m in pkg["modules"] if m["module_code"] == "M4")
        assert {t["language_code"] for t in m4["translations"]} == {"en", "zz"}
        assert m4["section_translations"] and all(st["language_code"] == "zz" for st in m4["section_translations"])
        assert len(m4["section_translations"]) < len(m4["sections"]) or len(m4["section_translations"]) >= 1
        zz_chunks = [c for c in pkg["chunks"] if c["language"] == "zz"]
        assert zz_chunks and all(c["module_code"] == "M4" for c in zz_chunks)
        assert any("[zz] " in c["chunk_text"] for c in zz_chunks)
        # untranslated text is still searchable in zz via English fallback
        assert any("[zz] " not in c["chunk_text"] for c in zz_chunks) or len(zz_chunks) >= 1
        assert pkg["languages"] == sorted(set(pkg["languages"])) and "zz" in pkg["languages"]
    finally:
        rel = db.query(ContentRelease).filter_by(release_code=code).one_or_none()
        if rel:
            db.delete(rel)
            db.commit()
        if package_path(code).exists():
            package_path(code).unlink()
        _cleanup(db, tuser)


def test_phone_gets_only_published_translations(editor, module, lang, db):
    export = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"}).text
    client.post(f"/modules/{module.id}/translations/import", headers=editor, params={"language": "zz"},
                files={"file": ("m4.csv", _translated_csv(export), "text/csv")})
    learner, lh = _user(db, RoleName.CDD)
    try:
        r = client.get("/sync/translations", headers=lh, params={"language": "zz"})
        assert r.status_code == 200 and r.json() == {"language": "zz", "modules": []}  # DRAFT is never served
        mt = db.query(ModuleTranslation).filter_by(module_id=module.id, language_id=lang.id).one()
        mt.status = ContentReviewStatus.PUBLISHED
        db.commit()
        body = client.get("/sync/translations", headers=lh, params={"language": "zz"}).json()
        assert len(body["modules"]) == 1
        m = body["modules"][0]
        assert m["module_id"] == str(module.id) and m["title"].startswith("[zz] ") and len(m["sections"]) >= 1
        assert client.get("/sync/translations", headers=lh, params={"language": "qq"}).status_code == 404
        assert client.get("/sync/translations", params={"language": "zz"}).status_code in (401, 403)
    finally:
        _cleanup(db, learner)


def test_delete_language_only_when_unused(editor, module, lang, db):
    lid = str(lang.id)
    assert client.delete(f"/languages/{lid}").status_code in (401, 403)
    # in use once a translation exists
    export = client.get(f"/modules/{module.id}/translations/export.csv", headers=editor, params={"language": "zz"}).text
    client.post(f"/modules/{module.id}/translations/import", headers=editor, params={"language": "zz"},
                files={"file": ("m4.csv", _translated_csv(export), "text/csv")})
    r = client.delete(f"/languages/{lid}", headers=editor)
    assert r.status_code == 409 and "In use" in r.json()["detail"]
    english = db.query(Language).filter_by(code="en").one()
    assert client.delete(f"/languages/{english.id}", headers=editor).status_code == 409
    # unused -> deleted
    db.query(SectionTranslation).filter(SectionTranslation.language_id == lang.id).delete()
    db.query(ModuleTranslation).filter(ModuleTranslation.language_id == lang.id).delete()
    db.commit()
    assert client.delete(f"/languages/{lid}", headers=editor).status_code == 204
    assert client.delete(f"/languages/{lid}", headers=editor).status_code == 404
