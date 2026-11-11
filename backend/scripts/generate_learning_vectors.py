"""
Generates tests/learning_vectors.json (copied to mobile/test/learning_vectors.json):
the shared contract that keeps the Python and Dart learning rules identical
(app/learning/rules.py <-> mobile/lib/learning/learning_rules.dart): the module
completion rule (inline quiz at the 90% pass mark + minimum active time) and the
retired per-module pre/post rule (kept: older attempts and older apps use it).
Every expectation below is ASSERTED against the Python rules first, so a wrong
hand-written expectation fails loudly here.

Usage: cd backend && python3 -m scripts.generate_learning_vectors
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.learning.rules import can_complete_module, module_quiz_passes, post_test_completes

AUTO_APPROVE = 90  # the shipped value of the POST_TEST_AUTO_APPROVE_PERCENT setting

# (pre correct, pre total, post correct, post total, completes, why)
CASES = [
    (5, 10, 9, 10, True, "exactly 90% and higher than the pre-test"),
    (5, 10, 8, 10, False, "80%: below the pass mark"),
    (5, 10, 89, 100, False, "89%: just below the pass mark"),
    (5, 10, 10, 10, True, "100%"),
    (9, 10, 9, 10, False, "90% but equal to the pre-test (must be strictly higher)"),
    (9, 10, 10, 10, True, "higher than a 90% pre-test"),
    (9, 10, 18, 20, False, "same fraction with different totals is not higher"),
    (9, 10, 19, 20, True, "95% beats 90% with different totals"),
    (8, 9, 9, 10, True, "pre 8/9 (88.9%) is below post 9/10 (90%): exact fractions, not rounded"),
    (1, 9, 8, 9, False, "post 8/9 (88.9%) beats the pre-test but is below the pass mark"),
    (10, 11, 9, 10, False, "pre 10/11 (90.9%) beats post 9/10 (90%): rounding would hide this"),
    (0, 10, 9, 10, True, "a zero pre-test"),
    (10, 10, 9, 10, True, "100% pre-test, 90% post-test: auto-approved"),
    (10, 10, 19, 20, True, "100% pre-test, 95% post-test: auto-approved"),
    (10, 10, 10, 10, True, "100% pre-test, 100% post-test: auto-approved"),
    (10, 10, 89, 100, False, "100% pre-test, 89% post-test: below the auto-approval threshold"),
    (10, 10, 8, 10, False, "100% pre-test, 80% post-test: below the auto-approval threshold"),
]

# (unlocked, quiz statements, quiz correct, seconds spent, min seconds, can complete, why)
# quiz correct None = no attempt yet; a module with 0 statements has no quiz.
COMPLETION = [
    (True, 3, 3, 180, 180, True, "quiz 3/3 and exactly 3 minutes"),
    (True, 3, 2, 600, 180, False, "quiz 2/3 (66.7%) is below the 90% pass mark"),
    (True, 3, 3, 179, 180, False, "one second short of the minimum time"),
    (True, 3, None, 600, 180, False, "quiz not taken yet"),
    (True, 0, None, 180, 180, True, "a module without a quiz needs only the time"),
    (True, 0, None, 30, 180, False, "a module without a quiz still needs the time"),
    (False, 3, 3, 600, 180, False, "locked: complete the previous module (or the General pre-test) first"),
    (True, 3, 3, 0, 0, True, "minimum time set to 0 by an administrator"),
    (True, 10, 9, 200, 180, True, "a 10-statement quiz at exactly 90%"),
]


def main() -> None:
    out = []
    for pre_c, pre_t, post_c, post_t, expected, why in CASES:
        got = post_test_completes(post_c, post_t, pre_c, pre_t, auto_approve_at=AUTO_APPROVE)
        assert got is expected, (why, got)
        out.append({"pre_correct": pre_c, "pre_total": pre_t, "post_correct": post_c, "post_total": post_t,
                    "completes": expected, "why": why})
    completion = []
    for unlocked, n, correct, secs, min_secs, expected, why in COMPLETION:
        passed = n > 0 and correct is not None and module_quiz_passes(correct, n)
        got = can_complete_module(unlocked, n > 0, passed, secs, min_secs)
        assert got is expected, (why, got)
        completion.append({"unlocked": unlocked, "quiz_statements": n, "quiz_correct": correct, "seconds": secs,
                           "min_seconds": min_secs, "can_complete": expected, "why": why})
    backend = Path(__file__).resolve().parents[1]
    target = backend / "tests" / "learning_vectors.json"
    target.write_text(json.dumps({"pass_mark": 90, "auto_approve_percent": AUTO_APPROVE, "module_min_seconds": 180,
                                     "cases": out, "completion": completion}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mobile = backend.parent / "mobile" / "test" / "learning_vectors.json"
    shutil.copyfile(target, mobile)
    print(f"wrote {len(out)} + {len(completion)} cases to {target} and {mobile}")


if __name__ == "__main__":
    main()
