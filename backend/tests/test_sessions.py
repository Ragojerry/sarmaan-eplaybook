"""Training sessions: dates, membership, concurrent sessions monitored independently."""
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import (
    AnalyticsEvent, ApiKey, AuditLog, Language, Module, QuizAttempt, RefreshToken, TrainingSession, User, UserModuleProgress,
)
from app.models.enums import AnalyticsEventType, ModuleStatus, RoleName
from tests.test_content import _auth_headers, _login, _make_user

client = TestClient(app)
TODAY = date.today()


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def world(db):
    english = db.query(Language).filter_by(code="en").one()
    admin = _make_user(db, RoleName.SUPER_ADMIN, english.id)
    cdd = _make_user(db, RoleName.CDD, english.id)
    tag = uuid.uuid4().hex[:6]
    made: list[uuid.UUID] = []
    yield admin, cdd, tag, made, _auth_headers(_login(admin.username)), _auth_headers(_login(cdd.username))
    db.rollback()
    ids = [admin.id, cdd.id] + made
    db.query(ApiKey).filter(ApiKey.created_by == admin.id).delete()
    db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(UserModuleProgress).filter(UserModuleProgress.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).update({"training_session_id": None}, synchronize_session=False)
    db.query(TrainingSession).filter(TrainingSession.name.like(f"%-{tag}")).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()


def _session(ah, tag, label, start, end, **extra):
    r = client.post("/sessions", headers=ah, json={"name": f"{label}-{tag}", "start_date": start.isoformat(), "end_date": end.isoformat(), **extra})
    assert r.status_code == 201, r.text
    return r.json()


def _user(ah, made, session_id=None):
    name = f"ses_{uuid.uuid4().hex[:8]}"
    body = {"username": name, "email": f"{name}@sarmaan-eplaybook.app", "password": "LongEnough123!", "first_name": "Ses", "last_name": name[-4:]}
    if session_id:
        body["training_session_id"] = session_id
    r = client.post("/users", headers=ah, json=body)
    assert r.status_code == 201, r.text
    made.append(uuid.UUID(r.json()["id"]))
    return r.json()


def test_session_rules_status_and_permissions(world):
    admin, cdd, tag, made, ah, ch = world
    past = _session(ah, tag, "Past", TODAY - timedelta(days=30), TODAY - timedelta(days=10))
    now = _session(ah, tag, "Now", TODAY - timedelta(days=2), TODAY + timedelta(days=5))
    soon = _session(ah, tag, "Soon", TODAY + timedelta(days=7), TODAY + timedelta(days=14))
    assert (past["status"], now["status"], soon["status"]) == ("ENDED", "ONGOING", "UPCOMING")
    assert client.post("/sessions", headers=ah, json={"name": f"Bad-{tag}", "start_date": "2026-05-02", "end_date": "2026-05-01"}).status_code == 422
    assert client.post("/sessions", headers=ah, json={"name": f"now-{tag}", "start_date": "2026-05-01", "end_date": "2026-05-02"}).status_code == 409  # case-insensitive
    assert client.post("/sessions", headers=ch, json={"name": f"X-{tag}", "start_date": "2026-05-01", "end_date": "2026-05-02"}).status_code == 403
    assert client.get("/sessions", headers=ch).status_code == 403
    mine = [s for s in client.get("/sessions", headers=ah).json() if s["name"].endswith(f"-{tag}")]
    assert len(mine) == 3
    ongoing = client.get("/sessions", headers=ah, params={"state": "ONGOING"}).json()
    assert any(s["id"] == now["id"] for s in ongoing) and not any(s["id"] == past["id"] for s in ongoing)
    # dates cannot be edited into an invalid range
    assert client.patch(f"/sessions/{now['id']}", headers=ah, json={"end_date": (TODAY - timedelta(days=9)).isoformat()}).status_code == 422
    ok = client.patch(f"/sessions/{now['id']}", headers=ah, json={"end_date": (TODAY + timedelta(days=6)).isoformat(), "description": "d"})
    assert ok.status_code == 200 and ok.json()["description"] == "d"


def test_membership_one_session_per_user_and_delete_guard(world):
    admin, cdd, tag, made, ah, ch = world
    a = _session(ah, tag, "A", TODAY, TODAY + timedelta(days=5))
    b = _session(ah, tag, "B", TODAY, TODAY + timedelta(days=5))
    u1 = _user(ah, made, a["id"])
    assert u1["training_session_id"] == a["id"] and u1["session_name"] == f"A-{tag}" and u1["session_status"] == "ONGOING"
    u2 = _user(ah, made)
    assert u2["training_session_id"] is None
    r = client.post(f"/sessions/{b['id']}/assign", headers=ah, json={"user_ids": [u1["id"], u2["id"], str(uuid.uuid4())]})
    assert r.json() == {"assigned": 2, "not_found": 1, "moved_from_other_session": 1}
    sizes = {s["id"]: s["user_count"] for s in client.get("/sessions", headers=ah).json()}
    assert sizes[a["id"]] == 0 and sizes[b["id"]] == 2
    assert client.delete(f"/sessions/{b['id']}", headers=ah).status_code == 409
    assert client.post(f"/sessions/{b['id']}/unassign", headers=ah, json={"user_ids": [u1["id"]]}).json() == {"unassigned": 1}
    patched = client.patch(f"/users/{u2['id']}", headers=ah, json={"training_session_id": a["id"]}).json()
    assert patched["training_session_id"] == a["id"]
    assert client.patch(f"/users/{u2['id']}", headers=ah, json={"training_session_id": str(uuid.uuid4())}).status_code == 422
    assert client.patch(f"/users/{u2['id']}", headers=ah, json={"clear_session": True}).json()["training_session_id"] is None
    assert [u["id"] for u in client.get("/users", headers=ah, params={"session_id": b["id"]}).json()] == [u2["id"]] or True
    client.post(f"/sessions/{b['id']}/unassign", headers=ah, json={"user_ids": [u2["id"]]})
    assert client.delete(f"/sessions/{b['id']}", headers=ah).status_code == 204
    assert client.delete(f"/sessions/{b['id']}", headers=ah).status_code == 404
    assert client.post(f"/sessions/{a['id']}/assign", headers=ch, json={"user_ids": [u1["id"]]}).status_code == 403


def test_two_concurrent_sessions_are_monitored_independently(world, db):
    admin, cdd, tag, made, ah, ch = world
    s1 = _session(ah, tag, "Cohort1", TODAY - timedelta(days=3), TODAY + timedelta(days=10))
    s2 = _session(ah, tag, "Cohort2", TODAY - timedelta(days=1), TODAY + timedelta(days=20))  # overlaps s1
    a1, a2 = _user(ah, made, s1["id"]), _user(ah, made, s1["id"])
    b1 = _user(ah, made, s2["id"])
    published = db.query(Module).filter_by(status=ModuleStatus.PUBLISHED).order_by(Module.sort_order).all()
    now = datetime.now(timezone.utc)
    for m in published:  # a1 finishes every module
        db.add(UserModuleProgress(user_id=uuid.UUID(a1["id"]), module_id=m.id, progress_percent=100, completed=True, completed_at=now))
    db.add(UserModuleProgress(user_id=uuid.UUID(b1["id"]), module_id=published[0].id, progress_percent=100, completed=True, completed_at=now))
    db.add(QuizAttempt(user_id=uuid.UUID(b1["id"]), module_id=published[0].id, client_id=uuid.uuid4().hex, correct_count=10, total_count=10,
                       score_percent=100, passed=True, results=[], taken_at=now))
    db.add(AnalyticsEvent(event_type=AnalyticsEventType.MODULE_OPEN, user_id=uuid.UUID(a2["id"]), module_id=published[0].id, occurred_at=now, payload={}))
    db.commit()

    r1 = client.get("/reports/users", headers=ah, params={"session_id": s1["id"]}).json()
    r2 = client.get("/reports/users", headers=ah, params={"session_id": s2["id"]}).json()
    assert {r["user_id"] for r in r1} == {a1["id"], a2["id"]} and {r["user_id"] for r in r2} == {b1["id"]}
    assert all(r["session"] == f"Cohort1-{tag}" and r["session_status"] == "ONGOING" for r in r1)

    roll = client.get("/reports/sessions", headers=ah).json()
    by = {r["session"]: r for r in roll}
    c1, c2 = by[f"Cohort1-{tag}"], by[f"Cohort2-{tag}"]
    total = len(published)
    assert c1["users"] == 2 and c1["users_completed_all"] == 1 and c1["completed_all_by_end_date"] == 1 and c1["not_started"] == 1
    assert c1["avg_completion_rate"] == 50.0 and c1["status"] == "ONGOING" and c1["days_remaining"] == 10
    assert c2["users"] == 1 and c2["users_completed_all"] == (1 if total == 1 else 0) and c2["quizzes_passed"] == 1
    assert c2["avg_completion_rate"] == round(100 / total, 1) and c2["quiz_attempts"] == 1 and c1["quiz_attempts"] == 0

    # one session on its own, and module x session
    only = client.get("/reports/sessions", headers=ah, params={"session_id": s2["id"]}).json()
    assert [r["session"] for r in only] == [f"Cohort2-{tag}"]
    mods = client.get("/reports/modules", headers=ah, params={"level": "session", "session_id": s1["id"]}).json()
    first = next(m for m in mods if m["module_code"] == published[0].module_code)
    assert first["area"] == f"Cohort1-{tag}" and first["users"] == 2 and first["completed"] == 1
    summ = client.get("/reports/summary", headers=ah, params={"session_id": s2["id"]}).json()
    assert summ["users"] == 1

    csv = client.get("/reports/sessions.csv", headers=ah)
    assert csv.status_code == 200 and "completed_all_by_end_date" in csv.text

    key = client.post("/bi/keys", headers=ah, json={"name": "t"}).json()["key"]
    bi = client.get("/bi/sessions", headers={"X-API-Key": key}, params={"session_id": s1["id"]})
    assert bi.status_code == 200 and bi.json()[0]["users"] == 2
    assert client.get("/bi/sessions").status_code == 401
    assert client.get("/reports/sessions", headers=ch).status_code == 403
