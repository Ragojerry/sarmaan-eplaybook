"""User administration + team code (SUPER_ADMIN only)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, Language, RefreshToken, User
from app.models.enums import AuditAction, RoleName
from tests.test_content import _auth_headers, _login, _make_user

client = TestClient(app)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def actors(db):
    english = db.query(Language).filter_by(code="en").one()
    admin = _make_user(db, RoleName.SUPER_ADMIN, english.id)
    cdd = _make_user(db, RoleName.CDD, english.id)
    made = []
    yield admin, cdd, made, _auth_headers(_login(admin.username)), _auth_headers(_login(cdd.username))
    db.rollback()
    ids = [admin.id, cdd.id] + made
    db.query(AuditLog).filter(AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()


def test_create_user_with_team_code_and_me_returns_it(actors, db):
    admin, cdd, made, ah, _ = actors
    name = f"cdd_{uuid.uuid4().hex[:8]}"
    r = client.post("/users", headers=ah, json={
        "username": name, "email": f"{name}@sarmaan-eplaybook.app", "password": "LongEnough123!",
        "first_name": "Aisha", "last_name": "Bello", "team_code": "0041",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    made.append(uuid.UUID(body["id"]))
    assert body["team_code"] == "0041" and body["role"] == "CDD" and "password" not in str(body).lower().replace("password_hash", "")
    me = client.get("/auth/me", headers=_auth_headers(_login(name, "LongEnough123!")))
    assert me.status_code == 200 and me.json()["team_code"] == "0041"
    assert db.query(AuditLog).filter_by(entity_id=uuid.UUID(body["id"]), action=AuditAction.USER_CREATE).count() == 1


def test_update_team_code_audited_and_clearable(actors, db):
    admin, cdd, _, ah, _ = actors
    r = client.patch(f"/users/{cdd.id}", headers=ah, json={"team_code": "0099"})
    assert r.status_code == 200 and r.json()["team_code"] == "0099"
    assert db.query(AuditLog).filter_by(entity_id=cdd.id, action=AuditAction.USER_UPDATE).count() == 1
    assert client.patch(f"/users/{cdd.id}", headers=ah, json={"team_code": ""}).json()["team_code"] is None
    assert client.get("/users", headers=ah, params={"team_code": "0099"}).json() == []


def test_validation_and_safety_rules(actors):
    admin, cdd, _, ah, ch = actors
    assert client.patch(f"/users/{cdd.id}", headers=ah, json={"team_code": "bad code!"}).status_code == 422
    assert client.patch(f"/users/{admin.id}", headers=ah, json={"role": "CDD"}).status_code == 400
    assert client.patch(f"/users/{admin.id}", headers=ah, json={"status": "INACTIVE"}).status_code == 400
    assert client.patch(f"/users/{uuid.uuid4()}", headers=ah, json={"team_code": "1"}).status_code == 404
    dup = {"username": cdd.username, "email": "x@sarmaan-eplaybook.app", "password": "LongEnough123!",
           "first_name": "A", "last_name": "B"}
    assert client.post("/users", headers=ah, json=dup).status_code == 409
    short = {**dup, "username": "newone", "password": "short"}
    assert client.post("/users", headers=ah, json=short).status_code == 422


def test_only_super_admin_can_manage_users(actors):
    _, cdd, _, _, ch = actors
    assert client.get("/users", headers=ch).status_code == 403
    assert client.patch(f"/users/{cdd.id}", headers=ch, json={"team_code": "1"}).status_code == 403
    assert client.get("/users").status_code == 401
