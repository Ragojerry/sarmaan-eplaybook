"""The pass rule, as pure functions (shared vectors: tests/learning_vectors.json,
which the Dart rules must also pass).

A post-test completes a module when BOTH hold:
  1. it scores at least PASS_MARK (90%), and
  2. it scores strictly higher than the learner's pre-test.
Scores are compared as exact fractions (correct/total), because the two tests
may have different numbers of questions and rounded percentages can tie or
cross. A pre-test of 100% makes rule 2 impossible; only an administrator's
approved exception replaces rule 2 then, and rule 1 still applies.
"""
from app.quiz.grading import passed


def beats(post_correct: int, post_total: int, pre_correct: int, pre_total: int) -> bool:
    return post_total > 0 and pre_total > 0 and post_correct * pre_total > pre_correct * post_total


def is_perfect(correct: int, total: int) -> bool:
    return total > 0 and correct >= total


def post_test_completes(
    post_correct: int, post_total: int, pre_correct: int, pre_total: int, exception_approved: bool = False
) -> bool:
    if not passed(post_correct, post_total):
        return False
    if beats(post_correct, post_total, pre_correct, pre_total):
        return True
    return exception_approved and is_perfect(pre_correct, pre_total)
