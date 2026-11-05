"""Where each learner is in each module, computed from stored rows.

Flow per module (modules with active quiz questions; "has_tests"):
  LOCKED       an earlier module (in the learner's own visible order) is not complete
  PRE_TEST     no valid pre-test yet: reading is blocked until it is taken
  READING      pre-test taken, reading not finished
  POST_TEST    reading finished, no post-test has met the rule yet (a 100% pre-test
               is auto-approved by a post-test at the auto-approval threshold)
  COMPLETED    completed (a module, once completed, stays completed)
Modules without questions go READING -> COMPLETED via "Mark as complete".

"Proceed" means COMPLETED, which also unlocks the next module.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.learning.access import visible_modules
from app.learning.rules import is_perfect, post_test_completes
from app.models import Module, QuizAttempt, QuizQuestion, User, UserModuleProgress
from app.models.enums import QuestionUsage, TestType

READING_PERCENT = 50  # mobile LocalDatabase.readingPercent


def _counts(usages: list[QuestionUsage]) -> tuple[int, int]:
    total = len(usages)
    pre = sum(1 for u in usages if u in (QuestionUsage.BOTH, QuestionUsage.PRE)) or total
    post = sum(1 for u in usages if u in (QuestionUsage.BOTH, QuestionUsage.POST)) or total
    return pre, post


def test_question_counts(db: Session, module_id: uuid.UUID) -> tuple[int, int]:
    """(pre-test questions, post-test questions). A test with no questions of
    its own falls back to every active question, so a module is never left
    with only one of the two tests."""
    return _counts([u for (u,) in db.query(QuizQuestion.usage).filter_by(module_id=module_id, is_active=True)])


def all_test_question_counts(db: Session) -> dict[uuid.UUID, tuple[int, int]]:
    by_module: dict[uuid.UUID, list] = {}
    for mid, usage in db.query(QuizQuestion.module_id, QuizQuestion.usage).filter_by(is_active=True):
        by_module.setdefault(mid, []).append(usage)
    return {mid: _counts(us) for mid, us in by_module.items()}


@dataclass
class ModuleState:
    module: Module
    pre_questions: int
    post_questions: int
    progress: UserModuleProgress | None
    pre: QuizAttempt | None
    posts: list[QuizAttempt] = field(default_factory=list)
    unlocked: bool = True

    @property
    def has_tests(self) -> bool:
        return self.pre_questions > 0

    @property
    def completed(self) -> bool:
        return bool(self.progress and self.progress.completed)

    @property
    def reading_done(self) -> bool:
        return bool(self.progress and self.progress.reading_completed_at is not None)

    @property
    def pre_perfect(self) -> bool:
        return self.pre is not None and is_perfect(self.pre.correct_count, self.pre.total_count)

    def completing_post(self) -> QuizAttempt | None:
        """The first valid post-test that meets the rule, if any."""
        if self.pre is None:
            return None
        for a in sorted(self.posts, key=lambda a: a.taken_at):
            if post_test_completes(a.correct_count, a.total_count, self.pre.correct_count, self.pre.total_count):
                return a
        return None

    @property
    def status(self) -> str:
        if self.completed:
            return "COMPLETED"
        if not self.unlocked:
            return "LOCKED"
        if not self.has_tests:
            return "READING"
        if self.pre is None:
            return "PRE_TEST"
        if not self.reading_done:
            return "READING"
        return "POST_TEST"


def build_states(
    modules: list[Module],
    counts: dict[uuid.UUID, tuple[int, int]],
    progress: dict[uuid.UUID, UserModuleProgress],
    valid_attempts: list[QuizAttempt],
) -> list[ModuleState]:
    """States for one user's visible modules (in order) from preloaded rows,
    with locks applied: a module is unlocked when it is already completed or
    every earlier one is. Used per request and, in bulk, by reports."""
    states, all_before_done = [], True
    for m in modules:
        pre_n, post_n = counts.get(m.id, (0, 0))
        mine = sorted((a for a in valid_attempts if a.module_id == m.id), key=lambda a: a.taken_at)
        pres = [a for a in mine if a.test_type == TestType.PRE]
        s = ModuleState(
            module=m, pre_questions=pre_n, post_questions=post_n, progress=progress.get(m.id),
            pre=pres[-1] if pres else None,  # the latest valid pre-test is the baseline
            posts=[a for a in mine if a.test_type == TestType.POST],
        )
        s.unlocked = s.completed or all_before_done
        all_before_done = all_before_done and s.completed
        states.append(s)
    return states


def learning_states(db: Session, user: User) -> list[ModuleState]:
    """Every module the user may see, in order, with locks applied."""
    modules = visible_modules(db, user)
    ids = [m.id for m in modules]
    if not ids:
        return []
    progress = {p.module_id: p for p in db.query(UserModuleProgress).filter(
        UserModuleProgress.user_id == user.id, UserModuleProgress.module_id.in_(ids))}
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.module_id.in_(ids), QuizAttempt.valid.is_(True))
        .all()
    )
    counts = {mid: test_question_counts(db, mid) for mid in ids}
    return build_states(modules, counts, progress, attempts)


def module_state(db: Session, user: User, module_id: uuid.UUID) -> ModuleState | None:
    """None when the module is not visible to this user."""
    return next((s for s in learning_states(db, user) if s.module.id == module_id), None)


def complete(db: Session, user: User, module_id: uuid.UUID, when: datetime | None = None) -> UserModuleProgress:
    row = db.query(UserModuleProgress).filter_by(user_id=user.id, module_id=module_id).with_for_update().one_or_none()
    if row is None:
        row = UserModuleProgress(user_id=user.id, module_id=module_id, progress_percent=0)
        db.add(row)
    if not row.completed:
        row.completed = True
        row.progress_percent = 100
        row.completed_at = when or datetime.now(timezone.utc)
    db.flush()
    return row
