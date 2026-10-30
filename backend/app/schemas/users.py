import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import RoleName, UserStatus

TEAM_CODE_PATTERN = r"^[A-Za-z0-9-]{1,20}$"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=10, max_length=255)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    role: RoleName = RoleName.CDD
    team_code: str | None = Field(default=None, pattern=TEAM_CODE_PATTERN)
    language_id: uuid.UUID | None = None
    # deepest area chosen (country, state, LGA, ward or facility); its parents are filled in
    boundary_id: uuid.UUID | None = None
    training_session_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    # empty string clears the team
    team_code: str | None = Field(default=None, pattern=r"^([A-Za-z0-9-]{1,20})?$")
    role: RoleName | None = None
    status: UserStatus | None = None
    language_id: uuid.UUID | None = None
    # a boundary id sets the area; clear_boundary removes it
    boundary_id: uuid.UUID | None = None
    clear_boundary: bool = False
    # a session id moves the person to that training session; clear_session removes them from it
    training_session_id: uuid.UUID | None = None
    clear_session: bool = False
