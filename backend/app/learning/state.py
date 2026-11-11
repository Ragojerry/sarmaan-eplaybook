"""Where each learner is in the training, computed from stored rows.

General test (when switched on, setting general_test_active):
  - the General PRE-test is taken once, before any module can be opened;
  - the General POST-test (same questions) unlocks when every module the learner
    may see is completed, and is also taken once.

Per module, in the learner's own visible order:
  LOCKED     an earlier module is not completed, or the General pre-test is not taken yet
  READING    open: reading, answering the inline True/False quiz, time accumulating
  COMPLETED  completed (a module, once completed, stays completed and review-only)

A module can be completed when it is unlocked and
  1. its inline quiz (TRUE_FALSE sections), if it has one, has been passed: one valid
     MODULE_QUIZ attempt scoring at least the 90% pass mark (exact arithmetic; with
     three statements that means all three right). Retakes are unlimited until the
     module is completed and every attempt is kept;
  2. the learner has spent at least module_min_seconds of active time in it
     (reported by the phone, like quiz grading).
"Proceed" means COMPLETED, which also unlocks the next module.

The per-module pre-/post-tests used until 2026-11 are archived: their attempts stay in
the database as history but no longer affect any state.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.learning.access import visible_modules
from app.learning.rules import module_quiz_passes
from app.learning.settings import training_settings
from app.models import ContentSection, GeneralTestAttempt, GeneralTestQuestion, Module, QuizAttempt, User, UserModuleProgress
from app.models.enums import ContentType, TestType

READING_PERCENT = 50  # mobile LocalDatabase.readingPercent
GATE_REASON = "take the General pre-test first"


def quiz_statement_counts(db: Session, module_ids=None) -> dict[uuid.UUID, int]:
    q = db.query(ContentSection.module_id, func.count()).filter(ContentSection.content_type == ContentType.TRUE_FALSE)
    if module_ids is not None:
        q = q.filter(ContentSection.module_id.in_(module_ids))
    return dict(q.group_by(ContentSection.module_id).all())


@dataclass
class ModuleState:
    module: Module
    quiz_statements: int
    progress: UserModuleProgress | None
    quiz_attempts: list[QuizAttempt] = field(default_factory=list)  # valid MODULE_QUIZ attempts, oldest first
    min_seconds: int = 0
    unlocked: bool = True
    lock_reason: str | None = None

    @property
    def completed(self) -> bool:
        return bool(self.progress and self.progress.completed)

    @property
    def reading_done(self) -> bool:
        return bool(self.progress and self.progress.reading_completed_at is not None)

    @property
    def seconds_spent(self) -> int:
        return self.progress.seconds_spent if self.progress else 0

    @property
    def has_quiz(self) -> bool:
        return self.quiz_statements > 0

    def passing_quiz(self) -> QuizAttempt | None:
        """The first valid quiz attempt that reaches the pass mark, if any."""
        return next((a for a in self.quiz_attempts if module_quiz_passes(a.correct_count, a.total_count)), None)

    @property
    def quiz_passed(self) -> bool:
        return not self.has_quiz or self.passing_quiz() is not None

    @property
    def time_met(self) -> bool:
        return self.seconds_spent >= self.min_seconds

    @property
    def status(self) -> str:
        if self.completed:
            return "COMPLETED"
        if not self.unlocked:
            return "LOCKED"
        return "READING"

    def completion_problem(self) -> str | None:
        """Why the module cannot be completed now (None = it can, or it already is)."""
        if self.completed:
            return None
        if not self.unlocked:
            return self.lock_reason or "module is locked: complete the previous module first"
        if not self.quiz_passed:
            return "module quiz not passed yet"
        if not self.time_met:
            return f"less than {self.min_seconds} seconds in this module"
        return None


def build_states(
    modules: list[Module],
    quiz_counts: dict[uuid.UUID, int],
    progress: dict[uuid.UUID, UserModuleProgress],
    valid_quiz_attempts: list[QuizAttempt],
    min_seconds: int,
    gate_open: bool = True,
) -> list[ModuleState]:
    """States for one user's visible modules (in order) from preloaded rows, with locks
    applied: a module is unlocked when it is already completed, or when the General
    pre-test gate is open and every earlier module is completed. Used per request and,
    in bulk, by reports."""
    states, all_before_done = [], True
    for m in modules:
        mine = sorted((a for a in valid_quiz_attempts if a.module_id == m.id and a.test_type == TestType.MODULE_QUIZ),
                      key=lambda a: a.taken_at)
        s = ModuleState(module=m, quiz_statements=quiz_counts.get(m.id, 0), progress=progress.get(m.id),
                        quiz_attempts=mine, min_seconds=min_seconds)
        s.unlocked = s.completed or (gate_open and all_before_done)
        if not s.unlocked:
            s.lock_reason = GATE_REASON if not gate_open else "module is locked: complete the previous module first"
        all_before_done = all_before_done and s.completed
        states.append(s)
    return states


@dataclass
class GeneralState:
    active: bool
    questions: int
    pre: GeneralTestAttempt | None
    post: GeneralTestAttempt | None
    modules_total: int
    modules_completed: int

    @property
    def all_modules_completed(self) -> bool:
        return self.modules_total > 0 and self.modules_completed == self.modules_total

    @property
    def gate_open(self) -> bool:
        return not self.active or self.pre is not None

    @property
    def post_unlocked(self) -> bool:
        return self.active and self.pre is not None and self.post is None and self.all_modules_completed


def first_valid(attempts: list[GeneralTestAttempt], test_type: TestType) -> GeneralTestAttempt | None:
    mine = sorted((a for a in attempts if a.valid and a.test_type == test_type), key=lambda a: a.taken_at)
    return mine[0] if mine else None


def general_attempts(db: Session, user: User) -> list[GeneralTestAttempt]:
    return db.query(GeneralTestAttempt).filter_by(user_id=user.id).order_by(GeneralTestAttempt.taken_at).all()


def learning_states(db: Session, user: User) -> list[ModuleState]:
    """Every module the user may see, in order, with locks applied."""
    return learning_overview(db, user)[0]


def learning_overview(db: Session, user: User) -> tuple[list[ModuleState], GeneralState]:
    settings = training_settings(db)
    attempts = general_attempts(db, user)
    pre, post = first_valid(attempts, TestType.PRE), first_valid(attempts, TestType.POST)
    gate_open = not settings.general_test_active or pre is not None
    modules = visible_modules(db, user)
    ids = [m.id for m in modules]
    states = []
    if ids:
        progress = {p.module_id: p for p in db.query(UserModuleProgress).filter(
            UserModuleProgress.user_id == user.id, UserModuleProgress.module_id.in_(ids))}
        quiz = (db.query(QuizAttempt)
                .filter(QuizAttempt.user_id == user.id, QuizAttempt.module_id.in_(ids), QuizAttempt.valid.is_(True),
                        QuizAttempt.test_type == TestType.MODULE_QUIZ)
                .all())
        states = build_states(modules, quiz_statement_counts(db, ids), progress, quiz, settings.module_min_seconds, gate_open)
    general = GeneralState(
        active=settings.general_test_active,
        questions=db.query(GeneralTestQuestion).filter_by(is_active=True).count(),
        pre=pre, post=post, modules_total=len(states), modules_completed=sum(1 for s in states if s.completed),
    )
    return states, general


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
