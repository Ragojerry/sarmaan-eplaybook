"""Item 2: deactivating and reactivating users: login, token refresh and sync are
refused with a recognisable answer, refresh tokens are revoked at once, all data
is kept, the self and last-super-admin protections, permissions and the audit trail."""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.account import ACCOUNT_STATUS_HEADER, DEACTIVATED_MESSAGE
from app.auth.security import hash_password
from app.database import SessionLocal, engine
from app.main import app
from app.models import AuditLog, Language, Module, RefreshToken, User, UserModuleProgress
from app.models.enums import AuditAction, LearnerRole, ModuleStatus, RoleName, UserStatus
from app.routers import users as users_router

client = TestClient(app)


def _make_user(db, role, learner_role=None):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_deact_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(username=username, email=f"{username}@sarmaan-eplaybook.app", password_hash=hash_password("TestPass123!"),
                first_name="Test", last_name=role.value, role=role, learner_role=learner_role, language_id=english.id,
                status=UserStatus.ACTIVE)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _tokens(user):
    resp = client.post("/auth/login", json={"username": user.username, "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _h(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def users():
    db = SessionLocal()
    made = {"admin": _make_user(db, RoleName.SUPER_ADMIN), "content": _make_user(db, RoleName.CONTENT_ADMIN),
            "learner": _make_user(db, RoleName.CDD, LearnerRole.CDD)}
    yield made
    ids = [u.id for u in made.values()]
    db.query(User).filter(User.id.in_(ids)).update({User.deactivated_by: None}, synchronize_session=False)
    for model in (UserModuleProgress, RefreshToken, AuditLog):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def _deactivated(resp, code):
    assert resp.status_code == code, resp.text
    assert resp.headers.get(ACCOUNT_STATUS_HEADER) == "deactivated"
    assert resp.json()["detail"] == DEACTIVATED_MESSAGE


def test_deactivation_blocks_login_refresh_and_sync_and_keeps_data(users):
    admin = _h(_tokens(users["admin"]))
    learner = users["learner"]
    tokens = _tokens(learner)
    second = _tokens(learner)  # another phone
    db = SessionLocal()
    module = db.query(Module).filter_by(status=ModuleStatus.PUBLISHED).order_by(Module.sort_order).first()
    db.add(UserModuleProgress(user_id=learner.id, module_id=module.id, progress_percent=40, completed=False))
    db.commit()
    db.close()

    resp = client.post(f"/users/{learner.id}/deactivate", headers=admin, json={"reason": "Left the programme"})
    assert resp.status_code == 200 and resp.json()["status"] == "INACTIVE"
    assert resp.json()["deactivation_reason"] == "Left the programme" and resp.json()["deactivated_at"]

    db = SessionLocal()
    assert all(t.revoked for t in db.query(RefreshToken).filter_by(user_id=learner.id)), "every refresh token revoked at once"
    (log,) = db.query(AuditLog).filter_by(action=AuditAction.USER_DEACTIVATE, entity_id=learner.id).all()
    assert log.user_id == users["admin"].id and log.details["reason"] == "Left the programme"
    assert log.details["refresh_tokens_revoked"] == 2
    db.close()

    _deactivated(client.post("/auth/login", json={"username": learner.username, "password": "TestPass123!"}), 403)
    _deactivated(client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}), 401)
    _deactivated(client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]}), 401)
    _deactivated(client.post("/sync/progress", headers=_h(tokens), json={"device_id": "dev", "items": []}), 401)
    _deactivated(client.get("/sync/learning", headers=_h(tokens)), 401)

    db = SessionLocal()
    assert db.query(UserModuleProgress).filter_by(user_id=learner.id).count() == 1, "data kept"
    db.close()

    resp = client.post(f"/users/{learner.id}/reactivate", headers=admin, json={"reason": "Back for round 2"})
    assert resp.status_code == 200 and resp.json()["status"] == "ACTIVE" and resp.json()["deactivation_reason"] is None
    fresh = _tokens(learner)
    assert client.get("/sync/progress", headers=_h(fresh)).json()[0]["progress_percent"] == 40, "progress intact"
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401, "old tokens stay revoked"
    db = SessionLocal()
    (log,) = db.query(AuditLog).filter_by(action=AuditAction.USER_REACTIVATE, entity_id=learner.id).all()
    assert log.details["reason"] == "Back for round 2"
    db.close()


def test_protections_and_permissions(users):
    admin_user = users["admin"]
    admin = _h(_tokens(admin_user))
    content = _h(_tokens(users["content"]))
    resp = client.post(f"/users/{admin_user.id}/deactivate", headers=admin, json={})
    assert resp.status_code == 400 and "your own account" in resp.json()["detail"]
    assert client.patch(f"/users/{admin_user.id}", headers=admin, json={"status": "INACTIVE"}).status_code == 400
    assert client.post(f"/users/{users['learner'].id}/deactivate", headers=content).status_code == 403
    assert client.post(f"/users/{uuid.uuid4()}/deactivate", headers=admin).status_code == 404

    # Changing the status through the general edit follows the same rules and audit.
    learner = users["learner"]
    tokens = _tokens(learner)
    assert client.patch(f"/users/{learner.id}", headers=admin, json={"status": "INACTIVE"}).json()["status"] == "INACTIVE"
    _deactivated(client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}), 401)
    db = SessionLocal()
    assert db.query(AuditLog).filter_by(action=AuditAction.USER_DEACTIVATE, entity_id=learner.id).count() == 1
    db.close()


def test_the_last_active_super_admin_cannot_be_deactivated(users):
    # In a transaction that is rolled back: make the test admin the only active super admin.
    conn = engine.connect()
    outer = conn.begin()
    db = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        target = db.get(User, users["admin"].id)
        actor = db.get(User, users["content"].id)
        db.query(User).filter(User.role == RoleName.SUPER_ADMIN, User.id != target.id).update(
            {User.status: UserStatus.INACTIVE}, synchronize_session=False)
        db.flush()
        with pytest.raises(HTTPException) as e:
            users_router._set_status(db, target, actor, UserStatus.INACTIVE, None)
        assert e.value.status_code == 409 and "last active super admin" in e.value.detail
        # With a second active super admin it is allowed.
        other = db.get(User, users["learner"].id)
        other.role, other.status = RoleName.SUPER_ADMIN, UserStatus.ACTIVE
        db.flush()
        assert users_router._set_status(db, target, actor, UserStatus.INACTIVE, "test") is True
    finally:
        db.close()
        outer.rollback()
        conn.close()


def test_reports_show_status_and_can_leave_deactivated_users_out(users):
    admin = _h(_tokens(users["admin"]))
    learner = users["learner"]
    client.post(f"/users/{learner.id}/deactivate", headers=admin, json={"reason": "x"})
    rows = client.get("/reports/users", headers=admin, params={"q.username": learner.username}).json()
    assert rows[0]["status"] == "INACTIVE" and rows[0]["deactivated_at"]
    assert client.get("/reports/users", headers=admin, params={"q.username": learner.username, "in.status": "ACTIVE"}).json() == []
    stamp = datetime.now(timezone.utc).date().isoformat()
    assert len(client.get("/reports/users", headers=admin, params={"q.username": learner.username, "from.deactivated_at": stamp}).json()) == 1
