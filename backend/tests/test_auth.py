"""
Phase 4 automated tests. Requires a real Postgres+pgvector instance reachable
via DATABASE_URL (same one used for `alembic upgrade head`), with the schema
already migrated. Run:

    cd backend
    python3 -m alembic upgrade head   # if not already done
    python3 -m pytest tests/test_auth.py -v

Each test creates its own user via the ORM directly (not via scripts.seed),
so this suite doesn't depend on seed data existing, and can run repeatedly
against the same database without collisions (usernames are randomized).
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User, Language, RefreshToken
from app.models.audit_log import AuditLog
from app.models.enums import RoleName, UserStatus
from app.auth.security import hash_password

client = TestClient(app)


@pytest.fixture()
def test_user():
    db = SessionLocal()
    english = db.query(Language).filter_by(code="en").one()
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username,
        email=f"{username}@sarmaan-eplaybook.app",
        password_hash=hash_password("TestPass123!"),
        first_name="Test",
        last_name="User",
        role=RoleName.CDD,
        language_id=english.id,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user, "TestPass123!"
    # Delete dependent rows first. audit_logs.user_id and
    # refresh_tokens.user_id deliberately have NO cascade-delete in the
    # schema (audit trails must survive even after a user account is
    # deleted — that's correct production behavior, not a bug) so test
    # cleanup has to remove them explicitly in FK order.
    db.query(AuditLog).filter_by(user_id=user.id).delete()
    db.query(RefreshToken).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()
    db.close()


def test_login_wrong_password_rejected(test_user):
    user, _ = test_user
    resp = client.post("/auth/login", json={"username": user.username, "password": "wrong"})
    assert resp.status_code == 401


def test_login_success_returns_tokens(test_user):
    user, password = test_user
    resp = client.post("/auth/login", json={"username": user.username, "password": password})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_me_requires_token():
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(test_user):
    user, password = test_user
    login = client.post("/auth/login", json={"username": user.username, "password": password}).json()
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == user.username


def test_rbac_blocks_non_admin_role(test_user):
    """test_user has role CDD, which is NOT in the allowed list for POST /modules."""
    user, password = test_user
    login = client.post("/auth/login", json={"username": user.username, "password": password}).json()
    resp = client.post("/modules", headers={"Authorization": f"Bearer {login['access_token']}"})
    assert resp.status_code == 403


def test_refresh_then_logout_revokes_token(test_user):
    user, password = test_user
    login = client.post("/auth/login", json={"username": user.username, "password": password}).json()
    refresh_token = login["refresh_token"]

    refreshed = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()

    logout_resp = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert logout_resp.status_code == 204

    # The same refresh token must now be rejected — this is the check that
    # proves logout actually revokes server-side, not just a client no-op.
    reused = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert reused.status_code == 401
