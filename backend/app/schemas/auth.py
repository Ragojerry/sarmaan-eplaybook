import uuid
from datetime import datetime

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
    role: RoleName
    language_id: uuid.UUID | None
    status: UserStatus
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
