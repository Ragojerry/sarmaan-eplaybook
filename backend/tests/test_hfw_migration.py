"""
HFW role modules: the import script, the credit script, and credited completions
in learning state and reports. Uses the real content in content/hfw_flipbook and
removes everything it creates.

    cd backend && python -m pytest tests/test_hfw_migration.py -v
"""
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.database import SessionLocal
from app.learning.access import visible_modules
from app.learning.state import learning_states
from app.models import (
    AuditLog,
    ContentSection,
    Language,
    MediaAsset,
    Module,
    ModuleCompletionCredit,
    ModuleTranslation,
    QuizAttempt,
    QuizQuestion,
    SectionTranslation,
    UserModuleProgress,
)
from app.models.enums import LearnerRole, ModuleStatus, RoleName, TestType
from app.reports.activity import Filters, module_rows, user_rows
from app.routers.learning import _report_rows
from app.training.restart import restart_training
from scripts import credit_hfw_modules, import_hfw_content
from tests.test_content import _make_user
from tests.test_sync import _cleanup

CONTENT = Path(__file__).resolve().parents[2] / "content" / "hfw_flipbook"
T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


def _remove_hfw(db):
    mods = db.query(Module).filter(Module.module_code.like("HFW-%")).all()
    ids = [m.id for m in mods]
    if ids:
        sec_ids = [s.id for s in db.query(ContentSection.id).filter(ContentSection.module_id.in_(ids))]
        db.query(ModuleCompletionCredit).filter(ModuleCompletionCredit.module_id.in_(ids)).delete(synchronize_session=False)
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
    db.query(AuditLog).filter(AuditLog.entity_type.in_(["hfw_import", "module_completion_credit"])).delete(synchronize_session=False)
    db.commit()


@pytest.fixture()
def imported(db, tmp_path):
    _remove_hfw(db)
    rep = import_hfw_content.run(CONTENT, dry_run=False, media_root=tmp_path)
    assert not rep.errors, rep.errors
    yield rep, tmp_path
    _remove_hfw(db)


def _people(db, *roles):
    english = db.query(Language).filter_by(code="en").one()
    out = []
    for r in roles:
        u = _make_user(db, RoleName.CDD, english.id)
        u.learner_role = r
        out.append(u)
    db.commit()
    return out


def _drop_people(db, users):
    for u in users:
        db.query(ModuleCompletionCredit).filter_by(user_id=u.id).delete()
        db.commit()
        _cleanup(db, u)


# ---------- import ----------
def test_dry_run_changes_nothing(db, tmp_path):
    _remove_hfw(db)
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
    assert rep.counts["modules created"] == 17
    hfw = db.query(Module).filter(Module.module_code.like("HFW-%")).all()
    assert len(hfw) == 17 and all(m.status == ModuleStatus.DRAFT for m in hfw)
    ids = [m.id for m in hfw]
    assert db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).count() == 254
    assert db.query(QuizQuestion).filter(QuizQuestion.module_id.in_(ids)).count() == 170
    assert len(list((media / "images" / "hfw").iterdir())) == 39
    # every image section points at its uploaded asset
    for s in db.query(ContentSection).filter(ContentSection.module_id.in_(ids), ContentSection.content_type == "IMAGE"):
        assert db.get(MediaAsset, uuid.UUID(s.content["media_asset_id"])) is not None
        assert s.content["alt"] and s.content["caption"]
    # section UUIDs are the CSV keys
    key = (CONTENT / "en" / "module_hfw_09.csv").read_text(encoding="utf-8-sig").splitlines()[3].split("|")[0]
    assert db.get(ContentSection, uuid.UUID(key)).module_id == next(m.id for m in hfw if m.module_code == "HFW-09")

    again = import_hfw_content.run(CONTENT, dry_run=False, media_root=media)
    assert not again.errors
    assert again.counts["modules created"] == 0 and again.counts["modules updated"] == 17
    assert again.counts["sections created"] == 0 and again.counts["quiz questions created"] == 0
    assert again.counts["images already present (reused)"] == 39
    assert db.query(Module).filter(Module.module_code.like("HFW-%")).count() == 17
    assert db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).count() == 254


def test_shared_module_is_one_module_for_every_role(db, imported):
    callin = db.query(Module).filter_by(module_code="HFW-09").one()
    assert sorted(callin.learner_roles) == ["CDD", "HEALTH_WORKER", "MONITOR_SUPERVISOR", "OTHER"]
    assert db.query(Module).filter_by(module_code="HFW-01").one().learner_roles == []
    db.query(Module).filter(Module.module_code.like("HFW-%")).update({"status": ModuleStatus.PUBLISHED}, synchronize_session=False)
    db.commit()
    people = _people(db, LearnerRole.CDD, LearnerRole.HEALTH_WORKER, LearnerRole.MONITOR_SUPERVISOR,
                     LearnerRole.OTHER, LearnerRole.LOGISTICIAN)
    try:
        seen = {u.learner_role: {m.module_code for m in visible_modules(db, u) if m.module_code.startswith("HFW-")} for u in people}
        for role in (LearnerRole.CDD, LearnerRole.HEALTH_WORKER, LearnerRole.MONITOR_SUPERVISOR, LearnerRole.OTHER):
            assert "HFW-09" in seen[role]
        assert "HFW-09" not in seen[LearnerRole.LOGISTICIAN]
        assert {"HFW-10", "HFW-16"} <= seen[LearnerRole.LOGISTICIAN]
        general = {"HFW-01", "HFW-02", "HFW-04", "HFW-06", "HFW-12", "HFW-14", "HFW-17"}
        assert all(general <= s for s in seen.values())
    finally:
        _drop_people(db, people)


def test_uuid_collision_blocks_the_import(db, tmp_path):
    _remove_hfw(db)
    m1 = db.query(Module).filter_by(module_code="M1").one()
    key = (CONTENT / "en" / "module_hfw_01.csv").read_text(encoding="utf-8-sig").splitlines()[3].split("|")[0]
    db.add(ContentSection(id=uuid.UUID(key), module_id=m1.id, section_number=999, content_type="TEXT", content={"text": "x"}, sort_order=999))
    db.commit()
    try:
        rep = import_hfw_content.run(CONTENT, dry_run=False, media_root=tmp_path)
        assert any("UUID collision" in e and key in e for e in rep.errors)
        assert db.query(Module).filter(Module.module_code.like("HFW-%")).count() == 0  # nothing written
    finally:
        db.query(ContentSection).filter_by(id=uuid.UUID(key)).delete()
        db.commit()


# ---------- credit ----------
def _complete(db, user, code, when, with_tests=False):
    m = db.query(Module).filter_by(module_code=code).one()
    db.add(UserModuleProgress(user_id=user.id, module_id=m.id, progress_percent=100, completed=True, completed_at=when,
                              reading_completed_at=when - timedelta(minutes=5)))
    if with_tests:
        for tt, correct, mins in ((TestType.PRE, 6, -20), (TestType.POST, 10, -1)):
            db.add(QuizAttempt(user_id=user.id, module_id=m.id, client_id=uuid.uuid4().hex, correct_count=correct,
                               total_count=10, score_percent=correct * 10, passed=correct >= 9, test_type=tt,
                               taken_at=when + timedelta(minutes=mins)))
    db.commit()


def _snapshot(db, users):
    ids = [u.id for u in users]
    old = [m.id for m in db.query(Module).filter(Module.module_code.in_(["M1", "M2", "M3", "M4", "M5", "M6"]))]
    prog = sorted((str(p.id), p.completed, p.completed_at, p.progress_percent, p.updated_at) for p in
                  db.query(UserModuleProgress).filter(UserModuleProgress.user_id.in_(ids), UserModuleProgress.module_id.in_(old)))
    att = sorted((str(a.id), a.score_percent, a.valid) for a in db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(ids)))
    return prog, att


def test_credit_from_old_modules(db, imported):
    cdd, hw, none, earned = _people(db, LearnerRole.CDD, LearnerRole.HEALTH_WORKER, LearnerRole.CDD, LearnerRole.CDD)
    try:
        _complete(db, cdd, "M4", T0, with_tests=True)
        _complete(db, hw, "M2", T0 + timedelta(days=1))
        _complete(db, hw, "M4", T0 + timedelta(days=2))
        _complete(db, earned, "M4", T0)
        hfw07 = db.query(Module).filter_by(module_code="HFW-07").one()
        db.add(UserModuleProgress(user_id=earned.id, module_id=hfw07.id, progress_percent=100, completed=True,
                                  completed_at=T0 + timedelta(days=3)))
        db.commit()
        before = _snapshot(db, [cdd, hw, none, earned])

        dry = credit_hfw_modules.run(dry_run=True, map_path=CONTENT / "content_sections.json", db=db)
        assert db.query(ModuleCompletionCredit).count() == 0
        per = {r["module"]: r for r in dry["modules"]}
        # CDD: M4 -> HFW-06/07/08/10 (HFW-11 is not for CDDs); HW: M2 -> HFW-02, M4 -> HFW-06/10
        assert per["HFW-06"]["records"] == 3 and per["HFW-10"]["records"] == 3
        assert per["HFW-07"]["records"] == 1 and per["HFW-07"]["skipped"]["already completed in the new module (earned)"] == 1
        assert per["HFW-02"]["records"] == 1 and per["HFW-03"]["records"] == 0
        assert per["HFW-11"]["records"] == 0 and per["HFW-11"]["skipped"]["new module is not for the learner's role"] == 3

        res = credit_hfw_modules.run(dry_run=False, map_path=CONTENT / "content_sections.json", db=db, run_id="credit-test-1")
        assert res["total_records"] == dry["total_records"]
        mine = {(c.user_id, c.module_id): c for c in db.query(ModuleCompletionCredit).filter_by(run_id="credit-test-1")}
        c07 = mine[(cdd.id, hfw07.id)]
        assert c07.source_module_code == "M4" and c07.source_completed_at == T0 and c07.source_score_percent == 100
        assert c07.label == "credited from M4"
        hw02 = mine[(hw.id, db.query(Module).filter_by(module_code="HFW-02").one().id)]
        assert hw02.source_score_percent is None  # completed without a post-test
        p = db.query(UserModuleProgress).filter_by(user_id=cdd.id, module_id=hfw07.id).one()
        assert p.completed and p.completed_at == T0
        # old progress and test rows untouched
        assert _snapshot(db, [cdd, hw, none, earned]) == before
        # re-run adds nothing
        again = credit_hfw_modules.run(dry_run=False, map_path=CONTENT / "content_sections.json", db=db, run_id="credit-test-2")
        assert again["total_records"] == 0

        # learning state, the pre/post report and the activity reports tell credited from earned
        db.query(Module).filter(Module.module_code.like("HFW-%")).update({"status": ModuleStatus.PUBLISHED}, synchronize_session=False)
        db.commit()
        st = next(s for s in learning_states(db, cdd) if s.module.module_code == "HFW-07")
        assert st.status == "COMPLETED"
        rows = {(r["username"], r["module_code"]): r for r in _report_rows(db, Filters())}
        r = rows[(cdd.username, "HFW-07")]
        assert (r["completion_source"], r["credited_from"], r["credited_score"]) == ("credited", "M4", 100)
        assert rows[(earned.username, "HFW-07")]["completion_source"] == "earned"
        assert rows[(none.username, "HFW-07")]["completion_source"] is None
        urow = next(x for x in user_rows(db, Filters()) if x["username"] == cdd.username)
        assert urow["modules_completed_credited"] == 4 and urow["modules_completed"] == 5  # M4 earned + 4 credited
        mrow = next(x for x in module_rows(db, Filters()) if x["module_code"] == "HFW-07")
        assert mrow["completed_credited"] >= 1 and mrow["completed"] >= 2

        # undo removes one run's credits and the progress rows it created
        und = credit_hfw_modules.undo("credit-test-1", dry_run=False, db=db)
        assert und["credits removed"] == res["total_records"]
        assert db.query(UserModuleProgress).filter_by(user_id=cdd.id, module_id=hfw07.id).one_or_none() is None
        assert db.query(UserModuleProgress).filter_by(user_id=earned.id, module_id=hfw07.id).one().completed  # earned: kept
        assert _snapshot(db, [cdd, hw, none, earned]) == before
    finally:
        _drop_people(db, [cdd, hw, none, earned])


def test_restart_removes_credits(db, imported):
    (cdd,) = _people(db, LearnerRole.CDD)
    try:
        _complete(db, cdd, "M1", T0)
        credit_hfw_modules.run(dry_run=False, map_path=CONTENT / "content_sections.json", db=db, run_id="credit-test-r")
        assert db.query(ModuleCompletionCredit).filter_by(user_id=cdd.id).count() == 1
        restart_training(db, cdd, datetime.now(timezone.utc), cdd, via="test")
        db.commit()
        assert db.query(ModuleCompletionCredit).filter_by(user_id=cdd.id).count() == 0
        assert db.query(UserModuleProgress).filter_by(user_id=cdd.id).count() == 0
    finally:
        _drop_people(db, [cdd])
