import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import RoleName, UserStatus


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    team_code: str | None = None
    country_id: uuid.UUID | None = None
    state_id: uuid.UUID | None = None
    lga_id: uuid.UUID | None = None
    ward_id: uuid.UUID | None = None
    facility_id: uuid.UUID | None = None
    country_name: str | None = None
    state_name: str | None = None
    lga_name: str | None = None
    ward_name: str | None = None
    facility_name: str | None = None
    training_session_id: uuid.UUID | None = None
    training_attempt: int = 1
    training_restarted_at: datetime | None = None
    session_name: str | None = None
    session_start_date: date | None = None
    session_end_date: date | None = None
    session_status: str | None = None
    role: RoleName
    language_id: uuid.UUID | None
    status: UserStatus
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
