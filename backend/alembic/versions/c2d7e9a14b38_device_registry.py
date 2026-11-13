"""Device registry: the app installs each account uses (Item 1)

Revision ID: c2d7e9a14b38
Revises: b6e1f4a92c07
Create Date: 2026-11-13 14:00:00.000000

Adds one empty table, devices (nothing existing is changed or deleted). Rows
appear when app 0.1.16+ logs in or syncs; older apps keep working without one.

Rollback: `alembic downgrade b6e1f4a92c07` drops the table (the device list is
lost; no user, attempt or progress record is touched).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c2d7e9a14b38'
down_revision: Union[str, None] = 'b6e1f4a92c07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('install_id', sa.String(64), nullable=False),
        sa.Column('os', sa.String(20), nullable=True),
        sa.Column('os_version', sa.String(120), nullable=True),
        sa.Column('model', sa.String(120), nullable=True),
        sa.Column('app_version', sa.String(40), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('user_id', 'install_id', name='uq_devices_user_install'),
    )
    op.create_index('ix_devices_user_id', 'devices', ['user_id'])
    op.create_index('ix_devices_last_seen_at', 'devices', ['last_seen_at'])


def downgrade() -> None:
    op.drop_index('ix_devices_last_seen_at', table_name='devices')
    op.drop_index('ix_devices_user_id', table_name='devices')
    op.drop_table('devices')
