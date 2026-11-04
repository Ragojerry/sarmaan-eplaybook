"""
Phase 12 tests: idempotent, per-item-result sync uploads and the release
package. Real Postgres, same as the other suites.

    cd backend && python3 -m pytest tests/test_sync.py -v
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.auth.security import hash_password  # noqa: F401
from app.database import SessionLocal
from app.main import app
from app.models import (
    AiQuestionLog,
    AnalyticsEvent,
    AuditLog,
    ContentChunk,
    ContentRelease,
    Language,
    Module,
    QuizAttempt,
    QuizQuestion,
    RefreshToken,
    TestException,
    User,
    UserModuleProgress,
)
from app.models.enums import ModuleStatus, ReleaseStatus, RoleName
from app.releases.packager import package_path
from tests.test_content import _auth_headers, _login, _make_user

client = TestClient(app)
NOW = datetime.now(timezone.utc)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


def _cleanup(db, user, device_ids=()):
    db.query(TestException).filter((TestException.user_id == user.id) | (TestException.approved_by == user.id)).delete()
    db.query(QuizAttempt).filter_by(user_id=user.id).delete()
    db.query(UserModuleProgress).filter_by(user_id=user.id).delete()
    db.query(AiQuestionLog).filter_by(user_id=user.id).delete()
    db.query(AnalyticsEvent).filter_by(user_id=user.id).delete()
    db.query(ContentRelease).filter_by(created_by=user.id).update({"created_by": None})
    db.query(ContentRelease).filter_by(approved_by=user.id).update({"approved_by": None})
    db.query(RefreshToken).filter_by(user_id=user.id).delete()
    db.query(AuditLog).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()


@pytest.fixture()
def cdd(db):
    english = db.query(Language).filter_by(code="en").one()
    user = _make_user(db, RoleName.CDD, english.id)
    yield user, _auth_headers(_login(user.username))
    _cleanup(db, user)


@pytest.fixture()
def module_id(db):
    return str(db.query(Module).first().id)


def _prog(module_id, pct, completed=False, opened=None, section="s1"):
    return {
        "module_id": module_id,
        "progress_percent": pct,
        "completed": completed,
        "last_section": section,
        "last_opened_at": (opened or NOW).isoformat(),
        "completed_at": NOW.isoformat() if completed else None,
    }


def _post(path, headers, device, items):
    r = client.post(path, headers=headers, json={"device_id": device, "items": items})
    assert r.status_code == 200, r.text
    return r.json()["results"]


# ---------- progress ----------


def test_progress_create_then_resend_is_safe(cdd, db, module_id):
    user, h = cdd
    res = _post("/sync/progress", h, "dev-1", [_prog(module_id, 40)])
    assert res[0]["status"] == "ok"
    _post("/sync/progress", h, "dev-1", [_prog(module_id, 40)])
    rows = db.query(UserModuleProgress).filter_by(user_id=user.id).all()
    assert len(rows) == 1 and rows[0].progress_percent == 40


def test_progress_older_write_does_not_overwrite_newer(cdd, db, module_id):
    user, h = cdd
    _post("/sync/progress", h, "dev-1", [_prog(module_id, 80, opened=NOW)])
    _post("/sync/progress", h, "dev-2", [_prog(module_id, 20, opened=NOW - timedelta(hours=3))])
    db.expire_all()
    row = db.query(UserModuleProgress).filter_by(user_id=user.id).one()
    assert row.progress_percent == 80


def test_completed_never_uncompletes(cdd, db):
    user, h = cdd
    # A first-in-order module without a quiz completes directly (quiz modules: test_learning.py).
    m = Module(module_code=f"TU{uuid.uuid4().hex[:6]}", module_number=990, title="No quiz",
               status=ModuleStatus.PUBLISHED, sort_order=-1000)
    db.add(m)
    db.commit()
    module_id = str(m.id)
    try:
        _post("/sync/progress", h, "dev-1", [_prog(module_id, 100, completed=True, opened=NOW - timedelta(hours=1))])
        # A newer but not-completed record from another device (e.g. re-opened to re-read).
        _post("/sync/progress", h, "dev-2", [_prog(module_id, 30, completed=False, opened=NOW)])
        db.expire_all()
        row = db.query(UserModuleProgress).filter_by(user_id=user.id).one()
        assert row.completed is True and row.progress_percent == 100 and row.completed_at is not None
    finally:
        db.query(UserModuleProgress).filter_by(module_id=m.id).delete()
        db.delete(db.get(Module, m.id))
        db.commit()


def test_progress_unknown_module_rejected_but_others_land(cdd, db, module_id):
    user, h = cdd
    res = _post("/sync/progress", h, "dev-1", [_prog(str(uuid.uuid4()), 10), _prog(module_id, 50)])
    assert res[0]["status"] == "rejected" and res[1]["status"] == "ok"
    assert db.query(UserModuleProgress).filter_by(user_id=user.id).count() == 1


# ---------- AI questions ----------


def _q(cid, text="what dose for 4 months?", matched=True):
    return {
        "client_id": cid,
        "question": text,
        "answer": "3-4 months: 4 ml" if matched else None,
        "matched": matched,
        "confidence": 0.9,
        "language": "en",
        "asked_at": NOW.isoformat(),
    }


def test_ai_questions_idempotent(cdd, db):
    user, h = cdd
    cid = uuid.uuid4().hex
    assert _post("/sync/ai-questions", h, "dev-1", [_q(cid)])[0]["status"] == "ok"
    assert _post("/sync/ai-questions", h, "dev-1", [_q(cid)])[0]["status"] == "duplicate"
    assert db.query(AiQuestionLog).filter_by(user_id=user.id).count() == 1


def test_ai_questions_batch_reports_each_item(cdd, db):
    user, h = cdd
    a, b = uuid.uuid4().hex, uuid.uuid4().hex
    _post("/sync/ai-questions", h, "dev-1", [_q(a)])
    res = _post("/sync/ai-questions", h, "dev-1", [_q(a), _q(b, matched=False)])
    assert [r["status"] for r in res] == ["duplicate", "ok"]
    assert [r["key"] for r in res] == [a, b]
    unmatched = db.query(AiQuestionLog).filter_by(user_id=user.id, client_id=b).one()
    assert unmatched.matched is False and unmatched.answer is None


def test_ai_questions_bad_module_reference_is_rejected_not_fatal(cdd, db):
    user, h = cdd
    bad = _q(uuid.uuid4().hex)
    bad["module_id"] = str(uuid.uuid4())
    good = _q(uuid.uuid4().hex)
    res = _post("/sync/ai-questions", h, "dev-1", [bad, good])
    assert res[0]["status"] == "rejected" and res[1]["status"] == "ok"


# ---------- analytics ----------


def _ev(cid, etype="MODULE_OPEN", module_id=None):
    return {"client_id": cid, "event_type": etype, "module_id": module_id, "language": "en", "occurred_at": NOW.isoformat()}


def test_analytics_idempotent_and_validates_event_type(cdd, db, module_id):
    user, h = cdd
    cid = uuid.uuid4().hex
    res = _post(
        "/sync/analytics", h, "dev-A", [_ev(cid, module_id=module_id), _ev(uuid.uuid4().hex, "CLICKED_AD")]
    )
    assert [r["status"] for r in res] == ["ok", "rejected"]
    assert _post("/sync/analytics", h, "dev-A", [_ev(cid, module_id=module_id)])[0]["status"] == "duplicate"
    assert db.query(AnalyticsEvent).filter_by(user_id=user.id).count() == 1
    # same client_id from a DIFFERENT device is a different event
    assert _post("/sync/analytics", h, "dev-B", [_ev(cid)])[0]["status"] == "ok"


def test_sync_requires_auth():
    r = client.post("/sync/progress", json={"device_id": "x", "items": []})
    assert r.status_code in (401, 403)


def test_batch_size_is_capped(cdd):
    _, h = cdd
    items = [_q(uuid.uuid4().hex) for _ in range(201)]
    r = client.post("/sync/ai-questions", headers=h, json={"device_id": "d", "items": items})
    assert r.status_code == 422


# ---------- release package ----------


@pytest.fixture()
def tech(db):
    english = db.query(Language).filter_by(code="en").one()
    user = _make_user(db, RoleName.TECHNICAL_REVIEWER, english.id)
    created = []
    yield user, _auth_headers(_login(user.username)), created
    for code in created:
        rel = db.query(ContentRelease).filter_by(release_code=code).one_or_none()
        if rel:
            db.delete(rel)
        db.commit()
        p = package_path(code)
        if p.exists():
            p.unlink()
    _cleanup(db, user)
    # publishing rebuilt the chunk table; leave it consistent for other suites
    from app.ai.indexer import rebuild_chunks

    rebuild_chunks(db)
    db.commit()


def test_publish_builds_verifiable_package_and_phone_flow(tech, cdd, db):
    user, th, created = tech
    code = f"TEST-{uuid.uuid4().hex[:8]}"
    created.append(code)
    r = client.post("/releases", headers=th, json={"release_code": code, "version": "9.9.9", "mandatory": True})
    # RELEASE_MANAGERS are CONTENT_ADMIN/TECHNICAL_REVIEWER (+SUPER_ADMIN)
    assert r.status_code == 201, r.text
    rel_id = r.json()["id"]
    pub = client.post(f"/releases/{rel_id}/publish", headers=th)
    assert pub.status_code == 200, pub.text
    assert pub.json()["checksum"] and pub.json()["package_size"] > 0

    _, ch = cdd
    cur = client.get("/sync/release/current", headers=ch, params={"installed": "OLD"}).json()
    assert cur["release"]["release_code"] == code and cur["update_available"] is True
    assert cur["release"]["mandatory"] is True
    same = client.get("/sync/release/current", headers=ch, params={"installed": code}).json()
    assert same["update_available"] is False

    dl = client.get(f"/sync/release/{code}/package", headers=ch)
    assert dl.status_code == 200
    assert hashlib.sha256(dl.content).hexdigest() == cur["release"]["checksum"]
    assert len(dl.content) == cur["release"]["package_size"]
    pkg = json.loads(dl.content)
    assert pkg["counts"]["modules"] == len(pkg["modules"]) >= 1
    assert pkg["counts"]["chunks"] == len(pkg["chunks"]) >= 1
    assert all(m["checksum"] and m["translations"] and m["sections"] for m in pkg["modules"])
    assert pkg["counts"]["sections"] == sum(len(m["sections"]) for m in pkg["modules"])


def test_rolled_back_release_is_not_offered(tech, cdd, db):
    user, th, created = tech
    code = f"TEST-{uuid.uuid4().hex[:8]}"
    created.append(code)
    rel_id = client.post("/releases", headers=th, json={"release_code": code, "version": "9.9.8"}).json()["id"]
    client.post(f"/releases/{rel_id}/publish", headers=th)
    assert client.post(f"/releases/{rel_id}/rollback", headers=th).status_code == 200
    _, ch = cdd
    assert client.get(f"/sync/release/{code}/package", headers=ch).status_code == 404
    cur = client.get("/sync/release/current", headers=ch).json()
    assert cur["release"] is None or cur["release"]["release_code"] != code


def test_publish_with_nothing_to_ship_fails_cleanly(tech, db, monkeypatch):
    user, th, created = tech
    code = f"TEST-{uuid.uuid4().hex[:8]}"
    created.append(code)
    rel_id = client.post("/releases", headers=th, json={"release_code": code, "version": "9.9.7"}).json()["id"]
    import app.routers.releases as rr

    monkeypatch.setattr(rr, "build_package", lambda d, r: {"counts": {"modules": 0}})
    resp = client.post(f"/releases/{rel_id}/publish", headers=th)
    assert resp.status_code == 422
    db.expire_all()
    assert db.query(ContentRelease).filter_by(id=rel_id).one().status != ReleaseStatus.PUBLISHED


def test_each_account_only_sees_its_own_progress(cdd, db, module_id):
    """A second learner on the same phone must start fresh, and the first
    learner must get their own progress back after signing in again."""
    _, ha = cdd
    english = db.query(Language).filter_by(code="en").one()
    other = _make_user(db, RoleName.CDD, english.id)
    try:
        hb = _auth_headers(_login(other.username))
        assert client.get("/sync/progress", headers=ha).json() == []
        _post("/sync/progress", ha, "dev-A", [_prog(module_id, 62, section="Dosing protocol")])

        mine = client.get("/sync/progress", headers=ha).json()
        assert [(p["module_id"], p["progress_percent"], p["last_section"]) for p in mine] == [
            (module_id, 62, "Dosing protocol")
        ]
        assert client.get("/sync/progress", headers=hb).json() == []  # B starts fresh
        assert client.get("/sync/progress").status_code == 401
    finally:
        _cleanup(db, other)
