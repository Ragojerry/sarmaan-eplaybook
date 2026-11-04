"""
Learner roles, role-based content, and the pre-test -> reading -> post-test flow.

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
    TestException,
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


# ---------- the rule itself (the Dart rules pass the same file) ----------
@pytest.mark.parametrize("case", VECTORS["cases"], ids=lambda c: c["why"][:50])
def test_pass_rule_vectors(case):
    assert VECTORS["pass_mark"] == 90
    got = rules.post_test_completes(case["post_correct"], case["post_total"], case["pre_correct"], case["pre_total"],
                                    exception_approved=case["exception_approved"])
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
        db.add(QuizQuestion(module_id=m.id, question_type="MULTIPLE_CHOICE", prompt=f"Question {key}?",
                            content={"options": ["a", "b"], "correct": 0}))
        db.add(ModuleTranslation(module_id=m.id, language_id=english.id, title=m.title,
                                 status=ContentReviewStatus.PUBLISHED))
        sec = ContentSection(module_id=m.id, section_number=1, title=f"Section {key}", content_type=ContentType.TEXT,
                             content={"text": f"Secret words for module {key} zebracrossing{key}"}, sort_order=1)
        db.add(sec)
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
    db.query(TestException).filter(TestException.module_id.in_(ids)).delete(synchronize_session=False)
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


def _upload(h, *items):
    r = client.post("/sync/quiz-attempts", headers=h, json={"device_id": "dev", "items": list(items)})
    assert r.status_code == 200, r.text
    return r.json()["results"]


def _read(h, module, minute, completed=False):
    item = {"module_id": str(module.id), "progress_percent": 100 if completed else 50, "completed": completed,
            "last_opened_at": at(minute), "reading_completed_at": at(minute)}
    r = client.post("/sync/progress", headers=h, json={"device_id": "dev", "items": [item]})
    assert r.status_code == 200, r.text
    return r.json()["results"][0]


def _state(h, module):
    body = client.get("/sync/learning", headers=h).json()
    return next((m for m in body["modules"] if m["module_id"] == str(module.id)), None)


def _complete_through_tests(h, module, start=0):
    assert _upload(h, _attempt(f"pre-{uuid.uuid4().hex[:8]}", module, 2, 10, "PRE", start))[0]["detail"] is None
    _read(h, module, start + 1)
    assert _upload(h, _attempt(f"post-{uuid.uuid4().hex[:8]}", module, 10, 10, "POST", start + 2))[0]["detail"] == "completed"


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
        questions = client.get("/sync/quiz-questions", headers=h[role]).json()
        assert questions and all(q["usage"] in ("BOTH", "PRE", "POST") for q in questions)


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
        quiz_modules = {q["module_id"] for q in client.get("/sync/quiz-questions", headers=lh).json()}
        assert str(a.id) in quiz_modules and (str(r.id) in quiz_modules) is mine
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


# ---------- the pre-test -> reading -> post-test sequence ----------
def test_pre_test_before_reading_and_post_test_only_after_reading(world):
    m, h = world["m"], world["h"]
    lh = h[LearnerRole.CDD]
    a = m["A"]
    assert _state(lh, a)["status"] == "PRE_TEST"
    res = _upload(lh, _attempt("s1", a, 9, 10, "POST", 1))[0]
    assert res["status"] == "ok" and res["detail"] == "no pre-test yet"  # kept, but it does not count
    assert _upload(lh, _attempt("s2", a, 5, 10, "PRE", 2))[0]["detail"] is None
    st = _state(lh, a)
    assert st["status"] == "READING" and st["pre_test"]["score_percent"] == 50
    assert _upload(lh, _attempt("s3", a, 10, 10, "POST", 3))[0]["detail"] == "reading not finished"
    _read(lh, a, 4)
    assert _state(lh, a)["status"] == "POST_TEST"
    assert _upload(lh, _attempt("s4", a, 10, 10, "POST", 3))[0]["detail"] == "taken before reading was finished"
    assert _upload(lh, _attempt("s5", a, 9, 10, "POST", 5))[0]["detail"] == "completed"
    st = _state(lh, a)
    assert st["status"] == "COMPLETED" and st["completed"] is True
    attempts = client.get("/sync/learning", headers=lh).json()["attempts"]
    mine = {x["client_id"]: x for x in attempts if x["module_id"] == str(a.id)}
    assert set(mine) == {"s1", "s2", "s3", "s4", "s5"}  # every attempt is kept as history
    assert [k for k, x in mine.items() if x["valid"]] == ["s2", "s5"]
    # B: reading before the pre-test means the pre-test cannot count.
    b = m["B"]
    _read(lh, b, 10)
    assert _upload(lh, _attempt("s6", b, 2, 10, "PRE", 11))[0]["detail"] == "pre-test must be taken before reading"


def test_next_module_is_locked_until_the_previous_one_is_completed(world):
    m, h = world["m"], world["h"]
    lh = h[LearnerRole.LOGISTICIAN]
    assert _state(lh, m["B"])["status"] == "LOCKED"
    assert _upload(lh, _attempt("k1", m["B"], 2, 10, "PRE", 1))[0]["detail"] == "module is locked: complete the previous module first"
    res = _read(lh, m["B"], 2, completed=True)
    assert res["detail"] == "not completed: module is locked: complete the previous module first"
    _complete_through_tests(lh, m["A"], start=3)
    assert _state(lh, m["B"])["status"] == "PRE_TEST"
    assert _upload(lh, _attempt("k2", m["B"], 2, 10, "PRE", 10))[0]["detail"] is None


@pytest.mark.parametrize("pre,post,completes", [
    ((5, 10), (9, 10), True),     # exactly 90%
    ((5, 10), (8, 10), False),    # below 90%
    ((9, 10), (9, 10), False),    # 90% but not higher than the pre-test
    ((9, 10), (19, 20), True),    # higher, with a different number of questions
])
def test_ninety_percent_and_strictly_higher_than_the_pre_test(world, pre, post, completes):
    m, lh = world["m"], world["h"][LearnerRole.OTHER]
    a = m["A"]
    _upload(lh, _attempt("p1", a, *pre, "PRE", 1))
    _read(lh, a, 2)
    res = _upload(lh, _attempt("p2", a, *post, "POST", 3))[0]
    assert (res["detail"] == "completed") is completes
    assert _state(lh, a)["completed"] is completes
    assert _state(lh, m["B"])["unlocked"] is completes


def test_failed_post_tests_can_be_retried_but_a_new_pre_test_cannot_lower_the_bar(world):
    m, lh = world["m"], world["h"][LearnerRole.MONITOR_SUPERVISOR]
    a = m["A"]
    _upload(lh, _attempt("r1", a, 9, 10, "PRE", 1))
    _read(lh, a, 2)
    assert _upload(lh, _attempt("r2", a, 9, 10, "POST", 3))[0]["detail"] is None  # equal: not completed
    res = _upload(lh, _attempt("r3", a, 1, 10, "PRE", 4))[0]  # trying to lower the baseline
    assert res["status"] == "ok" and res["detail"] == "pre-test already taken"
    assert _upload(lh, _attempt("r4", a, 9, 10, "POST", 5))[0]["detail"] is None
    st = _state(lh, a)
    assert st["pre_test"]["client_id"] == "r1" and st["post_test_attempts"] == 2 and st["status"] == "POST_TEST"
    assert _upload(lh, _attempt("r5", a, 10, 10, "POST", 6))[0]["detail"] == "completed"


def test_perfect_pre_test_needs_an_approved_exception(world):
    m, h, db = world["m"], world["h"], world["db"]
    learner = world["learners"][LearnerRole.CDD]
    lh = h[LearnerRole.CDD]
    a = m["A"]
    _upload(lh, _attempt("e1", a, 10, 10, "PRE", 1))
    _read(lh, a, 2)
    assert _state(lh, a)["status"] == "EXCEPTION"
    assert _upload(lh, _attempt("e2", a, 10, 10, "POST", 3))[0]["detail"] is None  # cannot be higher
    waiting = client.get("/learning/review", headers=h[RoleName.CONTENT_ADMIN]).json()["exceptions_waiting"]
    assert any(w["user_id"] == str(learner.id) and w["module_id"] == str(a.id) for w in waiting)

    body = {"user_id": str(learner.id), "module_id": str(a.id), "reason": "Scored 100% on the pre-test; supervisor confirmed."}
    assert client.post("/learning/exceptions", headers=lh, json=body).status_code == 403
    assert client.post("/learning/exceptions", headers=h[RoleName.TECHNICAL_REVIEWER], json=body).status_code == 403
    other = world["learners"][LearnerRole.OTHER]
    r = client.post("/learning/exceptions", headers=h[RoleName.CONTENT_ADMIN], json={**body, "user_id": str(other.id)})
    assert r.status_code == 409  # no 100% pre-test
    r = client.post("/learning/exceptions", headers=h[RoleName.PROGRAM_REVIEWER], json=body)
    assert r.status_code == 201 and r.json() == {"approved": True, "module_completed": True}  # the 100% post-test now counts
    assert client.post("/learning/exceptions", headers=h[RoleName.CONTENT_ADMIN], json=body).status_code == 409
    st = _state(lh, a)
    assert st["completed"] is True and st["exception_approved"] is True
    assert db.query(AuditLog).filter_by(entity_id=learner.id, action=AuditAction.TEST_EXCEPTION_APPROVE).count() == 1
    # A training restart replaces the exception along with the attempts.
    assert client.post(f"/users/{learner.id}/reset-training", headers=h[RoleName.SUPER_ADMIN]).status_code == 200
    db.expire_all()
    assert db.query(TestException).filter_by(user_id=learner.id).count() == 0


def test_offline_batch_in_any_order_and_duplicates_are_idempotent(world):
    m, lh, db = world["m"], world["h"][LearnerRole.HEALTH_WORKER], world["db"]
    learner = world["learners"][LearnerRole.HEALTH_WORKER]
    a = m["A"]
    # The phone was offline: it uploads reading first, then both tests (listed post first).
    _read(lh, a, 2)
    batch = [_attempt("o-post", a, 10, 10, "POST", 3), _attempt("o-pre", a, 3, 10, "PRE", 1)]
    first = _upload(lh, *batch)
    assert {x["key"]: x["detail"] for x in first} == {"o-pre": None, "o-post": "completed"}
    again = _upload(lh, *batch)
    assert [x["status"] for x in again] == ["duplicate", "duplicate"]
    assert db.query(QuizAttempt).filter_by(user_id=learner.id, module_id=a.id).count() == 2
    assert _read(lh, a, 4, completed=True)["status"] == "ok"  # the phone's own "completed" is accepted now
    assert _state(lh, a)["completed"] is True


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

    # Questions can be tagged for the pre-test, the post-test or both.
    q = {"question_type": "TRUE_FALSE", "prompt": "Pre only?", "content": {"correct": True}, "usage": "PRE"}
    r = client.post(f"/quiz/modules/{a.id}/questions", headers=ch, json=q)
    assert r.status_code == 201 and r.json()["usage"] == "PRE"
    s = client.get(f"/quiz/modules/{a.id}/summary", headers=ch).json()
    assert (s["questions"], s["pre_test_questions"], s["post_test_questions"]) == (2, 2, 1)
    assert client.patch(f"/quiz/questions/{r.json()['id']}", headers=ch, json={"usage": "POST"}).json()["usage"] == "POST"
    phone = [x for x in client.get("/sync/quiz-questions", headers=h[LearnerRole.CDD]).json() if x["module_id"] == str(a.id)]
    assert sorted(x["usage"] for x in phone) == ["BOTH", "POST"]


def test_report_shows_pre_and_post_tests_separately(world):
    m, h = world["m"], world["h"]
    lh = h[LearnerRole.LOGISTICIAN]
    a = m["A"]
    _upload(lh, _attempt("t1", a, 4, 10, "PRE", 1))
    _read(lh, a, 2)
    _upload(lh, _attempt("t2", a, 7, 10, "POST", 3), _attempt("t3", a, 9, 10, "POST", 4))
    rows = client.get("/learning/report?learner_role=LOGISTICIAN", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    row = next(r for r in rows if r["module_code"] == a.module_code and r["username"] == world["learners"][LearnerRole.LOGISTICIAN].username)
    assert row["pre_test_score"] == 40 and row["post_test_attempts"] == 2
    assert row["post_test_best_score"] == 90 and row["post_test_latest_score"] == 90
    assert row["met_both_rules"] is True and row["status"] == "COMPLETED" and row["learner_role"] == "LOGISTICIAN"
    csv = client.get("/learning/report.csv?learner_role=LOGISTICIAN", headers=h[RoleName.PROGRAM_REVIEWER])
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    assert "pre_test_score" in csv.text.splitlines()[0] and "post_test_best_score" in csv.text.splitlines()[0]
    assert client.get("/learning/report", headers=lh).status_code == 403
    detail = client.get(f"/learning/attempts/{world['learners'][LearnerRole.LOGISTICIAN].id}", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    assert [(d["test_type"], d["score_percent"]) for d in detail if d["module_code"] == a.module_code] == [("PRE", 40), ("POST", 70), ("POST", 90)]
    users = client.get("/reports/users?learner_role=LOGISTICIAN", headers=h[RoleName.PROGRAM_REVIEWER]).json()
    assert users and all(u["learner_role"] == "LOGISTICIAN" for u in users)
