"""user team code

Revision ID: e6b3d8a27f19
Revises: d3a7f95b1c48
Create Date: 2026-10-28 00:40:36.044105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6b3d8a27f19'
down_revision: Union[str, None] = 'd3a7f95b1c48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres cannot drop an enum value, so downgrade leaves USER_UPDATE in place (harmless).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'USER_UPDATE'")
    op.add_column('users', sa.Column('team_code', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'team_code')
