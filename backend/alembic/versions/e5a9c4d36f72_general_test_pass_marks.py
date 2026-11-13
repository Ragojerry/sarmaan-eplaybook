"""General pre/post-test pass mark stored with each attempt (Item 3)

Revision ID: e5a9c4d36f72
Revises: d4f8a3b25c61
Create Date: 2026-11-13 14:20:00.000000

Adds general_test_attempts.pass_mark (nullable). Existing attempts keep NULL:
they are never recalculated, and their certificate rule stays 90%. The pass
marks themselves are platform_settings rows (general_pass_mark_cdd = 60,
general_pass_mark_other = 80), read with those defaults until an admin saves
them, so no row is inserted here. Module quizzes are not touched.

Rollback: `alembic downgrade d4f8a3b25c61` drops the column (the stored marks
are lost; scores stay).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e5a9c4d36f72'
down_revision: Union[str, None] = 'd4f8a3b25c61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('general_test_attempts', sa.Column('pass_mark', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('general_test_attempts', 'pass_mark')
