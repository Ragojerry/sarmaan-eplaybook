"""User deactivation: who, when and why (Item 2)

Revision ID: d4f8a3b25c61
Revises: c2d7e9a14b38
Create Date: 2026-11-13 14:10:00.000000

Reuses the existing users.status (ACTIVE / INACTIVE / SUSPENDED). Adds three
nullable columns (deactivated_at, deactivated_by, deactivation_reason) and the
audit actions USER_DEACTIVATE / USER_REACTIVATE. Existing rows are untouched
(all NULL); no user or record is deleted.

Rollback: `alembic downgrade c2d7e9a14b38` drops the three columns (the recorded
reasons are lost; statuses stay). The enum values stay (Postgres cannot drop them).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd4f8a3b25c61'
down_revision: Union[str, None] = 'c2d7e9a14b38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'USER_DEACTIVATE'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'USER_REACTIVATE'")
    op.add_column('users', sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deactivated_by', postgresql.UUID(as_uuid=True),
                                     sa.ForeignKey('users.id', ondelete='SET NULL', name='fk_users_deactivated_by'), nullable=True))
    op.add_column('users', sa.Column('deactivation_reason', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_constraint('fk_users_deactivated_by', 'users', type_='foreignkey')
    op.drop_column('users', 'deactivation_reason')
    op.drop_column('users', 'deactivated_by')
    op.drop_column('users', 'deactivated_at')
