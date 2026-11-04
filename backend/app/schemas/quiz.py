import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import QuestionType, QuestionUsage


class QuestionCreate(BaseModel):
    question_type: QuestionType
    prompt: str = Field(min_length=3, max_length=1000)
    content: dict[str, Any]
    explanation: str | None = Field(default=None, max_length=1000)
    sort_order: int | None = None
    usage: QuestionUsage = QuestionUsage.BOTH


class QuestionUpdate(BaseModel):
    prompt: str | None = Field(default=None, min_length=3, max_length=1000)
    content: dict[str, Any] | None = None
    explanation: str | None = Field(default=None, max_length=1000)
    sort_order: int | None = None
    is_active: bool | None = None
    usage: QuestionUsage | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    question_type: QuestionType
    prompt: str
    content: dict[str, Any]
    explanation: str | None
    sort_order: int
    is_active: bool
    usage: QuestionUsage = QuestionUsage.BOTH

    model_config = {"from_attributes": True}


class QuizSummary(BaseModel):
    module_id: uuid.UUID
    questions: int
    pass_mark: int
    attempts: int
    learners_passed: int  # learners who completed the module through its post-test
    pre_test_questions: int = 0
    post_test_questions: int = 0
    pre_test_attempts: int = 0
    post_test_attempts: int = 0
    # Set when admins tagged every question for one test only (the other test then uses all questions).
    warning: str | None = None
