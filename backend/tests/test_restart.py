"""Training restart: the newest attempt replaces the old one."""
import uuid
from datetime import datetime, timedelta, timezone

from tests.test_sessions import client, db, world  # noqa: F401  (fixtures)
from app.models import Module, QuizAttempt, UserModuleProgress, AuditLog
from app.models.enums import AuditAction, ModuleStatus


def _iso(dt):
    return dt.isoformat()


def _seed_old(db, cdd, module):
    now = datetime.now(timezone.utc)
    db.add(UserModuleProgress(user_id=cdd.id, module_id=module.id, progress_percent=100, completed=True,
                              completed_at=now - timedelta(days=2), last_opened_at=now - timedelta(days=2)))
    db.add(QuizAttempt(user_id=cdd.id, module_id=module.id, client_id=uuid.uuid4().hex, correct_count=10, total_count=10,
                       score_percent=100, passed=True, results=[], taken_at=now - timedelta(days=2)))
    db.commit()


def test_restart_replaces_old_attempt_and_is_idempotent(world, db):
    admin, cdd, tag, made, ah, ch = world
    module = db.query(Module).filter_by(status=ModuleStatus.PUBLISHED).order_by(Module.sort_order).first()
    _seed_old(db, cdd, module)
    t0 = datetime.now(timezone.utc)
    body = {"device_id": "d1", "items": [{"client_id": "r1", "restarted_at": _iso(t0)}]}
    assert client.post("/sync/training-restart", headers=ch, json=body).json()["results"][0]["status"] == "ok"
    assert client.get("/sync/progress", headers=ch).json() == []
    assert db.query(QuizAttempt).filter_by(user_id=cdd.id).count() == 0
    st = client.get("/sync/training", headers=ch).json()
    assert st["attempt"] == 2 and st["restarted_at"] is not None
    # a retry of the same upload changes nothing
    assert client.post("/sync/training-restart", headers=ch, json=body).json()["results"][0]["status"] == "duplicate"
    assert client.get("/sync/training", headers=ch).json()["attempt"] == 2
    assert db.query(AuditLog).filter_by(entity_id=cdd.id, action=AuditAction.TRAINING_RESTART).count() == 1


def test_old_data_from_before_restart_is_rejected_new_data_accepted(world, db):
    admin, cdd, tag, made, ah, ch = world
    module = db.query(Module).filter_by(status=ModuleStatus.PUBLISHED).order_by(Module.sort_order).first()
    t0 = datetime.now(timezone.utc)
    client.post("/sync/training-restart", headers=ch, json={"device_id": "d1", "items": [{"client_id": "r1", "restarted_at": _iso(t0)}]})
    old = _iso(t0 - timedelta(hours=1))
    new = _iso(t0 + timedelta(minutes=5))
    # another phone still holding the previous attempt uploads it late
    p = client.post("/sync/progress", headers=ch, json={"device_id": "d2", "items": [
        {"module_id": str(module.id), "progress_percent": 40, "last_opened_at": old}]}).json()["results"][0]
    assert p["status"] == "rejected"
    q = client.post("/sync/quiz-attempts", headers=ch, json={"device_id": "d2", "items": [
        {"client_id": "old1", "module_id": str(module.id), "correct_count": 10, "total_count": 10, "taken_at": old, "results": []}]}).json()["results"][0]
    assert q["status"] == "rejected"
    ok = client.post("/sync/progress", headers=ch, json={"device_id": "d1", "items": [
        {"module_id": str(module.id), "progress_percent": 40, "last_opened_at": new}]}).json()["results"][0]
    assert ok["status"] == "ok"
    assert client.get("/sync/progress", headers=ch).json()[0]["progress_percent"] == 40


def test_admin_reset_and_reports_show_only_latest_attempt(world, db):
    admin, cdd, tag, made, ah, ch = world
    module = db.query(Module).filter_by(status=ModuleStatus.PUBLISHED).order_by(Module.sort_order).first()
    _seed_old(db, cdd, module)
    assert client.post(f"/users/{cdd.id}/reset-training", headers=ch).status_code == 403
    r = client.post(f"/users/{cdd.id}/reset-training", headers=ah)
    assert r.status_code == 200 and r.json()["training_attempt"] == 2
    assert client.post(f"/users/{uuid.uuid4()}/reset-training", headers=ah).status_code == 404
    row = next(x for x in client.get("/reports/users", headers=ah, params={"all_roles": True}).json() if x["user_id"] == str(cdd.id))
    assert row["training_attempt"] == 2 and row["modules_completed"] == 0 and row["quiz_attempts"] == 0
    # the phone learns about it
    assert client.get("/sync/training", headers=ch).json()["attempt"] == 2
