"""Training restart: the learner (or an admin) starts the whole training over and
the newest attempt REPLACES the old one.

Replaced: module progress, credited completions and quiz attempts (pre- and post-tests), hard-deleted. Kept: the append-only
audit log entry, and raw analytics/Q&A rows (reports ignore anything that happened
before the user's latest restart, so those never count toward the new attempt)."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AuditLog, ModuleCompletionCredit, QuizAttempt, User, UserModuleProgress
from app.models.enums import AuditAction


def restart_training(db: Session, user: User, restarted_at: datetime, actor: User, via: str) -> bool:
    """Returns False (no change) when this restart is not newer than the last one,
    which makes a retried upload idempotent."""
    if restarted_at.tzinfo is None:
        restarted_at = restarted_at.replace(tzinfo=timezone.utc)
    if user.training_restarted_at is not None and restarted_at <= user.training_restarted_at:
        return False
    # Credited completions are progress too: a restart starts the learner over from nothing.
    removed_credits = db.query(ModuleCompletionCredit).filter_by(user_id=user.id).delete()
    removed_progress = db.query(UserModuleProgress).filter_by(user_id=user.id).delete()
    removed_quiz = db.query(QuizAttempt).filter_by(user_id=user.id).delete()
    previous = user.training_attempt
    user.training_attempt = previous + 1
    user.training_restarted_at = restarted_at
    db.add(AuditLog(
        user_id=actor.id, action=AuditAction.TRAINING_RESTART, entity_type="user", entity_id=user.id,
        details={"via": via, "attempt": user.training_attempt, "replaced_attempt": previous,
                 "progress_rows_removed": removed_progress, "quiz_attempts_removed": removed_quiz,
                 "credits_removed": removed_credits},
    ))
    return True


def is_stale(user: User, moment: datetime | None) -> bool:
    """Data stamped before the latest restart belongs to the replaced attempt."""
    if user.training_restarted_at is None:
        return False
    if moment is None:
        return True
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment < user.training_restarted_at
