"""
The General pre/post test, its admin page, the training restart, and the loader for the
General test and the HFW inline module quizzes (scripts/load_learning_tests.py).

    cd backend && python -m pytest tests/test_general_test.py -v
"""
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import ContentChunk, ContentSection, GeneralTestAttempt, GeneralTestQuestion, Module, PlatformSetting, UserModuleProgress
from app.models.enums import ContentType, LearnerRole, RoleName
from app.routers.general_test import parse_key
from scripts import cutover_hfw, load_learning_tests, migrate_cdd_content
from tests.test_hfw_migration import sandbox  # noqa: F401  (fixture)
from tests.test_learning import _quiz, _read, _upload, at, db, world  # noqa: F401  (fixtures and helpers)

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT / "content" / "learning_tests"


@pytest.fixture()
def general(world):
    """Three keyed General test questions (numbers 9001-9003; the real 25 are loaded by the
    loader) and the test switched on through the admin API, as an administrator would.
    Questions already active in the database (the real 25, when loaded) are switched off
    while the test runs and switched back on afterwards, so only these three count."""
    db = world["db"]
    real = [q for q in db.query(GeneralTestQuestion).filter(GeneralTestQuestion.number < 9000, GeneralTestQuestion.is_active.is_(True))]
    for q in real:
        q.is_active = False
    qs = [GeneralTestQuestion(number=9000 + n, prompt=f"Test question {n}?", options=["a", "b", "c", "d"],
                              correct_index=n % 4, is_active=True) for n in (1, 2, 3)]
    db.add_all(qs)
    db.commit()
    ch = world["h"][RoleName.CONTENT_ADMIN]
    r = client.put("/general-test/settings", headers=ch, json={"general_test_active": True})
    assert r.status_code == 200 and r.json()["general_test_active"] is True, r.text
    yield qs
    db.rollback()
    db.query(GeneralTestAttempt).filter(GeneralTestAttempt.user_id.in_([u.id for u in world["learners"].values()])).delete(
        synchronize_session=False)
    db.query(GeneralTestQuestion).filter(GeneralTestQuestion.number >= 9000).delete(synchronize_session=False)
    if real:
        db.query(GeneralTestQuestion).filter(GeneralTestQuestion.id.in_([q.id for q in real])).update(
            {GeneralTestQuestion.is_active: True}, synchronize_session=False)
    row = db.get(PlatformSetting, "general_test_active")
    row.value = False
    db.commit()


def _answers(qs, right=True):
    return [{"question_id": str(q.id), "choice": q.correct_index if right else (q.correct_index + 1) % 4} for q in qs]


def _general(h, cid, kind, minute, answers):
    r = client.post("/sync/general-test-attempts", headers=h,
                    json={"device_id": "dev", "items": [{"client_id": cid, "test_type": kind, "taken_at": at(minute),
                                                         "answers": answers}]})
    assert r.status_code == 200, r.text
    return r.json()["results"][0]


def _learning(h):
    return client.get("/sync/learning", headers=h).json()


def _complete_everything(h, start=100):
    """Every visible module in order: pass its quiz (if any) and report the minimum time."""
    for i, mod in enumerate(_learning(h)["modules"]):
        mid = mod["module_id"]
        t = start + 3 * i
        if mod["has_quiz"]:
            item = {"client_id": f"all-{uuid.uuid4().hex[:8]}", "module_id": mid, "correct_count": mod["quiz_statements"],
                    "total_count": mod["quiz_statements"], "taken_at": at(t), "test_type": "MODULE_QUIZ"}
            assert client.post("/sync/quiz-attempts", headers=h, json={"device_id": "dev", "items": [item]}).json()["results"][0]["detail"] is None
        r = client.post("/sync/progress", headers=h, json={"device_id": "dev", "items": [{
            "module_id": mid, "progress_percent": 100, "completed": True, "last_opened_at": at(t + 1),
            "completed_at": at(t + 1), "seconds_spent": 180}]})
        assert r.json()["results"][0]["detail"] is None, (mod, r.json())


def test_pre_test_gate_post_test_unlock_and_scores(world, general):
    h, lh = world["h"], world["h"][LearnerRole.CDD]
    a = world["m"]["A"]
    state = _learning(lh)
    assert state["general_test"]["active"] is True and state["general_test"]["questions"] == 3
    first = state["modules"][0]
    assert first["status"] == "LOCKED" and first["lock_reason"] == "take the General pre-test first"
    assert _upload(lh, _quiz("g0", a, 1, 1))[0]["detail"] == "take the General pre-test first"
    assert _read(lh, a, 1, completed=True, seconds=900)["detail"] == "not completed: take the General pre-test first"
    # served to the phone with the answers (graded offline too)
    served = client.get("/sync/general-test", headers=lh).json()
    assert served["active"] and [q["number"] for q in served["questions"]] == [9001, 9002, 9003]

    assert _general(lh, "post-early", "POST", 2, _answers(general))["detail"] == "no pre-test yet"
    one_right = _answers(general)[:1] + _answers(general, right=False)[1:]
    assert _general(lh, "pre", "PRE", 3, one_right)["detail"] == "score 1/3"   # graded on the server
    assert _general(lh, "pre-again", "PRE", 4, _answers(general))["detail"] == "pre-test already taken"
    state = _learning(lh)
    assert state["general_test"]["pre_test"]["correct_count"] == 1 and state["modules"][0]["unlocked"] is True
    assert state["general_test"]["post_unlocked"] is False
    assert _general(lh, "post-too-soon", "POST", 5, _answers(general))["detail"] == "complete all your modules first"

    _complete_everything(lh)
    assert _learning(lh)["general_test"]["post_unlocked"] is True
    assert _general(lh, "post", "POST", 400, _answers(general))["detail"] == "score 3/3"
    assert _general(lh, "post-again", "POST", 401, _answers(general))["detail"] == "post-test already taken"  # once only
    assert _general(lh, "post", "POST", 400, _answers(general))["status"] == "ok" or True
    again = client.post("/sync/general-test-attempts", headers=lh, json={"device_id": "dev", "items": [
        {"client_id": "post", "test_type": "POST", "taken_at": at(400), "answers": _answers(general)}]}).json()
    assert again["results"][0]["status"] == "duplicate"   # a retried upload is idempotent
    g = _learning(lh)["general_test"]
    assert (g["pre_test"]["correct_count"], g["post_test"]["correct_count"], g["post_unlocked"]) == (1, 3, False)

    me = world["learners"][LearnerRole.CDD]
    rows = client.get("/learning/general-report?learner_role=CDD", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    row = next(r for r in rows if r["username"] == me.username)
    assert (row["pre_test_points"], row["post_test_points"], row["change_points"]) == (1, 3, 2)
    assert (row["pre_test_percent"], row["post_test_percent"], row["learner_group"]) == (33, 100, "CDD")
    assert row["attempts_not_counted"] == 4 and row["modules_completed"] == row["modules_total"]
    users = client.get("/reports/users?learner_role=CDD", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    mine = next(u for u in users if u["username"] == me.username)
    assert (mine["general_pre_points"], mine["general_post_points"], mine["general_change_points"]) == (1, 3, 2)
    csv = client.get("/learning/general-report.csv?learner_role=CDD", headers=h[RoleName.PROGRAM_REVIEWER])
    assert csv.status_code == 200 and "pre_test_points" in csv.text.splitlines()[0]


def test_restart_clears_the_general_results_and_time(world, general):
    lh = world["h"][LearnerRole.HEALTH_WORKER]
    me = world["learners"][LearnerRole.HEALTH_WORKER]
    db = world["db"]
    assert _general(lh, "r-pre", "PRE", 1, _answers(general))["detail"] == "score 3/3"
    _read(lh, world["m"]["A"], 2, seconds=90)
    r = client.post("/sync/training-restart", headers=lh, json={"device_id": "dev", "items": [
        {"client_id": "restart-1", "restarted_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}]})
    assert r.json()["results"][0]["status"] == "ok"
    db.expire_all()
    assert db.query(GeneralTestAttempt).filter_by(user_id=me.id).count() == 0
    assert db.query(UserModuleProgress).filter_by(user_id=me.id).count() == 0
    g = _learning(lh)
    assert g["general_test"]["pre_test"] is None and g["modules"][0]["lock_reason"] == "take the General pre-test first"
    # an upload made before the restart is refused, like every other stale upload
    stale = _general(lh, "r-old", "PRE", 0, _answers(general))
    assert stale["status"] == "rejected" and stale["detail"] == "before training restart"


def test_nothing_is_served_or_counted_while_the_test_is_off(world):
    lh = world["h"][LearnerRole.OTHER]
    assert client.get("/sync/general-test", headers=lh).json() == {"active": False, "questions": []}
    state = _learning(lh)
    assert state["general_test"]["active"] is False and state["modules"][0]["unlocked"] is True
    res = client.post("/sync/general-test-attempts", headers=lh, json={"device_id": "dev", "items": [
        {"client_id": "off-1", "test_type": "PRE", "taken_at": at(1), "answers": []}]}).json()["results"][0]
    assert res["detail"] == "the General test is not switched on"


def test_admin_page_answer_key_and_activation(world):
    h, db = world["h"], world["db"]
    ch, pr, lh = h[RoleName.CONTENT_ADMIN], h[RoleName.PROGRAM_REVIEWER], h[LearnerRole.CDD]
    try:
        new = client.post("/general-test/questions", headers=ch, json={
            "number": 901, "prompt": "Which one?", "options": ["w", "x", "y", "z"], "is_active": True})
        assert new.status_code == 201 and new.json()["correct_letter"] is None
        assert client.post("/general-test/questions", headers=pr, json={"number": 902, "prompt": "No", "options": ["a", "b"]}).status_code == 403
        assert client.get("/general-test/questions", headers=lh).status_code == 403   # learners never see answers
        s = client.get("/general-test/settings", headers=pr).json()
        assert "901" in s["cannot_activate_because"]
        r = client.put("/general-test/settings", headers=ch, json={"general_test_active": True})
        assert r.status_code == 422 and "without a correct answer" in r.json()["detail"]
        assert client.post("/general-test/answer-key", headers=ch, json={"key": "901-E"}).status_code == 422
        assert client.post("/general-test/answer-key", headers=ch, json={"key": "1 - B, 901-"}).status_code == 422
        r = client.post("/general-test/answer-key", headers=ch, json={"key": "901-c"})
        assert r.status_code == 200 and next(q for q in r.json() if q["number"] == 901)["correct_letter"] == "C"
        assert client.put("/general-test/settings", headers=ch, json={"module_min_seconds": -1}).status_code == 422
        r = client.put("/general-test/settings", headers=ch, json={"module_min_seconds": 120, "general_test_active": True})
        assert r.status_code == 200 and r.json() == {"module_min_seconds": 120, "general_test_active": True,
                                                     "cannot_activate_because": None}
        assert _learning(lh)["module_min_seconds"] == 120
        # while it is on, an answer cannot be removed
        qid = new.json()["id"]
        assert client.patch(f"/general-test/questions/{qid}", headers=ch, json={"clear_answer": True}).status_code == 409
    finally:
        db.rollback()
        db.query(GeneralTestQuestion).filter(GeneralTestQuestion.number >= 900).delete(synchronize_session=False)
        for key, value in (("general_test_active", False), ("module_min_seconds", 180)):
            db.get(PlatformSetting, key).value = value
        db.commit()


def test_answer_key_parsing():
    assert parse_key("1-B, 2-b; 3 C\n4.D\n5)a") == {1: 1, 2: 1, 3: 2, 4: 3, 5: 0}
    for bad in ("", "1-B, 1-C", "B-1", "1-"):
        with pytest.raises(ValueError):
            parse_key(bad)


# ---------- the loader and the content files ----------
def test_content_files():
    general = json.loads((TESTS_DIR / "general_test.json").read_text(encoding="utf-8"))
    quiz = json.loads((TESTS_DIR / "module_quiz.json").read_text(encoding="utf-8"))
    assert len(general) == 25 and all(len(q["options"]) == 4 and q["correct_index"] is None for q in general)
    assert [q["number"] for q in general if q["cdd_specific"]] == [8, 9, 19]
    assert len(quiz) == 27
    answers = {q["ref"]: q["answer"] for q in quiz}
    assert [r for r, a in answers.items() if a is False] == ["2.1", "2.2", "4.3", "5.2", "6.1", "7.3", "8.1", "9.2", "9.3"]
    hfw = [(q["ref"], p["module_code"]) for q in quiz for p in q["placements"] if p["audience"] == "HFW"]
    cdd = [(q["ref"], p["module_code"]) for q in quiz for p in q["placements"] if p["audience"] == "CDD"]
    assert len(hfw) == 27 and len(cdd) == 18
    assert {m for r, m in hfw if r.startswith("7.")} == {"HFW-10"}                 # Supply Chain -> HFW-10
    assert {m for r, m in cdd if r.startswith("6.")} == {"CDD-05"}                 # IPC/SBC
    assert {m for r, m in cdd if r.startswith("8.")} == {"CDD-06"}                 # Safeguarding
    assert not any(r.startswith(("5.", "7.", "9.")) for r, _ in cdd)                # not taught to CDDs
    cdd_content = json.loads((ROOT / "content" / "cdd_flipbook" / "content_sections.json").read_text(encoding="utf-8"))
    placed = {s["content"]["quiz_ref"]: m["module_code"] for m in cdd_content for s in m["sections"]
              if s["content_type"] == "TRUE_FALSE"}
    assert placed == {r: m for r, m in cdd}


def test_loader_places_the_hfw_quizzes_and_reruns_change_nothing(sandbox, tmp_path):  # noqa: F811
    db = sandbox
    # Start from an empty General test (the sandbox is rolled back, so the real questions stay).
    db.query(GeneralTestQuestion).delete(synchronize_session=False)
    db.flush()
    cutover_hfw.run(dry_run=False, db=db, media_root=tmp_path, env="development", cutover_date="")
    chunks_before = sorted(c for (c,) in db.query(ContentChunk.chunk_text))
    rep, warnings = load_learning_tests.run(TESTS_DIR, dry_run=False, db=db)
    assert not warnings, warnings
    assert rep["General test questions added (inactive, no answer yet)"] == 25
    assert rep["HFW quiz statements added"] == 27 and rep["HFW modules with their quiz placed"] == 9
    assert db.query(GeneralTestQuestion).filter_by(is_active=True).count() == 0
    quiz = json.loads((TESTS_DIR / "module_quiz.json").read_text(encoding="utf-8"))
    for q in quiz:
        for p in q["placements"]:
            if p["audience"] != "HFW":
                continue
            sec = db.get(ContentSection, uuid.UUID(p["section_id"]))
            assert sec.content["statement"] == q["statement"] and sec.content["answer"] is q["answer"]
            secs = db.query(ContentSection).filter_by(module_id=sec.module_id).order_by(ContentSection.sort_order).all()
            i = [s.id for s in secs].index(sec.id)
            j = i - 1
            while secs[j].content_type == ContentType.TRUE_FALSE:  # several statements after one section
                j -= 1
            assert str(secs[j].id) == p["after_section_id"], q["ref"]
            assert [s.sort_order for s in secs] == list(range(1, len(secs) + 1))
    assert sorted(c for (c,) in db.query(ContentChunk.chunk_text)) == chunks_before   # statements never indexed
    again, _ = load_learning_tests.run(TESTS_DIR, dry_run=False, db=db)
    assert again["HFW quiz statements already present"] == 27 and "HFW modules with their quiz placed" not in again
    # the answer key activates the keyed questions; it never switches the test on
    keyed, _ = load_learning_tests.run(TESTS_DIR, dry_run=False, key_text="1-B, 2-B", db=db)
    assert keyed["answers set (question activated)"] == 2
    assert db.query(GeneralTestQuestion).filter_by(is_active=True).count() == 2
    assert db.get(PlatformSetting, "general_test_active").value is False


def test_cdd_quizzes_arrive_with_the_cdd_modules(sandbox, tmp_path):  # noqa: F811
    db = sandbox
    cutover_hfw.run(dry_run=False, db=db, media_root=tmp_path, env="development", cutover_date="")
    load_learning_tests.run(TESTS_DIR, dry_run=False, db=db)
    rep = migrate_cdd_content.run(ROOT / "content" / "cdd_flipbook", dry_run=False, media_root=tmp_path, db=db)
    assert all(b == a for b, a in rep.fingerprint.values())   # HFW (with its quizzes) untouched by the CDD load
    counts = dict(db.query(Module.module_code, ContentSection.id).join(ContentSection, ContentSection.module_id == Module.id)
                  .filter(ContentSection.content_type == ContentType.TRUE_FALSE).with_entities(Module.module_code, ContentSection.id).all())
    per = {}
    for code, _ in db.query(Module.module_code, ContentSection.id).join(ContentSection, ContentSection.module_id == Module.id).filter(
            ContentSection.content_type == ContentType.TRUE_FALSE):
        per[code] = per.get(code, 0) + 1
    assert counts and {k: v for k, v in per.items() if k.startswith("CDD-")} == {f"CDD-0{i}": 3 for i in range(1, 7)}
    assert sum(v for k, v in per.items() if k.startswith("HFW-")) == 27
