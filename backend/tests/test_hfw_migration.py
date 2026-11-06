"""
HFW curriculum: the import script, the changeover (cutover / rollback), legacy
records and reports. Uses the real content in content/hfw_flipbook and puts the
database back as it found it.

    cd backend && python -m pytest tests/test_hfw_migration.py -v
"""
import json
import os
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai.indexer import rebuild_all_chunks
from app.database import SessionLocal
from app.learning.access import visible_modules
from app.learning.state import learning_states
from app.main import app
from app.models import (
    AuditLog,
    ContentChunk,
    ContentRelease,
    ContentSection,
    Language,
    MediaAsset,
    Module,
    ModuleTranslation,
    QuizAttempt,
    QuizQuestion,
    SectionTranslation,
    User,
    UserModuleProgress,
)
from app.models.enums import LearnerRole, ModuleStatus, RoleName, TestType
from app.releases.packager import package_path
from app.reports.activity import Filters, module_rows
from app.reports.legacy import LEGACY_LABEL, legacy_rows
from scripts import anonymise_staging, cutover_hfw, import_hfw_content
from tests.test_content import _auth_headers, _login, _make_user
from tests.test_sync import _cleanup

CONTENT = Path(__file__).resolve().parents[2] / "content" / "hfw_flipbook"
T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
OLD = ["M1", "M2", "M3", "M4", "M5", "M6"]
GENERAL = ["HFW-01", "HFW-02", "HFW-04", "HFW-06", "HFW-12", "HFW-14", "HFW-17"]
client = TestClient(app)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


def _remove_hfw(db):
    """Test clean-up: the HFW modules, their content and the test releases only."""
    mods = db.query(Module).filter(Module.module_code.like("HFW-%")).all()
    ids = [m.id for m in mods]
    if ids:
        sec_ids = [s.id for s in db.query(ContentSection.id).filter(ContentSection.module_id.in_(ids))]
        db.query(ContentChunk).filter(ContentChunk.module_id.in_(ids)).delete(synchronize_session=False)
        db.query(QuizAttempt).filter(QuizAttempt.module_id.in_(ids)).delete(synchronize_session=False)
        db.query(UserModuleProgress).filter(UserModuleProgress.module_id.in_(ids)).delete(synchronize_session=False)
        db.query(QuizQuestion).filter(QuizQuestion.module_id.in_(ids)).delete(synchronize_session=False)
        if sec_ids:
            db.query(SectionTranslation).filter(SectionTranslation.section_id.in_(sec_ids)).delete(synchronize_session=False)
        db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).delete(synchronize_session=False)
        db.query(ModuleTranslation).filter(ModuleTranslation.module_id.in_(ids)).delete(synchronize_session=False)
        db.query(Module).filter(Module.id.in_(ids)).delete(synchronize_session=False)
    for a in db.query(MediaAsset).all():
        if (a.asset_metadata or {}).get("source") == "hfw_flipbook":
            db.delete(a)
    db.query(ContentRelease).filter(ContentRelease.release_code.like("HFW-%")).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.entity_type.in_(["hfw_import", "curriculum_cutover"])).delete(synchronize_session=False)
    db.query(AuditLog).filter(AuditLog.details["via"].astext == "scripts/cutover_hfw.py").delete(synchronize_session=False)
    db.query(Module).filter(Module.module_code.in_(OLD)).update({"status": ModuleStatus.PUBLISHED}, synchronize_session=False)
    db.commit()
    rebuild_all_chunks(db)
    db.commit()


@pytest.fixture()
def clean(db):
    _remove_hfw(db)
    yield
    _remove_hfw(db)


@pytest.fixture()
def imported(db, tmp_path, clean):
    rep = import_hfw_content.run(CONTENT, dry_run=False, media_root=tmp_path)
    assert not rep.errors, rep.errors
    yield rep, tmp_path


def _people(db, *roles):
    english = db.query(Language).filter_by(code="en").one()
    out = []
    for r in roles:
        u = _make_user(db, RoleName.CDD, english.id)
        u.learner_role = r
        out.append(u)
    db.commit()
    return out


def _snapshot(db):
    """Every progress and test row in the database (the changeover must leave them as they are)."""
    prog = sorted((str(p.id), str(p.module_id), p.completed, p.completed_at, p.progress_percent, p.updated_at)
                  for p in db.query(UserModuleProgress))
    att = sorted((str(a.id), str(a.module_id), a.score_percent, a.valid, a.invalid_reason) for a in db.query(QuizAttempt))
    return prog, att


def _old_records(db, user, completed_code="M1", started_code="M2"):
    mods = {m.module_code: m for m in db.query(Module).filter(Module.module_code.in_(OLD))}
    db.add(UserModuleProgress(user_id=user.id, module_id=mods[completed_code].id, progress_percent=100, completed=True,
                              completed_at=T0, reading_completed_at=T0 - timedelta(minutes=5)))
    db.add(UserModuleProgress(user_id=user.id, module_id=mods[started_code].id, progress_percent=40, last_opened_at=T0))
    db.add(QuizAttempt(user_id=user.id, module_id=mods[completed_code].id, client_id=uuid.uuid4().hex, correct_count=10,
                       total_count=10, score_percent=100, passed=True, test_type=TestType.POST, taken_at=T0))
    db.commit()


# ---------- import ----------
def test_import_dry_run_changes_nothing(db, tmp_path, clean):
    media_before = db.query(MediaAsset).count()
    rep = import_hfw_content.run(CONTENT, dry_run=True, media_root=tmp_path)
    assert not rep.errors
    assert rep.counts["modules created"] == 17 and rep.counts["sections created"] == 254
    assert rep.counts["quiz questions created"] == 170
    assert db.query(Module).filter(Module.module_code.like("HFW-%")).count() == 0
    assert db.query(MediaAsset).count() == media_before
    assert not any(tmp_path.iterdir())  # no file copied


def test_import_creates_and_rerun_never_duplicates(db, imported):
    rep, media = imported
    hfw = db.query(Module).filter(Module.module_code.like("HFW-%")).all()
    assert len(hfw) == 17 and all(m.status == ModuleStatus.DRAFT for m in hfw)
    ids = [m.id for m in hfw]
    assert db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).count() == 254
    assert db.query(QuizQuestion).filter(QuizQuestion.module_id.in_(ids)).count() == 170
    assert len(list((media / "images" / "hfw").iterdir())) == 39
    for s in db.query(ContentSection).filter(ContentSection.module_id.in_(ids), ContentSection.content_type == "IMAGE"):
        assert db.get(MediaAsset, uuid.UUID(s.content["media_asset_id"])) is not None
        assert s.content["alt"] and s.content["caption"]
    key = (CONTENT / "en" / "module_hfw_09.csv").read_text(encoding="utf-8-sig").splitlines()[3].split("|")[0]
    assert db.get(ContentSection, uuid.UUID(key)).module_id == next(m.id for m in hfw if m.module_code == "HFW-09")
    again = import_hfw_content.run(CONTENT, dry_run=False, media_root=media)
    assert not again.errors
    assert again.counts["modules created"] == 0 and again.counts["modules updated"] == 17
    assert again.counts["sections created"] == 0 and again.counts["quiz questions created"] == 0
    assert db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).count() == 254


def test_uuid_collision_blocks_the_import(db, tmp_path, clean):
    m1 = db.query(Module).filter_by(module_code="M1").one()
    key = (CONTENT / "en" / "module_hfw_01.csv").read_text(encoding="utf-8-sig").splitlines()[3].split("|")[0]
    db.add(ContentSection(id=uuid.UUID(key), module_id=m1.id, section_number=999, content_type="TEXT", content={"text": "x"}, sort_order=999))
    db.commit()
    try:
        rep = import_hfw_content.run(CONTENT, dry_run=False, media_root=tmp_path)
        assert any("UUID collision" in e and key in e for e in rep.errors)
        assert db.query(Module).filter(Module.module_code.like("HFW-%")).count() == 0
    finally:
        db.query(ContentSection).filter_by(id=uuid.UUID(key)).delete()
        db.commit()


# ---------- changeover ----------
def test_cutover_dry_run_changes_nothing(db, tmp_path, clean):
    before = _snapshot(db)
    releases = db.query(ContentRelease).count()
    rep = cutover_hfw.run(dry_run=True, media_root=tmp_path, env="development", cutover_date="")
    assert rep["modules archived"] == 6 and rep["new modules published"] == 17
    assert rep["release"]["curriculum"] == "hfw-2026" and rep["release"]["modules"] == 17
    assert "learner accounts (all affected: their list becomes the new curriculum)" in rep["learners"]
    db.expire_all()
    assert {m.status for m in db.query(Module).filter(Module.module_code.in_(OLD))} == {ModuleStatus.PUBLISHED}
    assert db.query(Module).filter(Module.module_code.like("HFW-%")).count() == 0
    assert db.query(ContentRelease).count() == releases
    assert _snapshot(db) == before


def test_cutover_rollback_and_cutover_again(db, tmp_path, clean):
    cdd, logi = _people(db, LearnerRole.CDD, LearnerRole.LOGISTICIAN)
    try:
        _old_records(db, cdd)
        before = _snapshot(db)

        rep = cutover_hfw.run(dry_run=False, media_root=tmp_path, env="development", cutover_date="")
        assert rep["modules archived"] == 6 and rep["new modules published"] == 17
        db.expire_all()
        assert {m.status for m in db.query(Module).filter(Module.module_code.in_(OLD))} == {ModuleStatus.ARCHIVED}
        assert _snapshot(db) == before, "old progress and test records are untouched"

        # the content version moved on: the newest package is the new curriculum only
        rel = db.query(ContentRelease).filter_by(release_code=rep["release"]["code"]).one()
        pkg = json.loads(package_path(rel.release_code).read_text(encoding="utf-8"))
        assert pkg["curriculum"] == "hfw-2026"
        assert {m["module_code"] for m in pkg["modules"]} == {f"HFW-{i:02d}" for i in range(1, 18)}

        # each learner: the general modules first, then their role's; nothing old
        cdd_list = [m.module_code for m in visible_modules(db, cdd)]
        assert cdd_list[:7] == GENERAL
        assert cdd_list[7:] == ["HFW-03", "HFW-05", "HFW-07", "HFW-08", "HFW-09", "HFW-10"]
        assert [m.module_code for m in visible_modules(db, logi)] == GENERAL + ["HFW-10", "HFW-16"]
        states = learning_states(db, cdd)
        assert states[0].unlocked and not states[1].unlocked, "unlock chain starts again from the first general module"
        assert not any(s.completed for s in states), "new progress starts at zero; nothing old counts"

        # old records: shown as Legacy, never in the current rates
        legacy = [r for r in legacy_rows(db, Filters()) if r["username"] == cdd.username]
        assert {(r["module_code"], r["completed"]) for r in legacy} == {("M1", True), ("M2", False)}
        assert all(r["curriculum"] == LEGACY_LABEL for r in legacy)
        assert not {r["module_code"] for r in module_rows(db, Filters())} & set(OLD)

        # a phone that was offline through the changeover uploads old-module work: kept, never counted
        headers = _auth_headers(_login(cdd.username))
        m3 = db.query(Module).filter_by(module_code="M3").one()
        r = client.post("/sync/progress", headers=headers, json={"device_id": "d1", "items": [{
            "module_id": str(m3.id), "progress_percent": 100, "completed": True, "last_section": "s9",
            "last_opened_at": datetime.now(timezone.utc).isoformat(), "completed_at": datetime.now(timezone.utc).isoformat()}]})
        assert r.status_code == 200 and r.json()["results"][0]["detail"] == cutover_hfw_legacy()
        q = client.post("/sync/quiz-attempts", headers=headers, json={"device_id": "d1", "items": [{
            "client_id": uuid.uuid4().hex, "module_id": str(m3.id), "correct_count": 9, "total_count": 10,
            "test_type": "POST", "taken_at": datetime.now(timezone.utc).isoformat(), "results": []}]})
        assert q.status_code == 200 and q.json()["results"][0]["status"] == "ok"
        db.expire_all()
        p3 = db.query(UserModuleProgress).filter_by(user_id=cdd.id, module_id=m3.id).one()
        assert not p3.completed and p3.progress_percent == 99
        a3 = db.query(QuizAttempt).filter_by(user_id=cdd.id, module_id=m3.id).one()
        assert a3.valid is False and "archived" in a3.invalid_reason

        # re-running changes nothing more
        again = cutover_hfw.run(dry_run=False, media_root=tmp_path, env="development", cutover_date="")
        assert again["modules archived"] == 0 and again["new modules published"] == 0

        # rollback: old modules back, new ones hidden, no data lost
        after_cutover = _snapshot(db)
        rb = cutover_hfw.run(dry_run=False, do_rollback=True, env="development", cutover_date="")
        assert rb["old modules restored (archived = false)"] == 6 and rb["new modules hidden (back to DRAFT)"] == 17
        db.expire_all()
        assert {m.status for m in db.query(Module).filter(Module.module_code.in_(OLD))} == {ModuleStatus.PUBLISHED}
        assert {m.status for m in db.query(Module).filter(Module.module_code.like("HFW-%"))} == {ModuleStatus.DRAFT}
        assert _snapshot(db) == after_cutover
        rb_pkg = json.loads(package_path(rb["release"]["code"]).read_text(encoding="utf-8"))
        assert rb_pkg["curriculum"] == "legacy"
        assert [m.module_code for m in visible_modules(db, cdd)][:6] == OLD

        # and the cutover can be run again after a rollback
        third = cutover_hfw.run(dry_run=False, media_root=tmp_path, env="development", cutover_date="")
        assert third["modules archived"] == 6 and third["new modules published"] == 17
        assert _snapshot(db) == after_cutover
    finally:
        for u in (cdd, logi):
            _cleanup(db, u)


def cutover_hfw_legacy():
    from app.routers.sync import LEGACY
    return LEGACY


# ---------- guards ----------
def test_production_needs_a_cutover_date_confirmation_and_backup(tmp_path):
    with pytest.raises(cutover_hfw.Refused, match="CUTOVER_DATE is not set"):
        cutover_hfw.check_cutover_date("production", None, dry_run=True)
    with pytest.raises(cutover_hfw.Refused, match="before it"):
        cutover_hfw.check_cutover_date("production", "2026-12-01", dry_run=False, today=date(2026, 11, 30))
    assert "2026-12-01" in cutover_hfw.check_cutover_date("production", "2026-12-01", dry_run=False, today=date(2026, 12, 1))
    assert "not set" in cutover_hfw.check_cutover_date("staging", None, dry_run=False)
    with pytest.raises(cutover_hfw.Refused, match="CUTOVER_DATE is not set"):
        cutover_hfw.run(dry_run=True, env="production", cutover_date="")
    with pytest.raises(cutover_hfw.Refused, match="--confirm-production"):
        cutover_hfw.run(dry_run=False, env="production", cutover_date="2026-01-01")
    with pytest.raises(cutover_hfw.Refused, match="no --backup"):
        cutover_hfw.run(dry_run=False, env="production", cutover_date="2026-01-01", confirm_production=True)


def test_backup_is_verified(tmp_path, monkeypatch):
    monkeypatch.setattr(cutover_hfw.shutil, "which", lambda _: None)  # header check only (no pg_restore here)
    bad = tmp_path / "bad.dump"
    bad.write_bytes(b"not a dump")
    with pytest.raises(cutover_hfw.Refused, match="custom-format"):
        cutover_hfw.verify_backup(bad)
    partial = tmp_path / "partial.dump"
    partial.write_bytes(b"PGDMP\x01\x0e TABLE DATA public users ")
    with pytest.raises(cutover_hfw.Refused, match="user_module_progress"):
        cutover_hfw.verify_backup(partial)
    good = tmp_path / "good.dump"
    good.write_bytes(b"PGDMP\x01\x0e" + b" TABLE DATA public users  TABLE DATA public user_module_progress "
                     b" TABLE DATA public quiz_attempts " + b"x" * 1000)
    assert "verified" in cutover_hfw.verify_backup(good)
    old = time.time() - 13 * 3600
    os.utime(good, (old, old))
    with pytest.raises(cutover_hfw.Refused, match="h old"):
        cutover_hfw.verify_backup(good)
    with pytest.raises(cutover_hfw.Refused, match="does not exist"):
        cutover_hfw.verify_backup(tmp_path / "missing.dump")


def test_anonymise_replaces_personal_data_without_deleting(db):
    english = db.query(Language).filter_by(code="en").one()
    u = _make_user(db, RoleName.CDD, english.id)
    try:
        u.phone = "+2348000000000"
        db.commit()
        users = db.query(User).count()
        counts = anonymise_staging.anonymise(db, "staging-password-123")
        assert counts["users anonymised"] == users
        db.refresh(u)
        assert u.phone is None and u.email.endswith("@staging.invalid") and u.username.startswith("user")
        assert u.first_name == "Cdd" and u.last_name.isdigit()
        assert db.query(User).count() == users  # nothing deleted
        db.rollback()  # the dev database itself is never anonymised
        db.refresh(u)
        assert u.phone == "+2348000000000"
    finally:
        db.rollback()
        _cleanup(db, u)
