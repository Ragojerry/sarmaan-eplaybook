"""learner roles, module audience, pre/post tests

Revision ID: a3c8e4f61b29
Revises: f5b3d9e1a246
Create Date: 2026-11-04 17:00:00.000000

Existing data is kept and mapped explicitly:
- users with role CDD get learner_role CDD (CDD was the only learner role);
  SUPERVISOR accounts may or may not be field learners, so they get no learner
  role and are flagged for review; other staff roles get none.
- every existing module stays visible to everyone (GENERAL) and is flagged for
  an administrator to confirm its audience.
- every existing quiz question serves both tests (BOTH).
- existing quiz attempts are kept as history but marked not valid (they were
  taken without a pre-test); completed modules stay completed.
- reading already recorded is kept and marked legacy_reading.

Rollback: `alembic downgrade f5b3d9e1a246` drops the new columns, the
test_exceptions table and the enum types. Learner roles, module audiences,
question usage, pre-test attempts' type and approved exceptions are lost, so
take a pg_dump first. Added audit_action values stay (Postgres cannot remove
enum values); they are harmless.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a3c8e4f61b29'
down_revision: Union[str, None] = 'f5b3d9e1a246'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_ATTEMPT = "legacy: taken before pre/post tests"

# The data mapping, kept apart so tests/test_learning.py can check it.
BACKFILL = [
    "UPDATE users SET learner_role = 'CDD' WHERE role = 'CDD' AND learner_role IS NULL",
    "UPDATE users SET learner_role_needs_review = true WHERE role = 'SUPERVISOR' AND learner_role IS NULL",
    "UPDATE modules SET audience_needs_review = true",
    f"UPDATE quiz_attempts SET valid = false, invalid_reason = '{LEGACY_ATTEMPT}'",
    "UPDATE user_module_progress SET reading_completed_at = COALESCE(completed_at, last_opened_at, updated_at), "
    "legacy_reading = true WHERE progress_percent >= 50 OR completed",
]

learner_role = postgresql.ENUM('CDD', 'HEALTH_WORKER', 'LOGISTICIAN', 'MONITOR_SUPERVISOR', 'OTHER', name='learner_role', create_type=False)
module_audience = postgresql.ENUM('GENERAL', 'ROLE_SPECIFIC', name='module_audience', create_type=False)
test_type = postgresql.ENUM('PRE', 'POST', name='test_type', create_type=False)
question_usage = postgresql.ENUM('BOTH', 'PRE', 'POST', name='question_usage', create_type=False)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'AUDIENCE_CHANGE'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'TEST_EXCEPTION_APPROVE'")
    bind = op.get_bind()
    for e in (learner_role, module_audience, test_type, question_usage):
        e.create(bind, checkfirst=True)

    op.add_column('users', sa.Column('learner_role', learner_role, nullable=True))
    op.add_column('users', sa.Column('learner_role_needs_review', sa.Boolean(), server_default='false', nullable=False))

    op.add_column('modules', sa.Column('audience', module_audience, server_default='GENERAL', nullable=False))
    op.add_column('modules', sa.Column('learner_roles', postgresql.JSONB(), server_default='[]', nullable=False))
    op.add_column('modules', sa.Column('audience_needs_review', sa.Boolean(), server_default='false', nullable=False))

    op.add_column('quiz_questions', sa.Column('usage', question_usage, server_default='BOTH', nullable=False))

    op.add_column('quiz_attempts', sa.Column('test_type', test_type, server_default='POST', nullable=False))
    op.add_column('quiz_attempts', sa.Column('valid', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('quiz_attempts', sa.Column('invalid_reason', sa.String(length=120), nullable=True))

    op.add_column('user_module_progress', sa.Column('reading_completed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_module_progress', sa.Column('legacy_reading', sa.Boolean(), server_default='false', nullable=False))
    for statement in BACKFILL:
        op.execute(statement)

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


def downgrade() -> None:
    op.drop_index('ix_test_exceptions_user_id', table_name='test_exceptions')
    op.drop_table('test_exceptions')
    op.drop_column('user_module_progress', 'legacy_reading')
    op.drop_column('user_module_progress', 'reading_completed_at')
    op.drop_column('quiz_attempts', 'invalid_reason')
    op.drop_column('quiz_attempts', 'valid')
    op.drop_column('quiz_attempts', 'test_type')
    op.drop_column('quiz_questions', 'usage')
    op.drop_column('modules', 'audience_needs_review')
    op.drop_column('modules', 'learner_roles')
    op.drop_column('modules', 'audience')
    op.drop_column('users', 'learner_role_needs_review')
    op.drop_column('users', 'learner_role')
    bind = op.get_bind()
    for e in (question_usage, test_type, module_audience, learner_role):
        e.drop(bind, checkfirst=True)
