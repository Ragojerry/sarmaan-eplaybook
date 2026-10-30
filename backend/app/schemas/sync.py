"""Phase 12 wire formats for /sync/*. Every upload is a batch; every response
reports a result PER ITEM so the phone can mark exactly the items that landed
as synced and retry only the ones that didn't."""
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

MAX_BATCH = 200


class ProgressItem(BaseModel):
    module_id: uuid.UUID
    progress_percent: int = Field(ge=0, le=100)
    completed: bool = False
    last_section: str | None = Field(default=None, max_length=100)
    last_opened_at: datetime | None = None
    completed_at: datetime | None = None


class ProgressOut(BaseModel):
    module_id: uuid.UUID
    progress_percent: int
    completed: bool
    last_section: str | None = None
    last_opened_at: datetime | None = None
    completed_at: datetime | None = None

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


class CurrentReleaseResponse(BaseModel):
    release: ReleaseInfo | None
    installed: str | None
    update_available: bool


class QuizResultItem(BaseModel):
    question_id: uuid.UUID
    correct: bool


class QuizAttemptItem(BaseModel):
    client_id: str = Field(min_length=1, max_length=80)
    module_id: uuid.UUID
    correct_count: int = Field(ge=0, le=500)
    total_count: int = Field(ge=1, le=500)
    taken_at: datetime
    results: list[QuizResultItem] = Field(default_factory=list, max_length=500)


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
