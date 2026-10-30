"""Administrative boundaries, user areas/location, activity reports, CSV export
and the API-key protected Power BI endpoints."""
import csv
import io
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import (
    AdminBoundary, ApiKey, AuditLog, Language, Module, QuizAttempt, RefreshToken, User, UserModuleProgress, AnalyticsEvent,
)
from app.models.enums import AnalyticsEventType, ModuleStatus, RoleName
from tests.test_content import _auth_headers, _login, _make_user

client = TestClient(app)
NOW = datetime.now(timezone.utc).isoformat()


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
    made_users: list[uuid.UUID] = []
    yield admin, cdd, tag, made_users, _auth_headers(_login(admin.username)), _auth_headers(_login(cdd.username))
    db.rollback()
    ids = [admin.id, cdd.id] + made_users
    db.query(ApiKey).filter(ApiKey.created_by == admin.id).delete()
    db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(UserModuleProgress).filter(UserModuleProgress.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    # boundaries: leaf first
    for _ in range(5):
        for b in db.query(AdminBoundary).filter(AdminBoundary.name.like(f"%-{tag}")).all():
            if not db.query(AdminBoundary).filter_by(parent_id=b.id).count():
                db.delete(b)
        db.commit()
    db.commit()


def _post(path, h, **json):
    return client.post(path, headers=h, json=json)


def _tree(ah, tag):
    ids = {}
    parent = None
    for level in ["COUNTRY", "STATE", "LGA", "WARD", "FACILITY"]:
        r = _post("/boundaries", ah, level=level, name=f"{level.title()}-{tag}", parent_id=parent)
        assert r.status_code == 201, r.text
        parent = ids[level] = r.json()["id"]
    return ids


def _new_user(ah, made, tag, boundary_id, **extra):
    name = f"rep_{uuid.uuid4().hex[:8]}"
    r = client.post("/users", headers=ah, json={
        "username": name, "email": f"{name}@sarmaan-eplaybook.app", "password": "LongEnough123!",
        "first_name": "Rep", "last_name": name[-4:], "boundary_id": boundary_id, **extra})
    assert r.status_code == 201, r.text
    made.append(uuid.UUID(r.json()["id"]))
    return r.json()


def test_hierarchy_rules_and_permissions(world):
    admin, cdd, tag, made, ah, ch = world
    ids = _tree(ah, tag)
    # wrong parent level / orphan / duplicate / permissions
    assert _post("/boundaries", ah, level="LGA", name=f"Bad-{tag}", parent_id=ids["COUNTRY"]).status_code == 422
    assert _post("/boundaries", ah, level="WARD", name=f"Bad-{tag}").status_code == 422
    assert _post("/boundaries", ah, level="COUNTRY", name=f"Country-{tag}").status_code == 409
    assert _post("/boundaries", ch, level="COUNTRY", name=f"X-{tag}").status_code == 403
    assert client.get("/boundaries", headers=ch).status_code == 403
    kids = client.get("/boundaries", headers=ah, params={"parent_id": ids["COUNTRY"]}).json()
    assert [k["name"] for k in kids] == [f"State-{tag}"]
    # in use -> cannot delete; leaf deletes
    assert client.delete(f"/boundaries/{ids['STATE']}", headers=ah).status_code == 409
    renamed = client.patch(f"/boundaries/{ids['FACILITY']}", headers=ah, json={"code": "F1"}).json()
    assert renamed["code"] == "F1" and "latitude" not in renamed


def test_import_is_atomic_and_idempotent(world):
    admin, cdd, tag, made, ah, ch = world
    good = f"country,state,lga,ward,facility\nC-{tag},S-{tag},L-{tag},W-{tag},F-{tag}\nC-{tag},S-{tag},L2-{tag},,,\n"
    r = client.post("/boundaries/import", headers=ah, files={"file": ("b.csv", good.encode(), "text/csv")})
    assert r.status_code == 200 and r.json()["created"] == 6  # C, S, L, W, F, L2
    again = client.post("/boundaries/import", headers=ah, files={"file": ("b.csv", good.encode(), "text/csv")})
    assert again.json()["created"] == 0
    bad = f"country,state,lga,ward,facility\nC2-{tag},S2-{tag},,W2-{tag},\n"
    r = client.post("/boundaries/import", headers=ah, files={"file": ("b.csv", bad.encode(), "text/csv")})
    assert r.status_code == 422 and "empty level" in r.json()["detail"]
    assert client.get("/boundaries", headers=ah, params={"q": f"C2-{tag}"}).json() == []  # nothing written
    assert client.post("/boundaries/import", headers=ch, files={"file": ("b.csv", good.encode(), "text/csv")}).status_code == 403


def test_user_area_and_location(world, db):
    admin, cdd, tag, made, ah, ch = world
    ids = _tree(ah, tag)
    u = _new_user(ah, made, tag, ids["WARD"])
    assert u["ward_id"] == ids["WARD"] and u["lga_id"] == ids["LGA"] and u["state_id"] == ids["STATE"] and u["country_id"] == ids["COUNTRY"]
    assert u["facility_id"] is None and u["ward_name"] == f"Ward-{tag}"
    moved = client.patch(f"/users/{u['id']}", headers=ah, json={"boundary_id": ids["FACILITY"]}).json()
    assert moved["facility_id"] == ids["FACILITY"] and moved["ward_id"] == ids["WARD"]
    cleared = client.patch(f"/users/{u['id']}", headers=ah, json={"clear_boundary": True}).json()
    assert cleared["state_id"] is None and "latitude" not in cleared
    assert client.post("/users", headers=ah, json={"username": "zz_nobody", "email": "zz@x.org", "password": "LongEnough123!",
                       "first_name": "a", "last_name": "b", "boundary_id": str(uuid.uuid4())}).status_code == 422


def test_reports_rollups_csv_and_filters(world, db):
    admin, cdd, tag, made, ah, ch = world
    ids = _tree(ah, tag)
    a = _new_user(ah, made, tag, ids["FACILITY"])
    b = _new_user(ah, made, tag, ids["FACILITY"])
    published = db.query(Module).filter_by(status=ModuleStatus.PUBLISHED).order_by(Module.sort_order).all()
    m1 = published[0]
    db.add(UserModuleProgress(user_id=uuid.UUID(a["id"]), module_id=m1.id, progress_percent=100, completed=True,
                              completed_at=datetime.now(timezone.utc)))
    db.add(QuizAttempt(user_id=uuid.UUID(a["id"]), module_id=m1.id, client_id=uuid.uuid4().hex, correct_count=9, total_count=10,
                       score_percent=90, passed=True, results=[], taken_at=datetime.now(timezone.utc)))
    db.add(AnalyticsEvent(event_type=AnalyticsEventType.MODULE_OPEN, user_id=uuid.UUID(a["id"]), module_id=m1.id,
                          occurred_at=datetime.now(timezone.utc), payload={}))
    db.add(AnalyticsEvent(event_type=AnalyticsEventType.SYNC_FAILED, user_id=uuid.UUID(b["id"]),
                          occurred_at=datetime.now(timezone.utc), payload={}))
    db.commit()

    f = {"state_id": ids["STATE"]}
    rows = client.get("/reports/users", headers=ah, params=f).json()
    by = {r["user_id"]: r for r in rows}
    ra, rb = by[a["id"]], by[b["id"]]
    total = len(published)
    assert ra["modules_completed"] == 1 and ra["completion_rate"] == round(100 / total, 1)
    assert ra["quizzes_passed"] == 1 and ra["avg_best_quiz_score"] == 90 and ra["training_events"] == 1 and ra["module_opens"] == 1
    assert rb["modules_completed"] == 0 and rb["technical_events"] == 1 and rb["last_activity"]
    assert ra["state"] == f"State-{tag}" and ra["facility"] == f"Facility-{tag}"

    roll = client.get("/reports/boundaries", headers=ah, params={**f, "level": "lga"}).json()
    assert len(roll) == 1 and roll[0]["area"] == f"Lga-{tag}" and roll[0]["state"] == f"State-{tag}"
    assert roll[0]["users"] == 2 and roll[0]["modules_completed"] == 1 and roll[0]["quizzes_passed"] == 1
    assert roll[0]["avg_completion_rate"] == round((ra["completion_rate"] + 0) / 2, 1)

    mods = client.get("/reports/modules", headers=ah, params={**f, "level": "state"}).json()
    mine = next(m for m in mods if m["module_code"] == m1.module_code)
    assert mine["users"] == 2 and mine["completed"] == 1 and mine["completion_rate"] == 50.0 and mine["quiz_passed"] == 1

    summ = client.get("/reports/summary", headers=ah, params=f).json()
    assert summ["users"] == 2 and summ["users_not_started"] == 1 and summ["active_users_30d"] == 2

    # future-only date window excludes everything that happened today
    future = client.get("/reports/users", headers=ah, params={**f, "date_from": "2999-01-01"}).json()
    assert all(r["modules_completed"] == 0 and r["training_events"] == 0 for r in future)

    # other state shows nothing of ours
    assert client.get("/reports/users", headers=ah, params={"state_id": str(uuid.uuid4())}).json() == []

    text = client.get("/reports/users.csv", headers=ah, params=f)
    assert text.status_code == 200 and text.text.startswith("﻿") and text.headers["content-type"].startswith("text/csv")
    parsed = list(csv.DictReader(io.StringIO(text.text.lstrip("﻿"))))
    assert len(parsed) == 2 and {"state", "completion_rate", "session"} <= set(parsed[0])
    assert client.get("/reports/boundaries.csv", headers=ah, params={**f, "level": "ward"}).status_code == 200

    # field staff cannot read reports
    assert client.get("/reports/users", headers=ch).status_code == 403
    assert client.get("/reports/users").status_code in (401, 403)
    assert client.get("/reports/boundaries", headers=ah, params={"level": "planet"}).status_code == 422


def test_bi_api_key_lifecycle(world):
    admin, cdd, tag, made, ah, ch = world
    ids = _tree(ah, tag)
    _new_user(ah, made, tag, ids["FACILITY"])
    assert client.post("/bi/keys", headers=ch, json={"name": "x"}).status_code == 403
    r = client.post("/bi/keys", headers=ah, json={"name": "Power BI test"})
    assert r.status_code == 201
    key = r.json()["key"]
    assert key.startswith("sarmaan_bi_") and len(key) > 30
    assert key not in str(client.get("/bi/keys", headers=ah).json())  # never listed again

    h = {"X-API-Key": key}
    ok = client.get("/bi/users", headers=h, params={"state_id": ids["STATE"]})
    assert ok.status_code == 200 and isinstance(ok.json(), list) and len(ok.json()) == 1
    assert client.get("/bi/boundaries", headers=h, params={"level": "state", "state_id": ids["STATE"]}).status_code == 200
    assert client.get("/bi/modules", headers=h, params={"level": "state", "state_id": ids["STATE"]}).status_code == 200
    csv_out = client.get("/bi/users", headers=h, params={"state_id": ids["STATE"], "format": "csv"})
    assert csv_out.status_code == 200 and csv_out.headers["content-type"].startswith("text/csv")
    # a normal login token is not an API key, and bad keys are refused
    assert client.get("/bi/users", headers=ah).status_code == 401
    assert client.get("/bi/users", headers={"X-API-Key": "sarmaan_bi_wrong"}).status_code == 401
    assert client.get("/bi/users").status_code == 401

    listed = client.get("/bi/keys", headers=ah).json()
    mine = next(k for k in listed if k["id"] == r.json()["id"])
    assert mine["last_used_at"] and not mine["revoked"]
    assert client.delete(f"/bi/keys/{mine['id']}", headers=ah).status_code == 204
    assert client.get("/bi/users", headers=h).status_code == 401
