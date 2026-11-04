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
from app.models import ContentRelease, Language, MediaAsset, Module, QuizAttempt, QuizQuestion, UserModuleProgress
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
    db.delete(db.get(Module, module.id))
    db.commit()
    _cleanup(db, learner)
    _cleanup(db, editor)


def _mc(prompt="Which?", correct=1):
    return {"question_type": "MULTIPLE_CHOICE", "prompt": prompt, "content": {"options": ["a", "b", "c"], "correct": correct},
            "explanation": "because"}


def test_author_all_seven_types_and_learner_cannot_read_answers(world, db):
    module, eh, lh, _ = world
    image = db.query(MediaAsset).first()
    bodies = [
        _mc(),
        {"question_type": "TRUE_FALSE", "prompt": "AZM is a vitamin.", "content": {"correct": False}},
        {"question_type": "MULTIPLE_SELECT", "prompt": "Pick two", "content": {"options": ["a", "b", "c", "d"], "correct": [1, 3]}},
        {"question_type": "MATCHING", "prompt": "Match", "content": {"pairs": [{"left": "1-2 months", "right": "2 ml"}, {"left": "3-4 months", "right": "3 ml"}]}},
        {"question_type": "ORDERING", "prompt": "Order", "content": {"items": ["one", "two", "three"]}},
        {"question_type": "IMAGE_CHOICE", "prompt": "What is shown?", "content": {"media_asset_id": str(image.id), "options": ["x", "y"], "correct": 0}},
        {"question_type": "NUMERIC", "prompt": "How many ml?", "content": {"correct": 15, "unit": "ml"}},
    ]
    for b in bodies:
        r = client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json=b)
        assert r.status_code == 201, (b["question_type"], r.text)
    listing = client.get(f"/quiz/modules/{module.id}/questions", headers=eh).json()
    assert [q["question_type"] for q in listing] == [b["question_type"] for b in bodies]  # authored order kept
    assert client.get(f"/quiz/modules/{module.id}/questions", headers=lh).status_code == 403
    assert client.post(f"/quiz/modules/{module.id}/questions", headers=lh, json=bodies[0]).status_code == 403

    bad = client.post(f"/quiz/modules/{module.id}/questions", headers=eh,
                      json={"question_type": "IMAGE_CHOICE", "prompt": "Pic?", "content": {"media_asset_id": str(uuid.uuid4()), "options": ["a", "b"], "correct": 0}})
    assert bad.status_code == 422
    qid = listing[0]["id"]
    up = client.patch(f"/quiz/questions/{qid}", headers=eh, json={"content": {"options": ["a", "b", "c"], "correct": 2}, "prompt": "New wording?"})
    assert up.status_code == 200 and up.json()["content"]["correct"] == 2
    assert client.patch(f"/quiz/questions/{qid}", headers=eh, json={"content": {"options": ["a"], "correct": 0}}).status_code == 422
    assert client.delete(f"/quiz/questions/{qid}", headers=eh).status_code == 204
    assert client.delete(f"/quiz/questions/{qid}", headers=eh).status_code == 404


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


def test_module_with_a_quiz_cannot_be_completed_by_mark_as_complete(world):
    module, eh, lh, _ = world
    client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json=_mc())
    done = {"module_id": str(module.id), "progress_percent": 100, "completed": True, "last_opened_at": NOW, "completed_at": NOW}

    r = client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [done]})
    assert r.json()["results"][0]["detail"].startswith("not completed: post-test not passed")

    # Even a 90% quiz from an old app (no test_type) does not complete it.
    client.post("/sync/quiz-attempts", headers=lh, json={"device_id": "d", "items": [_attempt("f2", module, 9, 10)]})
    client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [done]})
    mine = [p for p in client.get("/sync/progress", headers=lh).json() if p["module_id"] == str(module.id)]
    assert mine and mine[0]["completed"] is False and mine[0]["progress_percent"] == 99


def test_module_without_a_quiz_can_still_be_completed(world):
    module, _, lh, _ = world
    done = {"module_id": str(module.id), "progress_percent": 100, "completed": True, "last_opened_at": NOW, "completed_at": NOW}
    r = client.post("/sync/progress", headers=lh, json={"device_id": "d", "items": [done]})
    assert r.json()["results"][0] == {"key": str(module.id), "status": "ok", "detail": None}
    mine = [p for p in client.get("/sync/progress", headers=lh).json() if p["module_id"] == str(module.id)]
    assert mine and mine[0]["completed"] is True


def test_questions_and_image_ship_in_the_release_package(world, db):
    module, eh, _, _ = world
    image = db.query(MediaAsset).first()
    client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json=_mc("Text question?"))
    client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json={
        "question_type": "IMAGE_CHOICE", "prompt": "Pic?", "content": {"media_asset_id": str(image.id), "options": ["a", "b"], "correct": 0}})
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
        assert pkg["quiz_pass_mark"] == 90 and len(entry["quiz_questions"]) == 2
        assert {q["question_type"] for q in entry["quiz_questions"]} == {"MULTIPLE_CHOICE", "IMAGE_CHOICE"}
        assert str(image.id) in {m["id"] for m in pkg["media"]}
        assert pkg["counts"]["quiz_questions"] >= 2
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


def test_learner_can_fetch_quiz_for_home_sync(world):
    module, eh, lh, _ = world
    client.post(f"/quiz/modules/{module.id}/questions", headers=eh, json=_mc("Sync me?"))
    r = client.get("/sync/quiz-questions", headers=lh)
    assert r.status_code == 200
    mine = [q for q in r.json() if q["module_id"] == str(module.id)]
    assert len(mine) == 1 and mine[0]["prompt"] == "Sync me?" and mine[0]["content"]["correct"] == 1
    assert client.get("/sync/quiz-questions").status_code in (401, 403)
