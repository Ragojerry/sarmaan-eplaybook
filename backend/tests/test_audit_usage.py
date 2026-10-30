"""
Phase 13 tests: audit trail (failed logins, filters, CSV export, RBAC) and the
usage / unanswered-question reports.

    cd backend && python3 -m pytest tests/test_audit_usage.py -v
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AiQuestionLog, AnalyticsEvent, AuditLog, ContentRelease, Language, Module, RefreshToken, User, UserModuleProgress
from app.models.enums import AuditAction, RoleName
from tests.test_content import _auth_headers, _login, _make_user

client = TestClient(app)
NOW = datetime.now(timezone.utc)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


def _drop(db, user):
    db.query(UserModuleProgress).filter_by(user_id=user.id).delete()
    db.query(AiQuestionLog).filter_by(user_id=user.id).delete()
    db.query(AnalyticsEvent).filter_by(user_id=user.id).delete()
    db.query(ContentRelease).filter_by(created_by=user.id).update({"created_by": None})
    db.query(ContentRelease).filter_by(approved_by=user.id).update({"approved_by": None})
    db.query(RefreshToken).filter_by(user_id=user.id).delete()
    db.query(AuditLog).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()


def _user_fixture(db, role):
    english = db.query(Language).filter_by(code="en").one()
    return _make_user(db, role, english.id)


@pytest.fixture()
def admin(db):
    u = _user_fixture(db, RoleName.CONTENT_ADMIN)
    yield u, _auth_headers(_login(u.username))
    _drop(db, u)


@pytest.fixture()
def cdd(db):
    u = _user_fixture(db, RoleName.CDD)
    yield u, _auth_headers(_login(u.username))
    _drop(db, u)


# ---------- audit ----------


def test_failed_login_is_audited_without_the_password(db, admin):
    user, h = admin
    bad = f"nobody_{uuid.uuid4().hex[:8]}"
    r = client.post("/auth/login", json={"username": bad, "password": "SuperSecret999!"})
    assert r.status_code == 401
    r = client.post("/auth/login", json={"username": user.username, "password": "wrong-password"})
    assert r.status_code == 401
    try:
        items = client.get("/audit", headers=h, params={"action": "LOGIN_FAILED", "limit": 200}).json()["items"]
        unknown = [i for i in items if i["details"].get("username") == bad]
        known = [i for i in items if i["user_id"] == str(user.id)]
        assert len(unknown) == 1 and unknown[0]["user_id"] is None
        assert len(known) == 1 and known[0]["username"] == user.username
        assert unknown[0]["ip_address"]
        assert "SuperSecret999" not in str(items) and "wrong-password" not in str(items)
    finally:
        db.query(AuditLog).filter(AuditLog.details["username"].astext == bad).delete(synchronize_session=False)
        db.commit()


def test_successful_login_records_ip(db, admin):
    user, h = admin
    items = client.get("/audit", headers=h, params={"action": "LOGIN", "user_id": str(user.id)}).json()["items"]
    assert items and items[0]["ip_address"]


def test_audit_requires_privileged_role(cdd, admin):
    assert client.get("/audit", headers=cdd[1]).status_code == 403
    assert client.get("/audit/export.csv", headers=cdd[1]).status_code == 403
    assert client.get("/audit", headers=admin[1]).status_code == 200
    assert client.get("/audit").status_code == 401


def test_audit_filters_and_pagination(db, admin):
    user, h = admin
    for i in range(3):
        db.add(AuditLog(user_id=user.id, action=AuditAction.CONTENT_EDIT, entity_type="module_test", details={"i": i}))
    db.commit()
    page = client.get("/audit", headers=h, params={"entity_type": "module_test", "limit": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    page2 = client.get("/audit", headers=h, params={"entity_type": "module_test", "limit": 2, "offset": 2}).json()
    assert len(page2["items"]) == 1
    assert client.get("/audit", headers=h, params={"entity_type": "module_test", "action": "RELEASE_PUBLISH"}).json()["total"] == 0
    future = (NOW + timedelta(days=1)).isoformat()
    assert client.get("/audit", headers=h, params={"entity_type": "module_test", "date_from": future}).json()["total"] == 0
    assert client.get("/audit", headers=h, params={"limit": 1000}).status_code == 422
    assert client.get("/audit", headers=h, params={"action": "NOT_AN_ACTION"}).status_code == 422
    assert "LOGIN_FAILED" in client.get("/audit/actions", headers=h).json()


def test_csv_export_neutralises_formulas(db, admin):
    user, h = admin
    evil = f"=HYPERLINK(\"http://x\")_{uuid.uuid4().hex[:6]}"
    client.post("/auth/login", json={"username": evil, "password": "x"})
    try:
        r = client.get("/audit/export.csv", headers=h, params={"action": "LOGIN_FAILED"})
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
        lines = r.text.splitlines()
        assert lines[0].startswith("time_utc,action,user,role")
        import csv, io
        cells = [c for row in csv.reader(io.StringIO(r.text)) for c in row]
        assert any("=HYPERLINK" in c for c in cells)  # the attempt is in the export...
        assert not any(c[:1] in ("=", "+", "-", "@") for c in cells)  # ...but never as a live formula cell
    finally:
        db.query(AuditLog).filter(AuditLog.details["username"].astext == evil[:100]).delete(synchronize_session=False)
        db.commit()


# ---------- usage ----------


def _events(h, device, items):
    r = client.post("/sync/analytics", headers=h, json={"device_id": device, "items": items})
    assert r.status_code == 200, r.text
    return r.json()["results"]


def _ev(etype, module_id=None, payload=None, language="en", when=None):
    return {
        "client_id": uuid.uuid4().hex,
        "event_type": etype,
        "module_id": module_id,
        "language": language,
        "payload": payload or {},
        "occurred_at": (when or NOW).isoformat(),
    }


def test_usage_requires_non_cdd_role(cdd, admin):
    assert client.get("/analytics/usage", headers=cdd[1]).status_code == 403
    assert client.get("/analytics/questions", headers=cdd[1]).status_code == 403
    assert client.get("/analytics/usage", headers=admin[1]).status_code == 200


def test_usage_report_counts_real_events(db, admin, cdd):
    _, ah = admin
    _, ch = cdd
    module_id = str(db.query(Module).first().id)
    before = client.get("/analytics/usage", headers=ah, params={"days": 7}).json()
    dev = f"dev-{uuid.uuid4().hex[:6]}"
    _events(ch, dev, [
        _ev("MODULE_OPEN", module_id), _ev("MODULE_OPEN", module_id), _ev("MODULE_COMPLETE", module_id),
        _ev("APPLICATION_ERROR", payload={"type": "StateError"}), _ev("DOWNLOAD_FAILED"),
        _ev("DEVICE_HEARTBEAT", language="ha"),
    ])
    after = client.get("/analytics/usage", headers=ah, params={"days": 7}).json()

    assert len(after["daily"]) == 8 and after["daily"][-1]["date"] == NOW.date().isoformat()
    assert after["devices"]["active_1d"] == before["devices"]["active_1d"] + 1
    mod = lambda rep: next(m for m in rep["modules"] if m["module_id"] == module_id)
    assert mod(after)["opens"] == mod(before)["opens"] + 2
    assert mod(after)["completions"] == mod(before)["completions"] + 1
    assert after["technical"]["app_errors"] == before["technical"]["app_errors"] + 1
    assert after["technical"]["download_failures"] == before["technical"]["download_failures"] + 1
    lang = lambda rep: next((l["count"] for l in rep["languages"] if l["language_code"] == "ha"), 0)
    assert lang(after) == lang(before) + 1
    assert client.get("/analytics/usage", headers=ah, params={"days": 0}).status_code == 422


def test_release_adoption_counts_distinct_devices(db, admin, cdd):
    _, ah = admin
    _, ch = cdd
    code = f"ADOPT-{uuid.uuid4().hex[:6]}"
    _events(ch, "dev-a", [_ev("UPDATE_INSTALLED", payload={"release_code": code}), _ev("UPDATE_INSTALLED", payload={"release_code": code})])
    _events(ch, "dev-b", [_ev("UPDATE_INSTALLED", payload={"release_code": code})])
    rep = client.get("/analytics/usage", headers=ah).json()
    row = next(r for r in rep["release_adoption"] if r["release_code"] == code)
    assert row["devices"] == 2  # two devices, three events


def test_questions_report_groups_case_insensitively(db, admin, cdd):
    _, ah = admin
    _, ch = cdd
    q = f"zzgap {uuid.uuid4().hex[:6]}?"
    items = [
        {"client_id": uuid.uuid4().hex, "question": text, "matched": False, "language": "en", "asked_at": NOW.isoformat()}
        for text in (q, q.upper(), f"  {q}  ")
    ]
    items.append({"client_id": uuid.uuid4().hex, "question": "what is the dose?", "answer": "x", "matched": True, "language": "en", "asked_at": NOW.isoformat()})
    r = client.post("/sync/ai-questions", headers=ch, json={"device_id": "d", "items": items})
    assert r.status_code == 200
    rep = client.get("/analytics/questions", headers=ah, params={"limit": 100}).json()
    row = next(x for x in rep["top_unanswered"] if x["question"] == q.lower())
    assert row["count"] == 3
    assert rep["total"] == rep["matched"] + rep["unmatched"] and rep["unmatched"] >= 3
    assert 0 <= rep["answer_rate_percent"] <= 100
    assert any(x["question"] == "what is the dose?" for x in rep["top_answered"])


def test_csv_safe_prefixes_formula_cells():
    from app.routers.audit import _csv_safe

    assert _csv_safe("=1+1") == "'=1+1"
    assert _csv_safe("+cmd") == "'+cmd" and _csv_safe("@x") == "'@x" and _csv_safe("-5") == "'-5"
    assert _csv_safe("hello") == "hello" and _csv_safe(None) == ""
