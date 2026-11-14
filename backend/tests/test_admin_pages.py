"""Portal pages ticked per account (app/auth/pages.py): ticks only narrow what
the role allows, the server enforces them, and phone endpoints ignore them."""
import uuid

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.auth.dependencies import get_staff_user
from app.auth.pages import PAGES, api_pages, check_page
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, Language, RefreshToken, User
from app.models.enums import RoleName, UserStatus

client = TestClient(app)
PASSWORD = "TestPass123!"


def _make_user(db, role, pages=None):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_pages_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username, email=f"{username}@sarmaan-eplaybook.app", password_hash=hash_password(PASSWORD),
        first_name="Test", last_name=role.value, role=role, language_id=english.id, status=UserStatus.ACTIVE,
        admin_pages=pages,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(username):
    resp = client.post("/auth/login", json={"username": username, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def db():
    session = SessionLocal()
    made: list[uuid.UUID] = []
    session.made = made
    yield session
    ids = made + [u.id for u in session.query(User).filter(User.username.like("test_pages_new_%"))]
    for model in (RefreshToken, AuditLog):
        session.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    session.query(AuditLog).filter(AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
    session.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    session.commit()
    session.close()


def _user(db, role, pages=None):
    user = _make_user(db, role, pages)
    db.made.append(user.id)
    return user


def _uses_staff_check(dependant) -> bool:
    return any(d.call is get_staff_user or _uses_staff_check(d) for d in dependant.dependencies)


def test_every_portal_endpoint_belongs_to_a_page():
    routes = [r for r in app.routes if isinstance(r, APIRoute)]
    # Newer FastAPI nests included routers; fail rather than check nothing.
    assert len(routes) > 100, "app.routes no longer lists every endpoint: update this test"
    missing = [r.path for r in routes if _uses_staff_check(r.dependant) and api_pages(r.path) is None]
    assert missing == [], f"add these to API_PAGES in app/auth/pages.py: {missing}"


def test_check_uses_the_address_called_not_the_route_template():
    """FastAPI 0.162 (production) gives scope["route"] the path without its router
    prefix; the check must still find the page."""
    from starlette.requests import Request

    class Route:
        path = "/summary"

    class Ticked:
        role = RoleName.SUPERVISOR
        admin_pages = ["reports"]

    request = Request({"type": "http", "method": "GET", "path": "/reports/summary", "root_path": "",
                       "query_string": b"", "headers": [], "route": Route()})
    check_page(request, Ticked())  # no 403


def test_ticked_pages_are_enforced_by_the_server(db):
    sup = _user(db, RoleName.SUPERVISOR, ["reports"])
    h = _login(sup.username)
    assert client.get("/reports/summary", headers=h).status_code == 200
    assert client.get("/languages", headers=h).status_code == 200  # shared by every page
    assert client.get("/analytics/usage", headers=h).status_code == 403
    assert client.get("/tools/items", headers=h).status_code == 403
    assert client.get("/analytics/dashboard", headers=h).status_code == 403
    me = client.get("/auth/me", headers=h).json()
    assert me["admin_pages"] == ["reports"] and me["pages"] == ["reports"]


def test_no_ticks_means_every_page_the_role_allows(db):
    h = _login(_user(db, RoleName.SUPERVISOR).username)
    assert client.get("/analytics/usage", headers=h).status_code == 200
    me = client.get("/auth/me", headers=h).json()
    assert me["admin_pages"] is None
    assert "consent" not in me["pages"] and "users" not in me["pages"] and "reports" in me["pages"]


def test_reading_a_shared_endpoint_does_not_allow_changing_it(db):
    videos_only = _login(_user(db, RoleName.CONTENT_ADMIN, ["videos"]).username)
    assert client.get("/modules", headers=videos_only).status_code == 200
    assert client.patch(f"/languages/{uuid.uuid4()}", json={}, headers=videos_only).status_code == 403
    languages = _login(_user(db, RoleName.CONTENT_ADMIN, ["languages"]).username)
    assert client.patch(f"/languages/{uuid.uuid4()}", json={}, headers=languages).status_code == 404


def test_phone_endpoints_ignore_portal_ticks(db):
    h = _login(_user(db, RoleName.SUPERVISOR, ["reports"]).username)
    assert client.get("/modules", headers=h).status_code == 200  # the phone's module list
    assert client.get("/sync/learning", headers=h).status_code == 200


def test_super_admin_ticks_pages_when_creating_and_editing(db):
    admin = _login(_user(db, RoleName.SUPER_ADMIN).username)
    base = {"password": "LongPassword1", "first_name": "New", "last_name": "Staff", "role": "SUPERVISOR"}

    def create(**extra):
        name = f"test_pages_new_{uuid.uuid4().hex[:8]}"
        return client.post("/users", json={**base, "username": name, "email": f"{name}@example.org", **extra}, headers=admin)

    assert create(admin_pages=["consent"]).status_code == 422  # a supervisor cannot open Consent text
    assert create(admin_pages=["nope"]).status_code == 422
    assert create(admin_pages=[]).status_code == 422
    resp = create(admin_pages=["reports", "dashboard"])
    assert resp.status_code == 201, resp.text
    new = resp.json()
    assert new["admin_pages"] == ["dashboard", "reports"]  # menu order

    resp = client.patch(f"/users/{new['id']}", json={"admin_pages": ["analytics"]}, headers=admin)
    assert resp.json()["admin_pages"] == ["analytics"]
    resp = client.patch(f"/users/{new['id']}", json={"all_pages": True}, headers=admin)
    assert resp.json()["admin_pages"] is None
    assert set(resp.json()["pages"]) == {p for p, (_, roles) in PAGES.items() if RoleName.SUPERVISOR in roles}


def test_role_change_keeps_only_pages_the_new_role_allows(db):
    admin = _login(_user(db, RoleName.SUPER_ADMIN).username)
    target = _user(db, RoleName.CONTENT_ADMIN, ["consent", "reports"])
    resp = client.patch(f"/users/{target.id}", json={"role": "SUPERVISOR"}, headers=admin)
    assert resp.status_code == 200, resp.text
    assert resp.json()["admin_pages"] == ["reports"]
    only_consent = _user(db, RoleName.CONTENT_ADMIN, ["consent"])
    assert client.patch(f"/users/{only_consent.id}", json={"role": "SUPERVISOR"}, headers=admin).status_code == 422


def test_catalog_lists_every_page(db):
    assert client.get("/auth/pages").status_code == 401
    rows = client.get("/auth/pages", headers=_login(_user(db, RoleName.READ_ONLY).username)).json()
    assert [r["key"] for r in rows] == list(PAGES)
    assert next(r for r in rows if r["key"] == "users")["roles"] == []
