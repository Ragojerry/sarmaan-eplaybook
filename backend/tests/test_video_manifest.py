"""Videos on demand: the phone gets a video manifest (size, SHA-256, CDN URL,
version), never video bytes; files live in S3 behind CloudFront and are uploaded
straight from the admin browser; old apps keep working; the backfill script is
safe to run twice. S3 is replaced by FakeStorage here (no AWS calls)."""
import base64
import hashlib
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import video_storage
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AnalyticsEvent, AuditLog, Language, Module, RefreshToken, User, Video
from app.models.enums import RoleName, UserStatus, VideoStatus

client = TestClient(app)
PASSWORD = "TestPass123!"
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + bytes(range(256)) * 40
CDN = "https://cdn.example.test"


class FakeStorage:
    """Stands in for S3VideoStorage: remembers what was 'uploaded'."""

    def __init__(self):
        self.objects: dict[str, tuple[bytes, str]] = {}
        self.puts = 0

    def key_for(self, video_id, sha256, mime):
        return video_storage.object_key("videos", video_id, sha256, mime)

    def url(self, key):
        return f"{CDN}/{key}"

    def upload_target(self, key, mime, size, sha256):
        return {"url": f"https://s3.example.test/{key}?signed", "method": "PUT",
                "headers": video_storage.upload_headers(mime, sha256)}

    def stat(self, key):
        if key not in self.objects:
            return None
        data, mime = self.objects[key]
        return video_storage.Stat(size=len(data), sha256=hashlib.sha256(data).hexdigest(), content_type=mime, head=data[:16])

    def put_file(self, path, key, mime, sha256):
        self.puts += 1
        self.objects[key] = (Path(path).read_bytes(), mime)


@pytest.fixture()
def s3(monkeypatch):
    fake = FakeStorage()
    monkeypatch.setattr(video_storage, "current", lambda: fake)
    return fake


@pytest.fixture()
def db():
    session = SessionLocal()
    session.made_users, session.made_videos = [], []
    yield session
    session.rollback()
    vids = session.made_videos
    uids = session.made_users
    session.query(AnalyticsEvent).filter(AnalyticsEvent.user_id.in_(uids)).delete(synchronize_session=False)
    session.query(AuditLog).filter(AuditLog.entity_id.in_(vids)).delete(synchronize_session=False)
    session.query(Video).filter(Video.id.in_(vids)).delete(synchronize_session=False)
    for model in (RefreshToken, AuditLog):
        session.query(model).filter(model.user_id.in_(uids)).delete(synchronize_session=False)
    session.query(User).filter(User.id.in_(uids)).delete(synchronize_session=False)
    session.commit()
    session.close()


def _user(db, role):
    en = db.query(Language).filter_by(code="en").one()
    name = f"test_vman_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    u = User(username=name, email=f"{name}@sarmaan-eplaybook.app", password_hash=hash_password(PASSWORD),
             first_name="T", last_name="V", role=role, language_id=en.id, status=UserStatus.ACTIVE,
             learner_role="CDD" if role == RoleName.CDD else None)
    db.add(u)
    db.commit()
    db.made_users.append(u.id)
    r = client.post("/auth/login", json={"username": name, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return u, {"Authorization": f"Bearer {r.json()['access_token']}"}


def _video(db, *, status=VideoStatus.PUBLISHED, data=MP4, module_id=None, key=True, title="Demo"):
    vid = uuid.uuid4()
    sha = hashlib.sha256(data).hexdigest()
    storage_key = video_storage.object_key("videos", vid, sha, "video/mp4") if key else None
    v = Video(id=vid, title=title, module_id=module_id, filename=(storage_key or "NOT_YET_UPLOADED").rsplit("/", 1)[-1],
              storage_path=storage_key or "NOT_YET_UPLOADED", storage_key=storage_key, mime_type="video/mp4",
              file_size=len(data) if key else None, checksum=sha if key else None, duration_seconds=42,
              language="en", status=status)
    db.add(v)
    db.commit()
    db.made_videos.append(v.id)
    return v


def _visible_module(db, user):
    from app.learning.access import visible_modules
    mods = visible_modules(db, user)
    assert mods, "the test database needs at least one module visible to a CDD"
    return mods[0]


# --- Manifest ----------------------------------------------------------------

MANIFEST_KEYS = {"video_id", "module_id", "title", "language", "size_bytes", "duration_seconds", "content_hash",
                 "url", "version", "required_for_completion", "mime_type"}


def test_manifest_has_size_hash_and_url_for_every_published_video_and_no_bytes(db, s3):
    learner, h = _user(db, RoleName.CDD)
    mod = _visible_module(db, learner)
    shown = _video(db, module_id=mod.id, title="Shown")
    general = _video(db, title="For everyone")
    _video(db, status=VideoStatus.DRAFT, title="Draft")
    _video(db, key=False, title="No file yet")

    r = client.get("/sync/videos", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    entries = {e["video_id"]: e for e in body["videos"]}
    assert str(shown.id) in entries and str(general.id) in entries
    titles = {e["title"] for e in body["videos"]}
    assert "Draft" not in titles and "No file yet" not in titles
    for e in body["videos"]:
        assert set(e) == MANIFEST_KEYS
        assert e["size_bytes"] > 0 and len(e["content_hash"]) == 64
        assert e["url"].startswith(CDN + "/videos/") and e["url"].endswith(".mp4")
        assert e["required_for_completion"] is False and e["version"] >= 1
    e = entries[str(shown.id)]
    assert e["size_bytes"] == len(MP4) and e["content_hash"] == hashlib.sha256(MP4).hexdigest()
    assert e["module_id"] == str(mod.id) and e["duration_seconds"] == 42
    # Never video bytes, never a "download everything" instruction.
    raw = r.content
    assert MP4[:24] not in raw and base64.b64encode(MP4[:24]) not in raw
    assert len(raw) < 2000 * max(1, len(body["videos"]))
    assert "download_all" not in json.dumps(body) and "auto_download" not in json.dumps(body)


def test_manifest_hides_videos_of_modules_the_learner_cannot_see(db, s3):
    learner, h = _user(db, RoleName.CDD)
    visible = {m.id for m in __import__("app.learning.access", fromlist=["x"]).visible_modules(db, learner)}
    hidden = db.query(Module).filter(~Module.id.in_(visible)).first() if visible else None
    if hidden is None:
        pytest.skip("every module is visible to a CDD in this database")
    v = _video(db, module_id=hidden.id, title="Hidden")
    ids = {e["video_id"] for e in client.get("/sync/videos", headers=h).json()["videos"]}
    assert str(v.id) not in ids


def test_a_replaced_video_gets_a_new_version_and_url(db, s3):
    _, admin = _user(db, RoleName.CONTENT_ADMIN)
    v = _video(db, status=VideoStatus.DRAFT, key=False)
    first = _upload(s3, admin, v.id, MP4)
    second_bytes = MP4 + b"new-cut"
    second = _upload(s3, admin, v.id, second_bytes)
    assert second["version"] == first["version"] + 1
    db.refresh(v)
    assert v.storage_key != first["storage_key"] and v.checksum == hashlib.sha256(second_bytes).hexdigest()


# --- Direct-to-S3 upload -------------------------------------------------------

def _upload(s3, headers, video_id, data, mime="video/mp4"):
    sha = hashlib.sha256(data).hexdigest()
    r = client.post(f"/videos/{video_id}/upload-url", headers=headers,
                    json={"mime_type": mime, "size_bytes": len(data), "sha256": sha, "filename": "clip.mp4"})
    assert r.status_code == 200, r.text
    target = r.json()
    assert target["method"] == "PUT"
    assert target["headers"]["x-amz-checksum-sha256"] == base64.b64encode(bytes.fromhex(sha)).decode()
    assert target["headers"]["Content-Type"] == mime
    assert "immutable" in target["headers"]["Cache-Control"]
    s3.objects[target["key"]] = (data, mime)  # what the browser's PUT does
    r = client.post(f"/videos/{video_id}/upload-complete", headers=headers, json={"key": target["key"], "duration_seconds": 12})
    assert r.status_code == 200, r.text
    out = r.json()
    return {**out, "storage_key": target["key"]}


def test_direct_upload_records_size_hash_and_returns_published_video_to_draft(db, s3):
    _, admin = _user(db, RoleName.CONTENT_ADMIN)
    v = _video(db, status=VideoStatus.PUBLISHED, key=False)
    out = _upload(s3, admin, v.id, MP4)
    db.refresh(v)
    assert (v.file_size, v.checksum) == (len(MP4), hashlib.sha256(MP4).hexdigest())
    assert v.storage_key == out["storage_key"] and v.status == VideoStatus.DRAFT and v.duration_seconds == 12
    assert out["has_file"] is True


def test_upload_complete_refuses_a_file_that_does_not_match(db, s3):
    _, admin = _user(db, RoleName.CONTENT_ADMIN)
    v = _video(db, status=VideoStatus.DRAFT, key=False)
    sha = hashlib.sha256(MP4).hexdigest()
    target = client.post(f"/videos/{v.id}/upload-url", headers=admin,
                         json={"mime_type": "video/mp4", "size_bytes": len(MP4), "sha256": sha}).json()
    assert client.post(f"/videos/{v.id}/upload-complete", headers=admin, json={"key": target["key"]}).status_code == 422  # nothing uploaded
    s3.objects[target["key"]] = (b"not a video at all, just text", "video/mp4")
    assert client.post(f"/videos/{v.id}/upload-complete", headers=admin, json={"key": target["key"]}).status_code == 422
    other = video_storage.object_key("videos", uuid.uuid4(), sha, "video/mp4")
    assert client.post(f"/videos/{v.id}/upload-complete", headers=admin, json={"key": other}).status_code == 422
    db.refresh(v)
    assert v.storage_key is None and v.checksum is None


def test_upload_url_checks_type_size_and_role(db, s3):
    _, admin = _user(db, RoleName.CONTENT_ADMIN)
    _, learner = _user(db, RoleName.CDD)
    v = _video(db, status=VideoStatus.DRAFT, key=False)
    ok = {"mime_type": "video/mp4", "size_bytes": 1000, "sha256": "a" * 64}
    assert client.post(f"/videos/{v.id}/upload-url", headers=learner, json=ok).status_code == 403
    assert client.post(f"/videos/{v.id}/upload-url", headers=admin, json={**ok, "mime_type": "text/plain"}).status_code == 415
    assert client.post(f"/videos/{v.id}/upload-url", headers=admin, json={**ok, "size_bytes": 10 ** 12}).status_code == 413
    assert client.post(f"/videos/{v.id}/upload-url", headers=admin, json={**ok, "sha256": "xyz"}).status_code == 422


def test_s3_upload_link_is_signed_for_the_sha256_and_content_type():
    pytest.importorskip("boto3")
    store = video_storage.S3VideoStorage(bucket="example-bucket", prefix="videos", cdn_base_url=CDN, region="eu-north-1",
                                         credentials={"aws_access_key_id": "AKIAEXAMPLE", "aws_secret_access_key": "secret"})
    sha = hashlib.sha256(MP4).hexdigest()
    key = store.key_for(uuid.uuid4(), sha, "video/mp4")
    target = store.upload_target(key, "video/mp4", len(MP4), sha)
    signed = target["url"].split("X-Amz-SignedHeaders=")[1].split("&")[0].lower()
    assert "x-amz-checksum-sha256" in signed and "content-type" in signed
    assert "crc32" not in target["url"].lower()
    assert key in target["url"] and store.url(key) == f"{CDN}/{key}"


# --- Old apps ------------------------------------------------------------------

def test_old_apps_still_get_valid_sync_and_video_responses(db, s3):
    learner, h = _user(db, RoleName.CDD)
    v = _video(db, module_id=_visible_module(db, learner).id)
    learning = client.get("/sync/learning", headers=h)
    assert learning.status_code == 200 and "min_app_version" in learning.json()
    assert client.get("/sync/release/current", headers=h).status_code in (200, 404)
    meta = client.get(f"/videos/{v.id}", headers=h).json()
    for k in ("id", "title", "module_id", "duration_seconds", "file_size", "checksum", "language",
              "offline_available", "required_offline", "status", "has_file"):
        assert k in meta
    assert meta["file_size"] == len(MP4) and meta["checksum"] == hashlib.sha256(MP4).hexdigest()
    # Old apps download /videos/{id}/file: now a redirect to CloudFront, bytes never through the API.
    r = client.get(f"/videos/{v.id}/file", headers={**h, "Range": "bytes=10-"}, follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == f"{CDN}/{v.storage_key}"
    assert MP4[10:40] not in r.content


# --- Backfill ------------------------------------------------------------------

def test_backfill_is_safe_to_run_twice(db, s3, tmp_path, monkeypatch):
    from scripts import backfill_videos

    v = _video(db, status=VideoStatus.PUBLISHED, key=False)
    local = tmp_path / f"{v.id}_legacy.mp4"
    local.write_bytes(MP4)
    v.filename, v.storage_path = local.name, f"videos/{local.name}"
    db.commit()
    monkeypatch.setattr(backfill_videos, "local_path", lambda video: local if video.id == v.id else Path("/nonexistent"))

    first = backfill_videos.run(SessionLocal, only=[v.id])
    assert first == {"checked": 1, "hashed": 1, "uploaded": 1, "missing": 0}
    db.refresh(v)
    assert v.file_size == len(MP4) and v.checksum == hashlib.sha256(MP4).hexdigest() and v.storage_key in s3.objects
    second = backfill_videos.run(SessionLocal, only=[v.id])
    assert second == {"checked": 1, "hashed": 0, "uploaded": 0, "missing": 0}
    assert s3.puts == 1


# --- Download analytics --------------------------------------------------------

def test_download_completed_events_sync_once(db, s3):
    learner, h = _user(db, RoleName.CDD)
    v = _video(db)
    item = {"client_id": f"dl-{uuid.uuid4()}", "event_type": "DOWNLOAD_COMPLETED", "video_id": str(v.id),
            "occurred_at": "2026-11-14T10:00:00Z", "payload": {"bytes": len(MP4)}}
    for _ in range(2):
        r = client.post("/sync/analytics", headers=h, json={"device_id": "test-device", "items": [item]})
        assert r.status_code == 200, r.text
    assert db.query(AnalyticsEvent).filter_by(user_id=learner.id, video_id=v.id).count() == 1
    from datetime import datetime, timezone
    now = {**item, "client_id": f"dl-{uuid.uuid4()}", "occurred_at": datetime.now(timezone.utc).isoformat()}
    client.post("/sync/analytics", headers=h, json={"device_id": "test-device", "items": [now]})
    _, admin = _user(db, RoleName.SUPER_ADMIN)
    rows = {r["video_id"]: r for r in client.get("/analytics/usage", headers=admin).json()["videos"]}
    assert rows[str(v.id)]["downloads_completed"] >= 1


# --- Video sections ------------------------------------------------------------

def test_a_video_section_uploads_straight_to_storage(db, s3):
    from app.models import ContentSection
    from app.models.enums import ContentType

    _, admin = _user(db, RoleName.CONTENT_ADMIN)
    m = Module(module_code=f"VMAN-{uuid.uuid4().hex[:6]}", module_number=97, title="Video section test", sort_order=97)
    db.add(m)
    db.commit()
    try:
        s = ContentSection(module_id=m.id, section_number=1, sort_order=1, content_type=ContentType.VIDEO, title="Clip", content={})
        db.add(s)
        db.commit()
        # The old multipart route refuses videos once storage is S3.
        r = client.post(f"/modules/sections/{s.id}/media", headers=admin, files={"file": ("c.mp4", MP4, "video/mp4")})
        assert r.status_code == 409
        r = client.post(f"/modules/sections/{s.id}/video", headers=admin)
        assert r.status_code == 200, r.text
        video_id = r.json()["video_id"]
        db.made_videos.append(uuid.UUID(video_id))
        assert client.post(f"/modules/sections/{s.id}/video", headers=admin).json()["video_id"] == video_id  # same video again
        _upload(s3, admin, video_id, MP4)
        db.expire_all()
        content = db.get(ContentSection, s.id).content
        assert content["video_id"] == video_id and content["size_bytes"] == len(MP4) and content["mime_type"] == "video/mp4"
    finally:
        db.rollback()
        db.query(ContentSection).filter_by(module_id=m.id).delete()
        db.commit()
        db.query(AuditLog).filter(AuditLog.entity_type == "content_section").filter(
            AuditLog.details["video_id"].astext.in_([str(v) for v in db.made_videos])).delete(synchronize_session=False)
        db.query(Video).filter(Video.module_id == m.id).delete(synchronize_session=False)
        db.delete(db.get(Module, m.id))
        db.commit()
