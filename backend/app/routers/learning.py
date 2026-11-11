"""
Administration of role-based content and learning results:

  GET  /learning/review              what needs an administrator: modules whose
                                     audience is unconfirmed and accounts whose
                                     learner role is unknown
  GET  /learning/report[.csv]        per learner and module: status, inline module quiz,
                                     active time, and the retired per-module pre/post
                                     test results kept as history (same filters as /reports)
  GET  /learning/general-report[.csv]  per learner: General pre-test and post-test scores
                                     (points and percent) and the change
Rows say which curriculum they belong to (CDD or HFW), so the two can be reported apart.
"""
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.learning.access import module_visible_to
from app.learning.rules import auto_approve_percent
from app.learning.settings import training_settings
from app.learning.state import build_states, first_valid, quiz_statement_counts
from app.models import GeneralTestAttempt, Module, QuizAttempt, User, UserModuleProgress
from app.models.enums import LEARNER_ROLE_LABELS, LearnerRole, ModuleStatus, RoleName, TestType
from app.quiz.grading import PASS_MARK
from app.reports.activity import LEVELS, Filters
from app.reports.params import report_filters
from app.routers.reports import csv_response

router = APIRouter()
VIEWERS = tuple(r for r in RoleName if r != RoleName.CDD)


def _learners(db: Session, f: Filters) -> list[User]:
    q = db.query(User).filter(User.role == RoleName.CDD)
    for level in LEVELS:
        v = getattr(f, f"{level}_id")
        if v:
            q = q.filter(getattr(User, f"{level}_id") == v)
    if f.session_id:
        q = q.filter(User.training_session_id == f.session_id)
    if f.learner_role:
        q = q.filter(User.learner_role == f.learner_role)
    if f.team_code:
        q = q.filter(User.team_code == f.team_code)
    return q.order_by(User.last_name, User.first_name).all()


def curriculum_of(module_code: str) -> str:
    return "CDD" if module_code.startswith("CDD-") else "HFW"


def learner_group(u: User) -> str:
    return "CDD" if u.learner_role == LearnerRole.CDD else "HFW & others"


def _states_by_user(db: Session, users: list[User]):
    """(user, [ModuleState], quiz attempts by (user, module), General attempts) for each
    learner, loaded in a handful of queries."""
    modules = (
        db.query(Module).filter(Module.status == ModuleStatus.PUBLISHED)
        .order_by(Module.sort_order, Module.module_number, Module.module_code).all()
    )
    ids = [u.id for u in users]
    counts = quiz_statement_counts(db)
    settings = training_settings(db)
    progress, quiz, all_attempts, general = defaultdict(dict), defaultdict(list), defaultdict(list), defaultdict(list)
    if ids:
        for p in db.query(UserModuleProgress).filter(UserModuleProgress.user_id.in_(ids)):
            progress[p.user_id][p.module_id] = p
        for a in db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(ids)):
            all_attempts[(a.user_id, a.module_id)].append(a)
            if a.valid and a.test_type == TestType.MODULE_QUIZ:
                quiz[a.user_id].append(a)
        for g in db.query(GeneralTestAttempt).filter(GeneralTestAttempt.user_id.in_(ids)):
            general[g.user_id].append(g)
    for u in users:
        mine = [m for m in modules if module_visible_to(m, u)]
        gate_open = not settings.general_test_active or first_valid(general[u.id], TestType.PRE) is not None
        states = build_states(mine, counts, progress[u.id], quiz[u.id], settings.module_min_seconds, gate_open)
        yield u, states, all_attempts, general[u.id]


def _person(u: User) -> dict:
    return {
        "user_id": str(u.id),
        "username": u.username,
        "full_name": f"{u.first_name} {u.last_name}",
        "learner_role": u.learner_role.value if u.learner_role else None,
        "team_code": u.team_code,
        "state": u.state_name,
        "lga": u.lga_name,
        "session": u.session_name,
    }


@router.get("/review")
def review(db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    modules = db.query(Module).order_by(Module.sort_order, Module.module_number).all()
    flagged_users = (
        db.query(User)
        .filter(User.learner_role_needs_review.is_(True) | ((User.role == RoleName.CDD) & User.learner_role.is_(None)))
        .order_by(User.last_name, User.first_name)
        .limit(500)
        .all()
    )
    settings = training_settings(db)
    return {
        "auto_approve_percent": auto_approve_percent(),
        "module_min_seconds": settings.module_min_seconds,
        "general_test_active": settings.general_test_active,
        "learner_roles": [{"value": r.value, "label": label} for r, label in LEARNER_ROLE_LABELS.items()],
        "modules": [
            {
                "id": str(m.id), "module_code": m.module_code, "title": m.title, "status": m.status.value,
                "audience": m.audience.value, "learner_roles": m.learner_roles or [],
                "needs_review": m.audience_needs_review,
            }
            for m in modules
        ],
        "users_needing_review": [
            {**_person(u), "role": u.role.value, "email": u.email,
             "reason": "learner account without a learner role" if u.role == RoleName.CDD and u.learner_role is None
             else "existing account: confirm whether this person is a learner and which role"}
            for u in flagged_users
        ],
    }


def _legacy(attempts: list[QuizAttempt]) -> dict:
    """The retired per-module pre/post tests, kept in the report as history."""
    pres = sorted((a for a in attempts if a.valid and a.test_type == TestType.PRE), key=lambda a: a.taken_at)
    posts = sorted((a for a in attempts if a.valid and a.test_type == TestType.POST), key=lambda a: a.taken_at)
    pre = pres[-1] if pres else None
    best = max(posts, key=lambda a: (a.correct_count / a.total_count, a.taken_at), default=None)
    latest = posts[-1] if posts else None
    return {
        "pre_test_score": pre.score_percent if pre else None,
        "pre_test_correct": f"{pre.correct_count}/{pre.total_count}" if pre else None,
        "pre_test_taken_at": pre.taken_at.isoformat() if pre else None,
        "post_test_attempts": len(posts),
        "post_test_best_score": best.score_percent if best else None,
        "post_test_latest_score": latest.score_percent if latest else None,
        "post_test_latest_at": latest.taken_at.isoformat() if latest else None,
    }


def _report_rows(db: Session, f: Filters) -> list[dict]:
    rows = []
    for u, states, attempts, _ in _states_by_user(db, _learners(db, f)):
        for st in states:
            mine = attempts[(u.id, st.module.id)]
            quiz = sorted((a for a in mine if a.test_type == TestType.MODULE_QUIZ), key=lambda a: a.taken_at)
            passing = st.passing_quiz()
            rows.append({
                **_person(u),
                "learner_group": learner_group(u),
                "curriculum": curriculum_of(st.module.module_code),
                "module_code": st.module.module_code,
                "module_title": st.module.title,
                "status": st.status,
                "quiz_statements": st.quiz_statements,
                "quiz_attempts": len(quiz),
                "quiz_passed": st.has_quiz and passing is not None,
                "quiz_passed_at": passing.taken_at.isoformat() if passing else None,
                "quiz_latest_score": quiz[-1].score_percent if quiz else None,
                "seconds_spent": st.seconds_spent,
                "min_seconds": st.min_seconds,
                "pass_mark": PASS_MARK,
                **_legacy(mine),
                # kept for older CSV readers: the per-module tests no longer decide completion
                "met_both_rules": False,
                "auto_approved": False,
                "attempts_not_counted": sum(1 for a in mine if not a.valid),
                "completed_at": st.progress.completed_at.isoformat() if st.completed and st.progress.completed_at else None,
            })
    return rows


def _general_rows(db: Session, f: Filters) -> list[dict]:
    rows = []
    for u, states, _, general in _states_by_user(db, _learners(db, f)):
        pre, post = first_valid(general, TestType.PRE), first_valid(general, TestType.POST)
        rows.append({
            **_person(u),
            "learner_group": learner_group(u),
            "modules_total": len(states),
            "modules_completed": sum(1 for s in states if s.completed),
            "seconds_spent_total": sum(s.seconds_spent for s in states),
            "pre_test_points": pre.correct_count if pre else None,
            "pre_test_total": pre.total_count if pre else None,
            "pre_test_percent": pre.score_percent if pre else None,
            "pre_test_taken_at": pre.taken_at.isoformat() if pre else None,
            "post_test_points": post.correct_count if post else None,
            "post_test_total": post.total_count if post else None,
            "post_test_percent": post.score_percent if post else None,
            "post_test_taken_at": post.taken_at.isoformat() if post else None,
            "change_points": post.correct_count - pre.correct_count if pre and post else None,
            "change_percent": post.score_percent - pre.score_percent if pre and post else None,
            "attempts_not_counted": sum(1 for g in general if not g.valid),
        })
    return rows


@router.get("/report")
def test_report(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return _report_rows(db, f)


@router.get("/report.csv")
def test_report_csv(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(_report_rows(db, f), "module_learning")


@router.get("/general-report")
def general_report(f: Filters = Depends(report_filters), db: Session = Depends(get_db),
                   user: User = Depends(require_roles(*VIEWERS))):
    return _general_rows(db, f)


@router.get("/general-report.csv")
def general_report_csv(f: Filters = Depends(report_filters), db: Session = Depends(get_db),
                       user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(_general_rows(db, f), "general_test")


@router.get("/attempts/{user_id}")
def learner_attempts(user_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    """Every attempt one learner made (module quizzes, the retired per-module tests and the
    General tests; counted or not), for the admin's detail view."""
    rows = (
        db.query(QuizAttempt, Module.module_code)
        .join(Module, Module.id == QuizAttempt.module_id)
        .filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.taken_at)
        .all()
    )
    return [
        {"module_code": code, "test_type": a.test_type.value, "score_percent": a.score_percent,
         "correct": a.correct_count, "total": a.total_count, "valid": a.valid, "invalid_reason": a.invalid_reason,
         "taken_at": a.taken_at.isoformat()}
        for a, code in rows
    ] + [
        {"module_code": "GENERAL", "test_type": g.test_type.value, "score_percent": g.score_percent,
         "correct": g.correct_count, "total": g.total_count, "valid": g.valid, "invalid_reason": g.invalid_reason,
         "taken_at": g.taken_at.isoformat()}
        for g in db.query(GeneralTestAttempt).filter_by(user_id=user_id).order_by(GeneralTestAttempt.taken_at)
    ]

