"""
Repairs learners stuck by the upload-order bug (app/learning/revalidate.py): a module
whose quiz was passed and whose minimum time was met on the phone, but which the
server never marked complete because the passing attempt (or the completion) reached
it before the previous module's completion.

For every learner, module by module in learning order, a module is repaired when ALL hold:
  - it is open now (the General pre-test gate and every earlier module are completed,
    counting modules repaired earlier in this run) and not completed;
  - it HAS a quiz, and a passing module-quiz attempt that counts, or one refused only
    for the order reasons, taken after the module opened (revalidate.py). Modules
    without a quiz are never touched: the bug cannot affect them, and a learner who
    simply has not pressed "Complete" yet must press it themselves;
  - its active time on the server meets the minimum (3 minutes by default);
  - the account is still active.
Repair = those attempts count again (their original refusal goes into the audit log)
and the module is completed at the time of the passing attempt. A General post-test
refused only because it arrived before the last completion counts again too. Nothing
is deleted; no quiz, time or order rule is relaxed.

    cd backend && python -m scripts.repair_stuck_completions            # dry run (default): prints what it would change
    cd backend && python -m scripts.repair_stuck_completions --apply    # changes it (ENVIRONMENT=production also needs --allow-production)

--only-refused narrows it to modules the phone already tried to complete: the server
stores a refused completion as 99% progress (sync.py), so only those are repaired;
learners who passed but have not pressed "Complete" yet are left to press it.
"""
import argparse
import sys
from datetime import timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.learning.access import is_learner
from app.learning.revalidate import revalidate
from app.learning.state import complete, learning_overview
from app.models import AuditLog, User
from app.models.enums import AuditAction, UserStatus


REFUSED_PERCENT = 99  # what the server stores for a completion it refused


def plan_user(db: Session, user: User, only_refused: bool = False) -> list[dict]:
    """Repairs one learner inside the caller's transaction; returns what changed."""
    changes = []
    for _ in range(200):  # each round completes at most one module (it may open the next)
        fixed = revalidate(db, user)
        states, _general = learning_overview(db, user)
        target = next((s for s in states if s.unlocked and not s.completed), None)
        passing = target.passing_quiz() if target is not None and target.has_quiz else None
        tried = target is not None and target.progress is not None and target.progress.progress_percent >= REFUSED_PERCENT
        if passing is None or not target.time_met or (only_refused and not tried):
            # (A post-test or an attempt that counts again is still reported.)
            changes += [dict(c, action="attempt counts again") for c in fixed]
            break
        when = passing.taken_at
        if when is not None and when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        complete(db, user, target.module.id, when)
        changes += [dict(c, action="attempt counts again") for c in fixed]
        changes.append({"kind": "completion", "module_id": str(target.module.id), "module": target.module.module_code,
                        "seconds": target.seconds_spent, "min_seconds": target.min_seconds,
                        "quiz": f"{passing.correct_count}/{passing.total_count}",
                        "completed_at": when.isoformat() if when else None, "action": "module completed"})
    return changes


def run(apply: bool, db: Session | None = None, only_refused: bool = False) -> list[tuple[dict, list[dict]]]:
    """[(learner, changes)] for every learner with something to repair; learner =
    {id, username, name, learner_role} (plain values, usable after the session closes)."""
    own = db is None
    db = db or SessionLocal()
    out = []
    try:
        users = db.query(User).filter(User.status == UserStatus.ACTIVE).order_by(User.username).all()
        for user in users:
            if not is_learner(user):
                continue
            who = {"id": user.id, "username": user.username, "name": f"{user.first_name} {user.last_name}",
                   "learner_role": user.learner_role.value if user.learner_role else "no role"}
            changes = plan_user(db, user, only_refused)
            if changes:
                out.append((who, changes))
                if apply:
                    db.add(AuditLog(user_id=None, action=AuditAction.USER_UPDATE, entity_type="user", entity_id=user.id,
                                    details={"repair": "stuck completions (upload order)", "changes": changes}))
        if apply:
            db.commit()
        else:
            db.rollback()
    finally:
        if own:
            db.close()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="make the changes (default: dry run)")
    ap.add_argument("--allow-production", action="store_true")
    ap.add_argument("--only-refused", action="store_true", help="only modules whose completion the server refused (99%%)")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    env = get_settings().environment
    if env == "production" and a.apply and not a.allow_production:
        print("Refused: ENVIRONMENT=production needs --allow-production (take a pg_dump first).")
        return 2
    result = run(a.apply, only_refused=a.only_refused)
    print(f"# Stuck completions ({'APPLIED' if a.apply else 'DRY RUN, nothing changed'}, environment {env})")
    if not result:
        print("Nothing to repair: no learner has a passed quiz and met time on an open, uncompleted module,")
        print("and no attempt is waiting only because of upload order.")
    for who, changes in result:
        print(f"\n{who['username']} ({who['name']}, {who['learner_role']})")
        for c in changes:
            if c["kind"] == "completion":
                print(f"  - {c['module']}: {c['action']} at {c['completed_at']} (quiz {c['quiz']}, "
                      f"{c['seconds']}s of {c['min_seconds']}s)")
            else:
                print(f"  - {c['kind']} {c['attempt']}: {c['action']} (was: {c['was']})")
    print(f"\n{sum(1 for _u, cs in result for c in cs if c['kind'] == 'completion')} module completion(s), "
          f"{sum(1 for _u, cs in result for c in cs if c['kind'] != 'completion')} attempt(s), {len(result)} learner(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
