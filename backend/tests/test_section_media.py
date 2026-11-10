"""
Audio/video files on content sections (app/routers/section_media.py): upload,
replace, remove, byte-based type checks, size limits, permissions, audit
entries, and that release packages carry section audio. Files are written to a
temporary storage folder, never to the real content/ folder.
"""
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.content import media_upload
from app.database import SessionLocal
from app.main import app
from app.models import AuditLog, ContentSection, Language, MediaAsset, Module, Video
from app.models.enums import AuditAction, MediaAssetType, RoleName, VideoStatus
from app.releases.variants import _media_ids
from tests.test_videos import _auth_headers, _cleanup_user, _login, _make_user

client = TestClient(app)
settings = get_settings()

MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + bytes(range(256)) * 8
M4A = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00M4A mp42isom" + bytes(200)
WAV = b"RIFF\x24\x08\x00\x00WAVEfmt " + bytes(200)
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + bytes(range(256)) * 8
WEBM = b"\x1a\x45\xdf\xa3" + bytes(300)
PNG = b"\x89PNG\r\n\x1a\n" + bytes(200)


@pytest.fixture()
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def storage(tmp_path, monkeypatch):
    """Points media storage at a temporary folder (videos go to its sibling `videos/`)."""
    media = tmp_path / "media"
    media.mkdir()
    monkeypatch.setattr(settings, "storage_local_path", str(media))
    return tmp_path


@pytest.fixture()
def english(db):
    return db.query(Language).filter_by(code="en").one()


@pytest.fixture()
def admin(db, english):
    user = _make_user(db, RoleName.CONTENT_ADMIN, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def cdd(db, english):
    user = _make_user(db, RoleName.CDD, english.id)
    yield user
    _cleanup_user(db, user)


@pytest.fixture()
def module(db):
    m = Module(module_code=f"MEDIA-{uuid.uuid4().hex[:6]}", module_number=98, title="Media test", sort_order=98)
    db.add(m)
    db.commit()
    yield m
    db.rollback()
    db.query(ContentSection).filter_by(module_id=m.id).delete()
    vids = db.query(Video).filter_by(module_id=m.id).all()
    for v in vids:
        db.delete(v)
    db.query(MediaAsset).filter(MediaAsset.asset_metadata["source"].astext == "section_upload").delete(
        synchronize_session=False)
    db.delete(db.get(Module, m.id))
    db.commit()


def _section(db, module, content_type):
    s = ContentSection(module_id=module.id, section_number=1, sort_order=1, content_type=content_type,
                       title="A section", content={"text": "keep me"})
    db.add(s)
    db.commit()
    return str(s.id)


def _upload(token, section_id, data, name="file.bin", ctype="application/octet-stream"):
    return client.post(f"/modules/sections/{section_id}/media", files={"file": (name, data, ctype)},
                       headers=_auth_headers(token))


def _audit(db, section_id, action):
    db.expire_all()
    return db.query(AuditLog).filter_by(entity_id=uuid.UUID(section_id), action=action).all()


# ---------- Type detection (bytes, not names) ----------

@pytest.mark.parametrize("data,fmt", [(MP3, "mp3"), (M4A, "m4a"), (WAV, "wav"), (b"\xff\xfb\x90\x00" + bytes(20), "mp3")])
def test_audio_is_recognised_from_bytes(data, fmt):
    assert media_upload.sniff_audio(data[:16]).fmt == fmt


def test_video_container_is_never_taken_for_audio():
    assert media_upload.sniff_audio(MP4[:16]) is None
    assert media_upload.sniff_video(MP4[:16]).fmt == "mp4"
    assert media_upload.sniff_video(M4A[:16]) is None
    assert media_upload.sniff_video(WEBM[:16]).fmt == "webm"


# ---------- Audio ----------

def test_admin_uploads_audio_and_learners_can_fetch_it(db, admin, cdd, module, storage):
    sid = _section(db, module, "AUDIO")
    resp = _upload(_login(admin.username), sid, MP3, name="../../lesson one.mp3", ctype="video/mp4")
    assert resp.status_code == 200, resp.text
    content = resp.json()["content"]
    assert content["text"] == "keep me"  # existing content is kept
    assert content["mime_type"] == "audio/mpeg" and content["size_bytes"] == len(MP3)
    assert "/" not in content["filename"] and content["filename"].endswith("lesson one.mp3")  # path parts stripped

    asset = db.get(MediaAsset, uuid.UUID(content["media_asset_id"]))
    assert asset.asset_type == MediaAssetType.AUDIO
    stored = Path(settings.storage_local_path) / asset.storage_path
    assert stored.read_bytes() == MP3 and stored.parent.name == "audio"
    assert not list(stored.parent.glob("*.part"))

    logs = _audit(db, sid, AuditAction.MEDIA_UPLOAD)
    assert len(logs) == 1 and logs[0].details["kind"] == "AUDIO" and logs[0].details["size_bytes"] == len(MP3)

    got = client.get(f"/media/{asset.id}/file", headers=_auth_headers(_login(admin.username)))
    assert got.status_code == 200 and got.content == MP3
    # The audio follows its module's visibility: this draft module is hidden from learners.
    assert client.get(f"/media/{asset.id}/file", headers=_auth_headers(_login(cdd.username))).status_code == 404


def test_replacing_audio_points_the_section_at_the_new_file(db, admin, module):
    sid = _section(db, module, "AUDIO")
    token = _login(admin.username)
    first = _upload(token, sid, MP3).json()["content"]["media_asset_id"]
    second = _upload(token, sid, WAV, name="new.wav").json()["content"]
    assert second["media_asset_id"] != first and second["mime_type"] == "audio/wav"
    assert len(_audit(db, sid, AuditAction.MEDIA_UPLOAD)) == 2


def test_wrong_file_with_audio_name_is_rejected(db, admin, module):
    sid = _section(db, module, "AUDIO")
    token = _login(admin.username)
    for data in (PNG, MP4, b"plain text pretending to be mp3"):
        resp = _upload(token, sid, data, name="song.mp3", ctype="audio/mpeg")
        assert resp.status_code == 415, resp.text
    db.expire_all()
    assert "media_asset_id" not in db.get(ContentSection, uuid.UUID(sid)).content
    assert not _audit(db, sid, AuditAction.MEDIA_UPLOAD)
    assert not list((Path(settings.storage_local_path) / "audio").glob("*"))


def test_audio_format_list_comes_from_settings(db, admin, module, monkeypatch):
    sid = _section(db, module, "AUDIO")
    monkeypatch.setattr(settings, "audio_upload_formats", ["mp3"])
    assert _upload(_login(admin.username), sid, WAV).status_code == 415


def test_audio_over_the_size_limit_is_rejected_and_not_kept(db, admin, module, monkeypatch):
    sid = _section(db, module, "AUDIO")
    monkeypatch.setattr(settings, "max_audio_upload_mb", 1)
    resp = _upload(_login(admin.username), sid, MP3[:10] + bytes(1024 * 1024))
    assert resp.status_code == 413
    assert not list((Path(settings.storage_local_path) / "audio").glob("*"))


def test_empty_file_is_rejected(db, admin, module):
    assert _upload(_login(admin.username), _section(db, module, "AUDIO"), b"").status_code == 400


# ---------- Video ----------

def test_video_upload_creates_a_draft_video_and_replacing_keeps_it(db, admin, module, storage):
    sid = _section(db, module, "VIDEO")
    token = _login(admin.username)
    resp = _upload(token, sid, MP4, name="demo.mp4", ctype="application/octet-stream")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["video_status"] == "DRAFT"
    vid = uuid.UUID(body["content"]["video_id"])
    video = db.get(Video, vid)
    assert video.module_id == module.id and video.checksum and video.file_size == len(MP4)
    first_file = storage / video.storage_path
    assert first_file.read_bytes() == MP4

    video.status = VideoStatus.PUBLISHED
    db.commit()
    again = _upload(token, sid, MP4 + b"v2", name="demo2.mp4").json()
    assert again["content"]["video_id"] == str(vid)
    assert again["video_status"] == "DRAFT"  # new footage is re-approved before learners get it
    db.expire_all()
    assert not first_file.exists()
    assert (storage / db.get(Video, vid).storage_path).read_bytes() == MP4 + b"v2"
    logs = _audit(db, sid, AuditAction.MEDIA_UPLOAD)
    assert len(logs) == 2 and any(log.details["returned_to_draft"] for log in logs)


def test_video_formats_come_from_settings(db, admin, module, monkeypatch):
    sid = _section(db, module, "VIDEO")
    token = _login(admin.username)
    assert _upload(token, sid, WEBM, name="clip.mp4", ctype="video/mp4").status_code == 415
    assert _upload(token, sid, M4A, name="clip.mp4").status_code == 415
    monkeypatch.setattr(settings, "video_upload_formats", ["mp4", "webm"])
    assert _upload(token, sid, WEBM, name="clip.webm").status_code == 200


def test_video_over_the_size_limit_is_rejected(db, admin, module, monkeypatch, storage):
    sid = _section(db, module, "VIDEO")
    monkeypatch.setattr(settings, "max_video_upload_mb", 1)
    assert _upload(_login(admin.username), sid, MP4[:16] + bytes(1024 * 1024)).status_code == 413
    assert not list((storage / "videos").glob("*"))


# ---------- Remove ----------

def test_remove_detaches_the_file_and_is_audited(db, admin, module):
    sid = _section(db, module, "AUDIO")
    token = _login(admin.username)
    asset_id = _upload(token, sid, MP3).json()["content"]["media_asset_id"]
    resp = client.delete(f"/modules/sections/{sid}/media", headers=_auth_headers(token))
    assert resp.status_code == 200
    content = resp.json()["content"]
    assert content == {"text": "keep me"}
    logs = _audit(db, sid, AuditAction.MEDIA_REMOVE)
    assert len(logs) == 1 and logs[0].details["media_asset_id"] == asset_id
    assert db.get(MediaAsset, uuid.UUID(asset_id)) is not None  # kept: a published release may still use it
    assert client.delete(f"/modules/sections/{sid}/media", headers=_auth_headers(token)).status_code == 404


# ---------- Permissions and section types ----------

def test_learner_cannot_upload_or_remove(db, cdd, module):
    sid = _section(db, module, "AUDIO")
    token = _login(cdd.username)
    assert _upload(token, sid, MP3).status_code == 403
    assert client.delete(f"/modules/sections/{sid}/media", headers=_auth_headers(token)).status_code == 403


def test_upload_requires_login(db, module):
    sid = _section(db, module, "AUDIO")
    assert client.post(f"/modules/sections/{sid}/media", files={"file": ("a.mp3", MP3)}).status_code in (401, 403)


def test_only_audio_and_video_sections_take_files(db, admin, module):
    token = _login(admin.username)
    assert _upload(token, _section(db, module, "TEXT"), MP3).status_code == 422
    assert _upload(token, str(uuid.uuid4()), MP3).status_code == 404


# ---------- Release packages ----------

def test_release_packages_carry_section_audio():
    module = {"sections": [
        {"content_type": "AUDIO", "content": {"media_asset_id": "a1"}},
        {"content_type": "IMAGE", "content": {"media_asset_id": "i1"}},
        {"content_type": "VIDEO", "content": {"video_id": "v1"}},
    ]}
    assert _media_ids(module) == {"a1", "i1"}
