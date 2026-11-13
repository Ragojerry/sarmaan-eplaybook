"""Support contacts: validation per type, who may manage them, the audit trail,
audience filtering and "changed since" for phones, and an empty deck when no
contact is active. Values are reserved test values only (555-01xx numbers,
example.org), never real contacts."""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import false, true

from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, Language, PlatformSetting, RefreshToken, SupportContact, User
from app.models.enums import AuditAction, LearnerRole, RoleName, SupportContactType, UserStatus
from app.routers.support_contacts import NOTE_KEY
from app.support.validation import ContactValueError, normalise_value

client = TestClient(app)

PHONE = {"type": "PHONE", "label": "Call the support line", "value": "+1 555 010 0001", "availability": "Mon-Fri 8am-5pm",
         "languages": "English, Hausa"}


def _make_user(db, role, learner_role=None):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_support_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username, email=f"{username}@sarmaan-eplaybook.app", password_hash=hash_password("TestPass123!"),
        first_name="Test", last_name=role.value, role=role, learner_role=learner_role, language_id=english.id,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(user):
    resp = client.post("/auth/login", json={"username": user.username, "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def users():
    db = SessionLocal()
    existing = {c.id for c in db.query(SupportContact)}
    note_before = db.get(PlatformSetting, NOTE_KEY)
    note_value = note_before.value if note_before else None
    made = {
        "admin": _make_user(db, RoleName.CONTENT_ADMIN),
        "reader": _make_user(db, RoleName.READ_ONLY),
        "reviewer": _make_user(db, RoleName.PROGRAM_REVIEWER),
        "cdd": _make_user(db, RoleName.CDD, LearnerRole.CDD),
        "hw": _make_user(db, RoleName.CDD, LearnerRole.HEALTH_WORKER),
        "no_role": _make_user(db, RoleName.CDD),
    }
    made["existing"] = existing
    yield made
    ids = [u.id for k, u in made.items() if k != "existing"]
    db.query(SupportContact).filter(SupportContact.id.notin_(existing) if existing else true()).delete(synchronize_session=False)
    row = db.get(PlatformSetting, NOTE_KEY)
    if note_value is None and row is not None:
        db.delete(row)
    elif row is not None:
        row.value, row.updated_by = note_value, None
    db.flush()
    for model in (RefreshToken, AuditLog):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def _create(headers, **fields):
    resp = client.post("/support-contacts", headers=headers, json={**PHONE, **fields})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _audit(user, action):
    db = SessionLocal()
    rows = db.query(AuditLog).filter_by(user_id=user.id, action=action).all()
    db.close()
    return rows


def _sync(headers, since=None):
    resp = client.get("/sync/support-contacts", headers=headers, params={"since": since} if since else None)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------- validation ----------

@pytest.mark.parametrize("contact_type", [SupportContactType.PHONE, SupportContactType.SMS, SupportContactType.WHATSAPP])
def test_numbers_must_be_international(contact_type):
    assert normalise_value(contact_type, " +1 555 010 0001 ") == "+15550100001"
    for bad in ("05550100001", "+0555010001", "+1 (555) 010-0001", "+1555", "+1555010000112345", "tel:+15550100001", "+1555O100001"):
        with pytest.raises(ContactValueError):
            normalise_value(contact_type, bad)


def test_email_and_link_formats():
    assert normalise_value(SupportContactType.EMAIL, "help.desk@example.org") == "help.desk@example.org"
    for bad in ("help", "help@", "@example.org", "help@example", "a b@example.org", "help@@example.org", "help..x@example.org",
                "mailto:help@example.org"):
        with pytest.raises(ContactValueError):
            normalise_value(SupportContactType.EMAIL, bad)
    assert normalise_value(SupportContactType.LINK, "https://example.org/help?x=1") == "https://example.org/help?x=1"
    for bad in ("http://example.org", "example.org", "https://", "https://localhost", "javascript:alert(1)", "https://exa mple.org",
                "ftp://example.org"):
        with pytest.raises(ContactValueError):
            normalise_value(SupportContactType.LINK, bad)


def test_api_rejects_bad_values_with_a_clear_message(users):
    admin = _login(users["admin"])
    cases = [("PHONE", "0555 010 0001", "international format"), ("SMS", "+abc", "international format"),
             ("WHATSAPP", "15550100001", "international format"), ("EMAIL", "not-an-email", "valid email"),
             ("LINK", "http://example.org", "https://")]
    for contact_type, value, message in cases:
        resp = client.post("/support-contacts", headers=admin, json={**PHONE, "type": contact_type, "value": value})
        assert resp.status_code == 422 and message in resp.json()["detail"], (contact_type, resp.text)
    assert client.post("/support-contacts", headers=admin, json={**PHONE, "type": "FAX"}).status_code == 422
    assert client.post("/support-contacts", headers=admin, json={**PHONE, "audience": ["PILOT"]}).status_code == 422
    assert client.post("/support-contacts", headers=admin, json={**PHONE, "label": "   "}).status_code == 422


def test_fields_that_do_not_apply_to_the_type_are_cleared(users):
    admin = _login(users["admin"])
    phone = _create(admin, whatsapp_message="Hello", email_subject="Help", include_app_version=True)
    assert phone["value"] == "+15550100001"
    assert phone["whatsapp_message"] is None and phone["email_subject"] is None and phone["include_app_version"] is False
    wa = _create(admin, type="WHATSAPP", whatsapp_message=" Hello, I need help with the app ", email_subject="x",
                 include_app_version=True)
    assert wa["whatsapp_message"] == "Hello, I need help with the app" and wa["email_subject"] is None and wa["include_app_version"]
    mail = _create(admin, type="EMAIL", value="help@example.org", email_subject="e-Playbook question")
    assert mail["email_subject"] == "e-Playbook question" and mail["whatsapp_message"] is None


# ---------- permissions ----------

def test_permissions(users):
    admin, reader, reviewer, cdd = (_login(users[k]) for k in ("admin", "reader", "reviewer", "cdd"))
    contact = _create(admin)
    assert client.get("/support-contacts").status_code == 401
    assert client.get("/support-contacts", headers=cdd).status_code == 403
    for headers in (reader, reviewer):
        assert client.get("/support-contacts", headers=headers).status_code == 200
        assert client.get("/support-contacts/settings", headers=headers).status_code == 200
        assert client.post("/support-contacts", headers=headers, json=PHONE).status_code == 403
        assert client.put(f"/support-contacts/{contact['id']}", headers=headers, json=PHONE).status_code == 403
        assert client.put(f"/support-contacts/{contact['id']}/active", headers=headers, json={"active": False}).status_code == 403
        assert client.post("/support-contacts/reorder", headers=headers, json={"ids": [contact["id"]]}).status_code == 403
        assert client.delete(f"/support-contacts/{contact['id']}", headers=headers).status_code == 403
        assert client.put("/support-contacts/settings", headers=headers, json={"note": "x"}).status_code == 403
    assert client.get("/sync/support-contacts").status_code == 401


# ---------- audit ----------

def test_every_change_is_audited(users):
    admin_user = users["admin"]
    admin = _login(admin_user)
    a = _create(admin)
    b = _create(admin, type="EMAIL", value="help@example.org", label="Email the support team")
    assert [r.entity_id for r in _audit(admin_user, AuditAction.SUPPORT_CONTACT_CREATE)] and \
        len(_audit(admin_user, AuditAction.SUPPORT_CONTACT_CREATE)) == 2
    assert b["display_order"] == a["display_order"] + 1

    updated = client.put(f"/support-contacts/{a['id']}", headers=admin, json={**PHONE, "label": "Call the help line"})
    assert updated.status_code == 200 and updated.json()["label"] == "Call the help line"
    (log,) = _audit(admin_user, AuditAction.SUPPORT_CONTACT_UPDATE)
    assert log.details["before"]["label"] == "Call the support line" and log.details["after"]["label"] == "Call the help line"
    # Saving the same values again is not a change.
    client.put(f"/support-contacts/{a['id']}", headers=admin, json={**PHONE, "label": "Call the help line"})
    assert len(_audit(admin_user, AuditAction.SUPPORT_CONTACT_UPDATE)) == 1

    ids = [c["id"] for c in client.get("/support-contacts", headers=admin).json()]
    new_order = [b["id"], a["id"]] + [i for i in ids if i not in (a["id"], b["id"])]
    resp = client.post("/support-contacts/reorder", headers=admin, json={"ids": new_order})
    assert resp.status_code == 200 and [c["id"] for c in resp.json()] == new_order
    (log,) = _audit(admin_user, AuditAction.SUPPORT_CONTACT_REORDER)
    assert log.details["after"] == new_order
    assert client.post("/support-contacts/reorder", headers=admin, json={"ids": [a["id"]] * 2}).status_code == 422

    assert client.put(f"/support-contacts/{a['id']}/active", headers=admin, json={"active": False}).json()["is_active"] is False
    assert client.put(f"/support-contacts/{a['id']}/active", headers=admin, json={"active": True}).json()["is_active"] is True
    assert len(_audit(admin_user, AuditAction.SUPPORT_CONTACT_DEACTIVATE)) == 1
    assert len(_audit(admin_user, AuditAction.SUPPORT_CONTACT_ACTIVATE)) == 1

    assert client.delete(f"/support-contacts/{b['id']}", headers=admin).status_code == 204
    (log,) = _audit(admin_user, AuditAction.SUPPORT_CONTACT_DELETE)
    assert log.details["previous"]["value"] == "help@example.org"
    assert b["id"] not in [c["id"] for c in client.get("/support-contacts", headers=admin).json()]
    assert client.put(f"/support-contacts/{b['id']}", headers=admin, json=PHONE).status_code == 404

    assert client.put("/support-contacts/settings", headers=admin, json={"note": " Go to the nearest health facility. "}).json()["note"] \
        == "Go to the nearest health facility."
    db = SessionLocal()
    setting_log = db.query(AuditLog).filter_by(user_id=admin_user.id, action=AuditAction.SETTING_CHANGE).one()
    db.close()
    assert setting_log.details["key"] == NOTE_KEY
    assert client.put("/support-contacts/settings", headers=admin, json={"note": "x" * 201}).status_code == 422


# ---------- phones ----------

def test_audience_filtering(users):
    admin = _login(users["admin"])
    everyone = _create(admin, label="Everyone")
    health = _create(admin, label="Health workers", audience=["HEALTH_WORKER"])
    logistics = _create(admin, label="Logisticians", audience=["LOGISTICIAN", "MONITOR_SUPERVISOR"])
    hidden = _create(admin, label="Inactive", is_active=False)

    def seen(key):
        return {c["id"] for c in _sync(_login(users[key]))["contacts"]}

    mine = {everyone["id"], health["id"], logistics["id"], hidden["id"]}
    assert seen("hw") & mine == {everyone["id"], health["id"]}
    assert seen("cdd") & mine == {everyone["id"]}
    assert seen("no_role") & mine == {everyone["id"]}
    assert seen("reviewer") & mine == {everyone["id"], health["id"], logistics["id"]}, "staff see every active contact"
    row = next(c for c in _sync(_login(users["hw"]))["contacts"] if c["id"] == health["id"])
    assert set(row) == {"id", "type", "label", "value", "whatsapp_message", "email_subject", "include_app_version",
                        "availability", "languages", "display_order"}, "no audit or audience details go to phones"


def test_changed_since(users):
    admin = _login(users["admin"])
    hw = _login(users["hw"])
    keep = _create(admin, label="Unchanged")
    edit = _create(admin, label="Edited")
    off = _create(admin, label="Deactivated")
    gone = _create(admin, label="Deleted")
    moved = _create(admin, label="Moved to logisticians")

    first = _sync(hw)
    assert first["full"] is True and first["removed"] == []
    assert {keep["id"], edit["id"], off["id"], gone["id"], moved["id"]} <= {c["id"] for c in first["contacts"]}

    # Changes are visible to "since" only after the sync overlap, so pretend the
    # first download happened long ago for the contacts made above.
    db = SessionLocal()
    db.query(SupportContact).filter(SupportContact.id.in_([uuid.UUID(c["id"]) for c in (keep, edit, off, gone, moved)])) \
        .update({SupportContact.updated_at: datetime(2020, 1, 1, tzinfo=timezone.utc)}, synchronize_session=False)
    db.commit()
    db.close()
    since = datetime(2020, 6, 1, tzinfo=timezone.utc).isoformat()
    assert {c["id"] for c in _sync(hw, since)["contacts"]} & {keep["id"], edit["id"]} == set()

    client.put(f"/support-contacts/{edit['id']}", headers=admin, json={**PHONE, "label": "Edited again"})
    client.put(f"/support-contacts/{off['id']}/active", headers=admin, json={"active": False})
    client.delete(f"/support-contacts/{gone['id']}", headers=admin)
    client.put(f"/support-contacts/{moved['id']}", headers=admin, json={**PHONE, "label": "Moved", "audience": ["LOGISTICIAN"]})

    changes = _sync(hw, since)
    assert changes["full"] is False
    ids = {c["id"] for c in changes["contacts"]}
    assert edit["id"] in ids and keep["id"] not in ids
    assert next(c for c in changes["contacts"] if c["id"] == edit["id"])["label"] == "Edited again"
    assert {off["id"], gone["id"], moved["id"]} <= set(changes["removed"])
    assert keep["id"] not in changes["removed"]
    # A naive timestamp is read as UTC; the server time is the next "since".
    assert _sync(hw, "2020-06-01T00:00:00")["full"] is False
    assert datetime.fromisoformat(changes["server_time"]) > datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_no_active_contacts_means_an_empty_deck(users):
    admin = _login(users["admin"])
    hw = _login(users["hw"])
    db = SessionLocal()
    others_active = db.query(SupportContact).filter(SupportContact.id.in_(users["existing"]) if users["existing"] else false(),
                                                    SupportContact.is_active.is_(True),
                                                    SupportContact.deleted_at.is_(None)).count()
    db.close()
    if others_active:
        pytest.skip("this database already has active support contacts")
    assert _sync(hw)["contacts"] == []
    a = _create(admin, is_active=False)
    b = _create(admin)
    client.delete(f"/support-contacts/{b['id']}", headers=admin)
    data = _sync(hw)
    assert data["contacts"] == [] and data["full"] is True, "inactive and deleted contacts are never sent"
    assert data["note"] in (None, ""), "the note is hidden unless an admin sets it"
    client.put(f"/support-contacts/{a['id']}/active", headers=admin, json={"active": True})
    assert [c["id"] for c in _sync(hw)["contacts"]] == [a["id"]]
