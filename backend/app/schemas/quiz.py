import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import QuestionType


class QuestionCreate(BaseModel):
    question_type: QuestionType
    prompt: str = Field(min_length=3, max_length=1000)
    content: dict[str, Any]
    explanation: str | None = Field(default=None, max_length=1000)
    sort_order: int | None = None


class QuestionUpdate(BaseModel):
    prompt: str | None = Field(default=None, min_length=3, max_length=1000)
    content: dict[str, Any] | None = None
    explanation: str | None = Field(default=None, max_length=1000)
    sort_order: int | None = None
    is_active: bool | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    question_type: QuestionType
    prompt: str
    content: dict[str, Any]
    explanation: str | None
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class QuizSummary(BaseModel):
    module_id: uuid.UUID
    questions: int
    pass_mark: int
    attempts: int
    learners_passed: int
