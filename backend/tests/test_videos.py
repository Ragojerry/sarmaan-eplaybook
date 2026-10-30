"""
Phase 9 automated tests: video upload, full download, resumable (Range)
download, checksum integrity, and RBAC on the upload/patch endpoints.
Uses a tiny real MP4 generated at import time (not a mocked byte string) so
the checksum/Range-slicing logic is exercised against real binary content.
"""
import hashlib
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User, Language, Video, RefreshToken, AuditLog
from app.models.content_release import ContentRelease
from app.models.enums import RoleName, UserStatus, VideoStatus
from app.auth.security import hash_password

client = TestClient(app)

# A minimal, structurally valid (if not playable) MP4 container: an `ftyp`
# box declaring the isom brand, enough for this test's purposes since we
# only care about byte-for-byte integrity through upload/download/resume,
# not actual video decoding.
_TEST_VIDEO_BYTES = (
    b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
    + b"\x00\x00\x00\x08free"
    + bytes(range(256)) * 20  # padding so Range-slicing has something to bite into
)


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
def cdd_user(db, english):
    user = _make_user(db, RoleName.CDD, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def test_video(db):
    video = Video(
        title="Test Video",
        description="A video created for automated Phase 9 tests.",
        filename="NOT_YET_UPLOADED",
        storage_path="NOT_YET_UPLOADED",
        mime_type="video/mp4",
        language="en",
        offline_available=False,
        required_offline=False,
        status=VideoStatus.DRAFT,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    video_id = video.id
    yield video_id
    db.expire_all()  # the API (another session) changed the row; don't read a stale cached copy
    v = db.get(Video, video_id)
    if v:
        if v.filename != "NOT_YET_UPLOADED":
            from app.routers.videos import _video_path

            _video_path(v).unlink(missing_ok=True)  # don't leave test footage on disk
        db.delete(v)
        db.commit()


def test_cdd_cannot_upload_video(cdd_user, test_video):
    token = _login(cdd_user.username)
    resp = client.post(
        f"/videos/{test_video}/file",
        headers=_auth_headers(token),
        files={"file": ("test.mp4", io.BytesIO(_TEST_VIDEO_BYTES), "video/mp4")},
    )
    assert resp.status_code == 403


def test_content_admin_can_upload_video(content_admin, test_video):
    token = _login(content_admin.username)
    resp = client.post(
        f"/videos/{test_video}/file",
        headers=_auth_headers(token),
        files={"file": ("test.mp4", io.BytesIO(_TEST_VIDEO_BYTES), "video/mp4")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["has_file"] is True
    assert body["checksum"] == hashlib.sha256(_TEST_VIDEO_BYTES).hexdigest()
    assert body["file_size"] == len(_TEST_VIDEO_BYTES)


def test_full_download_matches_uploaded_bytes(content_admin, cdd_user, test_video):
    admin_token = _login(content_admin.username)
    client.post(
        f"/videos/{test_video}/file",
        headers=_auth_headers(admin_token),
        files={"file": ("test.mp4", io.BytesIO(_TEST_VIDEO_BYTES), "video/mp4")},
    )

    cdd_token = _login(cdd_user.username)
    # Still a DRAFT: learners cannot see or download it.
    assert client.get(f"/videos/{test_video}/file", headers=_auth_headers(cdd_token)).status_code == 404

    pub = client.patch(f"/videos/{test_video}", headers=_auth_headers(admin_token), json={"status": "PUBLISHED"})
    assert pub.status_code == 200, pub.text

    # Once PUBLISHED, any authenticated role (not just CONTENT_ADMIN) can download.
    resp = client.get(f"/videos/{test_video}/file", headers=_auth_headers(cdd_token))
    assert resp.status_code == 200
    assert resp.content == _TEST_VIDEO_BYTES
    assert resp.headers["accept-ranges"] == "bytes"


def test_resumed_range_download_reassembles_correctly(content_admin, test_video):
    admin_token = _login(content_admin.username)
    client.post(
        f"/videos/{test_video}/file",
        headers=_auth_headers(admin_token),
        files={"file": ("test.mp4", io.BytesIO(_TEST_VIDEO_BYTES), "video/mp4")},
    )

    split_point = 3000
    already_have = _TEST_VIDEO_BYTES[:split_point]

    resp = client.get(
        f"/videos/{test_video}/file",
        headers={**_auth_headers(admin_token), "Range": f"bytes={split_point}-"},
    )
    assert resp.status_code == 206
    assert resp.headers["content-range"] == f"bytes {split_point}-{len(_TEST_VIDEO_BYTES) - 1}/{len(_TEST_VIDEO_BYTES)}"

    reassembled = already_have + resp.content
    assert reassembled == _TEST_VIDEO_BYTES
    assert hashlib.sha256(reassembled).hexdigest() == hashlib.sha256(_TEST_VIDEO_BYTES).hexdigest()


def test_invalid_range_returns_416(content_admin, test_video):
    admin_token = _login(content_admin.username)
    client.post(
        f"/videos/{test_video}/file",
        headers=_auth_headers(admin_token),
        files={"file": ("test.mp4", io.BytesIO(_TEST_VIDEO_BYTES), "video/mp4")},
    )
    resp = client.get(
        f"/videos/{test_video}/file",
        headers={**_auth_headers(admin_token), "Range": "bytes=999999999-"},
    )
    assert resp.status_code == 416


def test_download_before_upload_returns_404(cdd_user, test_video):
    token = _login(cdd_user.username)
    resp = client.get(f"/videos/{test_video}/file", headers=_auth_headers(token))
    assert resp.status_code == 404


def test_required_offline_flag_update(content_admin, test_video):
    token = _login(content_admin.username)
    resp = client.patch(f"/videos/{test_video}?required_offline=true", headers=_auth_headers(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["required_offline"] is True



# ---------- Phase 14 backlog: admin video management ----------

from app.models import Module  # noqa: E402


@pytest.fixture()
def created(db):
    """Video rows created through the API; removed (rows + files) afterwards."""
    ids = []
    yield ids
    from app.routers.videos import _video_path

    db.expire_all()
    for vid in ids:
        v = db.get(Video, vid)
        if v is None:
            continue
        if v.filename != "NOT_YET_UPLOADED":
            _video_path(v).unlink(missing_ok=True)
        db.delete(v)
    db.commit()


def _create(h, created, **extra):
    r = client.post("/videos", headers=h, json={"title": f"AdminTest {uuid.uuid4().hex[:6]}", **extra})
    assert r.status_code == 201, r.text
    created.append(uuid.UUID(r.json()["id"]))
    return r.json()


def _upload(h, vid, data=_TEST_VIDEO_BYTES, ctype="video/mp4", name="clip.mp4", **form):
    return client.post(f"/videos/{vid}/file", headers=h, files={"file": (name, io.BytesIO(data), ctype)}, data=form)


def test_admin_creates_uploads_and_publishes(db, content_admin, cdd_user, created):
    h = _auth_headers(_login(content_admin.username))
    ch = _auth_headers(_login(cdd_user.username))
    module_id = str(db.query(Module).first().id)
    v = _create(h, created, module_id=module_id, required_offline=True)
    assert v["status"] == "DRAFT" and v["has_file"] is False and v["module_id"] == module_id

    # cannot publish without footage
    assert client.patch(f"/videos/{v['id']}", headers=h, json={"status": "PUBLISHED"}).status_code == 409

    up = _upload(h, v["id"], duration_seconds="95")
    assert up.status_code == 200, up.text
    body = up.json()
    assert body["has_file"] and body["file_size"] == len(_TEST_VIDEO_BYTES) and body["duration_seconds"] == 95
    import hashlib

    assert body["checksum"] == hashlib.sha256(_TEST_VIDEO_BYTES).hexdigest()

    pub = client.patch(f"/videos/{v['id']}", headers=h, json={"status": "PUBLISHED"}).json()
    assert pub["status"] == "PUBLISHED" and pub["offline_available"] is True

    # learners now see it; the audit trail has it
    assert v["id"] in [x["id"] for x in client.get("/videos", headers=ch).json()]
    actions = {a.action.value for a in db.query(AuditLog).filter_by(entity_id=uuid.UUID(v["id"])).all()}
    assert {"CONTENT_CREATE", "VIDEO_UPLOAD", "VIDEO_UPDATE"} <= actions


def test_learners_do_not_see_drafts(db, content_admin, cdd_user, created):
    h = _auth_headers(_login(content_admin.username))
    ch = _auth_headers(_login(cdd_user.username))
    v = _create(h, created)
    assert v["id"] not in [x["id"] for x in client.get("/videos", headers=ch).json()]
    assert client.get(f"/videos/{v['id']}", headers=ch).status_code == 404
    assert v["id"] in [x["id"] for x in client.get("/videos", headers=h).json()]
    assert client.post("/videos", headers=ch, json={"title": "x"}).status_code == 403


def test_replacing_published_footage_returns_it_to_draft(db, content_admin, created):
    from app.routers.videos import _video_path

    h = _auth_headers(_login(content_admin.username))
    v = _create(h, created)
    _upload(h, v["id"])
    client.patch(f"/videos/{v['id']}", headers=h, json={"status": "PUBLISHED"})
    old_path = _video_path(db.get(Video, uuid.UUID(v["id"])))
    assert old_path.exists()

    new_bytes = _TEST_VIDEO_BYTES + b"extra"
    r = _upload(h, v["id"], data=new_bytes)
    assert r.status_code == 200
    assert r.json()["status"] == "DRAFT" and r.json()["offline_available"] is False
    assert r.json()["file_size"] == len(new_bytes)
    assert not old_path.exists()  # superseded file removed only after the swap


def test_upload_rejects_bad_type_fake_video_empty_and_oversize(db, content_admin, created, monkeypatch):
    h = _auth_headers(_login(content_admin.username))
    v = _create(h, created)
    assert _upload(h, v["id"], ctype="application/pdf", name="x.pdf").status_code == 415
    assert _upload(h, v["id"], data=b"MZ\x90\x00 this is not a video at all", name="evil.mp4").status_code == 415
    assert _upload(h, v["id"], data=b"").status_code == 400
    import app.routers.videos as vr

    monkeypatch.setattr(vr.settings, "max_video_upload_mb", 0)
    assert _upload(h, v["id"]).status_code == 413
    # nothing was left behind or recorded
    db.expire_all()
    assert db.get(Video, uuid.UUID(v["id"])).filename == "NOT_YET_UPLOADED"
    assert not list(vr._video_root().glob(f"{v['id']}*"))


def test_update_validates_module_and_edits_metadata(db, content_admin, created):
    h = _auth_headers(_login(content_admin.username))
    v = _create(h, created)
    assert client.patch(f"/videos/{v['id']}", headers=h, json={"module_id": str(uuid.uuid4())}).status_code == 422
    r = client.patch(f"/videos/{v['id']}", headers=h, json={"title": "Renamed", "language": "ha", "required_offline": True})
    assert r.status_code == 200 and r.json()["title"] == "Renamed" and r.json()["language"] == "ha"
