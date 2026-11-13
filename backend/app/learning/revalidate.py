"""Results that were refused only because of the order uploads arrived in.

A phone uploads in one sync, in order: the General pre-test, module-quiz attempts,
module progress, then (app 0.1.16+) the General post-test. Older apps upload the
post-test first. So the server can see module 2's passing quiz, or the post-test,
before the completion that unlocked it on the phone, and store it as not counting
(state.py lock reasons, sync._general_problem). The rules themselves are right; the
verdict was only premature.

This module re-checks exactly those refusals once the missing completion is on the
server: an attempt counts again when the module (or the post-test) is open now AND
the attempt was taken after it opened (the completion's time, with a small allowance
for clocks of two phones). Nothing else is ever re-checked, and no rule changes:
module order, the 90% quiz rule, the 3-minute rule and "each General test counts
once" all stay exactly as they are.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.learning.state import GATE_REASON, general_attempts, learning_overview
from app.models import GeneralTestAttempt, QuizAttempt, User
from app.models.enums import TestType

LOCKED_PREVIOUS = "module is locked: complete the previous module first"
QUIZ_ORDER_REASONS = (GATE_REASON, LOCKED_PREVIOUS)
POST_ORDER_REASON = "complete all your modules first"
CLOCK_ALLOWANCE = timedelta(minutes=5)


def _aware(t: datetime | None) -> datetime | None:
    if t is not None and t.tzinfo is None:
        return t.replace(tzinfo=timezone.utc)
    return t


def _opened_at(states, index: int, pre: GeneralTestAttempt | None) -> datetime | None:
    """When module [index] opened: the previous module's completion, or the pre-test for the first one."""
    if index > 0:
        prev = states[index - 1].progress
        return _aware(prev.completed_at) if prev else None
    return _aware(pre.taken_at) if pre else None


def revalidate(db: Session, user: User) -> list[dict]:
    """Lets order-refused attempts count when the rules now allow them (no commit).
    Returns what changed, for logs, tests and the repair script."""
    changed: list[dict] = []
    states, general = learning_overview(db, user)
    pre = general.pre
    for i, s in enumerate(states):
        if not s.unlocked or s.completed:
            continue
        opened = _opened_at(states, i, pre)
        rows = (db.query(QuizAttempt)
                .filter(QuizAttempt.user_id == user.id, QuizAttempt.module_id == s.module.id,
                        QuizAttempt.test_type == TestType.MODULE_QUIZ, QuizAttempt.valid.is_(False),
                        QuizAttempt.invalid_reason.in_(QUIZ_ORDER_REASONS))
                .all())
        for a in rows:
            if opened is None or _aware(a.taken_at) >= opened - CLOCK_ALLOWANCE:
                changed.append({"kind": "module_quiz", "module_id": str(s.module.id), "attempt": a.client_id,
                                "was": a.invalid_reason})
                a.valid, a.invalid_reason = True, None
    if general.active and general.post is None and general.all_modules_completed and pre is not None:
        last_done = max((_aware(s.progress.completed_at) for s in states if s.progress and s.progress.completed_at), default=None)
        waiting = sorted((a for a in general_attempts(db, user)
                          if a.test_type == TestType.POST and not a.valid and a.invalid_reason == POST_ORDER_REASON),
                         key=lambda a: a.taken_at)
        for a in waiting:
            if (last_done is None or _aware(a.taken_at) >= last_done - CLOCK_ALLOWANCE) and _aware(a.taken_at) >= _aware(pre.taken_at):
                changed.append({"kind": "post_test", "attempt": a.client_id, "was": a.invalid_reason})
                a.valid, a.invalid_reason = True, None
                break  # each General test counts once: the first one
    if changed:
        db.flush()
    return changed
