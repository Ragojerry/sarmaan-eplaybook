import re
import uuid
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, EmailStr, Field

from app.models.enums import LEARNER_ROLE_LABELS, LearnerRole, RoleName, UserStatus

TEAM_CODE_PATTERN = r"^[A-Za-z0-9-]{1,20}$"

_ROLE_WORDS = {re.sub(r"[^a-z]", "", label.lower()): role for role, label in LEARNER_ROLE_LABELS.items()}
_ROLE_WORDS.update({re.sub(r"[^a-z]", "", r.value.lower()): r for r in LearnerRole})
_ROLE_WORDS.update({"other": LearnerRole.OTHER, "healthworkers": LearnerRole.HEALTH_WORKER})


def parse_learner_role(value):
    """Accepts the enum value or the label people type in a spreadsheet
    ("Health Worker", "Monitor/Supervisor", "Others"); blank means none."""
    if value is None or isinstance(value, LearnerRole):
        return value
    text = re.sub(r"[^a-z]", "", str(value).lower())
    if not text:
        return None
    if text in _ROLE_WORDS:
        return _ROLE_WORDS[text]
    raise ValueError("must be one of: " + ", ".join(LEARNER_ROLE_LABELS.values()))


LearnerRoleField = Annotated[LearnerRole | None, BeforeValidator(parse_learner_role)]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(min_length=10, max_length=255)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    role: RoleName = RoleName.CDD
    # Required for learner accounts (role CDD); optional for staff.
    learner_role: LearnerRoleField = None
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
    learner_role: LearnerRoleField = None
    clear_learner_role: bool = False
    # Confirms the learner role (even unchanged or none) and clears the review flag.
    learner_role_reviewed: bool = False
    status: UserStatus | None = None
    language_id: uuid.UUID | None = None
    # a boundary id sets the area; clear_boundary removes it
    boundary_id: uuid.UUID | None = None
    clear_boundary: bool = False
    # a session id moves the person to that training session; clear_session removes them from it
    training_session_id: uuid.UUID | None = None
    clear_session: bool = False
