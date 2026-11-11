"""The pass rule, as pure functions (shared vectors: tests/learning_vectors.json,
which the Dart rules must also pass).

A post-test completes a module when BOTH hold:
  1. it scores at least PASS_MARK (90%), and
  2. it scores strictly higher than the learner's pre-test.
Scores are compared as exact fractions (correct/total), because the two tests
may have different numbers of questions and rounded percentages can tie or
cross.

A pre-test of 100% makes rule 2 impossible. Such a learner is auto-approved
instead: a post-test of at least the auto-approval threshold (setting
POST_TEST_AUTO_APPROVE_PERCENT, 90 by default) completes the module at once,
with no manual step.
"""
from app.config import get_settings
from app.quiz.grading import passed


def auto_approve_percent() -> int:
    return get_settings().post_test_auto_approve_percent


def beats(post_correct: int, post_total: int, pre_correct: int, pre_total: int) -> bool:
    return post_total > 0 and pre_total > 0 and post_correct * pre_total > pre_correct * post_total


def is_perfect(correct: int, total: int) -> bool:
    return total > 0 and correct >= total


def reaches(correct: int, total: int, percent: int) -> bool:
    """Exact integer arithmetic, like the pass mark (no rounding at the edge)."""
    return total > 0 and correct * 100 >= percent * total


def module_quiz_passes(correct: int, total: int) -> bool:
    """A module's inline True/False quiz is passed at the same 90% pass mark
    (exact arithmetic: 3 statements need 3 right, 2 of 3 is 66.7%)."""
    return passed(correct, total)


def can_complete_module(unlocked: bool, has_quiz: bool, quiz_passed: bool, seconds: int, min_seconds: int) -> bool:
    """The completion rule since 2026-11 (mirrored in the phone's learning_rules.dart)."""
    return unlocked and (not has_quiz or quiz_passed) and seconds >= min_seconds


def post_test_completes(
    post_correct: int, post_total: int, pre_correct: int, pre_total: int, auto_approve_at: int | None = None
) -> bool:
    if is_perfect(pre_correct, pre_total):
        threshold = auto_approve_percent() if auto_approve_at is None else auto_approve_at
        return reaches(post_correct, post_total, threshold)
    return passed(post_correct, post_total) and beats(post_correct, post_total, pre_correct, pre_total)
