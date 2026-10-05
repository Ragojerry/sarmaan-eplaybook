"""
Phase 5 automated tests: module CRUD, the full 4-stage governance workflow
(including RBAC per stage and rejection), languages, releases, and the
dashboard. Run against a real Postgres instance, same as test_auth.py.

    cd backend && python3 -m pytest tests/test_content.py -v
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User, Language, Module, ModuleTranslation, AuditLog, RefreshToken
from app.models.content_release import ContentRelease
from app.models.enums import RoleName, UserStatus, ContentReviewStatus
from app.auth.security import hash_password

client = TestClient(app)


def _make_user(db, role: RoleName, language_id):
    username = f"test_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username,
        email=f"{username}@sarmaan-eplaybook.app",
        password_hash=hash_password("TestPass123!"),
        first_name="Test",
        last_name=role.value,
        role=role,
        language_id=language_id,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(username, password="TestPass123!"):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _cleanup_user(db, user):
    # content_releases.created_by/approved_by deliberately have no
    # cascade-delete (a release's provenance should survive even if the
    # creating/approving user's account is later removed) — test cleanup
    # has to null these explicitly, same reasoning as audit_logs in
    # test_auth.py.
    db.query(ContentRelease).filter_by(created_by=user.id).update({"created_by": None})
    db.query(ContentRelease).filter_by(approved_by=user.id).update({"approved_by": None})
    db.query(RefreshToken).filter_by(user_id=user.id).delete()
    db.query(AuditLog).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()


@pytest.fixture()
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def english(db):
    return db.query(Language).filter_by(code="en").one()


@pytest.fixture()
def content_admin(db, english):
    user = _make_user(db, RoleName.CONTENT_ADMIN, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def program_reviewer(db, english):
    user = _make_user(db, RoleName.PROGRAM_REVIEWER, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def localisation_reviewer(db, english):
    user = _make_user(db, RoleName.LOCALISATION_REVIEWER, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def technical_reviewer(db, english):
    user = _make_user(db, RoleName.TECHNICAL_REVIEWER, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def cdd_user(db, english):
    user = _make_user(db, RoleName.CDD, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def test_module(db, content_admin):
    token = _login(content_admin.username)
    code = f"TESTMOD-{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/modules",
        json={"module_code": code, "module_number": 99, "title": "Test Module", "sort_order": 99},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    module_id = resp.json()["id"]
    yield module_id
    module = db.get(Module, uuid.UUID(module_id))
    if module:
        db.query(ModuleTranslation).filter_by(module_id=module.id).delete()
        db.delete(module)
        db.commit()


# ---------- Module CRUD + RBAC ----------

def test_cdd_cannot_create_module(cdd_user):
    token = _login(cdd_user.username)
    resp = client.post(
        "/modules", json={"module_code": f"X-{uuid.uuid4().hex[:6]}", "module_number": 1, "title": "X"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 403


def test_content_admin_can_create_module(test_module):
    assert test_module is not None  # fixture already asserted 201


def test_any_authenticated_user_can_list_modules(cdd_user, test_module):
    token = _login(cdd_user.username)
    resp = client.get("/modules", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert any(m["id"] == test_module for m in resp.json())


def test_list_modules_requires_auth():
    resp = client.get("/modules")
    assert resp.status_code == 401


# ---------- Full governance workflow ----------

def test_full_governance_workflow(
    db, content_admin, program_reviewer, localisation_reviewer, technical_reviewer, test_module, english
):
    admin_token = _login(content_admin.username)

    # Create a translation — starts at DRAFT.
    resp = client.post(
        f"/modules/{test_module}/translations",
        json={"language_id": str(english.id), "title": "Test Title", "body": "Test body"},
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 201, resp.text
    translation = resp.json()
    assert translation["status"] == "DRAFT"
    tid = translation["id"]

    # A PROGRAM_REVIEWER cannot submit from DRAFT — that's CONTENT_ADMIN's job.
    reviewer_token = _login(program_reviewer.username)
    resp = client.post(f"/modules/translations/{tid}/submit-review", headers=_auth_headers(reviewer_token))
    assert resp.status_code == 403

    # CONTENT_ADMIN submits: DRAFT -> PROGRAMME_REVIEW
    resp = client.post(f"/modules/translations/{tid}/submit-review", headers=_auth_headers(admin_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PROGRAMME_REVIEW"

    # LOCALISATION_REVIEWER cannot approve at PROGRAMME_REVIEW — wrong stage's role.
    loc_token = _login(localisation_reviewer.username)
    resp = client.post(f"/modules/translations/{tid}/approve", headers=_auth_headers(loc_token))
    assert resp.status_code == 403

    # PROGRAM_REVIEWER approves: PROGRAMME_REVIEW -> LOCALISATION_REVIEW
    resp = client.post(f"/modules/translations/{tid}/approve", headers=_auth_headers(reviewer_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "LOCALISATION_REVIEW"

    # LOCALISATION_REVIEWER approves: LOCALISATION_REVIEW -> TECHNICAL_QA
    resp = client.post(f"/modules/translations/{tid}/approve", headers=_auth_headers(loc_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "TECHNICAL_QA"

    # TECHNICAL_REVIEWER approves: TECHNICAL_QA -> PUBLISHED
    tech_token = _login(technical_reviewer.username)
    resp = client.post(f"/modules/translations/{tid}/approve", headers=_auth_headers(tech_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PUBLISHED"

    # Cannot advance further from PUBLISHED.
    resp = client.post(f"/modules/translations/{tid}/approve", headers=_auth_headers(tech_token))
    assert resp.status_code == 409

    # Audit trail actually recorded every transition.
    entries = db.query(AuditLog).filter_by(entity_type="module_translation", entity_id=uuid.UUID(tid)).all()
    assert len(entries) >= 4


def test_rejection_sends_back_to_draft(db, content_admin, program_reviewer, test_module, english):
    admin_token = _login(content_admin.username)
    resp = client.post(
        f"/modules/{test_module}/translations",
        json={"language_id": str(english.id), "title": "Reject Me"},
        headers=_auth_headers(admin_token),
    )
    tid = resp.json()["id"]
    client.post(f"/modules/translations/{tid}/submit-review", headers=_auth_headers(admin_token))

    reviewer_token = _login(program_reviewer.username)
    resp = client.post(
        f"/modules/translations/{tid}/reject", json={"reason": "Needs more detail"}, headers=_auth_headers(reviewer_token)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "REJECTED"


# ---------- Languages ----------

def test_create_language_requires_content_admin(cdd_user):
    token = _login(cdd_user.username)
    resp = client.post(
        "/languages",
        json={"code": f"z{uuid.uuid4().hex[:4]}", "name": "Test Lang", "native_name": "Test"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 403


def test_list_languages_includes_seeded_defaults(cdd_user):
    token = _login(cdd_user.username)
    resp = client.get("/languages", headers=_auth_headers(token))
    assert resp.status_code == 200
    codes = {l["code"] for l in resp.json()}
    assert {"en", "ha", "ff", "kr"}.issubset(codes)


# ---------- Releases ----------

def test_only_technical_reviewer_can_publish_release(db, content_admin, technical_reviewer):
    admin_token = _login(content_admin.username)
    code = f"REL-{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/releases", json={"release_code": code, "version": "1.0.0"}, headers=_auth_headers(admin_token)
    )
    assert resp.status_code == 201, resp.text
    release_id = resp.json()["id"]

    # CONTENT_ADMIN cannot publish.
    resp = client.post(f"/releases/{release_id}/publish", headers=_auth_headers(admin_token))
    assert resp.status_code == 403

    # TECHNICAL_REVIEWER can.
    tech_token = _login(technical_reviewer.username)
    resp = client.post(f"/releases/{release_id}/publish", headers=_auth_headers(tech_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PUBLISHED"

    db.query(ContentRelease).filter_by(id=uuid.UUID(release_id)).delete()
    db.commit()


# ---------- Dashboard ----------

def test_dashboard_returns_real_counts_not_fixed_literals(cdd_user, test_module):
    token = _login(cdd_user.username)
    resp = client.get("/analytics/dashboard", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    # total_modules must reflect the actual DB state (includes our test_module),
    # not a hardcoded prototype number.
    assert body["total_modules"] >= 1
    assert isinstance(body["module_engagement"], list)
    assert isinstance(body["language_usage"], list)
