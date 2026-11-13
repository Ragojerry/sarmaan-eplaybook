"""Tools repository: Tools modules assigned to learner roles, and their links

Revision ID: b6e1f4a92c07
Revises: a4d8e2c61f93
Create Date: 2026-11-13 12:00:00.000000

Adds (nothing existing is changed or deleted; no training table is touched):
  - the tool_item_type enum and the tool_modules and tool_items tables (empty);
    tool_modules reuses the existing module_audience enum for role assignment;
  - audit actions TOOL_CREATE / _UPDATE / _REORDER / _ACTIVATE / _DEACTIVATE /
    _DELETE / _IMPORT;
  - analytics event type TOOL_OPEN (opt-in, item id only).

Old app versions never call the new endpoint, so they keep working.

Rollback: `alembic downgrade a4d8e2c61f93` drops both tables and the type (any
Tools modules and links entered in the portal are lost). The added enum values
stay (Postgres cannot drop enum values; unused values are harmless).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'b6e1f4a92c07'
down_revision: Union[str, None] = 'a4d8e2c61f93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

item_type = postgresql.ENUM('DOCUMENT', 'SPREADSHEET', 'PRESENTATION', 'PDF', 'IMAGE', 'VIDEO_LINK', 'WEBSITE', 'FORM', 'OTHER',
                            name='tool_item_type', create_type=False)
audience = postgresql.ENUM('GENERAL', 'ROLE_SPECIFIC', name='module_audience', create_type=False)
AUDIT_ACTIONS = ('TOOL_CREATE', 'TOOL_UPDATE', 'TOOL_REORDER', 'TOOL_ACTIVATE', 'TOOL_DEACTIVATE', 'TOOL_DELETE', 'TOOL_IMPORT')


def _who():
    return [
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for value in AUDIT_ACTIONS:
            op.execute(f"ALTER TYPE audit_action ADD VALUE IF NOT EXISTS '{value}'")
        op.execute("ALTER TYPE analytics_event_type ADD VALUE IF NOT EXISTS 'TOOL_OPEN'")

    item_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'tool_modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('audience', audience, nullable=False, server_default='GENERAL'),
        sa.Column('learner_roles', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        *_who(),
    )
    op.create_table(
        'tool_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_module_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tool_modules.id'), nullable=False),
        sa.Column('title', sa.String(150), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('type', item_type, nullable=False),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('host', sa.String(20), nullable=True),
        sa.Column('category', sa.String(80), nullable=True),
        sa.Column('languages', sa.String(120), nullable=True),
        sa.Column('audience', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_reviewed', sa.Date(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        *_who(),
    )
    op.create_index('ix_tool_items_tool_module_id', 'tool_items', ['tool_module_id'])
    op.create_index('ix_tool_items_updated_at', 'tool_items', ['updated_at'])


def downgrade() -> None:
    op.drop_index('ix_tool_items_updated_at', table_name='tool_items')
    op.drop_index('ix_tool_items_tool_module_id', table_name='tool_items')
    op.drop_table('tool_items')
    op.drop_table('tool_modules')
    item_type.drop(op.get_bind(), checkfirst=True)
