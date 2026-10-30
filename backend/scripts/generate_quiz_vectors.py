"""
Generates tests/quiz_vectors.json (copied to mobile/test/quiz_vectors.json):
the shared contract that keeps the Python and Dart quiz graders identical.
Every expectation below is ASSERTED against app/quiz/grading.py first, so a
wrong hand-written expectation fails loudly here.

Usage: cd backend && python3 -m scripts.generate_quiz_vectors
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.enums import QuestionType as T
from app.quiz import grading

MC = {"options": ["a", "b", "c"], "correct": 1}
MS = {"options": ["a", "b", "c", "d"], "correct": [0, 2]}
MATCH = {"pairs": [{"left": "L0", "right": "R0"}, {"left": "L1", "right": "R1"}, {"left": "L2", "right": "R2"}]}
ORDER = {"items": ["first", "second", "third", "fourth"]}
NUM = {"correct": 15, "tolerance": 0}
NUM_TOL = {"correct": 11.5, "tolerance": 0.05}

# (type, content, answer, expected_correct)
CASES = [
    (T.MULTIPLE_CHOICE, MC, 1, True),
    (T.MULTIPLE_CHOICE, MC, 0, False),
    (T.MULTIPLE_CHOICE, MC, True, False),   # a boolean is not an option number
    (T.MULTIPLE_CHOICE, MC, "1", False),
    (T.MULTIPLE_CHOICE, MC, None, False),
    (T.IMAGE_CHOICE, {**MC, "media_asset_id": "56659c7d-bf5d-4166-b061-2d0dca90e1e3"}, 1, True),
    (T.TRUE_FALSE, {"correct": True}, True, True),
    (T.TRUE_FALSE, {"correct": True}, False, False),
    (T.TRUE_FALSE, {"correct": False}, False, True),
    (T.TRUE_FALSE, {"correct": True}, 1, False),
    (T.MULTIPLE_SELECT, MS, [0, 2], True),
    (T.MULTIPLE_SELECT, MS, [2, 0], True),   # order does not matter
    (T.MULTIPLE_SELECT, MS, [0], False),     # missing one
    (T.MULTIPLE_SELECT, MS, [0, 1, 2], False),  # extra one
    (T.MULTIPLE_SELECT, MS, [0, 0, 2], False),  # duplicates
    (T.MULTIPLE_SELECT, MS, [], False),
    (T.MATCHING, MATCH, [0, 1, 2], True),
    (T.MATCHING, MATCH, [1, 0, 2], False),
    (T.MATCHING, MATCH, [0, 1], False),
    (T.ORDERING, ORDER, [0, 1, 2, 3], True),
    (T.ORDERING, ORDER, [0, 2, 1, 3], False),
    (T.ORDERING, ORDER, [0, 1, 2], False),
    (T.NUMERIC, NUM, 15, True),
    (T.NUMERIC, NUM, 15.0, True),
    (T.NUMERIC, NUM, 14, False),
    (T.NUMERIC, NUM, "15", False),
    (T.NUMERIC, NUM, True, False),
    (T.NUMERIC, NUM_TOL, 11.5, True),
    (T.NUMERIC, NUM_TOL, 11.54, True),
    (T.NUMERIC, NUM_TOL, 11.6, False),
]

# (correct, total, passed, score_percent): the 90% rule, exactly
PASS_CASES = [
    (9, 10, True, 90), (8, 10, False, 80), (10, 10, True, 100), (0, 10, False, 0),
    (89, 100, False, 89), (90, 100, True, 90), (17, 19, False, 89), (18, 19, True, 94),
    (1, 1, True, 100), (0, 1, False, 0), (4, 5, False, 80), (0, 0, False, 0),
]

for t, content, answer, expected in CASES:
    got = grading.is_correct(t, grading.validate_content(t, content), answer)
    assert got == expected, (t, content, answer, expected, got)
for c, n, p, s in PASS_CASES:
    assert grading.passed(c, n) == p and grading.score_percent(c, n) == s, (c, n)

out = {
    "pass_mark": grading.PASS_MARK,
    "answers": [{"type": t.value, "content": c, "answer": a, "correct": e} for t, c, a, e in CASES],
    "passing": [{"correct": c, "total": n, "passed": p, "score_percent": s} for c, n, p, s in PASS_CASES],
}
dest = Path(__file__).resolve().parents[1] / "tests" / "quiz_vectors.json"
dest.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
mobile = Path(__file__).resolve().parents[2] / "mobile" / "test" / "quiz_vectors.json"
shutil.copyfile(dest, mobile)
print(f"{len(CASES)} answer cases, {len(PASS_CASES)} pass cases -> {dest} and {mobile}")
