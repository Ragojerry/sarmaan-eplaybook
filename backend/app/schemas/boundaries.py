import uuid

from pydantic import BaseModel, Field

from app.models.enums import BoundaryLevel


class BoundaryCreate(BaseModel):
    level: BoundaryLevel
    name: str = Field(min_length=1, max_length=200)
    code: str | None = Field(default=None, max_length=40)
    parent_id: uuid.UUID | None = None


class BoundaryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    code: str | None = Field(default=None, max_length=40)


class BoundaryResponse(BaseModel):
    id: uuid.UUID
    level: BoundaryLevel
    name: str
    code: str | None
    parent_id: uuid.UUID | None

    model_config = {"from_attributes": True}
