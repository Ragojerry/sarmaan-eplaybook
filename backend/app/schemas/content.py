import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ModuleStatus, ContentReviewStatus, ContentType


class ModuleCreate(BaseModel):
    module_code: str = Field(min_length=1, max_length=20)
    module_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sort_order: int = 0


class ModuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    sort_order: int | None = None
    status: ModuleStatus | None = None


class ModuleReorder(BaseModel):
    module_id: uuid.UUID
    sort_order: int


class ModuleResponse(BaseModel):
    id: uuid.UUID
    module_code: str
    module_number: int
    title: str
    description: str | None
    status: ModuleStatus
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModuleTranslationCreate(BaseModel):
    language_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    body: str | None = None
    audio_text: str | None = None


class ModuleTranslationUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    body: str | None = None
    audio_text: str | None = None


class ModuleTranslationResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    language_id: uuid.UUID
    title: str
    description: str | None
    body: str | None
    audio_text: str | None
    status: ContentReviewStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class ContentSectionCreate(BaseModel):
    section_number: int = Field(ge=1)
    title: str | None = None
    content_type: ContentType
    content: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0


class ContentSectionUpdate(BaseModel):
    title: str | None = None
    content_type: ContentType | None = None
    content: dict[str, Any] | None = None
    sort_order: int | None = None


class ContentSectionResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    section_number: int
    title: str | None
    content_type: ContentType
    content: dict[str, Any]
    sort_order: int

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    reason: str | None = None
