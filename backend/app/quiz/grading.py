"""
Quiz rules shared by the admin API (validation), the sync API (pass check) and,
by mirrored code + shared vectors (tests/quiz_vectors.json), the phone.

Question `content` and learner `answer` shapes:

MULTIPLE_CHOICE  content {options:[str], correct:int}              answer int (option index)
IMAGE_CHOICE     content {media_asset_id, alt?, options, correct}  answer int
TRUE_FALSE       content {correct:bool}                            answer bool
MULTIPLE_SELECT  content {options:[str], correct:[int]}            answer [int] (any order)
MATCHING         content {pairs:[{left,right}]}                    answer [int]: answer[i] = which
                                                                   right (by its pair index) the learner
                                                                   matched to left i
ORDERING         content {items:[str]} (stored in CORRECT order)   answer [int]: item indexes in the
                                                                   order the learner arranged them
NUMERIC          content {correct:number, tolerance?:number, unit?:str}   answer number

A question is right only if EVERY part is right (no partial credit). A module
quiz is passed at PASS_MARK percent or more.
"""
import math
import uuid

from app.models.enums import QuestionType as T

PASS_MARK = 90


class InvalidQuestion(ValueError):
    pass


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _strings(values, lo, hi, what, unique=True):
    if not isinstance(values, list) or not (lo <= len(values) <= hi):
        raise InvalidQuestion(f"{what} must be a list of {lo} to {hi} items")
    cleaned = []
    for v in values:
        if not isinstance(v, str) or not v.strip():
            raise InvalidQuestion(f"{what} cannot contain empty items")
        cleaned.append(v.strip())
    if unique and len({c.lower() for c in cleaned}) != len(cleaned):
        raise InvalidQuestion(f"{what} must all be different")
    return cleaned


def validate_content(qtype: T, content: dict) -> dict:
    """Returns a cleaned copy of `content` or raises InvalidQuestion."""
    if not isinstance(content, dict):
        raise InvalidQuestion("content must be an object")
    if qtype in (T.MULTIPLE_CHOICE, T.IMAGE_CHOICE):
        options = _strings(content.get("options"), 2, 8 if qtype == T.MULTIPLE_CHOICE else 6, "options")
        correct = content.get("correct")
        if not _is_int(correct) or not (0 <= correct < len(options)):
            raise InvalidQuestion("correct must be the number of one option")
        out = {"options": options, "correct": correct}
        if qtype == T.IMAGE_CHOICE:
            try:
                out["media_asset_id"] = str(uuid.UUID(str(content.get("media_asset_id"))))
            except ValueError as exc:
                raise InvalidQuestion("an image question needs a picture (media_asset_id)") from exc
            if content.get("alt"):
                out["alt"] = str(content["alt"]).strip()[:300]
        return out
    if qtype == T.TRUE_FALSE:
        if not isinstance(content.get("correct"), bool):
            raise InvalidQuestion("correct must be true or false")
        return {"correct": content["correct"]}
    if qtype == T.MULTIPLE_SELECT:
        options = _strings(content.get("options"), 3, 8, "options")
        correct = content.get("correct")
        if (
            not isinstance(correct, list)
            or not correct
            or not all(_is_int(c) and 0 <= c < len(options) for c in correct)
            or len(set(correct)) != len(correct)
        ):
            raise InvalidQuestion("correct must list at least one valid, different option number")
        if len(correct) == len(options):
            raise InvalidQuestion("not every option can be correct")
        return {"options": options, "correct": sorted(correct)}
    if qtype == T.MATCHING:
        pairs = content.get("pairs")
        if not isinstance(pairs, list) or not (2 <= len(pairs) <= 8):
            raise InvalidQuestion("pairs must be a list of 2 to 8 pairs")
        lefts = _strings([p.get("left") if isinstance(p, dict) else None for p in pairs], 2, 8, "left items")
        rights = _strings([p.get("right") if isinstance(p, dict) else None for p in pairs], 2, 8, "right items")
        return {"pairs": [{"left": a, "right": b} for a, b in zip(lefts, rights)]}
    if qtype == T.ORDERING:
        return {"items": _strings(content.get("items"), 3, 8, "items")}
    if qtype == T.NUMERIC:
        correct = content.get("correct")
        tol = content.get("tolerance", 0)
        if not _is_num(correct):
            raise InvalidQuestion("correct must be a number")
        if not _is_num(tol) or tol < 0:
            raise InvalidQuestion("tolerance must be zero or more")
        out = {"correct": correct, "tolerance": tol}
        if content.get("unit"):
            out["unit"] = str(content["unit"]).strip()[:20]
        return out
    raise InvalidQuestion("unknown question type")


def is_correct(qtype: T, content: dict, answer) -> bool:
    """Grades one answer. Malformed answers are simply wrong, never errors."""
    if qtype in (T.MULTIPLE_CHOICE, T.IMAGE_CHOICE):
        return _is_int(answer) and answer == content["correct"]
    if qtype == T.TRUE_FALSE:
        return isinstance(answer, bool) and answer == content["correct"]
    if qtype == T.MULTIPLE_SELECT:
        return (
            isinstance(answer, list)
            and all(_is_int(a) for a in answer)
            and len(set(answer)) == len(answer)
            and sorted(answer) == sorted(content["correct"])
        )
    if qtype == T.MATCHING:
        n = len(content["pairs"])
        return isinstance(answer, list) and len(answer) == n and all(_is_int(a) for a in answer) and answer == list(range(n))
    if qtype == T.ORDERING:
        n = len(content["items"])
        return isinstance(answer, list) and len(answer) == n and all(_is_int(a) for a in answer) and answer == list(range(n))
    if qtype == T.NUMERIC:
        return _is_num(answer) and abs(answer - content["correct"]) <= content.get("tolerance", 0) + 1e-9
    return False


def passed(correct: int, total: int) -> bool:
    """Exact integer arithmetic (no float rounding at the 90% edge)."""
    return total > 0 and correct * 100 >= PASS_MARK * total


def score_percent(correct: int, total: int) -> int:
    return 0 if total <= 0 else (correct * 100) // total
