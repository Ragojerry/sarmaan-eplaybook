"""
Generates tests/learning_vectors.json (copied to mobile/test/learning_vectors.json):
the shared contract that keeps the Python and Dart pre-/post-test rules
identical (app/learning/rules.py <-> mobile/lib/learning/learning_rules.dart).
Every expectation below is ASSERTED against the Python rules first, so a wrong
hand-written expectation fails loudly here.

Usage: cd backend && python3 -m scripts.generate_learning_vectors
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.learning.rules import post_test_completes

# (pre correct, pre total, post correct, post total, exception approved, completes, why)
CASES = [
    (5, 10, 9, 10, False, True, "exactly 90% and higher than the pre-test"),
    (5, 10, 8, 10, False, False, "80%: below the pass mark"),
    (5, 10, 89, 100, False, False, "89%: just below the pass mark"),
    (5, 10, 10, 10, False, True, "100%"),
    (9, 10, 9, 10, False, False, "90% but equal to the pre-test (must be strictly higher)"),
    (9, 10, 10, 10, False, True, "higher than a 90% pre-test"),
    (9, 10, 18, 20, False, False, "same fraction with different totals is not higher"),
    (9, 10, 19, 20, False, True, "95% beats 90% with different totals"),
    (8, 9, 9, 10, False, True, "pre 8/9 (88.9%) is below post 9/10 (90%): exact fractions, not rounded"),
    (1, 9, 8, 9, False, False, "post 8/9 (88.9%) beats the pre-test but is below the pass mark"),
    (10, 11, 9, 10, False, False, "pre 10/11 (90.9%) beats post 9/10 (90%): rounding would hide this"),
    (0, 10, 9, 10, False, True, "a zero pre-test"),
    (10, 10, 10, 10, False, False, "100% pre-test: a higher score is impossible without an exception"),
    (10, 10, 10, 10, True, True, "100% pre-test with an approved exception and a 100% post-test"),
    (10, 10, 9, 10, True, True, "100% pre-test with an exception: 90% post-test is enough"),
    (10, 10, 8, 10, True, False, "an exception never waives the 90% pass mark"),
    (9, 10, 9, 10, True, False, "an exception only applies to a 100% pre-test"),
]


def main() -> None:
    out = []
    for pre_c, pre_t, post_c, post_t, exc, expected, why in CASES:
        got = post_test_completes(post_c, post_t, pre_c, pre_t, exception_approved=exc)
        assert got is expected, (why, got)
        out.append({"pre_correct": pre_c, "pre_total": pre_t, "post_correct": post_c, "post_total": post_t,
                    "exception_approved": exc, "completes": expected, "why": why})
    backend = Path(__file__).resolve().parents[1]
    target = backend / "tests" / "learning_vectors.json"
    target.write_text(json.dumps({"pass_mark": 90, "cases": out}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mobile = backend.parent / "mobile" / "test" / "learning_vectors.json"
    shutil.copyfile(target, mobile)
    print(f"wrote {len(out)} cases to {target} and {mobile}")


if __name__ == "__main__":
    main()
