"""The old curriculum's records after the changeover, kept apart.

Modules archived at the changeover (M1-M6) drop out of every current report,
which measure PUBLISHED modules only, so old completions never mix with the
new completion rates. This report shows those archived modules' progress and
test results per learner, each row labelled LEGACY_LABEL, for the admin portal
and CSV export. Read-only: nothing here changes a record.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Module, QuizAttempt, User, UserModuleProgress
from app.models.enums import ModuleStatus, RoleName, TestType
from app.reports.activity import LEVELS, Filters

LEGACY_LABEL = "Legacy (M1-M6)"


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


def legacy_rows(db: Session, f: Filters) -> list[dict]:
    """One row per learner and archived module the learner touched."""
    mods = db.query(Module).filter(Module.status == ModuleStatus.ARCHIVED).order_by(Module.sort_order, Module.module_code).all()
    users = _learners(db, f)
    if not mods or not users:
        return []
    mod_ids = [m.id for m in mods]
    uids = [u.id for u in users]
    progress = {(p.user_id, p.module_id): p for p in db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id.in_(uids), UserModuleProgress.module_id.in_(mod_ids))}
    attempts = defaultdict(list)
    for a in db.query(QuizAttempt).filter(QuizAttempt.user_id.in_(uids), QuizAttempt.module_id.in_(mod_ids)):
        attempts[(a.user_id, a.module_id)].append(a)
    rows = []
    for u in users:
        for m in mods:
            p, att = progress.get((u.id, m.id)), attempts.get((u.id, m.id), [])
            if p is None and not att:
                continue
            counted = [a for a in att if a.valid]
            pre = max((a for a in counted if a.test_type == TestType.PRE), key=lambda a: a.taken_at, default=None)
            posts = [a for a in counted if a.test_type == TestType.POST]
            best = max(posts, key=lambda a: a.score_percent, default=None)
            rows.append({
                "curriculum": LEGACY_LABEL,
                "user_id": str(u.id),
                "username": u.username,
                "full_name": f"{u.first_name} {u.last_name}",
                "learner_role": u.learner_role.value if u.learner_role else None,
                "team_code": u.team_code,
                "state": u.state_name,
                "lga": u.lga_name,
                "module_code": m.module_code,
                "module_title": m.title,
                "progress_percent": p.progress_percent if p else 0,
                "completed": bool(p and p.completed),
                "completed_at": p.completed_at.isoformat() if p and p.completed_at else None,
                "pre_test_score": pre.score_percent if pre else None,
                "post_test_attempts": len(posts),
                "post_test_best_score": best.score_percent if best else None,
                "attempts_not_counted": len(att) - len(counted),
                "last_opened_at": p.last_opened_at.isoformat() if p and p.last_opened_at else None,
            })
    return rows
