"""Item 1: device registry (login and sync), active-device calculation, the user
report's device columns, column filters and sorting, and the filtered CSV export."""
import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.auth.security import hash_password
from app.database import SessionLocal
from app.devices import registry
from app.main import app
from app.models import AuditLog, Device, Language, RefreshToken, User
from app.models.enums import LearnerRole, RoleName, UserStatus
from app.reports import column_filters

client = TestClient(app)
INSTALL = "a1b2c3d4e5f6a7b8c9d0e1f2"


def _make_user(db, role, learner_role=None, tag=""):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_dev_{tag}{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(username=username, email=f"{username}@sarmaan-eplaybook.app", password_hash=hash_password("TestPass123!"),
                first_name="Test", last_name=role.value, role=role, learner_role=learner_role, language_id=english.id,
                status=UserStatus.ACTIVE)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(user, device=None):
    body = {"username": user.username, "password": "TestPass123!"}
    if device:
        body["device"] = device
    resp = client.post("/auth/login", json=body)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def users():
    db = SessionLocal()
    made = {"admin": _make_user(db, RoleName.SUPER_ADMIN), "reader": _make_user(db, RoleName.READ_ONLY),
            "a": _make_user(db, RoleName.CDD, LearnerRole.CDD, "a"), "b": _make_user(db, RoleName.CDD, LearnerRole.HEALTH_WORKER, "b")}
    yield made
    ids = [u.id for u in made.values()]
    for model in (Device, RefreshToken, AuditLog):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def _devices(user):
    db = SessionLocal()
    rows = db.query(Device).filter_by(user_id=user.id).all()
    db.close()
    return rows


def test_login_and_sync_register_the_device(users):
    a = users["a"]
    _login(a)  # an older app sends no device: still fine, no row
    assert _devices(a) == []
    info = {"install_id": INSTALL, "os": "android", "os_version": "14 (API 34)", "app_version": "0.1.16"}
    h = _login(a, info)
    (d,) = _devices(a)
    assert (d.os, d.os_version, d.app_version, d.model) == ("android", "14 (API 34)", "0.1.16", None)
    assert d.last_login_at and d.last_sync_at is None
    first_seen = d.first_seen_at

    r = client.post("/sync/device", headers=h, json={**info, "app_version": "0.1.17"})
    assert r.status_code == 200 and r.json()["active_days"] == 30 and r.json()["device"]["active"] is True
    (d,) = _devices(a)
    assert d.app_version == "0.1.17" and d.last_sync_at and d.first_seen_at == first_seen, "refreshed, not duplicated"

    _login(a, {**info, "install_id": "ffffffffffffffff0000"})  # second phone
    assert len(_devices(a)) == 2
    assert client.post("/sync/device", headers=h, json={"install_id": "IMEI 35-209900-176148-1"}).status_code == 422
    assert client.post("/sync/device", json=info).status_code == 401


def test_active_means_seen_within_the_setting(users):
    now = datetime(2026, 11, 13, tzinfo=timezone.utc)
    fresh = Device(last_seen_at=now - timedelta(days=29, hours=23))
    stale = Device(last_seen_at=now - timedelta(days=30, minutes=1))
    assert registry.is_active(fresh, now) and not registry.is_active(stale, now)


def test_report_device_columns_and_device_list(users):
    a, b, admin, reader = users["a"], users["b"], _login(users["admin"]), _login(users["reader"])
    _login(a, {"install_id": INSTALL, "os": "android", "os_version": "13", "app_version": "0.1.16"})
    _login(a, {"install_id": "0123456789abcdef0123", "os": "android", "os_version": "11", "app_version": "0.1.16"})
    db = SessionLocal()
    old = db.query(Device).filter_by(user_id=a.id, install_id="0123456789abcdef0123").one()
    old.last_seen_at = datetime.now(timezone.utc) - timedelta(days=45)
    db.commit()
    db.close()

    rows = {r["username"]: r for r in client.get("/reports/users", headers=admin).json()}
    assert (rows[a.username]["devices_active"], rows[a.username]["devices_total"]) == (1, 2)
    assert "inactive" in rows[a.username]["devices_summary"] and rows[a.username]["device_last_seen"]
    assert (rows[b.username]["devices_active"], rows[b.username]["devices_total"], rows[b.username]["devices_summary"]) == (0, 0, None)

    listing = client.get(f"/reports/users/{a.id}/devices", headers=reader).json()
    assert listing["active_days"] == 30 and [d["active"] for d in listing["devices"]] == [True, False]
    assert {"model", "os", "os_version", "app_version", "first_seen_at", "last_seen_at", "last_sync_at", "active"} <= set(listing["devices"][0])
    assert "install_id" not in listing["devices"][0], "the install id stays on the server"
    assert client.get(f"/reports/users/{a.id}/devices", headers=_login(a)).status_code == 403


def test_column_filters_unit():
    rows = [
        {"name": "Amina Bello", "status": "ACTIVE", "score": 84, "devices": 1, "seen": "2026-11-01T10:00:00+00:00"},
        {"name": "Musa Ali", "status": "INACTIVE", "score": 60, "devices": 0, "seen": "2026-10-15T08:00:00+00:00"},
        {"name": "Hauwa Musa", "status": "ACTIVE", "score": None, "devices": 2, "seen": None},
    ]
    names = lambda r: [x["name"] for x in r]  # noqa: E731
    assert names(column_filters.apply(rows, [("q.name", "musa")])) == ["Musa Ali", "Hauwa Musa"]
    assert names(column_filters.apply(rows, [("in.status", "ACTIVE")])) == ["Amina Bello", "Hauwa Musa"]
    assert names(column_filters.apply(rows, [("min.score", "61")])) == ["Amina Bello"], "empty cells never match a range"
    assert names(column_filters.apply(rows, [("max.devices", "1")])) == ["Amina Bello", "Musa Ali"]
    assert names(column_filters.apply(rows, [("from.seen", "2026-10-20"), ("to.seen", "2026-11-01")])) == ["Amina Bello"]
    assert names(column_filters.apply(rows, [("sort", "score"), ("order", "desc")])) == ["Amina Bello", "Musa Ali", "Hauwa Musa"]
    assert names(column_filters.apply(rows, [("sort", "name")])) == ["Amina Bello", "Hauwa Musa", "Musa Ali"]
    assert names(column_filters.apply(rows, [("in.status", "ACTIVE"), ("q.name", "hauwa")])) == ["Hauwa Musa"]
    with pytest.raises(ValueError):
        column_filters.apply(rows, [("q.nmae", "x")])
    with pytest.raises(ValueError):
        column_filters.apply(rows, [("min.score", "lots")])


def test_filtered_table_and_export_match(users):
    admin = _login(users["admin"])
    a, b = users["a"], users["b"]
    params = {"q.username": "test_dev_", "in.learner_role": "HEALTH_WORKER", "sort": "username"}
    table = client.get("/reports/users", headers=admin, params=params).json()
    assert [r["username"] for r in table] == [b.username]
    export = client.get("/reports/users.csv", headers=admin, params=params)
    assert export.status_code == 200
    exported = list(csv.DictReader(io.StringIO(export.text)))
    assert [r["username"] for r in exported] == [b.username]
    assert {"devices_active", "devices_total", "devices_summary", "device_last_seen"} <= set(exported[0])
    both = client.get("/reports/users.csv", headers=admin, params={"q.username": "test_dev_"}).text
    assert a.username in both and b.username in both
    assert client.get("/reports/users", headers=admin, params={"q.no_such_column": "x"}).status_code == 422
