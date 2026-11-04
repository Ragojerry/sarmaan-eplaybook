"""Editable, translatable consent text: public reading, who may edit what,
versioning, outdated-translation flags and the audit trail."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, ConsentText, Language, RefreshToken, User
from app.models.enums import AuditAction, RoleName, UserStatus

client = TestClient(app)

HAUSA = {
    "title": "Kafin ka fara",
    "body": "Ana amfani da wannan manhaja wajen koyar da masu raba magani (CDD) game da AZM.",
    "usage_label": "Raba bayanan amfani ba tare da suna ba (na zaɓi)",
    "button_label": "Na yarda, ci gaba",
}


def _make_user(db, role):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_consent_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username, email=f"{username}@sarmaan-eplaybook.app", password_hash=hash_password("TestPass123!"),
        first_name="Test", last_name=role.value, role=role, language_id=english.id, status=UserStatus.ACTIVE,
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
    original = {f: getattr(db.get(ConsentText, "en"), f) for f in ("title", "body", "usage_label", "button_label", "version")}
    made = {r: _make_user(db, r) for r in (RoleName.CONTENT_ADMIN, RoleName.LOCALISATION_REVIEWER, RoleName.CDD)}
    yield made
    ids = [u.id for u in made.values()]
    db.query(ConsentText).filter(ConsentText.language != "en").delete()
    en = db.get(ConsentText, "en")
    for f, v in original.items():
        setattr(en, f, v)
    en.updated_by = None
    db.flush()
    for model in (RefreshToken, AuditLog):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def _texts():
    resp = client.get("/consent")
    assert resp.status_code == 200
    return {c["language"]: c for c in resp.json()}


def test_public_and_seeded_with_the_text_the_app_showed():
    en = _texts()["en"]
    assert en["title"] == "Before you start" and en["button_label"] == "Agree and continue"
    assert "Community Drug Distributors" in en["body"] and en["version"] >= 1 and en["outdated"] is False


def test_translate_edit_and_flag_outdated_translations(users):
    admin = _login(users[RoleName.CONTENT_ADMIN])
    translator = _login(users[RoleName.LOCALISATION_REVIEWER])
    en_version = _texts()["en"]["version"]

    ha = client.put("/consent/ha", headers=translator, json=HAUSA)
    assert ha.status_code == 200, ha.text
    assert ha.json()["version"] == 1 and ha.json()["outdated"] is False
    assert _texts()["ha"]["title"] == "Kafin ka fara"

    # Saving identical text changes nothing.
    assert client.put("/consent/ha", headers=translator, json=HAUSA).json()["version"] == 1

    # English changes -> the Hausa translation is flagged until it is updated.
    en = {**{k: _texts()["en"][k] for k in HAUSA}, "body": "This app delivers AZM training to CDDs. " * 2}
    assert client.put("/consent/en", headers=admin, json=en).json()["version"] == en_version + 1
    assert _texts()["ha"]["outdated"] is True
    assert client.put("/consent/ha", headers=translator, json={**HAUSA, "title": "Kafin ka fara!"}).json()["outdated"] is False

    db = SessionLocal()
    logs = db.query(AuditLog).filter_by(action=AuditAction.CONSENT_UPDATE).filter(
        AuditLog.user_id.in_([users[RoleName.CONTENT_ADMIN].id, users[RoleName.LOCALISATION_REVIEWER].id])).all()
    db.close()
    assert len(logs) == 3
    english_log = next(log for log in logs if log.details["language"] == "en")
    assert english_log.details["previous"]["title"] == "Before you start" and english_log.details["new"]["body"] == en["body"].strip()

    assert client.delete("/consent/ha", headers=translator).status_code == 204
    assert "ha" not in _texts()
    assert client.delete("/consent/en", headers=admin).status_code == 409


def test_permissions_and_validation(users):
    translator = _login(users[RoleName.LOCALISATION_REVIEWER])
    cdd = _login(users[RoleName.CDD])
    assert client.put("/consent/ha", json=HAUSA).status_code == 401
    assert client.put("/consent/ha", headers=cdd, json=HAUSA).status_code == 403
    assert client.put("/consent/en", headers=translator, json=HAUSA).status_code == 403, "English is the source"
    assert client.put("/consent/xx", headers=translator, json=HAUSA).status_code == 404
    assert client.put("/consent/ha", headers=translator, json={**HAUSA, "body": "short"}).status_code == 422
