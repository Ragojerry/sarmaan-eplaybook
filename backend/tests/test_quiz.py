"""
Quiz: shared grading vectors, authoring API, attempt sync with the 90% rule,
the completion gate, and delivery in the release package.

    cd backend && python3 -m pytest tests/test_quiz.py -v
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import ContentRelease, ContentSection, Language, MediaAsset, Module, QuizAttempt, QuizQuestion, UserModuleProgress
from app.models.enums import ModuleStatus, QuestionType as T, RoleName
from app.quiz import grading
from app.releases.packager import package_path
from tests.test_content import _auth_headers, _login, _make_user
from tests.test_sync import _cleanup

client = TestClient(app)
VECTORS = json.loads((Path(__file__).parent / "quiz_vectors.json").read_text(encoding="utf-8"))
NOW = datetime.now(timezone.utc).isoformat()


# ---------- shared vectors (the Dart grader must pass the same file) ----------
@pytest.mark.parametrize("case", VECTORS["answers"], ids=lambda c: f'{c["type"]}-{c["answer"]}'[:40])
def test_grading_vectors(case):
    t = T(case["type"])
    content = grading.validate_content(t, case["content"])
    assert grading.is_correct(t, content, case["answer"]) is case["correct"]


@pytest.mark.parametrize("case", VECTORS["passing"], ids=lambda c: f'{c["correct"]}of{c["total"]}')
def test_ninety_percent_rule_is_exact(case):
    assert VECTORS["pass_mark"] == 90
    assert grading.passed(case["correct"], case["total"]) is case["passed"]
    assert grading.score_percent(case["correct"], case["total"]) == case["score_percent"]


@pytest.mark.parametrize(
    "qtype,content",
    [
        (T.MULTIPLE_CHOICE, {"options": ["only"], "correct": 0}),
        (T.MULTIPLE_CHOICE, {"options": ["a", "b"], "correct": 5}),
        (T.MULTIPLE_CHOICE, {"options": ["a", "A"], "correct": 0}),  # duplicates
        (T.TRUE_FALSE, {"correct": "yes"}),
        (T.MULTIPLE_SELECT, {"options": ["a", "b", "c"], "correct": [0, 1, 2]}),  # all correct
        (T.MULTIPLE_SELECT, {"options": ["a", "b", "c"], "correct": []}),
        (T.MATCHING, {"pairs": [{"left": "a", "right": "x"}]}),
        (T.MATCHING, {"pairs": [{"left": "a", "right": "x"}, {"left": "b", "right": "x"}]}),
        (T.ORDERING, {"items": ["a", "b"]}),
        (T.NUMERIC, {"correct": "abc"}),
        (T.NUMERIC, {"correct": 1, "tolerance": -1}),
        (T.IMAGE_CHOICE, {"options": ["a", "b"], "correct": 0}),  # no picture
    ],
)
def test_invalid_questions_are_rejected(qtype, content):
    with pytest.raises(grading.InvalidQuestion):
        grading.validate_content(qtype, content)


# ---------- API ----------
@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def world(db):
    english = db.query(Language).filter_by(code="en").one()
    editor = _make_user(db, RoleName.CONTENT_ADMIN, english.id)
    learner = _make_user(db, RoleName.CDD, english.id)
    n = uuid.uuid4().hex[:6]
    module = Module(module_code=f"TQ{n}", module_number=900 + int(n[:2], 16), title="Quiz test module",
                    status=ModuleStatus.PUBLISHED, sort_order=-1000)  # first in order, so never locked
    db.add(module)
    db.commit()
    eh, lh = _auth_headers(_login(editor.username)), _auth_headers(_login(learner.username))
    yield module, eh, lh, learner
    db.rollback()
    db.query(QuizAttempt).filter_by(module_id=module.id).delete()
    db.query(UserModuleProgress).filter_by(module_id=module.id).delete()
    db.query(QuizQuestion).filter_by(module_id=module.id).delete()
    db.query(ContentSection).filter_by(module_id=module.id).delete()
    db.delete(db.get(Module, module.id))
    db.commit()
    _cleanup(db, learner)
    _cleanup(db, editor)


def _mc(prompt="Which?", correct=1):
    return {"question_type": "MULTIPLE_CHOICE", "prompt": prompt, "content": {"options": ["a", "b", "c"], "correct": correct},
            "explanation": "because"}


def _archived(db, module, prompt="Which?", **content):
    """A per-module question as the retirement migration left it: kept, archived, never served."""
    q = QuizQuestion(module_id=module.id, question_type="MULTIPLE_CHOICE", prompt=prompt,
                     content=content or {"options": ["a", "b", "c"], "correct": 1}, is_active=False,
                     archived_at=datetime.now(timezone.utc))
    db.add(q)
    db.commit()
    return q


def test_per_module_tests_are_retired_and_kept_read_only(world, db):
    """2026-11: per-module pre/post tests were replaced by the General test and inline quizzes.
    The old questions stay for history; they cannot be added, re-activated or deleted here."""
    module, eh, lh, _ = world
    q = _archived(db, module)
    r = client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json=_mc())
    assert r.status_code == 410 and "retired" in r.json()["detail"]
    listing = client.get(f"/quiz/modules/{module.id}/questions", headers=eh).json()
    assert [x["id"] for x in listing] == [str(q.id)]  # still readable by staff
    assert client.get(f"/quiz/modules/{module.id}/questions", headers=lh).status_code == 403
    assert client.patch(f"/quiz/questions/{q.id}", headers=eh, json={"is_active": True}).status_code == 409
    assert client.delete(f"/quiz/questions/{q.id}", headers=eh).status_code == 409
    db.refresh(q)
    assert q.is_active is False and q.archived_at is not None


def _attempt(client_id, module, correct, total):
    return {"client_id": client_id, "module_id": str(module.id), "correct_count": correct, "total_count": total, "taken_at": NOW}


def test_attempts_are_idempotent_and_server_recomputes_pass(world):
    module, eh, lh, _ = world
    client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json=_mc())
    items = [_attempt("c1", module, 8, 10), _attempt("c2", module, 9, 10), _attempt("c3", module, 11, 10)]
    r = client.post("/sync/quiz-attempts", headers=lh, json={"device_id": "d1", "items": items})
    assert [x["status"] for x in r.json()["results"]] == ["ok", "ok", "rejected"]
    again = client.post("/sync/quiz-attempts", headers=lh, json={"device_id": "d1", "items": items[:2]})
    assert [x["status"] for x in again.json()["results"]] == ["duplicate", "duplicate"]
    s = client.get(f"/quiz/modules/{module.id}/summary", headers=eh).json()
    # An app without pre/post tests sends no test_type: kept as history, never counted.
    assert s["attempts"] == 2 and s["pre_test_attempts"] == 0 and s["post_test_attempts"] == 0
    assert s["learners_passed"] == 0 and s["pass_mark"] == 90


def test_an_old_apps_quiz_never_completes_a_module(world, db):
    """A module with an inline quiz needs that quiz; an older app's pre/post or untyped
    attempt is stored as history and never counts."""
    module, eh, lh, _ = world
    db.add(ContentSection(module_id=module.id, section_number=1, sort_order=1, content_type="TRUE_FALSE",
                          content={"statement": "AZM is given door to door", "answer": True, "audience": "HFW"}))
    db.commit()
    done = {"module_id": str(module.id), "progress_percent": 100, "completed": True, "last_opened_at": NOW,
            "completed_at": NOW, "seconds_spent": 600}
    r = client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [done]})
    assert r.json()["results"][0]["detail"] == "not completed: module quiz not passed yet"
    old = client.post("/sync/quiz-attempts", headers=lh, json={"device_id": "d", "items": [_attempt("f2", module, 9, 10)]})
    assert old.json()["results"][0]["detail"] == "per-module pre/post tests were replaced (2026-11)"
    client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [done]})
    mine = [p for p in client.get("/sync/progress", headers=lh).json() if p["module_id"] == str(module.id)]
    assert mine and mine[0]["completed"] is False and mine[0]["progress_percent"] == 99


def test_module_without_a_quiz_can_still_be_completed(world):
    module, _, lh, _ = world
    early = {"module_id": str(module.id), "progress_percent": 100, "completed": True, "last_opened_at": NOW,
             "completed_at": NOW, "seconds_spent": 179}
    r = client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [early]})
    assert r.json()["results"][0]["detail"] == "not completed: less than 180 seconds in this module"
    r = client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [{**early, "seconds_spent": 180}]})
    assert r.json()["results"][0] == {"key": str(module.id), "status": "ok", "detail": None}
    mine = [p for p in client.get("/sync/progress", headers=lh).json() if p["module_id"] == str(module.id)]
    assert mine and mine[0]["completed"] is True and mine[0]["seconds_spent"] == 180


def test_archived_questions_never_ship_in_the_release_package(world, db):
    module, eh, _, _ = world
    _archived(db, module, "Text question?")
    from app.models import ModuleTranslation
    from app.models.enums import ContentReviewStatus
    english = db.query(Language).filter_by(code="en").one()
    db.add(ModuleTranslation(module_id=module.id, language_id=english.id, title="T", status=ContentReviewStatus.PUBLISHED))
    db.commit()

    th_user = _make_user(db, RoleName.TECHNICAL_REVIEWER, english.id)
    th = _auth_headers(_login(th_user.username))
    code = f"TEST-{uuid.uuid4().hex[:8]}"
    try:
        rid = client.post("/releases", headers=th, json={"release_code": code, "version": "9.9.6"}).json()["id"]
        assert client.post(f"/releases/{rid}/publish", headers=th).status_code == 200
        pkg = json.loads(package_path(code).read_bytes())
        entry = next(m for m in pkg["modules"] if m["module_code"] == module.module_code)
        assert entry["quiz_questions"] == []
    finally:
        rel = db.query(ContentRelease).filter_by(release_code=code).one_or_none()
        if rel:
            db.delete(rel)
        db.query(ModuleTranslation).filter_by(module_id=module.id).delete()
        db.commit()
        if package_path(code).exists():
            package_path(code).unlink()
        _cleanup(db, th_user)
        from app.ai.indexer import rebuild_all_chunks
        rebuild_all_chunks(db)
        db.commit()


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_picture_upload_and_library_list(world, db):
    module, eh, lh, _ = world
    r = client.post("/media/images", headers=eh, files={"file": ("my pic!.png", PNG, "image/png")}, params={"alt": "A test"})
    assert r.status_code == 201, r.text
    mid = r.json()["id"]
    try:
        assert client.get("/media/" + mid + "/file", headers=eh).status_code == 200
        assert mid in {m["id"] for m in client.get("/media", headers=eh, params={"asset_type": "IMAGE"}).json()}
        assert client.post("/media/images", headers=eh, files={"file": ("x.png", b"not an image", "image/png")}).status_code == 415
        assert client.post("/media/images", headers=eh, files={"file": ("x.png", b"", "image/png")}).status_code == 415
        assert client.post("/media/images", headers=lh, files={"file": ("x.png", PNG, "image/png")}).status_code == 403
        assert client.get("/media", headers=lh).status_code == 403
    finally:
        from app.models import MediaAsset
        import uuid as _u
        a = db.get(MediaAsset, _u.UUID(mid))
        if a is not None:
            from app.routers.media import _media_root
            f = _media_root() / a.storage_path
            db.delete(a)
            db.commit()
            f.unlink(missing_ok=True)


def test_archived_questions_are_not_served_to_phones(world, db):
    module, eh, lh, _ = world
    _archived(db, module, "Sync me?")
    r = client.get("/sync/quiz-questions", headers=lh)
    assert r.status_code == 200
    assert [q for q in r.json() if q["module_id"] == str(module.id)] == []
    assert client.get("/sync/quiz-questions").status_code in (401, 403)


