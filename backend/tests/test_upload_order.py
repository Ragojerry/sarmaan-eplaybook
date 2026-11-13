"""Problems 1 and 2 (server side): results refused only because of the order uploads
arrived in now count once the missing completion arrives; nothing else is relaxed.
Problem 3 (server side): retry attempts store which statements were shown. And the
repair script for learners already stuck (dry run first)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.learning.revalidate import LOCKED_PREVIOUS
from app.main import app
from app.models import AuditLog, GeneralTestAttempt, QuizAttempt, User, UserModuleProgress
from app.models.enums import LearnerRole, TestType
from scripts import repair_stuck_completions as repair
from tests.test_general_test import _answers, _general, _learning, general  # noqa: F401  (fixture)
from tests.test_hfw_migration import sandbox  # noqa: F401
from tests.test_learning import _quiz, _state, _upload, at, db, world  # noqa: F401  (fixtures and helpers)

client = TestClient(app)


def _progress(h, *items):
    r = client.post("/sync/progress", headers=h, json={"device_id": "dev", "items": list(items)})
    assert r.status_code == 200, r.text
    return {res["key"]: res for res in r.json()["results"]}


def _done(module, minute, seconds=180):
    return {"module_id": str(module.id), "progress_percent": 100, "completed": True, "last_opened_at": at(minute),
            "completed_at": at(minute), "reading_completed_at": at(minute), "seconds_spent": seconds}


def _attempt(client_id):
    s = SessionLocal()
    a = s.query(QuizAttempt).filter_by(client_id=client_id).one()
    s.close()
    return a


@pytest.mark.parametrize("role", [LearnerRole.HEALTH_WORKER, LearnerRole.OTHER, LearnerRole.CDD])
def test_quiz_uploaded_before_the_previous_completion_counts(world, role):  # noqa: F811
    """The phone: quiz A (1), complete A (4), quiz B (5), complete B (9), offline; then one sync,
    which uploads every quiz attempt before any progress (and lists B before A)."""
    h, A, B = world["h"][role], world["m"]["A"], world["m"]["B"]
    res = _upload(h, _quiz(f"o-qa-{role.value}", A, 1, 1), _quiz(f"o-qb-{role.value}", B, 1, 5))
    assert res[1]["detail"] == LOCKED_PREVIOUS, "B looked locked when its quiz arrived (the old verdict)"
    out = _progress(h, _done(B, 9), _done(A, 4))
    assert out[str(A.id)]["detail"] is None and out[str(B.id)]["detail"] is None, out
    assert _state(h, B)["completed"] is True and _state(h, B)["quiz_passed"] is True
    assert _attempt(f"o-qb-{role.value}").valid is True and _attempt(f"o-qb-{role.value}").invalid_reason is None


def test_the_rules_are_not_relaxed(world):  # noqa: F811
    h, A, B = world["h"][LearnerRole.HEALTH_WORKER], world["m"]["A"], world["m"]["B"]
    # A quiz taken long before the module opened (A completed at 30) stays refused.
    _upload(h, _quiz("early-qa", A, 1, 1), _quiz("early-qb", B, 1, 2))
    out = _progress(h, _done(A, 30), _done(B, 35, seconds=60))
    assert out[str(B.id)]["detail"].startswith("not completed"), out
    assert _attempt("early-qb").valid is False
    # A failed quiz never counts, and the minimum time still applies (time only grows).
    _upload(h, _quiz("fail-qb", B, 0, 40))
    assert _progress(h, _done(B, 41, seconds=60))[str(B.id)]["detail"].startswith("not completed")
    _upload(h, _quiz("pass-qb", B, 1, 42))
    assert "seconds" in _progress(h, _done(B, 43, seconds=60))[str(B.id)]["detail"]
    assert _progress(h, _done(B, 44, seconds=180))[str(B.id)]["detail"] is None


def test_post_test_uploaded_before_the_last_completion_counts_and_a_second_is_kept_as_history(world, general):  # noqa: F811
    h = world["h"][LearnerRole.CDD]
    assert _general(h, "ord-pre", "PRE", 1, _answers(general))["detail"] == "score 3/3"
    mods = _learning(h)["modules"]
    minute = 10
    for mod in mods[:-1]:
        m_id = mod["module_id"]
        if mod["has_quiz"]:
            _upload(h, {"client_id": f"ord-q-{m_id[:8]}", "module_id": m_id, "correct_count": mod["quiz_statements"],
                        "total_count": mod["quiz_statements"], "taken_at": at(minute), "test_type": "MODULE_QUIZ"})
        assert _progress(h, {**_done(type("M", (), {"id": m_id}), minute + 1)})[m_id]["detail"] is None
        minute += 3
    last = mods[-1]
    if last["has_quiz"]:
        _upload(h, {"client_id": "ord-q-last", "module_id": last["module_id"], "correct_count": last["quiz_statements"],
                    "total_count": last["quiz_statements"], "taken_at": at(minute), "test_type": "MODULE_QUIZ"})
    # An older app uploads the post-test first: it is refused for now ...
    assert _general(h, "ord-post", "POST", minute + 3, _answers(general))["detail"] == "complete all your modules first"
    # ... and counts as soon as the last completion (made before it) arrives.
    assert _progress(h, _done(type("M", (), {"id": last["module_id"]}), minute + 2))[last["module_id"]]["detail"] is None
    post = _learning(h)["general_test"]["post_test"]
    assert post is not None and post["client_id"] == "ord-post" and post["passed"] is True
    # A second post-test after certification is tolerated and clearly ignored.
    again = _general(h, "ord-post-2", "POST", minute + 10, _answers(general, right=False))
    assert again["detail"] == "post-test already taken: certification already obtained, kept as history and does not count"
    assert _learning(h)["general_test"]["post_test"]["client_id"] == "ord-post", "the certification stands"


def test_retry_attempts_store_which_statements_were_shown(world):  # noqa: F811
    h, A = world["h"][LearnerRole.HEALTH_WORKER], world["m"]["A"]
    qid = str(uuid.uuid4())
    item = {**_quiz("retry-new", A, 1, 1), "results": [{"question_id": qid, "correct": True, "shown": False}]}
    old = {**_quiz("retry-old", A, 0, 0), "results": [{"question_id": qid, "correct": False}]}
    _upload(h, old, item)
    assert _attempt("retry-new").results == [{"question_id": qid, "correct": True, "shown": False}]
    assert _attempt("retry-old").results == [{"question_id": qid, "correct": False}], "older apps' format unchanged"


def test_repair_script_dry_run_then_apply(world):  # noqa: F811
    h, A, B = world["h"][LearnerRole.HEALTH_WORKER], world["m"]["A"], world["m"]["B"]
    me = world["learners"][LearnerRole.HEALTH_WORKER]
    _upload(h, _quiz("rep-qa", A, 1, 1))
    assert _progress(h, _done(A, 4))[str(A.id)]["detail"] is None
    # The state the bug left behind on the server: B's passing quiz refused as "locked",
    # the time met, the module not completed.
    s = SessionLocal()
    s.add(QuizAttempt(user_id=me.id, module_id=B.id, client_id="rep-qb", correct_count=1, total_count=1, score_percent=100,
                      passed=True, results=[], taken_at=at(5), test_type=TestType.MODULE_QUIZ, valid=False,
                      invalid_reason=LOCKED_PREVIOUS))
    s.add(UserModuleProgress(user_id=me.id, module_id=B.id, progress_percent=99, completed=False, seconds_spent=200))
    s.commit()
    s.close()

    dry = {who["id"]: c for who, c in repair.run(apply=False)}
    mine = dry[me.id]
    assert [c["kind"] for c in mine] == ["module_quiz", "completion"] and mine[1]["module_id"] == str(B.id)
    assert _state(h, B)["completed"] is False and _attempt("rep-qb").valid is False, "a dry run changes nothing"

    s = SessionLocal()
    user = s.get(User, me.id)
    changes = repair.plan_user(s, user)
    s.commit()
    s.close()
    assert [c["kind"] for c in changes] == ["module_quiz", "completion"]
    assert _state(h, B)["completed"] is True and _attempt("rep-qb").valid is True
    s = SessionLocal()
    assert repair.plan_user(s, s.get(User, me.id)) == [], "running it again finds nothing"
    s.rollback()
    s.close()
