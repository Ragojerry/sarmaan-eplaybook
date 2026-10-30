import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEntry(BaseModel):
    id: uuid.UUID
    created_at: datetime
    action: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    details: dict[str, Any]
    ip_address: str | None
    user_id: uuid.UUID | None
    username: str | None
    user_role: str | None


class AuditPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[AuditEntry]
