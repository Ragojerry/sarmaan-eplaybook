"""curated answers (faq_entries)

Revision ID: e2a7c5d83f14
Revises: d9f2b4c61e07
Create Date: 2026-11-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'e2a7c5d83f14'
down_revision: Union[str, None] = 'd9f2b4c61e07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres cannot drop enum values, so the audit values stay on downgrade (harmless).
    with op.get_context().autocommit_block():
        for value in ("FAQ_CREATE", "FAQ_UPDATE"):
            op.execute(f"ALTER TYPE audit_action ADD VALUE IF NOT EXISTS '{value}'")

    op.create_table(
        'faq_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('question', sa.String(length=500), nullable=False),
        sa.Column('alternates', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('status', postgresql.ENUM('DRAFT', 'APPROVED', 'ARCHIVED', name='faq_status'), nullable=False),
        sa.Column('source_question', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_faq_entries_status_language', 'faq_entries', ['status', 'language'])


def downgrade() -> None:
    op.drop_index('ix_faq_entries_status_language', table_name='faq_entries')
    op.drop_table('faq_entries')
    op.execute("DROP TYPE IF EXISTS faq_status")
