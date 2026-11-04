"""Reference library: upload, text extraction, review/approval rules and
permissions, and answering from approved documents."""
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.ai.reference_text import DOCX, PDF, TEXT, UnreadableDocument, extract_passages
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AiQuestionLog, AuditLog, Language, RefreshToken, ReferenceDocument, User
from app.models.enums import AuditAction, RoleName, UserStatus

client = TestClient(app)

GUIDE = b"""# Storage

Keep AZM bottles in a cool, dry place away from direct sunlight.
Do not freeze the suspension.

# Disposal

Return empty bottles to the health facility at the end of each day.
"""


def minimal_pdf(text: str) -> bytes:
    """A one-page PDF with real (selectable) text, built by hand."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def minimal_docx() -> bytes:
    import docx

    d = docx.Document()
    d.add_heading("Referral", level=1)
    d.add_paragraph("Refer any child with convulsions to the nearest health facility immediately.")
    table = d.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Sign"
    table.cell(0, 1).text = "Action"
    table.cell(1, 0).text = "Convulsions"
    table.cell(1, 1).text = "Refer now"
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


# ---------- extraction ----------
def test_text_and_markdown_headings_label_passages():
    mime, passages = extract_passages(GUIDE)
    assert mime == TEXT
    assert passages[0] == ("Storage", "Keep AZM bottles in a cool, dry place away from direct sunlight. Do not freeze the suspension.")
    assert passages[1][0] == "Disposal"


def test_pdf_text_is_read_per_page():
    mime, passages = extract_passages(minimal_pdf("Give AZM only to healthy children."))
    assert mime == PDF
    assert passages == [("Page 1", "Give AZM only to healthy children.")]


def test_docx_headings_and_tables_are_read():
    mime, passages = extract_passages(minimal_docx())
    assert mime == DOCX
    assert ("Referral", "Refer any child with convulsions to the nearest health facility immediately.") in passages
    assert ("Table", "Sign; Action. Convulsions; Refer now.") in passages


def test_long_sections_are_split_at_paragraphs():
    para = "Sentence about dosing. " * 30  # ~690 chars
    _, passages = extract_passages(f"# Dosing\n\n{para}\n\n{para}\n".encode())
    assert len(passages) == 2 and all(h == "Dosing" for h, _ in passages)


@pytest.mark.parametrize("data", [b"\x00\xff\xfe binary", b"PK\x03\x04not really a zip", minimal_pdf("")])
def test_unreadable_files_are_rejected(data):
    with pytest.raises(UnreadableDocument):
        extract_passages(data)


# ---------- API ----------
def _make_user(db, role):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_ref_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
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
    made = {role: _make_user(db, role) for role in (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.CDD)}
    yield made
    ids = [u.id for u in made.values()]
    db.query(ReferenceDocument).filter(ReferenceDocument.uploaded_by.in_(ids)).delete(synchronize_session=False)
    for model in (AiQuestionLog, RefreshToken, AuditLog):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def _upload(headers, data=GUIDE, filename="guide.md", title="AZM storage guide"):
    return client.post("/references", headers=headers, data={"title": title},
                       files={"file": (filename, data, "application/octet-stream")})


def test_upload_review_approve_archive_delete(users):
    admin = _login(users[RoleName.CONTENT_ADMIN])
    reviewer = _login(users[RoleName.PROGRAM_REVIEWER])

    resp = _upload(admin)
    assert resp.status_code == 201, resp.text
    doc = resp.json()
    assert doc["status"] == "DRAFT" and doc["passage_count"] == 2 and doc["mime_type"] == TEXT

    passages = client.get(f"/references/{doc['id']}/passages", headers=reviewer).json()
    assert [p["heading"] for p in passages] == ["Storage", "Disposal"]
    original = client.get(f"/references/{doc['id']}/file", headers=reviewer)
    assert original.status_code == 200 and original.content == GUIDE

    approved = client.patch(f"/references/{doc['id']}", headers=reviewer, json={"status": "APPROVED"}).json()
    assert approved["status"] == "APPROVED" and approved["approved_by"] == str(users[RoleName.PROGRAM_REVIEWER].id)
    assert client.delete(f"/references/{doc['id']}", headers=admin).status_code == 409

    assert client.patch(f"/references/{doc['id']}", headers=reviewer, json={"status": "ARCHIVED"}).status_code == 200
    assert client.delete(f"/references/{doc['id']}", headers=admin).status_code == 204
    assert client.get(f"/references/{doc['id']}/passages", headers=admin).status_code == 404

    db = SessionLocal()
    actions = [a.action for a in db.query(AuditLog).filter_by(entity_id=uuid.UUID(doc["id"])).all()]
    db.close()
    assert actions.count(AuditAction.REFERENCE_UPLOAD) == 1 and actions.count(AuditAction.REFERENCE_UPDATE) == 3


def test_permissions(users):
    admin = _login(users[RoleName.CONTENT_ADMIN])
    reviewer = _login(users[RoleName.PROGRAM_REVIEWER])
    cdd = _login(users[RoleName.CDD])

    assert client.get("/references", headers=cdd).status_code == 403
    assert _upload(cdd).status_code == 403
    assert _upload(reviewer).status_code == 403, "reviewers approve; content admins upload"
    doc = _upload(admin).json()
    assert client.patch(f"/references/{doc['id']}", headers=reviewer, json={"title": "Renamed"}).status_code == 403
    assert client.patch(f"/references/{doc['id']}", headers=cdd, json={"status": "APPROVED"}).status_code == 403
    assert client.get(f"/references/{doc['id']}/file", headers=cdd).status_code == 403


def test_bad_uploads_are_explained(users, monkeypatch):
    admin = _login(users[RoleName.CONTENT_ADMIN])
    resp = _upload(admin, data=minimal_pdf(""), filename="scan.pdf")
    assert resp.status_code == 422 and "Scanned" in resp.json()["detail"]
    assert _upload(admin, data=b"", filename="empty.txt").status_code == 422

    from app.routers import references

    monkeypatch.setattr(references.settings, "max_reference_upload_mb", 0)
    assert _upload(admin).status_code == 413


# ---------- answering from the library ----------
def test_only_approved_documents_answer_and_only_when_modules_cannot(users):
    from scripts import build_content_index

    build_content_index.run()
    admin = _login(users[RoleName.CONTENT_ADMIN])
    cdd = _login(users[RoleName.CDD])
    store = {"question": "Can I freeze the suspension?"}
    doc = _upload(admin).json()

    draft = client.post("/ai/ask", headers=cdd, json=store).json()
    assert draft["matched"] is False, "a draft is never quoted"

    client.patch(f"/references/{doc['id']}", headers=admin, json={"status": "APPROVED"})
    r = client.post("/ai/ask", headers=cdd, json=store).json()
    assert r["matched"] and "Do not freeze the suspension." in r["answer"]
    src = r["sources"][0]
    assert src["kind"] == "reference" and src["module_code"] == "REF" and src["module_id"] is None
    assert src["module_title"] == "AZM storage guide" and src["section_title"] == "Storage"

    # The modules answer this one, so the library is not consulted.
    vomit = client.post("/ai/ask", headers=cdd,
                        json={"question": "What should I do if the child vomits after the medicine?"}).json()
    assert vomit["sources"][0]["kind"] == "module" and vomit["sources"][0]["module_code"] == "M4"

    client.patch(f"/references/{doc['id']}", headers=admin, json={"status": "ARCHIVED"})
    assert client.post("/ai/ask", headers=cdd, json=store).json()["matched"] is False

    db = SessionLocal()
    rows = db.query(AiQuestionLog).filter_by(user_id=users[RoleName.CDD].id).all()
    assert len(rows) == 4 and sum(r.matched for r in rows) == 2
    assert all(r.source_module_id is None for r in rows if r.matched and "freeze" in (r.answer or ""))
    db.close()
