"""Videos on demand: S3 storage key, file version, required_for_completion

Revision ID: b8f4c2d7e051
Revises: a6d2e8f41c93
Create Date: 2026-11-14 18:00:00.000000

Adds videos.storage_key (S3 object, NULL until uploaded there), videos.version
(1, raised when the file is replaced) and videos.required_for_completion (false;
nothing reads it). videos.file_size becomes BIGINT. Adds the DOWNLOAD_COMPLETED
analytics event. Existing rows keep working unchanged.

Rollback: `alembic downgrade a6d2e8f41c93` drops the three columns and turns
file_size back into INTEGER (fine for files under 2 GB). The enum value stays
(Postgres cannot drop one); it is harmless.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b8f4c2d7e051'
down_revision: Union[str, None] = 'a6d2e8f41c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('storage_key', sa.String(length=500), nullable=True))
    op.add_column('videos', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('videos', sa.Column('required_for_completion', sa.Boolean(), nullable=False, server_default='false'))
    op.alter_column('videos', 'file_size', type_=sa.BigInteger(), existing_type=sa.Integer(), existing_nullable=True)
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE analytics_event_type ADD VALUE IF NOT EXISTS 'DOWNLOAD_COMPLETED'")


def downgrade() -> None:
    op.alter_column('videos', 'file_size', type_=sa.Integer(), existing_type=sa.BigInteger(), existing_nullable=True)
    op.drop_column('videos', 'required_for_completion')
    op.drop_column('videos', 'version')
    op.drop_column('videos', 'storage_key')
