import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class SessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def _dates(self):
        if self.end_date < self.start_date:
            raise ValueError("The end date cannot be before the start date.")
        return self


class SessionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    end_date: date | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    start_date: date
    end_date: date
    status: str
    user_count: int = 0
    created_at: datetime


class MemberBatch(BaseModel):
    user_ids: list[uuid.UUID] = Field(min_length=1, max_length=2000)
