"""
Administration of role-based content and pre-/post-tests:

  GET  /learning/review            what needs an administrator: modules whose
                                   audience is unconfirmed, accounts whose learner
                                   role is unknown, learners waiting for a
                                   100%-pre-test exception
  GET  /learning/exceptions        approved exceptions
  POST /learning/exceptions        approve one (audited); a post-test already
                                   at 90% or more then completes the module
  GET  /learning/report[.csv]      pre-test and post-test results per learner and
                                   module, kept apart (same filters as /reports)
"""
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.learning.access import module_visible_to
from app.learning.state import all_test_question_counts, build_states, complete, module_state
from app.models import AuditLog, Module, QuizAttempt, TestException, User, UserModuleProgress
from app.models.enums import LEARNER_ROLE_LABELS, AuditAction, ModuleStatus, RoleName
from app.quiz.grading import PASS_MARK
from app.reports.activity import LEVELS, Filters
from app.reports.params import report_filters
from app.routers.reports import csv_response

router = APIRouter()
VIEWERS = tuple(r for r in RoleName if r != RoleName.CDD)
APPROVERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER)  # + SUPER_ADMIN (always)


class ExceptionCreate(BaseModel):
    user_id: uuid.UUID
    module_id: uuid.UUID
    reason: str = Field(min_length=5, max_length=1000)


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


def _states_by_user(db: Session, users: list[User]):
    """(user, [ModuleState]) for each learner, loaded in a handful of queries."""
    modules = (
        db.query(Module).filter(Module.status == ModuleStatus.PUBLISHED)
        .order_by(Module.sort_order, Module.module_number, Module.module_code).all()
    )
    ids = [u.id for u in users]
    counts = all_test_question_counts(db)
    progress, attempts, exceptions, invalid = defaultdict(dict), defaultdict(list), defaultdict(dict), defaultdict(int)
    if ids:
        for p in db.query(UserModuleProgress).filter(UserModuleProgress.user_id.in_(ids)):
            progress[p.user_id][p.module_id] = p
        for a in db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(ids)):
            if a.valid:
                attempts[a.user_id].append(a)
            else:
                invalid[(a.user_id, a.module_id)] += 1
        for e in db.query(TestException).filter(TestException.user_id.in_(ids)):
            exceptions[e.user_id][e.module_id] = e
    for u in users:
        mine = [m for m in modules if module_visible_to(m, u)]
        yield u, build_states(mine, counts, progress[u.id], attempts[u.id], exceptions[u.id]), invalid


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
    waiting = []
    for u, states, _ in _states_by_user(db, db.query(User).filter(User.role == RoleName.CDD).all()):
        for st in states:
            if st.status == "EXCEPTION":
                waiting.append({
                    **_person(u),
                    "module_id": str(st.module.id), "module_code": st.module.module_code, "module_title": st.module.title,
                    "pre_test_score": st.pre.score_percent, "pre_test_taken_at": st.pre.taken_at.isoformat(),
                })
    return {
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
        "exceptions_waiting": waiting,
    }


@router.get("/exceptions")
def list_exceptions(db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    rows = (
        db.query(TestException, User, Module)
        .join(User, User.id == TestException.user_id)
        .join(Module, Module.id == TestException.module_id)
        .order_by(TestException.approved_at.desc())
        .limit(500)
        .all()
    )
    approvers = {u.id: u.username for u in db.query(User).filter(User.id.in_({e.approved_by for e, _, _ in rows}))} if rows else {}
    return [
        {**_person(u), "module_code": m.module_code, "module_title": m.title, "reason": e.reason,
         "approved_by": approvers.get(e.approved_by), "approved_at": e.approved_at.isoformat() if e.approved_at else None}
        for e, u, m in rows
    ]


@router.post("/exceptions", status_code=status.HTTP_201_CREATED)
def approve_exception(payload: ExceptionCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles(*APPROVERS))):
    """Only for a learner whose valid pre-test scored 100%: the post-test then
    needs 90% or more (the 90% rule is never waived)."""
    learner = db.get(User, payload.user_id)
    if learner is None or learner.role != RoleName.CDD:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learner not found")
    st = module_state(db, learner, payload.module_id)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found or not available to this learner")
    if not st.pre_perfect:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An exception is only for a learner whose pre-test scored 100%.")
    if st.exception is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already approved")
    db.add(TestException(user_id=learner.id, module_id=st.module.id, reason=payload.reason.strip(), approved_by=actor.id))
    db.flush()
    db.add(AuditLog(
        user_id=actor.id, action=AuditAction.TEST_EXCEPTION_APPROVE, entity_type="user", entity_id=learner.id,
        details={"module_code": st.module.module_code, "pre_test_score": st.pre.score_percent},
    ))
    completed = False
    st = module_state(db, learner, st.module.id)
    if st and not st.completed and st.unlocked and st.completing_post() is not None:
        complete(db, learner, st.module.id, when=st.completing_post().taken_at)
        completed = True
    db.commit()
    return {"approved": True, "module_completed": completed}


def _report_rows(db: Session, f: Filters) -> list[dict]:
    rows = []
    for u, states, invalid in _states_by_user(db, _learners(db, f)):
        for st in states:
            if not st.has_tests:
                continue
            posts = sorted(st.posts, key=lambda a: a.taken_at)
            best = max(posts, key=lambda a: (a.correct_count / a.total_count, a.taken_at), default=None)
            latest = posts[-1] if posts else None
            qualifying = st.completing_post()
            rows.append({
                **_person(u),
                "module_code": st.module.module_code,
                "module_title": st.module.title,
                "status": st.status,
                "pre_test_score": st.pre.score_percent if st.pre else None,
                "pre_test_correct": f"{st.pre.correct_count}/{st.pre.total_count}" if st.pre else None,
                "pre_test_taken_at": st.pre.taken_at.isoformat() if st.pre else None,
                "post_test_attempts": len(posts),
                "post_test_best_score": best.score_percent if best else None,
                "post_test_latest_score": latest.score_percent if latest else None,
                "post_test_latest_at": latest.taken_at.isoformat() if latest else None,
                "pass_mark": PASS_MARK,
                "met_both_rules": qualifying is not None,
                "exception_approved": st.exception is not None,
                "attempts_not_counted": invalid[(u.id, st.module.id)],
                "completed_at": st.progress.completed_at.isoformat() if st.completed and st.progress.completed_at else None,
            })
    return rows


@router.get("/report")
def test_report(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return _report_rows(db, f)


@router.get("/report.csv")
def test_report_csv(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(_report_rows(db, f), "pre_post_tests")


@router.get("/attempts/{user_id}")
def learner_attempts(user_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    """Every attempt one learner made (pre and post, counted or not), for the admin's detail view."""
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
    ]

