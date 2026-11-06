"""Module completion credits: completions given from an older module

Revision ID: c7d1e5a93f20
Revises: b4e9d2a71c58
Create Date: 2026-11-06 12:00:00.000000

Adds one table. Nothing existing is changed: old progress and quiz attempts
stay exactly as they are; a credit is stored alongside them.

Rollback: `alembic downgrade b4e9d2a71c58` drops the table. Progress rows
the credit script marked completed stay completed; to undo those as well,
run scripts/credit_hfw_modules.py --undo <run_id> BEFORE downgrading.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c7d1e5a93f20'
down_revision: Union[str, None] = 'b4e9d2a71c58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'module_completion_credits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_module_code', sa.String(length=20), nullable=False),
        sa.Column('source_completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_score_percent', sa.Integer(), nullable=True),
        sa.Column('run_id', sa.String(length=40), nullable=False),
        sa.Column('progress_existed', sa.Boolean(), nullable=False),
        sa.Column('previous_progress_percent', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id']),
        sa.ForeignKeyConstraint(['source_module_id'], ['modules.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'module_id', name='uq_credit_user_module'),
    )
    op.create_index('ix_module_completion_credits_user_id', 'module_completion_credits', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_module_completion_credits_user_id', table_name='module_completion_credits')
    op.drop_table('module_completion_credits')
