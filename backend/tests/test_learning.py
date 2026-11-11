"""
Learner roles, role-based content, and module completion (inline quiz + minimum time).
The General pre/post test is in tests/test_general_test.py.

    cd backend && python -m pytest tests/test_learning.py -v
"""
import hashlib
import importlib.util
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import SessionLocal, engine
from app.learning import rules
from app.main import app
from app.models import (
    AiQuestionLog,
    AuditLog,
    ContentChunk,
    ContentRelease,
    ContentSection,
    Language,
    Module,
    ModuleTranslation,
    QuizAttempt,
    QuizQuestion,
    User,
    UserModuleProgress,
    Video,
)
from app.models.enums import (
    AuditAction,
    ContentReviewStatus,
    ContentType,
    LearnerRole,
    ModuleAudience,
    ModuleStatus,
    RoleName,
    VideoStatus,
)
from app.releases.packager import package_path
from tests.test_content import _auth_headers, _login, _make_user
from tests.test_sync import _cleanup

client = TestClient(app)
VECTORS = json.loads((Path(__file__).parent / "learning_vectors.json").read_text(encoding="utf-8"))
T0 = datetime.now(timezone.utc) - timedelta(hours=10)


def at(minutes: int) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat()


# ---------- the rules themselves (the Dart rules pass the same file) ----------
@pytest.mark.parametrize("case", VECTORS["completion"], ids=lambda c: c["why"][:50])
def test_completion_rule_vectors(case):
    passed = case["quiz_statements"] > 0 and case["quiz_correct"] is not None and rules.module_quiz_passes(
        case["quiz_correct"], case["quiz_statements"])
    got = rules.can_complete_module(case["unlocked"], case["quiz_statements"] > 0, passed, case["seconds"], case["min_seconds"])
    assert got is case["can_complete"], case["why"]


@pytest.mark.parametrize("case", VECTORS["cases"], ids=lambda c: c["why"][:50])
def test_pass_rule_vectors(case):
    assert VECTORS["pass_mark"] == 90
    got = rules.post_test_completes(case["post_correct"], case["post_total"], case["pre_correct"], case["pre_total"],
                                    auto_approve_at=VECTORS["auto_approve_percent"])
    assert got is case["completes"], case["why"]


# ---------- fixtures ----------
@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def world(db):
    """Three published modules that come before M1-M6: A and B are general,
    R is for Health Workers only. One learner per learner role, plus staff."""
    english = db.query(Language).filter_by(code="en").one()
    n = uuid.uuid4().hex[:6]
    mods = {}
    for key, order, audience, roles in (
        ("A", -2000, ModuleAudience.GENERAL, []),
        ("B", -1990, ModuleAudience.GENERAL, []),
        ("R", -1980, ModuleAudience.ROLE_SPECIFIC, [LearnerRole.HEALTH_WORKER.value]),
    ):
        m = Module(module_code=f"L{key}{n}", module_number=800, title=f"Learning test {key}",
                   status=ModuleStatus.PUBLISHED, sort_order=order, audience=audience, learner_roles=roles)
        db.add(m)
        db.flush()
        # a retired per-module question, archived as the 2026-11 migration left every one of them
        db.add(QuizQuestion(module_id=m.id, question_type="MULTIPLE_CHOICE", prompt=f"Question {key}?",
                            content={"options": ["a", "b"], "correct": 0}, is_active=False,
                            archived_at=datetime.now(timezone.utc)))
        db.add(ModuleTranslation(module_id=m.id, language_id=english.id, title=m.title,
                                 status=ContentReviewStatus.PUBLISHED))
        sec = ContentSection(module_id=m.id, section_number=1, title=f"Section {key}", content_type=ContentType.TEXT,
                             content={"text": f"Secret words for module {key} zebracrossing{key}"}, sort_order=1)
        db.add(sec)
        db.add(ContentSection(module_id=m.id, section_number=2, content_type=ContentType.TRUE_FALSE, sort_order=2,
                              content={"statement": f"Module {key} quiz statement quaggafact{key}", "answer": True,
                                       "explanation": None, "audience": "HFW"}))
        db.flush()
        db.add(ContentChunk(module_id=m.id, module_code=m.module_code, section_id=sec.id, section_title=sec.title,
                            language="en", source_title=m.title, chunk_text=f"zebracrossing{key} dosage words"))
        mods[key] = m
    video = Video(title="Restricted video", module_id=mods["R"].id, filename="NOT_YET_UPLOADED",
                  storage_path="videos/none", mime_type="video/mp4", status=VideoStatus.PUBLISHED)
    db.add(video)
    db.commit()

    learners = {}
    for role in LearnerRole:
        u = _make_user(db, RoleName.CDD, english.id)
        u.learner_role = role
        learners[role] = u
    db.commit()
    staff = {r: _make_user(db, r, english.id) for r in (RoleName.SUPER_ADMIN, RoleName.CONTENT_ADMIN,
                                                        RoleName.PROGRAM_REVIEWER, RoleName.TECHNICAL_REVIEWER)}
    headers = {k: _auth_headers(_login(u.username)) for k, u in {**learners, **staff}.items()}
    yield {"m": mods, "video": video, "learners": learners, "staff": staff, "h": headers, "db": db}

    db.rollback()
    ids = [m.id for m in mods.values()]
    db.query(QuizAttempt).filter(QuizAttempt.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(UserModuleProgress).filter(UserModuleProgress.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(ContentChunk).filter(ContentChunk.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(AiQuestionLog).filter(AiQuestionLog.source_module_id.in_(ids)).delete(synchronize_session=False)
    db.query(Video).filter(Video.id == video.id).delete(synchronize_session=False)
    db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(ModuleTranslation).filter(ModuleTranslation.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(QuizQuestion).filter(QuizQuestion.module_id.in_(ids)).delete(synchronize_session=False)
    db.query(Module).filter(Module.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    for u in [*learners.values(), *staff.values()]:
        _cleanup(db, db.get(User, u.id))


def _attempt(cid, module, correct, total, kind, minute):
    return {"client_id": cid, "module_id": str(module.id), "correct_count": correct, "total_count": total,
            "taken_at": at(minute), "test_type": kind}


def _quiz(cid, module, correct, minute, total=1):
    return _attempt(cid, module, correct, total, "MODULE_QUIZ", minute)


def _upload(h, *items):
    r = client.post("/sync/quiz-attempts", headers=h, json={"device_id": "dev", "items": list(items)})
    assert r.status_code == 200, r.text
    return r.json()["results"]


def _read(h, module, minute, completed=False, seconds=None):
    item = {"module_id": str(module.id), "progress_percent": 100 if completed else 50, "completed": completed,
            "last_opened_at": at(minute), "reading_completed_at": at(minute), "seconds_spent": seconds}
    r = client.post("/sync/progress", headers=h, json={"device_id": "dev", "items": [item]})
    assert r.status_code == 200, r.text
    return r.json()["results"][0]


def _state(h, module):
    body = client.get("/sync/learning", headers=h).json()
    return next((m for m in body["modules"] if m["module_id"] == str(module.id)), None)


def _complete(h, module, start=0):
    """Pass the module's quiz and report the minimum time, as the phone does."""
    assert _upload(h, _quiz(f"q-{uuid.uuid4().hex[:8]}", module, 1, start))[0]["detail"] is None
    assert _read(h, module, start + 1, completed=True, seconds=180)["detail"] is None


# ---------- learner roles ----------
def test_learner_roles_on_create_edit_and_me_and_they_grant_no_permissions(world):
    h, db = world["h"], world["db"]
    ah = h[RoleName.SUPER_ADMIN]
    made = []
    try:
        for label, value in (("Health Worker", "HEALTH_WORKER"), ("Monitor/Supervisor", "MONITOR_SUPERVISOR"),
                             ("Others", "OTHER"), ("CDD", "CDD"), ("LOGISTICIAN", "LOGISTICIAN")):
            name = f"lr_{uuid.uuid4().hex[:8]}"
            r = client.post("/users", headers=ah, json={
                "username": name, "email": f"{name}@sarmaan-eplaybook.app", "password": "LongEnough123!",
                "first_name": "L", "last_name": "R", "learner_role": label})
            assert r.status_code == 201, r.text
            made.append(r.json()["id"])
            assert r.json()["role"] == "CDD" and r.json()["learner_role"] == value
        name = f"lr_{uuid.uuid4().hex[:8]}"
        base = {"username": name, "email": f"{name}@sarmaan-eplaybook.app", "password": "LongEnough123!",
                "first_name": "L", "last_name": "R"}
        r = client.post("/users", headers=ah, json=base)
        assert r.status_code == 422 and "learner_role is required" in r.text
        assert client.post("/users", headers=ah, json={**base, "learner_role": "Pilot"}).status_code == 422
        r = client.post("/users", headers=ah, json={**base, "role": "PROGRAM_REVIEWER"})  # staff need none
        assert r.status_code == 201 and r.json()["learner_role"] is None
        made.append(r.json()["id"])

        uid = made[0]
        db.query(User).filter_by(id=uuid.UUID(uid)).update({"learner_role_needs_review": True})
        db.commit()
        r = client.patch(f"/users/{uid}", headers=ah, json={"learner_role": "Logistician"})
        assert r.status_code == 200 and r.json()["learner_role"] == "LOGISTICIAN"
        assert r.json()["learner_role_needs_review"] is False
        log = db.query(AuditLog).filter_by(entity_id=uuid.UUID(uid), action=AuditAction.USER_UPDATE).order_by(
            AuditLog.created_at.desc()).first()
        assert log.details["learner_role"] == {"before": "HEALTH_WORKER", "after": "LOGISTICIAN"}
        assert client.patch(f"/users/{uid}", headers=ah, json={"clear_learner_role": True}).status_code == 422

        me = client.get("/auth/me", headers=h[LearnerRole.HEALTH_WORKER]).json()
        assert me["learner_role"] == "HEALTH_WORKER" and me["role"] == "CDD"
        for role in LearnerRole:  # a learner role is never a permission
            lh = h[role]
            assert client.get("/users", headers=lh).status_code == 403
            assert client.get("/learning/review", headers=lh).status_code == 403
            assert client.get("/reports/summary", headers=lh).status_code == 403
            assert client.get(f"/quiz/modules/{world['m']['A'].id}/questions", headers=lh).status_code == 403
            assert client.patch(f"/modules/{world['m']['A'].id}", headers=lh, json={"audience": "GENERAL"}).status_code == 403
    finally:
        for uid in made:
            u = db.get(User, uuid.UUID(uid))
            if u:
                _cleanup(db, u)


def test_bulk_import_validates_learner_roles_and_keeps_old_templates_working(world):
    ah, db = world["h"][RoleName.SUPER_ADMIN], world["db"]
    tag = uuid.uuid4().hex[:6]

    def csv(rows, header="first_name,last_name,username,email,role,learner_role"):
        return ("\n".join([header, *rows]) + "\n").encode()

    def upload(data):
        return client.post("/users/import", headers=ah, files={"file": ("users.csv", data, "text/csv")})

    rows = [f"A,B,imp{tag}a,imp{tag}a@x.org,,Monitor/Supervisor", f"A,B,imp{tag}b,imp{tag}b@x.org,,"]
    r = upload(csv(rows))
    assert r.status_code == 422 and "Row 3" in r.json()["detail"] and "learner_role is required" in r.json()["detail"]
    assert db.query(User).filter(User.username.like(f"imp{tag}%")).count() == 0  # all or nothing
    rows[1] = f"A,B,imp{tag}b,imp{tag}b@x.org,,Others"
    rows.append(f"A,B,imp{tag}c,imp{tag}c@x.org,PROGRAM_REVIEWER,")
    assert upload(csv(rows)).status_code == 200
    r = upload(csv([f"A,B,imp{tag}d,imp{tag}d@x.org"], header="first_name,last_name,username,email"))
    assert r.status_code == 200  # the old template (no learner_role column): CDD rows mean CDD
    db.expire_all()
    got = {u.username: (u.role.value, u.learner_role.value if u.learner_role else None)
           for u in db.query(User).filter(User.username.like(f"imp{tag}%"))}
    assert got == {f"imp{tag}a": ("CDD", "MONITOR_SUPERVISOR"), f"imp{tag}b": ("CDD", "OTHER"),
                   f"imp{tag}c": ("PROGRAM_REVIEWER", None), f"imp{tag}d": ("CDD", "CDD")}
    for u in db.query(User).filter(User.username.like(f"imp{tag}%")).all():
        _cleanup(db, u)


def test_migration_mapping_keeps_users_and_flags_what_it_cannot_map(db):
    """Runs the migration's data mapping (BACKFILL) inside a transaction that is rolled back."""
    path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "a3c8e4f61b29_learner_roles_and_pre_post_tests.py"
    spec = importlib.util.spec_from_file_location("mig", path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    english = db.query(Language).filter_by(code="en").one()
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            ids = {}
            for role in ("CDD", "SUPERVISOR", "CONTENT_ADMIN"):
                uid = uuid.uuid4()
                ids[role] = uid
                conn.execute(text(
                    "INSERT INTO users (id, username, email, password_hash, first_name, last_name, role, language_id, status) "
                    "VALUES (:id, :u, :e, 'x', 'M', 'G', :r, :l, 'ACTIVE')"),
                    {"id": uid, "u": f"mig_{uid.hex[:8]}", "e": f"mig_{uid.hex[:8]}@x.org", "r": role, "l": english.id})
            mod = conn.execute(text("SELECT id FROM modules WHERE module_code = 'M1'")).scalar()
            conn.execute(text("UPDATE modules SET audience_needs_review = false"))
            conn.execute(text(
                "INSERT INTO quiz_attempts (id, user_id, module_id, client_id, correct_count, total_count, score_percent, "
                "passed, results, taken_at) VALUES (:id, :u, :m, 'legacy-1', 9, 10, 90, true, '[]', now())"),
                {"id": uuid.uuid4(), "u": ids["CDD"], "m": mod})
            conn.execute(text(
                "INSERT INTO user_module_progress (id, user_id, module_id, progress_percent, completed, completed_at) "
                "VALUES (:id, :u, :m, 100, true, now())"), {"id": uuid.uuid4(), "u": ids["CDD"], "m": mod})
            for statement in mig.BACKFILL:
                conn.execute(text(statement))
            users = {r[0]: (r[1], r[2]) for r in conn.execute(text(
                "SELECT role, learner_role, learner_role_needs_review FROM users WHERE id = ANY(:ids)"),
                {"ids": list(ids.values())})}
            assert users == {"CDD": ("CDD", False), "SUPERVISOR": (None, True), "CONTENT_ADMIN": (None, False)}
            assert conn.execute(text("SELECT bool_and(audience_needs_review) FROM modules")).scalar() is True
            assert conn.execute(text("SELECT count(*) FROM modules WHERE audience <> 'GENERAL' AND module_code LIKE 'M_'")).scalar() == 0
            valid, reason = conn.execute(text("SELECT valid, invalid_reason FROM quiz_attempts WHERE client_id = 'legacy-1'")).one()
            assert valid is False and reason == mig.LEGACY_ATTEMPT
            done, legacy = conn.execute(text(
                "SELECT completed, legacy_reading FROM user_module_progress WHERE user_id = :u"), {"u": ids["CDD"]}).one()
            assert done is True and legacy is True  # completed modules stay completed
        finally:
            trans.rollback()


def test_existing_content_stays_available_to_every_learner_role(world):
    h = world["h"]
    for role in LearnerRole:
        codes = {m["module_code"] for m in client.get("/modules", headers=h[role]).json()}
        assert {"M1", "M2", "M3", "M4", "M5", "M6"} <= codes, role
        # the per-module pre/post tests were retired and archived (2026-11): none is served any more
        assert client.get("/sync/quiz-questions", headers=h[role]).json() == []


# ---------- role-based visibility, enforced on every route ----------
def test_general_content_for_every_role_and_restricted_content_only_for_its_role(world):
    m, h, video = world["m"], world["h"], world["video"]
    a, r = m["A"], m["R"]
    for role in LearnerRole:
        lh = h[role]
        mine = role == LearnerRole.HEALTH_WORKER
        ids = {x["id"] for x in client.get("/modules", headers=lh).json()}
        assert str(a.id) in ids and str(m["B"].id) in ids
        assert (str(r.id) in ids) is mine, role
        want = 200 if mine else 404
        assert client.get(f"/modules/{r.id}", headers=lh).status_code == want
        assert client.get(f"/modules/{r.id}/sections", headers=lh).status_code == want
        assert client.get(f"/modules/{r.id}/translations", headers=lh).status_code == want
        assert client.get(f"/videos/{video.id}", headers=lh).status_code == want
        assert (str(video.id) in {v["id"] for v in client.get("/videos", headers=lh).json()}) is mine
        assert client.get(f"/videos/{video.id}/file", headers=lh).status_code == 404  # (no file uploaded either way)
        # R's inline quiz statement travels with its sections (404 above for other roles)
        assert (_state(lh, r) is not None) is mine
        tr = {x["module_id"] for x in client.get("/sync/translations?language=en", headers=lh).json()["modules"]}
        assert (str(r.id) in tr) is mine
        chunks = {c["module_id"] for c in client.get("/ai/chunks?language=en", headers=lh).json()}
        assert str(a.id) in chunks and (str(r.id) in chunks) is mine
        ans = client.post("/ai/ask", headers=lh, json={"question": "zebracrossingR dosage", "language": "en"}).json()
        assert (str(r.id) in {s["module_id"] for s in ans["sources"]}) is mine
        if not mine:
            res = _upload(lh, _attempt(f"x-{uuid.uuid4().hex[:8]}", r, 9, 10, "PRE", 1))[0]
            assert res["status"] == "rejected" and res["detail"] == "not available for your learner role"
            assert _read(lh, r, 2)["status"] == "rejected"
    staff = h[RoleName.CONTENT_ADMIN]
    assert client.get(f"/modules/{r.id}/sections", headers=staff).status_code == 200  # staff preview everything


def test_release_package_is_filtered_per_role_and_a_role_change_triggers_a_new_download(world):
    m, h, db = world["m"], world["h"], world["db"]
    th = h[RoleName.TECHNICAL_REVIEWER]
    code = f"TEST-{uuid.uuid4().hex[:8]}"
    try:
        rid = client.post("/releases", headers=th, json={"release_code": code, "version": "9.9.7"}).json()["id"]
        assert client.post(f"/releases/{rid}/publish", headers=th).status_code == 200
        got = {}
        for role in (LearnerRole.HEALTH_WORKER, LearnerRole.CDD):
            cur = client.get(f"/sync/release/current?installed={code}", headers=h[role]).json()
            assert cur["release"]["release_code"] == code and cur["update_available"] is False
            dl = client.get(f"/sync/release/{code}/package", headers=h[role])
            assert dl.status_code == 200
            assert hashlib.sha256(dl.content).hexdigest() == cur["release"]["checksum"] == dl.headers["X-Package-SHA256"]
            assert len(dl.content) == cur["release"]["package_size"]
            pkg = json.loads(dl.content)
            got[role] = (cur["release"]["variant"], pkg)
        hw_variant, hw_pkg = got[LearnerRole.HEALTH_WORKER]
        cdd_variant, cdd_pkg = got[LearnerRole.CDD]
        assert hw_variant != cdd_variant
        hw_ids = {x["id"] for x in hw_pkg["modules"]}
        cdd_ids = {x["id"] for x in cdd_pkg["modules"]}
        assert str(m["R"].id) in hw_ids and str(m["R"].id) not in cdd_ids and str(m["A"].id) in cdd_ids
        assert str(m["R"].id) not in {c["module_id"] for c in cdd_pkg["chunks"]}
        entry = next(x for x in hw_pkg["modules"] if x["id"] == str(m["R"].id))
        assert entry["audience"] == "ROLE_SPECIFIC" and entry["learner_roles"] == ["HEALTH_WORKER"]
        assert cdd_pkg["counts"]["modules"] == len(cdd_pkg["modules"])

        # The Health Worker reads R, then becomes a Logistician.
        hw = world["learners"][LearnerRole.HEALTH_WORKER]
        _read(h[LearnerRole.HEALTH_WORKER], m["R"], 5)
        db.get(User, hw.id).learner_role = LearnerRole.LOGISTICIAN
        db.commit()
        cur = client.get(f"/sync/release/current?installed={code}&installed_variant={hw_variant}",
                         headers=h[LearnerRole.HEALTH_WORKER]).json()
        assert cur["update_available"] is True and cur["release"]["variant"] != hw_variant
        assert str(m["R"].id) not in {x["id"] for x in json.loads(
            client.get(f"/sync/release/{code}/package", headers=h[LearnerRole.HEALTH_WORKER]).content)["modules"]}
        # Their progress is kept (it would come back if the role changed back), but R is no longer theirs.
        db.expire_all()
        assert db.query(UserModuleProgress).filter_by(user_id=hw.id, module_id=m["R"].id).count() == 1
        assert _state(h[LearnerRole.HEALTH_WORKER], m["R"]) is None
    finally:
        rel = db.query(ContentRelease).filter_by(release_code=code).one_or_none()
        if rel:
            db.delete(rel)
            db.commit()
        for p in package_path(code).parent.glob(f"{code}*.package.json"):
            p.unlink()
        from app.ai.indexer import rebuild_all_chunks
        rebuild_all_chunks(db)
        db.commit()


# ---------- completing a module: inline quiz + minimum time ----------
def test_module_quiz_and_three_minutes_complete_a_module(world):
    m, h = world["m"], world["h"]
    lh = h[LearnerRole.CDD]
    a = m["A"]
    st = _state(lh, a)
    assert st["status"] == "READING" and st["has_quiz"] and st["quiz_statements"] == 1 and not st["quiz_passed"]
    assert st["has_tests"] is False and client.get("/sync/learning", headers=lh).json()["module_min_seconds"] == 180
    assert _read(lh, a, 1, completed=True, seconds=60)["detail"] == "not completed: module quiz not passed yet"
    assert _upload(lh, _quiz("w1", a, 0, 2))[0]["detail"] is None       # wrong answer: kept, not passed
    assert _state(lh, a)["quiz_passed"] is False
    assert _upload(lh, _quiz("w2", a, 1, 3))[0]["detail"] is None       # retake: passed
    st = _state(lh, a)
    assert st["quiz_passed"] is True and st["quiz_attempts"] == 2 and st["completed"] is False  # completing is the learner's step
    assert _read(lh, a, 4, completed=True, seconds=179)["detail"] == "not completed: less than 180 seconds in this module"
    assert _read(lh, a, 5, completed=True, seconds=180)["detail"] is None
    st = _state(lh, a)
    assert st["status"] == "COMPLETED" and st["seconds_spent"] == 180
    assert _state(lh, m["B"])["unlocked"] is True
    attempts = client.get("/sync/learning", headers=lh).json()["attempts"]
    assert {x["client_id"] for x in attempts if x["module_id"] == str(a.id)} == {"w1", "w2"}  # every attempt kept


def test_next_module_is_locked_until_the_previous_one_is_completed(world):
    m, h = world["m"], world["h"]
    lh = h[LearnerRole.LOGISTICIAN]
    assert _state(lh, m["B"])["status"] == "LOCKED"
    locked = "module is locked: complete the previous module first"
    assert _upload(lh, _quiz("k1", m["B"], 1, 1))[0]["detail"] == locked
    assert _read(lh, m["B"], 2, completed=True, seconds=900)["detail"] == f"not completed: {locked}"
    _complete(lh, m["A"], start=3)
    assert _state(lh, m["B"])["status"] == "READING"
    assert _upload(lh, _quiz("k2", m["B"], 1, 10))[0]["detail"] is None


def test_the_old_per_module_tests_no_longer_count(world):
    """Older apps may still upload PRE/POST attempts: they are kept as history and never
    complete or unlock anything; the archived questions are not served."""
    m, lh = world["m"], world["h"][LearnerRole.OTHER]
    a = m["A"]
    res = _upload(lh, _attempt("o1", a, 2, 10, "PRE", 1), _attempt("o2", a, 10, 10, "POST", 2),
                  {k: v for k, v in _attempt("o3", a, 10, 10, "POST", 3).items() if k != "test_type"})
    assert [r["detail"] for r in res] == ["per-module pre/post tests were replaced (2026-11)"] * 3
    st = _state(lh, a)
    assert st["completed"] is False and st["pre_test"] is None and st["post_test_attempts"] == 0
    assert _state(lh, m["B"])["unlocked"] is False
    assert [q for q in client.get("/sync/quiz-questions", headers=lh).json() if q["module_id"] == str(a.id)] == []
    assert client.post(f"/quiz/modules/{a.id}/questions", headers=world["h"][RoleName.CONTENT_ADMIN], json={
        "question_type": "MULTIPLE_CHOICE", "prompt": "Which one?", "content": {"options": ["a", "b", "c"], "correct": 1},
        "explanation": "because"}).status_code == 410


def test_a_completed_module_is_review_only(world, db):
    m, lh = world["m"], world["h"][LearnerRole.OTHER]
    learner = world["learners"][LearnerRole.OTHER]
    a = m["A"]
    _complete(lh, a)
    res = _upload(lh, _quiz("again", a, 0, 10))[0]
    assert res["status"] == "ok" and res["detail"] == "module already completed"
    assert _read(lh, a, 11)["status"] == "ok"
    db.expire_all()
    row = db.query(UserModuleProgress).filter_by(user_id=learner.id, module_id=a.id).one()
    assert row.completed is True and row.progress_percent == 100
    assert _state(lh, a)["quiz_passed"] is True


def test_offline_batch_is_idempotent_and_time_only_grows(world, db):
    m, lh = world["m"], world["h"][LearnerRole.HEALTH_WORKER]
    learner = world["learners"][LearnerRole.HEALTH_WORKER]
    a = m["A"]
    batch = [_quiz("o-1", a, 0, 1), _quiz("o-2", a, 1, 2)]
    assert [x["status"] for x in _upload(lh, *batch)] == ["ok", "ok"]
    assert [x["status"] for x in _upload(lh, *batch)] == ["duplicate", "duplicate"]
    assert db.query(QuizAttempt).filter_by(user_id=learner.id, module_id=a.id).count() == 2
    _read(lh, a, 3, seconds=120)
    _read(lh, a, 4, seconds=60)    # an older phone's smaller value never lowers it
    assert _state(lh, a)["seconds_spent"] == 120
    assert _read(lh, a, 5, completed=True, seconds=200)["detail"] is None
    assert _read(lh, a, 5, completed=True, seconds=200)["status"] in ("ok", "duplicate")
    assert _state(lh, a)["completed"] is True and _state(lh, a)["seconds_spent"] == 200


def test_a_module_completed_before_the_change_stays_completed(world, db):
    """Completed before the new rules (no quiz attempt, no time recorded): never re-locked."""
    m, lh = world["m"], world["h"][LearnerRole.CDD]
    learner = world["learners"][LearnerRole.CDD]
    db.add(UserModuleProgress(user_id=learner.id, module_id=m["A"].id, progress_percent=100, completed=True,
                              completed_at=T0, seconds_spent=0))
    db.commit()
    st = _state(lh, m["A"])
    assert st["completed"] is True and st["seconds_spent"] == 0 and st["quiz_passed"] is False
    assert _state(lh, m["B"])["unlocked"] is True


def test_quiz_statements_follow_the_module_audience_and_are_never_search_answers(world):
    m, h = world["m"], world["h"]
    r = m["R"]
    hw = client.get(f"/modules/{r.id}/sections", headers=h[LearnerRole.HEALTH_WORKER])
    assert hw.status_code == 200 and any(x["content_type"] == "TRUE_FALSE" for x in hw.json())
    assert client.get(f"/modules/{r.id}/sections", headers=h[LearnerRole.CDD]).status_code in (403, 404)
    from app.ai.indexer import rebuild_all_chunks
    rebuild_all_chunks(world["db"])
    world["db"].commit()
    ask = client.post("/ai/ask", headers=h[LearnerRole.HEALTH_WORKER], json={"question": "quaggafactR quiz statement"})
    assert all("quaggafact" not in (s.get("chunk_text") or "") for s in ask.json().get("sources", []))
    assert "quaggafact" not in (ask.json().get("answer") or "")


def test_true_false_sections_are_checked_when_saved(world):
    m, ch = world["m"], world["h"][RoleName.CONTENT_ADMIN]
    a = m["A"]
    base = {"section_number": 9, "content_type": "TRUE_FALSE", "sort_order": 9}
    assert client.post(f"/modules/{a.id}/sections", headers=ch, json={**base, "content": {"statement": "x"}}).status_code == 422
    bad = client.post(f"/modules/{a.id}/sections", headers=ch,
                      json={**base, "content": {"statement": "x", "answer": "yes", "audience": "HFW"}})
    assert bad.status_code == 422
    ok = client.post(f"/modules/{a.id}/sections", headers=ch, json={**base, "content": {
        "statement": "  AZM is given door to door ", "answer": True, "explanation": "", "audience": "CDD", "junk": 1}})
    assert ok.status_code == 201
    assert ok.json()["content"] == {"statement": "AZM is given door to door", "answer": True, "explanation": None, "audience": "CDD"}
    up = client.patch(f"/modules/sections/{ok.json()['id']}", headers=ch,
                      json={"content": {"statement": "Changed", "answer": False, "audience": "CDD"}})
    assert up.status_code == 200 and up.json()["content"]["answer"] is False
    assert _state(world["h"][LearnerRole.CDD], a)["quiz_statements"] == 2


# ---------- admin configuration and reports ----------
def test_admins_classify_modules_and_tag_questions(world):
    m, h, db = world["m"], world["h"], world["db"]
    ch = h[RoleName.CONTENT_ADMIN]
    a = m["A"]
    db.get(Module, a.id).audience_needs_review = True
    db.commit()
    assert any(x["id"] == str(a.id) and x["needs_review"] for x in client.get("/learning/review", headers=ch).json()["modules"])
    r = client.patch(f"/modules/{a.id}", headers=ch, json={"audience": "ROLE_SPECIFIC", "learner_roles": []})
    assert r.status_code == 422
    assert client.patch(f"/modules/{a.id}", headers=h[RoleName.PROGRAM_REVIEWER], json={"audience": "GENERAL"}).status_code == 403
    r = client.patch(f"/modules/{a.id}", headers=ch, json={"audience": "ROLE_SPECIFIC", "learner_roles": ["LOGISTICIAN", "CDD"]})
    assert r.status_code == 200 and r.json()["learner_roles"] == ["CDD", "LOGISTICIAN"] and r.json()["audience_needs_review"] is False
    log = db.query(AuditLog).filter_by(entity_id=a.id, action=AuditAction.AUDIENCE_CHANGE).one()
    assert log.details["before"]["audience"] == "GENERAL" and log.details["after"]["learner_roles"] == ["CDD", "LOGISTICIAN"]
    assert str(a.id) not in {x["id"] for x in client.get("/modules", headers=h[LearnerRole.OTHER]).json()}
    r = client.patch(f"/modules/{a.id}", headers=ch, json={"audience": "GENERAL", "learner_roles": ["CDD"]})
    assert r.json()["audience"] == "GENERAL" and r.json()["learner_roles"] == []



def test_report_shows_quiz_time_and_the_old_tests_separately(world):
    m, h = world["m"], world["h"]
    lh = h[LearnerRole.LOGISTICIAN]
    a = m["A"]
    _upload(lh, _attempt("t1", a, 4, 10, "PRE", 1))          # an old app's test: history only
    _upload(lh, _quiz("t2", a, 0, 2), _quiz("t3", a, 1, 3))
    _read(lh, a, 4, completed=True, seconds=240)
    rows = client.get("/learning/report?learner_role=LOGISTICIAN", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    row = next(r for r in rows if r["module_code"] == a.module_code and r["username"] == world["learners"][LearnerRole.LOGISTICIAN].username)
    assert row["status"] == "COMPLETED" and row["learner_role"] == "LOGISTICIAN" and row["learner_group"] == "HFW & others"
    assert row["quiz_attempts"] == 2 and row["quiz_passed"] is True and row["quiz_latest_score"] == 100
    assert row["seconds_spent"] == 240 and row["min_seconds"] == 180 and row["curriculum"] == "HFW"
    assert row["pre_test_score"] is None and row["attempts_not_counted"] == 1  # the old PRE was not counted
    csv = client.get("/learning/report.csv?learner_role=LOGISTICIAN", headers=h[RoleName.PROGRAM_REVIEWER])
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    header = csv.text.splitlines()[0]
    assert all(k in header for k in ("pre_test_score", "post_test_best_score", "quiz_passed", "seconds_spent"))
    assert client.get("/learning/report", headers=lh).status_code == 403
    detail = client.get(f"/learning/attempts/{world['learners'][LearnerRole.LOGISTICIAN].id}", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    assert [(d["test_type"], d["score_percent"]) for d in detail if d["module_code"] == a.module_code] == [
        ("PRE", 40), ("MODULE_QUIZ", 0), ("MODULE_QUIZ", 100)]
    users = client.get("/reports/users?learner_role=LOGISTICIAN", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    assert users and all(u["learner_role"] == "LOGISTICIAN" for u in users)
    me = next(u for u in users if u["username"] == world["learners"][LearnerRole.LOGISTICIAN].username)
    assert me["module_quiz_attempts"] == 2 and me["module_quizzes_passed"] == 1 and me["seconds_spent_total"] == 240
    assert me["general_pre_points"] is None and "quiz_attempts" in me  # existing fields are still there
