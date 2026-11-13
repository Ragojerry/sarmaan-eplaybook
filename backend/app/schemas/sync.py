"""Phase 12 wire formats for /sync/*. Every upload is a batch; every response
reports a result PER ITEM so the phone can mark exactly the items that landed
as synced and retry only the ones that didn't."""
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import TestType

MAX_BATCH = 200


class ProgressItem(BaseModel):
    module_id: uuid.UUID
    progress_percent: int = Field(ge=0, le=100)
    completed: bool = False
    last_section: str | None = Field(default=None, max_length=100)
    last_opened_at: datetime | None = None
    completed_at: datetime | None = None
    # When reading reached the end (app 0.1.8+). Older apps: inferred from progress_percent.
    reading_completed_at: datetime | None = None
    # Active time in the module, in seconds (app 0.1.12+). The server keeps the larger value.
    seconds_spent: int | None = Field(default=None, ge=0, le=10_000_000)


class ProgressOut(BaseModel):
    module_id: uuid.UUID
    progress_percent: int
    completed: bool
    last_section: str | None = None
    last_opened_at: datetime | None = None
    completed_at: datetime | None = None
    reading_completed_at: datetime | None = None
    seconds_spent: int = 0

    model_config = {"from_attributes": True}


class ProgressBatch(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    items: list[ProgressItem] = Field(max_length=MAX_BATCH)


class AiQuestionItem(BaseModel):
    client_id: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=2000)
    answer: str | None = None
    matched: bool = False
    confidence: float | None = None
    language: str = Field(default="en", max_length=10)
    module_id: uuid.UUID | None = None
    section_id: uuid.UUID | None = None
    asked_at: datetime


class AiQuestionBatch(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    items: list[AiQuestionItem] = Field(max_length=MAX_BATCH)


class AnalyticsItem(BaseModel):
    client_id: str = Field(min_length=1, max_length=80)
    event_type: str  # validated per item against AnalyticsEventType so one bad type can't fail the batch
    module_id: uuid.UUID | None = None
    video_id: uuid.UUID | None = None
    language: str | None = Field(default=None, max_length=10)
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


class AnalyticsBatch(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    items: list[AnalyticsItem] = Field(max_length=MAX_BATCH)


class ItemResult(BaseModel):
    """ok         -> stored (or merged); mark synced
       duplicate  -> already on the server (a retry); mark synced
       rejected   -> permanently invalid, retrying can never succeed; mark synced + drop
       error      -> transient server-side problem; keep queued and retry"""

    key: str
    status: Literal["ok", "duplicate", "rejected", "error"]
    detail: str | None = None


class BatchResult(BaseModel):
    results: list[ItemResult]


class ReleaseInfo(BaseModel):
    release_code: str
    version: str
    mandatory: bool
    description: str | None
    package_size: int | None
    checksum: str | None
    published_at: datetime | None
    # Which role-filtered copy of the package this account gets (app/releases/variants.py).
    variant: str | None = None


class CurrentReleaseResponse(BaseModel):
    release: ReleaseInfo | None
    installed: str | None
    update_available: bool


class QuizResultItem(BaseModel):
    question_id: uuid.UUID
    correct: bool
    # since app 0.1.16 (optional; older apps omit them): a retry shows only the statements
    # still wrong, so `shown` = asked in this attempt (False = credit kept from an earlier
    # attempt) and `answer` = the learner's True/False for a shown statement.
    shown: bool | None = None
    answer: bool | None = None


class QuizAttemptItem(BaseModel):
    client_id: str = Field(min_length=1, max_length=80)
    module_id: uuid.UUID
    correct_count: int = Field(ge=0, le=500)
    total_count: int = Field(ge=1, le=500)
    taken_at: datetime
    results: list[QuizResultItem] = Field(default_factory=list, max_length=500)
    # PRE or POST (app 0.1.8+). Missing = an older app's single quiz: kept as history, never counts.
    test_type: TestType | None = None


class QuizAttemptBatch(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    items: list[QuizAttemptItem] = Field(max_length=MAX_BATCH)


class TrainingRestartItem(BaseModel):
    client_id: str = Field(min_length=1, max_length=80)
    restarted_at: datetime


class TrainingRestartBatch(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    items: list[TrainingRestartItem] = Field(max_length=20)


class TrainingState(BaseModel):
    attempt: int
    restarted_at: datetime | None = None


class TestScore(BaseModel):
    client_id: str
    correct_count: int
    total_count: int
    score_percent: int
    taken_at: datetime
    # since 2026-11-13 (older apps ignore them): the pass mark that applied, and the verdict.
    pass_mark: int | None = None
    passed: bool | None = None


class ModuleLearning(BaseModel):
    module_id: uuid.UUID
    status: str
    unlocked: bool
    completed: bool
    # The retired per-module pre/post tests (always false/empty since 2026-11; kept for older apps).
    has_tests: bool
    pre_test: TestScore | None = None
    best_post_test: TestScore | None = None
    post_test_attempts: int = 0
    # The inline True/False quiz and the active time (app 0.1.12+).
    has_quiz: bool = False
    quiz_statements: int = 0
    quiz_passed: bool = True
    quiz_attempts: int = 0
    seconds_spent: int = 0
    lock_reason: str | None = None


class AttemptOut(BaseModel):
    client_id: str
    module_id: uuid.UUID
    test_type: TestType
    correct_count: int
    total_count: int
    score_percent: int
    passed: bool
    valid: bool
    invalid_reason: str | None = None
    taken_at: datetime

    model_config = {"from_attributes": True}


class LearningState(BaseModel):
    learner_role: str | None
    # A 100% pre-test is auto-approved by a post-test at or above this percentage.
    auto_approve_percent: int
    # Phones older than this show "Training updated, please update the app" (None = no minimum).
    # Only apps from 0.1.10 read it; older apps ignore unknown fields.
    min_app_version: str | None = None
    # Active time a learner must spend in a module before completing it (app 0.1.12+).
    module_min_seconds: int = 0
    general_test: "GeneralTestState | None" = None
    modules: list[ModuleLearning]
    attempts: list[AttemptOut]


class GeneralTestState(BaseModel):
    """The learner's General pre-/post-test (each counts once; the first valid one)."""
    active: bool
    questions: int
    pre_test: TestScore | None = None
    post_test: TestScore | None = None
    post_unlocked: bool = False
    modules_total: int = 0
    modules_completed: int = 0
    # This learner's current General pass mark (%), app/learning/settings.py.
    pass_mark: int | None = None


LearningState.model_rebuild()


class GeneralQuestionOut(BaseModel):
    id: uuid.UUID
    number: int
    prompt: str
    options: list[str]
    correct_index: int | None = None


class GeneralTestOut(BaseModel):
    active: bool
    questions: list[GeneralQuestionOut]


class GeneralAnswer(BaseModel):
    question_id: uuid.UUID
    choice: int | None = Field(default=None, ge=0, le=9)  # index of the chosen option; None = not answered


class GeneralAttemptItem(BaseModel):
    client_id: str = Field(min_length=1, max_length=80)
    test_type: TestType  # PRE or POST
    taken_at: datetime
    answers: list[GeneralAnswer] = Field(default_factory=list, max_length=200)


class GeneralAttemptBatch(BaseModel):
    device_id: str = Field(min_length=1, max_length=255)
    items: list[GeneralAttemptItem] = Field(max_length=20)
