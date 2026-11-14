"""Portal pages ticked per account (users.admin_pages)

Revision ID: a6d2e8f41c93
Revises: e5a9c4d36f72
Create Date: 2026-11-14 15:00:00.000000

Adds users.admin_pages (nullable text array). Every existing account keeps
NULL, which means every page its role allows, so nobody's access changes. A
super admin can then tick the pages an account sees (app/auth/pages.py).

Rollback: `alembic downgrade e5a9c4d36f72` drops the column; every account goes
back to every page its role allows.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a6d2e8f41c93'
down_revision: Union[str, None] = 'e5a9c4d36f72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('admin_pages', postgresql.ARRAY(sa.String(length=40)), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'admin_pages')
