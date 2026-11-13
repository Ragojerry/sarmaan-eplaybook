"""Support contacts for the Support deck on the phone's Ask tab

Revision ID: a4d8e2c61f93
Revises: f9c2a6d4e815
Create Date: 2026-11-13 09:00:00.000000

Adds (nothing existing is changed or deleted):
  - the support_contact_type enum and the support_contacts table (empty);
  - audit actions SUPPORT_CONTACT_CREATE / _UPDATE / _REORDER / _ACTIVATE /
    _DEACTIVATE / _DELETE;
  - analytics event type SUPPORT_CONTACT_TAP (opt-in, contact type only).
The optional deck note is a platform_settings row, created when first saved.

Old app versions never call the new endpoint, so they keep working.

Rollback: `alembic downgrade f9c2a6d4e815` drops the table and its type (any
contacts entered in the portal are lost). The added enum values stay
(Postgres cannot drop enum values; unused values are harmless).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a4d8e2c61f93'
down_revision: Union[str, None] = 'f9c2a6d4e815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

contact_type = postgresql.ENUM('PHONE', 'SMS', 'EMAIL', 'WHATSAPP', 'LINK', name='support_contact_type', create_type=False)
AUDIT_ACTIONS = ('SUPPORT_CONTACT_CREATE', 'SUPPORT_CONTACT_UPDATE', 'SUPPORT_CONTACT_REORDER',
                 'SUPPORT_CONTACT_ACTIVATE', 'SUPPORT_CONTACT_DEACTIVATE', 'SUPPORT_CONTACT_DELETE')


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for value in AUDIT_ACTIONS:
            op.execute(f"ALTER TYPE audit_action ADD VALUE IF NOT EXISTS '{value}'")
        op.execute("ALTER TYPE analytics_event_type ADD VALUE IF NOT EXISTS 'SUPPORT_CONTACT_TAP'")

    contact_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'support_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', contact_type, nullable=False),
        sa.Column('label', sa.String(80), nullable=False),
        sa.Column('value', sa.String(500), nullable=False),
        sa.Column('whatsapp_message', sa.Text(), nullable=True),
        sa.Column('email_subject', sa.String(150), nullable=True),
        sa.Column('include_app_version', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('availability', sa.String(120), nullable=True),
        sa.Column('languages', sa.String(120), nullable=True),
        sa.Column('audience', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_support_contacts_updated_at', 'support_contacts', ['updated_at'])


def downgrade() -> None:
    op.drop_index('ix_support_contacts_updated_at', table_name='support_contacts')
    op.drop_table('support_contacts')
    contact_type.drop(op.get_bind(), checkfirst=True)
