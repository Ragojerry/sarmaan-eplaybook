"""Curated answers: the review flow, permissions, and how approved answers
reach the Ask assistant online (/ai/ask), phones (/ai/chunks) and release
packages. Matching itself is covered by the parity vectors (test_qa.py)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.ai import qa_engine as qa
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AiQuestionLog, AuditLog, ContentRelease, FaqEntry, Language, Module, RefreshToken, User
from app.models.enums import AuditAction, ModuleStatus, RoleName, UserStatus
from app.releases.packager import build_package
from scripts import build_content_index

client = TestClient(app)

DOOR = "What do I write on the door?"
DOOR_ANSWER = "Write the house-marking code in chalk on the door frame."


def _make_user(db, role):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_faq_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
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
    build_content_index.run()
    db = SessionLocal()
    made = {r: _make_user(db, r) for r in (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.CDD)}
    yield made
    ids = [u.id for u in made.values()]
    db.query(FaqEntry).filter(FaqEntry.created_by.in_(ids)).delete(synchronize_session=False)
    for model in (AiQuestionLog, RefreshToken, AuditLog):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(ContentRelease).filter(ContentRelease.created_by.in_(ids)).update({"created_by": None})
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture()
def m4_id():
    db = SessionLocal()
    m = db.query(Module).filter_by(module_code="M4", status=ModuleStatus.PUBLISHED).first()
    db.close()
    assert m is not None
    return str(m.id)


def _create(headers, module_id, **extra):
    body = {"question": DOOR, "answer": DOOR_ANSWER, "module_id": module_id,
            "alternates": "What goes on the door frame?\n\n", "source_question": "what do i write on the door", **extra}
    return client.post("/faqs", headers=headers, json=body)


def _ask(headers, question):
    return client.post("/ai/ask", headers=headers, json={"question": question}).json()


def test_review_flow_and_where_approved_answers_go(users, m4_id):
    admin = _login(users[RoleName.CONTENT_ADMIN])
    reviewer = _login(users[RoleName.PROGRAM_REVIEWER])
    cdd = _login(users[RoleName.CDD])

    assert _ask(cdd, DOOR)["matched"] is False, "the modules alone cannot answer this"
    resp = _create(admin, m4_id)
    assert resp.status_code == 201, resp.text
    faq = resp.json()
    assert faq["status"] == "DRAFT" and faq["module_code"] == "M4" and faq["alternates"] == "What goes on the door frame?"
    assert _ask(cdd, DOOR)["matched"] is False, "a draft is never used"

    approved = client.patch(f"/faqs/{faq['id']}", headers=reviewer, json={"status": "APPROVED"}).json()
    assert approved["status"] == "APPROVED" and approved["approved_by"] == str(users[RoleName.PROGRAM_REVIEWER].id)

    # Online, at once — in other words too.
    for question in (DOOR, "what should I write on the door", "What goes on the door frame?"):
        r = _ask(cdd, question)
        assert r["matched"] and r["answer"] == DOOR_ANSWER, question
        assert r["sources"][0]["chunk_id"] == faq["id"] and r["sources"][0]["module_code"] == "M4"

    # To phones: the content sync and the next release package.
    chunks = client.get("/ai/chunks?language=en", headers=cdd).json()
    served = [c for c in chunks if c["id"] == faq["id"]]
    assert served and served[0]["faq_questions"] == [DOOR, "What goes on the door frame?"]
    assert all(c["faq_questions"] is None for c in chunks if c["id"] != faq["id"] and c["section_title"] != DOOR)
    db = SessionLocal()
    package = build_package(db, ContentRelease(release_code="TEST-FAQ", version="0.0.0", mandatory=False))
    db.close()
    packaged = [c for c in package["chunks"] if c["id"] == faq["id"]]
    assert packaged and packaged[0]["chunk_text"] == DOOR_ANSWER
    assert package["counts"]["chunks"] == len(package["chunks"])

    # Editing an approved answer takes it out of use until it is re-approved.
    edited = client.patch(f"/faqs/{faq['id']}", headers=admin, json={"answer": "Write the code in chalk."}).json()
    assert edited["status"] == "DRAFT"
    assert _ask(cdd, DOOR)["matched"] is False

    client.patch(f"/faqs/{faq['id']}", headers=reviewer, json={"status": "APPROVED"})
    assert client.delete(f"/faqs/{faq['id']}", headers=admin).status_code == 409
    client.patch(f"/faqs/{faq['id']}", headers=reviewer, json={"status": "ARCHIVED"})
    assert _ask(cdd, DOOR)["matched"] is False
    assert client.delete(f"/faqs/{faq['id']}", headers=admin).status_code == 204

    db = SessionLocal()
    actions = [a.action for a in db.query(AuditLog).filter_by(entity_id=uuid.UUID(faq["id"])).all()]
    db.close()
    assert actions.count(AuditAction.FAQ_CREATE) == 1 and actions.count(AuditAction.FAQ_UPDATE) == 5


def test_permissions_and_validation(users, m4_id):
    admin = _login(users[RoleName.CONTENT_ADMIN])
    reviewer = _login(users[RoleName.PROGRAM_REVIEWER])
    cdd = _login(users[RoleName.CDD])

    assert client.get("/faqs", headers=cdd).status_code == 403
    assert _create(cdd, m4_id).status_code == 403
    assert _create(reviewer, m4_id).status_code == 403, "reviewers approve; content admins write"
    faq = _create(admin, m4_id).json()
    assert client.patch(f"/faqs/{faq['id']}", headers=reviewer, json={"answer": "Changed"}).status_code == 403
    assert client.patch(f"/faqs/{faq['id']}", headers=cdd, json={"status": "APPROVED"}).status_code == 403

    assert _create(admin, str(uuid.uuid4())).status_code == 422, "unknown module"
    bad = _create(admin, m4_id, alternates="what is it?")
    assert bad.status_code == 422 and "no words" in bad.json()["detail"]
    listed = client.get("/faqs?status=DRAFT", headers=reviewer).json()
    assert any(f["id"] == faq["id"] for f in listed)


def test_a_curated_answer_never_answers_a_different_age():
    chunks = [{"id": "f1", "module_id": None, "section_id": None, "module_code": "M4", "source_title": "M4",
               "section_title": "dose", "chunk_text": "Give 4 ml.", "faq_questions": ["How much AZM for an 8 month old?"]}]
    assert qa.answer_question("How much AZM for an 8 month old?", chunks)["matched"]
    assert not qa.answer_question("How much AZM for a 3 month old?", chunks)["matched"]
    assert not qa.answer_question("How much AZM for a 2 year old?", chunks)["matched"]
