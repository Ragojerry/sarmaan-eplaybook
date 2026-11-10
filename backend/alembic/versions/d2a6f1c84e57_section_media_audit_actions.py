"""Audit actions for audio/video files uploaded to and removed from content sections

Revision ID: d2a6f1c84e57
Revises: b4e9d2a71c58
Create Date: 2026-11-10 09:00:00.000000

Only adds two values to the audit_action enum (MEDIA_UPLOAD, MEDIA_REMOVE).
No table or existing row changes, so it is safe on existing data. AUDIO/VIDEO
section types and media asset types already exist.

Rollback: `alembic downgrade b4e9d2a71c58` is a no-op (Postgres cannot drop
enum values; unused values are harmless).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd2a6f1c84e57'
down_revision: Union[str, None] = 'b4e9d2a71c58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'MEDIA_UPLOAD'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'MEDIA_REMOVE'")


def downgrade() -> None:
    pass
