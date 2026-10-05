import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReleaseStatus


class ContentReleaseCreate(BaseModel):
    release_code: str = Field(min_length=1, max_length=50)
    campaign_id: uuid.UUID | None = None
    version: str = Field(min_length=1, max_length=30)
    description: str | None = None
    mandatory: bool = False


class ContentReleaseResponse(BaseModel):
    id: uuid.UUID
    release_code: str
    campaign_id: uuid.UUID | None
    version: str
    description: str | None
    mandatory: bool
    status: ReleaseStatus
    package_size: int | None
    checksum: str | None
    created_by: uuid.UUID | None
    approved_by: uuid.UUID | None
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
