"""
The General pre/post test and the training rules, for the admin portal.

  GET   /general-test/questions           every question with its answer (staff)
  POST  /general-test/questions           add a question (content admins)
  PATCH /general-test/questions/{id}      edit text, options, answer, active, CDD note
  POST  /general-test/answer-key          set many answers at once: "1-B, 2-B, ..."
  GET   /general-test/settings            module_min_seconds, general_test_active (+ why it can't be on)
  PUT   /general-test/settings            change them; switching the test on needs every active
                                          question to have an answer

Every change is audited. Learners never reach these routes (they get /sync/general-test).
"""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.learning.settings import SettingError, change_setting, general_test_ready, training_settings
from app.models import AuditLog, GeneralTestQuestion, User
from app.models.enums import AuditAction, RoleName

router = APIRouter()
EDITORS = (RoleName.CONTENT_ADMIN,)
LETTERS = "ABCDEFGHIJ"


def _staff(user: User = Depends(get_current_user)) -> User:
    if user.role == RoleName.CDD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Test answers are not available to learners")
    return user


class QuestionIn(BaseModel):
    number: int = Field(ge=1, le=999)
    prompt: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=10)
    correct_index: int | None = Field(default=None, ge=0, le=9)
    cdd_specific: bool = False
    is_active: bool = False


class QuestionPatch(BaseModel):
    prompt: str | None = Field(default=None, min_length=1, max_length=2000)
    options: list[str] | None = Field(default=None, min_length=2, max_length=10)
    correct_index: int | None = Field(default=None, ge=0, le=9)
    clear_answer: bool = False
    cdd_specific: bool | None = None
    is_active: bool | None = None


class AnswerKeyIn(BaseModel):
    key: str = Field(min_length=1, max_length=2000, description='e.g. "1-B, 2-B, 3-C"')


class SettingsIn(BaseModel):
    module_min_seconds: int | None = None
    general_test_active: bool | None = None


def _out(q: GeneralTestQuestion) -> dict:
    return {"id": str(q.id), "number": q.number, "prompt": q.prompt, "options": q.options,
            "correct_index": q.correct_index,
            "correct_letter": LETTERS[q.correct_index] if q.correct_index is not None else None,
            "cdd_specific": q.cdd_specific, "is_active": q.is_active}


def _check_answer(options: list[str], index: int | None) -> None:
    if index is not None and index >= len(options):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"answer {LETTERS[index]} is not one of the {len(options)} options")


def _audit(db: Session, user: User, q: GeneralTestQuestion | None, details: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=AuditAction.GENERAL_TEST_UPDATE, entity_type="general_test_question",
                    entity_id=q.id if q else None, details=details))


def _still_ready(db: Session) -> None:
    """A change may not leave a switched-on test with an unanswered active question."""
    if training_settings(db).general_test_active:
        problem = general_test_ready(db)
        if problem:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"The General test is switched on: {problem}. Switch it off first.")


@router.get("/questions")
def list_questions(db: Session = Depends(get_db), user: User = Depends(_staff)):
    return [_out(q) for q in db.query(GeneralTestQuestion).order_by(GeneralTestQuestion.number)]


@router.post("/questions", status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*EDITORS))):
    if db.query(GeneralTestQuestion.id).filter_by(number=payload.number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"question {payload.number} already exists")
    _check_answer(payload.options, payload.correct_index)
    q = GeneralTestQuestion(**{**payload.model_dump(), "prompt": payload.prompt.strip(),
                               "options": [o.strip() for o in payload.options]})
    db.add(q)
    db.flush()
    _audit(db, user, q, {"created": _out(q)})
    _still_ready(db)
    db.commit()
    return _out(q)


@router.patch("/questions/{question_id}")
def update_question(question_id: uuid.UUID, payload: QuestionPatch, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(*EDITORS))):
    q = db.get(GeneralTestQuestion, question_id)
    if q is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    before = _out(q)
    changes = payload.model_dump(exclude_unset=True)
    if "prompt" in changes:
        q.prompt = changes["prompt"].strip()
    if "options" in changes:
        q.options = [o.strip() for o in changes["options"]]
    if changes.get("clear_answer"):
        q.correct_index = None
    elif "correct_index" in changes:
        q.correct_index = changes["correct_index"]
    _check_answer(q.options, q.correct_index)
    for k in ("cdd_specific", "is_active"):
        if changes.get(k) is not None:
            setattr(q, k, changes[k])
    db.flush()
    _audit(db, user, q, {"before": before, "after": _out(q)})
    _still_ready(db)
    db.commit()
    return _out(q)


def parse_key(text: str) -> dict[int, int]:
    """'1-B, 2-b; 3 C' -> {1: 1, 2: 1, 3: 2}. Raises ValueError on anything else."""
    out = {}
    for part in re.split(r"[,;\n]+", text):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*[-.:)\s]\s*([A-Ja-j])", part)
        if not m:
            raise ValueError(f"cannot read {part!r}: write it like 1-B")
        n = int(m.group(1))
        if n in out:
            raise ValueError(f"question {n} appears twice")
        out[n] = LETTERS.index(m.group(2).upper())
    if not out:
        raise ValueError("the key is empty")
    return out


@router.post("/answer-key")
def set_answer_key(payload: AnswerKeyIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*EDITORS))):
    """Sets the answers given; questions not listed keep theirs. Does not switch anything on."""
    try:
        key = parse_key(payload.key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    questions = {q.number: q for q in db.query(GeneralTestQuestion)}
    unknown = sorted(set(key) - set(questions))
    if unknown:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"no question numbered {', '.join(map(str, unknown))}")
    for n, index in key.items():
        _check_answer(questions[n].options, index)
    before = {n: _out(questions[n])["correct_letter"] for n in key}
    for n, index in key.items():
        questions[n].correct_index = index
    _audit(db, user, None, {"answer_key": {n: LETTERS[i] for n, i in sorted(key.items())}, "before": before})
    db.commit()
    return [_out(q) for q in sorted(questions.values(), key=lambda q: q.number)]


@router.get("/settings")
def get_settings_(db: Session = Depends(get_db), user: User = Depends(_staff)):
    s = training_settings(db)
    return {"module_min_seconds": s.module_min_seconds, "general_test_active": s.general_test_active,
            "cannot_activate_because": general_test_ready(db)}


@router.put("/settings")
def put_settings(payload: SettingsIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*EDITORS))):
    try:
        for key, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                change_setting(db, key, value, user)
    except SettingError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    db.commit()
    return get_settings_(db, user)
