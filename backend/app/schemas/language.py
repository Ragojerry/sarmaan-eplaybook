import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import LanguageStatus


class LanguageCreate(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    name: str = Field(min_length=1, max_length=100)
    native_name: str = Field(min_length=1, max_length=100)
    status: LanguageStatus = LanguageStatus.NOT_STARTED
    is_default: bool = False


class LanguageUpdate(BaseModel):
    name: str | None = None
    native_name: str | None = None
    status: LanguageStatus | None = None
    is_default: bool | None = None


class LanguageResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    native_name: str
    status: LanguageStatus
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}
