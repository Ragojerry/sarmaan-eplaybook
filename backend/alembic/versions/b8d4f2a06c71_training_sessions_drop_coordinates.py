"""training sessions, drop coordinates

Revision ID: b8d4f2a06c71
Revises: a7c2e5d91f33
Create Date: 2026-10-28 18:23:31.299275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d4f2a06c71'
down_revision: Union[str, None] = 'a7c2e5d91f33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres cannot drop enum values, so the audit value stays on downgrade (harmless).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'SESSION_CHANGE'")
    op.create_table('training_sessions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('end_date >= start_date', name='ck_training_sessions_dates'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.drop_column('admin_boundaries', 'longitude')
    op.drop_column('admin_boundaries', 'latitude')
    op.add_column('users', sa.Column('training_session_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_users_training_session_id'), 'users', ['training_session_id'], unique=False)
    op.create_foreign_key('fk_users_training_session_id', 'users', 'training_sessions', ['training_session_id'], ['id'])
    op.drop_column('users', 'longitude')
    op.drop_column('users', 'latitude')


def downgrade() -> None:
    op.add_column('users', sa.Column('latitude', sa.NUMERIC(precision=9, scale=6), nullable=True))
    op.add_column('users', sa.Column('longitude', sa.NUMERIC(precision=9, scale=6), nullable=True))
    op.drop_constraint('fk_users_training_session_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_training_session_id'), table_name='users')
    op.drop_column('users', 'training_session_id')
    op.add_column('admin_boundaries', sa.Column('latitude', sa.NUMERIC(precision=9, scale=6), nullable=True))
    op.add_column('admin_boundaries', sa.Column('longitude', sa.NUMERIC(precision=9, scale=6), nullable=True))
    op.drop_table('training_sessions')
