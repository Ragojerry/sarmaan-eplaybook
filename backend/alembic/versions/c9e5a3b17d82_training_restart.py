"""training restart

Revision ID: c9e5a3b17d82
Revises: b8d4f2a06c71
Create Date: 2026-10-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9e5a3b17d82'
down_revision: Union[str, None] = 'b8d4f2a06c71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres cannot drop enum values, so the audit value stays on downgrade (harmless).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'TRAINING_RESTART'")
    op.add_column('users', sa.Column('training_attempt', sa.Integer(), server_default='1', nullable=False))
    op.add_column('users', sa.Column('training_restarted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'training_restarted_at')
    op.drop_column('users', 'training_attempt')
