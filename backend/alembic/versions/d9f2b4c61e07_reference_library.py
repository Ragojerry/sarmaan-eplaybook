"""reference library

Revision ID: d9f2b4c61e07
Revises: c9e5a3b17d82
Create Date: 2026-11-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd9f2b4c61e07'
down_revision: Union[str, None] = 'c9e5a3b17d82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres cannot drop enum values, so the audit values stay on downgrade (harmless).
    with op.get_context().autocommit_block():
        for value in ("REFERENCE_UPLOAD", "REFERENCE_UPDATE"):
            op.execute(f"ALTER TYPE audit_action ADD VALUE IF NOT EXISTS '{value}'")

    op.create_table(
        'reference_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('status', postgresql.ENUM('DRAFT', 'APPROVED', 'ARCHIVED', name='reference_status'), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'reference_passages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('heading', sa.String(length=255), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['reference_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reference_passages_document', 'reference_passages', ['document_id'])


def downgrade() -> None:
    op.drop_index('ix_reference_passages_document', table_name='reference_passages')
    op.drop_table('reference_passages')
    op.drop_table('reference_documents')
    op.execute("DROP TYPE IF EXISTS reference_status")
