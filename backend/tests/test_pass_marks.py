"""Item 3: General pre/post-test pass marks per audience (CDD 60%, every other role
80%) in whole numbers, stored with each attempt (a later change never alters old
results), never blocking at the pre-test, the certificate rule, who may change the
marks, the report columns, and module quizzes left exactly as they were."""
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.learning.certificate import certificate_number, certifies, find_certificate
from app.learning.rules import general_passes, module_quiz_passes
from app.learning.settings import DEFAULTS, TrainingSettings
from app.main import app
from app.models import AuditLog, GeneralTestAttempt, PlatformSetting, User
from app.models.enums import AuditAction, LearnerRole, RoleName
from tests.test_general_test import _general, _learning, general  # noqa: F401  (fixture)
from tests.test_hfw_migration import sandbox  # noqa: F401
from tests.test_learning import at, db, world  # noqa: F401  (fixtures)

client = TestClient(app)


@pytest.fixture()
def clean_marks():
    yield
    s = SessionLocal()
    s.query(PlatformSetting).filter(PlatformSetting.key.in_(["general_pass_mark_cdd", "general_pass_mark_other"])).delete(
        synchronize_session=False)
    s.commit()
    s.close()


def _mixed(qs, right):
    """The first `right` questions correct, the rest wrong."""
    return [{"question_id": str(q.id), "choice": q.correct_index if i < right else (q.correct_index + 1) % 4}
            for i, q in enumerate(qs)]


def test_whole_number_pass_marks_on_25_questions():
    assert DEFAULTS["general_pass_mark_cdd"] == 60 and DEFAULTS["general_pass_mark_other"] == 80
    assert general_passes(15, 25, 60) and not general_passes(14, 25, 60)
    assert general_passes(20, 25, 80) and not general_passes(19, 25, 80)
    # Exact at the edge (floating point would get some of these wrong).
    assert general_passes(7, 10, 70) and general_passes(3, 5, 60) and not general_passes(57, 100, 58)
    assert not general_passes(0, 0, 60)


def test_the_mark_follows_the_learner_role():
    s = TrainingSettings(module_min_seconds=180, general_test_active=True)
    marks = {role: s.pass_mark_for(User(learner_role=role)) for role in LearnerRole}
    assert marks == {LearnerRole.CDD: 60, LearnerRole.HEALTH_WORKER: 80, LearnerRole.LOGISTICIAN: 80,
                     LearnerRole.MONITOR_SUPERVISOR: 80, LearnerRole.OTHER: 80}
    assert s.pass_mark_for(User(role=RoleName.SUPER_ADMIN, learner_role=None)) == 80


def test_attempts_store_their_mark_and_a_low_pre_test_never_blocks(world, general, clean_marks):  # noqa: F811
    cdd, hw = world["h"][LearnerRole.CDD], world["h"][LearnerRole.HEALTH_WORKER]
    # 2 of 3 = 66.7%: passes the CDD mark (60), not the HFW/Others mark (80).
    assert _general(cdd, "pm-cdd-pre", "PRE", 1, _mixed(general, 2))["detail"] == "score 2/3"
    assert _general(hw, "pm-hw-pre", "PRE", 1, _mixed(general, 2))["detail"] == "score 2/3"
    cdd_state, hw_state = _learning(cdd)["general_test"], _learning(hw)["general_test"]
    assert (cdd_state["pass_mark"], cdd_state["pre_test"]["pass_mark"], cdd_state["pre_test"]["passed"]) == (60, 60, True)
    assert (hw_state["pass_mark"], hw_state["pre_test"]["pass_mark"], hw_state["pre_test"]["passed"]) == (80, 80, False)
    # Below the mark at the pre-test: the modules open all the same (only taking it counts).
    assert _learning(hw)["modules"][0]["unlocked"] is True

    # Changing the setting never changes a stored result.
    admin, content = world["h"][RoleName.SUPER_ADMIN], world["h"][RoleName.CONTENT_ADMIN]
    assert client.put("/general-test/settings", headers=content, json={"general_pass_mark_other": 60}).status_code == 403
    r = client.put("/general-test/settings", headers=admin, json={"general_pass_mark_other": 60})
    assert r.status_code == 200 and r.json()["general_pass_mark_other"] == 60
    assert client.put("/general-test/settings", headers=admin, json={"general_pass_mark_cdd": 101}).status_code == 422
    hw_state = _learning(hw)["general_test"]
    assert hw_state["pass_mark"] == 60, "new attempts would use the new mark"
    assert (hw_state["pre_test"]["pass_mark"], hw_state["pre_test"]["passed"]) == (80, False), "the old attempt keeps its mark"
    s = SessionLocal()
    log = s.query(AuditLog).filter_by(action=AuditAction.SETTING_CHANGE, user_id=world["staff"][RoleName.SUPER_ADMIN].id).all()
    assert any(l.details["key"] == "general_pass_mark_other" and l.details["after"] == 60 for l in log)
    s.close()


def test_report_columns(world, general, clean_marks):  # noqa: F811
    h, admin = world["h"][LearnerRole.CDD], world["h"][RoleName.SUPER_ADMIN]
    me = world["learners"][LearnerRole.CDD]
    _general(h, "pm-rep-pre", "PRE", 1, _mixed(general, 1))
    s = SessionLocal()
    s.add(GeneralTestAttempt(user_id=me.id, client_id="pm-rep-post", test_type="POST", correct_count=3, total_count=3,
                             score_percent=100, answers=[], valid=True, pass_mark=60, taken_at=at(50)))
    s.commit()
    s.close()
    row = next(r for r in client.get("/reports/users", headers=admin, params={"q.username": me.username}).json())
    assert (row["general_pre_points"], row["general_pre_pass_mark"], row["general_pre_passed"]) == (1, 60, "NOT_PASSED")
    assert (row["general_post_points"], row["general_post_pass_mark"], row["general_post_passed"]) == (3, 60, "PASSED")
    assert (row["general_change_points"], row["general_change_percent"]) == (2, 67)
    filtered = client.get("/reports/users", headers=admin,
                          params={"q.username": me.username, "in.general_post_passed": "PASSED", "min.general_change_percent": "50"}).json()
    assert len(filtered) == 1
    assert client.get("/reports/users", headers=admin, params={"q.username": me.username, "in.general_pre_passed": "PASSED"}).json() == []


def test_certificate_follows_the_stored_mark_and_old_attempts_keep_90(world, general):  # noqa: F811
    me = world["learners"][LearnerRole.CDD]
    new = GeneralTestAttempt(user_id=me.id, client_id="pm-cert-new", test_type="POST", correct_count=15, total_count=25,
                             score_percent=60, answers=[], valid=True, pass_mark=60, taken_at=at(60))
    old = GeneralTestAttempt(user_id=me.id, client_id="pm-cert-old", test_type="POST", correct_count=20, total_count=25,
                             score_percent=80, answers=[], valid=True, pass_mark=None, taken_at=at(61))
    assert certifies(new) and not certifies(old), "old attempts without a stored mark keep the 90% rule"
    assert not certifies(GeneralTestAttempt(correct_count=19, total_count=25, pass_mark=80))
    s = SessionLocal()
    s.add_all([new, old])
    s.commit()
    assert find_certificate(s, certificate_number(me.id, "pm-cert-new", new.taken_at))["valid"] is True
    assert find_certificate(s, certificate_number(me.id, "pm-cert-old", old.taken_at)) is None
    s.close()


def test_module_quizzes_are_unchanged():
    # Still 90%, exact: 3 statements need 3 right.
    assert module_quiz_passes(3, 3) and not module_quiz_passes(2, 3)
    assert module_quiz_passes(9, 10) and not module_quiz_passes(8, 10)
