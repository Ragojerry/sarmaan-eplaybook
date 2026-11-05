"""100% pre-tests are auto-approved: drop the manual test exceptions

Revision ID: b4e9d2a71c58
Revises: a3c8e4f61b29
Create Date: 2026-11-05 09:00:00.000000

A learner whose pre-test was 100% is now auto-approved by a post-test at the
threshold in the POST_TEST_AUTO_APPROVE_PERCENT setting (90), so the manual
exception table and its audit entries are no longer used.

Nothing is deleted silently: if any exception or audit entry for one exists,
the upgrade stops and says so (decide what to keep, then run it again).
The audit_action enum keeps its old value (Postgres cannot drop enum values).

Rollback: `alembic downgrade a3c8e4f61b29` recreates the empty table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4e9d2a71c58'
down_revision: Union[str, None] = 'a3c8e4f61b29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    exceptions = bind.execute(sa.text("SELECT count(*) FROM test_exceptions")).scalar()
    audits = bind.execute(sa.text("SELECT count(*) FROM audit_logs WHERE action::text = 'TEST_EXCEPTION_APPROVE'")).scalar()
    if exceptions or audits:
        raise RuntimeError(
            f"{exceptions} approved test exception(s) and {audits} audit entr(ies) exist; "
            "export them before removing manual approvals, then run the upgrade again."
        )
    op.drop_index('ix_test_exceptions_user_id', table_name='test_exceptions')
    op.drop_table('test_exceptions')


def downgrade() -> None:
    op.create_table(
        'test_exceptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('approved_by', sa.UUID(), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'module_id', name='uq_test_exception_user_module'),
    )
    op.create_index('ix_test_exceptions_user_id', 'test_exceptions', ['user_id'])
