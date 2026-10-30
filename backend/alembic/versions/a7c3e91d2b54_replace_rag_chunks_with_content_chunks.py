"""replace rag_chunks (pgvector) with content_chunks (extractive search)

Revision ID: a7c3e91d2b54
Revises: 6dab31114b5b
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy

revision: str = 'a7c3e91d2b54'
down_revision: Union[str, None] = '6dab31114b5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'content_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('module_code', sa.String(length=20), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=True),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('source_title', sa.String(length=255), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id']),
        sa.ForeignKeyConstraint(['section_id'], ['content_sections.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_content_chunks_module_language', 'content_chunks', ['module_id', 'language'])
    # rag_chunks was schema-only (never populated) — safe to drop.
    op.drop_table('rag_chunks')


def downgrade() -> None:
    op.create_table(
        'rag_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('module_id', sa.UUID(), nullable=False),
        sa.Column('module_code', sa.String(length=20), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=True),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('release_id', sa.UUID(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('content_version', sa.Integer(), nullable=False),
        sa.Column('approval_status', sa.String(length=30), nullable=False),
        sa.Column('source_title', sa.String(length=255), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(384), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id']),
        sa.ForeignKeyConstraint(['section_id'], ['content_sections.id']),
        sa.ForeignKeyConstraint(['release_id'], ['content_releases.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.drop_index('ix_content_chunks_module_language', table_name='content_chunks')
    op.drop_table('content_chunks')
