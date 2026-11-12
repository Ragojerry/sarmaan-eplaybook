"""
Mobile app interface text: registry seeding, translation editing with placeholder
checks, the governance workflow and its permissions, import/export, and the phone
sync with English fallback and "changed since".

Uses the throw-away language "zz", test-only keys ("zztest.*") and obviously fake
"[zz]" text: this verifies the PLUMBING only. Real translations come from people.

    cd backend && python -m pytest tests/test_app_strings.py -v
"""
import csv
import io
import json
import time

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.l10n.seed import load_catalog, seed
from app.main import app
from app.models import AppString, AppStringTranslation, AuditLog, Language, RefreshToken
from app.models.enums import LanguageStatus, RoleName
from tests.test_content import _auth_headers, _login, _make_user

client = TestClient(app)
PREFIX = "zztest."
CATALOG = {
    "zztest.hello": {"en": "Hello {name}", "note": "Test greeting"},
    "zztest.count": {"en": "{count} items", "en_one": "{count} item", "note": "Test plural"},
    "zztest.plain": {"en": "Plain", "note": "Test plain"},
}


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def env(db):
    english = db.query(Language).filter_by(code="en").one()
    lang = Language(code="zz", name="Test language", native_name="Test", status=LanguageStatus.NOT_STARTED, is_default=False)
    db.add(lang)
    db.commit()
    seed(db, CATALOG, only_prefix=PREFIX)
    users = {
        "admin": _make_user(db, RoleName.CONTENT_ADMIN, english.id),
        "loc": _make_user(db, RoleName.LOCALISATION_REVIEWER, english.id),
        "loc2": _make_user(db, RoleName.LOCALISATION_REVIEWER, english.id),
        "prog": _make_user(db, RoleName.PROGRAM_REVIEWER, english.id),
        "tech": _make_user(db, RoleName.TECHNICAL_REVIEWER, english.id),
        "cdd": _make_user(db, RoleName.CDD, english.id),
    }
    headers = {k: _auth_headers(_login(u.username)) for k, u in users.items()}
    yield {"lang": lang, "users": users, "h": headers}
    db.rollback()
    ids = [u.id for u in users.values()]
    db.query(AppStringTranslation).filter_by(language_id=lang.id).delete()
    db.query(AppString).filter(AppString.key.like(PREFIX + "%")).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.entity_type == "app_string_registry", AuditLog.user_id.is_(None),
                              AuditLog.details["created"].astext.like('%zztest.%')).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id.in_(ids)).delete(synchronize_session=False)
    for u in users.values():
        db.delete(db.merge(u))
    db.delete(db.merge(lang))
    db.commit()


def _edit(h, key, text, text_one=None):
    return client.put(f"/app-strings/{key}/translations/zz", headers=h, json={"text": text, "text_one": text_one})


def _item(h, key, show="all"):
    r = client.get("/app-strings", headers=h, params={"language": "zz", "show": show})
    assert r.status_code == 200, r.text
    return next((i for i in r.json()["items"] if i["key"] == key), None)


def _publish(env, key):
    """admin submits, programme -> localisation -> technical (each a different person)."""
    h = env["h"]
    tid = _item(h["admin"], key)["translation_id"]
    for who, action in (("admin", "submit-review"), ("prog", "approve"), ("loc2", "approve"), ("tech", "approve")):
        r = client.post(f"/app-strings/translations/{tid}/{action}", headers=h[who])
        assert r.status_code == 200, (who, r.text)
    return tid


def _sync(since=None):
    r = client.get("/sync/app-strings", params={"language": "zz", **({"since": since} if since else {})})
    assert r.status_code == 200, r.text
    return r.json()


def test_english_fallback_only_published_text_reaches_phones(env):
    h = env["h"]
    assert _sync()["strings"] == [], "nothing published: phones keep English"
    assert _edit(h["admin"], "zztest.hello", "[zz] Hello {name}").status_code == 200
    assert _sync()["strings"] == [], "a DRAFT is never sent"
    _publish(env, "zztest.hello")
    assert _sync()["strings"] == [{"key": "zztest.hello", "text": "[zz] Hello {name}", "text_one": None}]
    # editing a published string keeps the approved text on phones until re-published
    assert _edit(h["loc"], "zztest.hello", "[zz] Hi {name}").json()["item"]["status"] == "DRAFT"
    assert _sync()["strings"][0]["text"] == "[zz] Hello {name}"
    item = _item(h["admin"], "zztest.hello")
    assert item["text"] == "[zz] Hi {name}" and item["published_text"] == "[zz] Hello {name}"


def test_workflow_roles_self_review_and_audit(env, db):
    h, users = env["h"], env["users"]
    assert client.get("/app-strings", headers=h["cdd"], params={"language": "zz"}).status_code == 403
    assert _edit(h["prog"], "zztest.plain", "[zz] Plain").status_code == 403, "reviewers outside localisation do not edit"
    assert _edit(h["cdd"], "zztest.plain", "[zz] Plain").status_code == 403
    assert _edit(h["loc"], "zztest.plain", "[zz] Plain").status_code == 200, "the localisation reviewer may translate"
    tid = _item(h["admin"], "zztest.plain")["translation_id"]
    post = lambda who, action, **kw: client.post(f"/app-strings/translations/{tid}/{action}", headers=h[who], **kw)

    assert post("loc", "submit-review").status_code == 403, "DRAFT -> review is the content admin's step (unchanged)"
    assert post("admin", "submit-review").status_code == 200
    assert post("tech", "approve").status_code == 403, "wrong stage for this role"
    assert post("prog", "approve").status_code == 200
    r = post("loc", "approve")
    assert r.status_code == 403 and "another reviewer" in r.json()["detail"], "nobody approves their own edit"
    assert post("loc2", "approve").status_code == 200
    assert post("tech", "approve").json()["status"] == "PUBLISHED"
    assert post("tech", "approve").status_code == 409, "already published"

    # reject sends it to REJECTED; an edit starts it again from DRAFT
    _edit(h["admin"], "zztest.plain", "[zz] Plain 2")
    post("admin", "submit-review")
    r = post("prog", "reject", json={"reason": "wording"})
    assert r.status_code == 200 and r.json()["status"] == "REJECTED"
    assert _edit(h["admin"], "zztest.plain", "[zz] Plain 3").json()["item"]["status"] == "DRAFT"

    actions = [a.action.value for a in db.query(AuditLog).filter_by(entity_type="app_string_translation", entity_id=tid)
               .order_by(AuditLog.created_at)]
    assert actions.count("CONTENT_EDIT") == 3
    assert {"CONTENT_REVIEW", "CONTENT_APPROVE", "CONTENT_REJECT"} <= set(actions)


def test_placeholder_and_plural_validation(env):
    h = env["h"]["admin"]
    r = _edit(h, "zztest.hello", "[zz] Hello {nmae}")
    assert r.status_code == 422 and "{nmae}" in r.json()["detail"]["errors"][0]
    r = _edit(h, "zztest.hello", "[zz] Hello")
    assert r.status_code == 200 and "{name}" in r.json()["warnings"][0], "a left-out placeholder is a warning"
    assert _edit(h, "zztest.count", "[zz] {count} many").status_code == 422, "plural needs both forms"
    assert _edit(h, "zztest.plain", "[zz] x", "[zz] y").status_code == 422, "no singular for a non-plural string"
    assert _edit(h, "zztest.plain", "   ").status_code == 422
    r = _edit(h, "zztest.count", "[zz] {count} many", "[zz] {count} one")
    assert r.status_code == 200 and r.json()["warnings"] == []
    assert _edit(h, "zztest.unknown", "[zz]").status_code == 404
    assert client.put("/app-strings/zztest.plain/translations/en", headers=h, json={"text": "x"}).status_code == 400


def test_needs_update_when_the_english_changes(env, db):
    h = env["h"]
    _edit(h["admin"], "zztest.hello", "[zz] Hello {name}")
    _publish(env, "zztest.hello")
    assert _item(h["admin"], "zztest.hello")["needs_update"] is False
    changed = dict(CATALOG, **{"zztest.hello": {"en": "Good day {name}", "note": "Test greeting"}})
    assert seed(db, changed, only_prefix=PREFIX)["updated"] == ["zztest.hello"]
    item = _item(h["admin"], "zztest.hello", show="needs_update")
    assert item and item["needs_update"] is True
    assert _sync()["strings"][0]["text"] == "[zz] Hello {name}", "still published until re-translated"
    _edit(h["admin"], "zztest.hello", "[zz] Good day {name}")
    assert _item(h["admin"], "zztest.hello")["needs_update"] is False
    stats = next(l for l in client.get("/app-strings/stats", headers=h["admin"]).json()["languages"] if l["language"] == "zz")
    assert stats["translated"] >= 1 and stats["published"] >= 1 and stats["needs_update"] == 0


def test_import_export_round_trip_csv_and_json(env):
    h = env["h"]
    r = client.get("/app-strings/export", headers=h["loc"], params={"language": "zz"})
    assert r.status_code == 200 and r.text.startswith("﻿")
    rows = {row["key"]: row for row in csv.DictReader(io.StringIO(r.text.lstrip("﻿")))}
    assert rows["zztest.hello"]["placeholders"] == "{name}" and rows["zztest.count"]["english_singular"] == "{count} item"

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(next(iter(rows.values())).keys()))
    w.writeheader()
    for key, row in rows.items():
        if key == "zztest.hello":
            row["translation"] = "[zz] Hello {name}"
        if key == "zztest.count":
            row["translation"], row["translation_singular"] = "[zz] {count} many", "[zz] {count} one"
        w.writerow(row)
    up = lambda data, name="t.csv": client.post("/app-strings/import", headers=h["loc"], params={"language": "zz"},
                                                files={"file": (name, data.encode("utf-8"), "text/csv")})
    r = up(buf.getvalue())
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 2
    assert up(buf.getvalue()).json()["unchanged"] == 2, "importing the same file again changes nothing"
    assert _item(h["admin"], "zztest.count")["text_one"] == "[zz] {count} one"

    data = json.loads(client.get("/app-strings/export", headers=h["loc"], params={"language": "zz", "format": "json"}).text)
    by_key = {s["key"]: s for s in data["strings"]}
    assert by_key["zztest.hello"]["translation"] == "[zz] Hello {name}"
    by_key["zztest.plain"]["translation"] = "[zz] Plain"
    r = up(json.dumps(data), "t.json")
    assert r.status_code == 200 and r.json()["created"] == 1 and r.json()["unchanged"] == 2


def test_a_bad_file_is_rejected_whole_with_every_problem_listed(env):
    h = env["h"]["admin"]
    bad = "key,translation,translation_singular\nzztest.plain,[zz] ok,\nzztest.nope,[zz] x,\nzztest.hello,[zz] {nam},\n"
    r = client.post("/app-strings/import", headers=h, params={"language": "zz"},
                    files={"file": ("t.csv", bad.encode(), "text/csv")})
    assert r.status_code == 422
    problems = r.json()["detail"]["problems"]
    assert {p["key"] for p in problems} == {"zztest.nope", "zztest.hello"}
    assert {p["row"] for p in problems} == {3, 4}
    assert _item(h, "zztest.plain")["translation_id"] is None, "the good row was not imported either"
    r = client.post("/app-strings/import", headers=h, params={"language": "zz"},
                    files={"file": ("t.csv", b"name,value\na,b\n", "text/csv")})
    assert r.status_code == 422
    r = client.post("/app-strings/import", headers=env["h"]["prog"], params={"language": "zz"},
                    files={"file": ("t.csv", bad.encode(), "text/csv")})
    assert r.status_code == 403


def test_sync_changed_since_removed_keys_and_repeats(env, db):
    h = env["h"]
    _edit(h["admin"], "zztest.hello", "[zz] Hello {name}")
    _publish(env, "zztest.hello")
    first = _sync()
    assert first["full"] is True and [s["key"] for s in first["strings"]] == ["zztest.hello"]
    since = first["server_time"]
    time.sleep(0.05)
    _edit(h["admin"], "zztest.count", "[zz] {count} many", "[zz] {count} one")
    _publish(env, "zztest.count")
    later = _sync(since)
    assert later["full"] is False
    assert {"key": "zztest.count", "text": "[zz] {count} many", "text_one": "[zz] {count} one"} in later["strings"]
    # a string the app no longer uses is retired and listed as removed
    retired = {k: v for k, v in CATALOG.items() if k != "zztest.hello"}
    assert seed(db, retired, only_prefix=PREFIX)["retired"] == ["zztest.hello"]
    again = _sync(since)
    assert "zztest.hello" in again["removed"]
    assert "zztest.hello" not in [s["key"] for s in again["strings"]]
    assert _sync(since)["strings"] == again["strings"], "asking twice gives the same answer"
    assert client.get("/sync/app-strings", params={"language": "en"}).json()["strings"] == []
    assert client.get("/sync/app-strings", params={"language": "qq"}).status_code == 404


def test_bulk_moves_all_or_nothing(env):
    h = env["h"]
    _edit(h["admin"], "zztest.plain", "[zz] Plain")
    _edit(h["loc"], "zztest.hello", "[zz] Hello {name}")
    ids = [_item(h["admin"], k)["translation_id"] for k in ("zztest.plain", "zztest.hello")]
    assert client.post("/app-strings/translations/bulk", headers=h["admin"],
                       json={"action": "submit-review", "ids": ids}).json() == {"moved": 2}
    assert client.post("/app-strings/translations/bulk", headers=h["prog"], json={"action": "approve", "ids": ids}).status_code == 200
    r = client.post("/app-strings/translations/bulk", headers=h["loc"], json={"action": "approve", "ids": ids})
    assert r.status_code == 409, "loc edited zztest.hello, so the whole batch is refused"
    assert [p["key"] for p in r.json()["detail"]["problems"]] == ["zztest.hello"]
    assert _item(h["admin"], "zztest.plain")["status"] == "LOCALISATION_REVIEW", "nothing moved"


def test_seed_is_idempotent_and_restores_returning_keys(env, db):
    assert seed(db, CATALOG, only_prefix=PREFIX)["unchanged"] == len(CATALOG)
    seed(db, {k: v for k, v in CATALOG.items() if k != "zztest.plain"}, only_prefix=PREFIX)
    assert db.query(AppString).filter_by(key="zztest.plain").one().retired_at is not None
    back = seed(db, CATALOG, only_prefix=PREFIX)
    assert back["restored"] == ["zztest.plain"] and not back["created"]
    # the app's real catalogue: a second run changes nothing
    real = load_catalog()
    seed(db, real)
    again = seed(db, real)
    assert again["unchanged"] == len(real) and not (again["created"] or again["updated"] or again["retired"])


def test_a_language_with_app_text_translations_cannot_be_deleted(env):
    _edit(env["h"]["admin"], "zztest.plain", "[zz] Plain")
    r = client.delete(f"/languages/{env['lang'].id}", headers=env["h"]["admin"])
    assert r.status_code == 409
