"""User administration + team code (SUPER_ADMIN only)."""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AdminBoundary, AuditLog, Language, RefreshToken, TrainingSession, User
from app.models.enums import AuditAction, BoundaryLevel, RoleName
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
        "first_name": "Aisha", "last_name": "Bello", "team_code": "0041", "learner_role": "CDD",
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


# ---------- bulk import ----------

HEADER = "first_name,last_name,username,email,phone,role,team_code,password,session,country,state,lga,ward,facility"


@pytest.fixture()
def place(db):
    """A training session and a Country > State > LGA chain, removed afterwards."""
    tag = uuid.uuid4().hex[:8]
    sess = TrainingSession(name=f"Import test {tag}", start_date=date(2026, 11, 1), end_date=date(2026, 11, 30))
    country = AdminBoundary(level=BoundaryLevel.COUNTRY, name=f"Testland {tag}")
    db.add_all([sess, country])
    db.flush()
    state = AdminBoundary(level=BoundaryLevel.STATE, name="North", parent_id=country.id)
    db.add(state)
    db.flush()
    lga = AdminBoundary(level=BoundaryLevel.LGA, name="Riverside", parent_id=state.id)
    db.add(lga)
    db.commit()
    yield sess, country, state, lga
    db.rollback()
    imported = db.query(User).filter(User.training_session_id == sess.id).all()
    ids = [u.id for u in imported]
    db.query(AuditLog).filter(AuditLog.entity_id.in_(ids)).delete(synchronize_session=False)
    db.query(RefreshToken).filter(RefreshToken.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    for model, row in ((AdminBoundary, lga), (AdminBoundary, state), (AdminBoundary, country), (TrainingSession, sess)):
        db.query(model).filter(model.id == row.id).delete(synchronize_session=False)  # child first
    db.commit()


def _upload(headers, text):
    return client.post("/users/import", headers=headers, files={"file": ("users.csv", text.encode("utf-8-sig"), "text/csv")})


def test_import_creates_users_with_session_area_and_generated_password(actors, place, db):
    admin, _, _, ah, _ = actors
    sess, country, state, lga = place
    a, b = f"imp_{uuid.uuid4().hex[:8]}", f"imp_{uuid.uuid4().hex[:8]}"
    csv_text = "\n".join([
        HEADER,
        f"Aisha,Bello,{a},{a}@sarmaan-eplaybook.app,0803,cdd,0041,LongEnough123!,{sess.name.upper()},{country.name},North,Riverside,,",
        f"Musa,Ali,{b},{b}@sarmaan-eplaybook.app,,,0042,,{sess.name},{country.name},north,,,",
        ",,,,,,,,,,,,,",
    ])
    r = _upload(ah, csv_text)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] == 2
    assert [g["username"] for g in body["generated_passwords"]] == [b]

    ua = db.query(User).filter_by(username=a).one()
    ub = db.query(User).filter_by(username=b).one()
    assert ua.role == RoleName.CDD and ua.team_code == "0041" and ua.training_session_id == sess.id
    assert (ua.country_id, ua.state_id, ua.lga_id) == (country.id, state.id, lga.id)
    assert ub.state_id == state.id and ub.lga_id is None
    assert db.query(AuditLog).filter_by(entity_id=ua.id, action=AuditAction.USER_CREATE).count() == 1
    assert _login(b, body["generated_passwords"][0]["password"])


def test_import_is_all_or_nothing_and_lists_every_bad_row(actors, place, db):
    _, cdd, _, ah, _ = actors
    sess, country, _, _ = place
    good = f"imp_{uuid.uuid4().hex[:8]}"
    csv_text = "\n".join([
        HEADER,
        f"Good,Row,{good},{good}@sarmaan-eplaybook.app,,,,,{sess.name},{country.name},North,,,",
        f"Bad,Session,x_{good},x_{good}@sarmaan-eplaybook.app,,,,,No Such Session,,,,,",
        f"Bad,Area,y_{good},y_{good}@sarmaan-eplaybook.app,,,,,,{country.name},Nowhere,,,",
        f"Bad,Role,z_{good},z_{good}@sarmaan-eplaybook.app,,SUPER_ADMIN,,,,,,,,",
        f"Dup,Name,{good},w_{good}@sarmaan-eplaybook.app,,,,,,,,,,",
        f"Short,Pw,v_{good},v_{good}@sarmaan-eplaybook.app,,,,short,,,,,,",
    ])
    r = _upload(ah, csv_text)
    assert r.status_code == 422
    detail = r.json()["detail"]
    for n in (3, 4, 5, 6, 7):
        assert f"Row {n}:" in detail
    assert "Row 2:" not in detail
    assert db.query(User).filter(User.username.like(f"%{good}")).count() == 0

    taken = _upload(ah, HEADER + f"\nOld,User,{cdd.username},new_{good}@sarmaan-eplaybook.app,,,,,,,,,,")
    assert taken.status_code == 422 and cdd.username in taken.json()["detail"]


def test_import_rejects_bad_files_and_non_admins(actors):
    _, _, _, ah, ch = actors
    assert _upload(ch, HEADER).status_code == 403
    assert _upload(ah, "name,email\nA,a@b.c").status_code == 422
    assert _upload(ah, HEADER).status_code == 422
    assert client.post("/users/import", headers=ah, files={"file": ("u.csv", b"\xff\xfe\x00bad", "text/csv")}).status_code == 422
