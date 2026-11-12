"""Mobile app interface text: string registry and per-language translations

Revision ID: f9c2a6d4e815
Revises: e7b2c4d91a35
Create Date: 2026-11-12 09:00:00.000000

Adds two new tables (nothing existing is changed or deleted):
  - app_strings: one row per interface string of the mobile app (key, English,
    translator note, placeholders, plural singular form, English version);
  - app_string_translations: one row per string and language, with the content
    governance status, who edited and reviewed it, and the last published text.
Reuses the existing content_review_status enum type.

The registry starts empty. Fill it with `python -m app.l10n.seed` (English only;
safe to run again after every app change).

Rollback: `alembic downgrade e7b2c4d91a35` drops both tables (any app-text
translations entered in the portal are lost; nothing else is touched).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'f9c2a6d4e815'
down_revision: Union[str, None] = 'e7b2c4d91a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

review_status = postgresql.ENUM(
    'DRAFT', 'PROGRAMME_REVIEW', 'LOCALISATION_REVIEW', 'TECHNICAL_QA', 'PUBLISHED', 'REJECTED',
    name='content_review_status', create_type=False,
)


def upgrade() -> None:
    op.create_table(
        'app_strings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(150), nullable=False, unique=True),
        sa.Column('english', sa.Text(), nullable=False),
        sa.Column('english_one', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=False, server_default=''),
        sa.Column('placeholders', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('source_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        'app_string_translations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('string_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_strings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('language_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('languages.id'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('text_one', sa.Text(), nullable=True),
        sa.Column('status', review_status, nullable=False, server_default='DRAFT'),
        sa.Column('source_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('edited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_text', sa.Text(), nullable=True),
        sa.Column('published_text_one', sa.Text(), nullable=True),
        sa.Column('published_source_version', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('string_id', 'language_id', name='uq_app_string_translation_lang'),
    )
    op.create_index('ix_app_string_translations_string_id', 'app_string_translations', ['string_id'])
    op.create_index('ix_app_string_translations_language_id', 'app_string_translations', ['language_id'])
    op.create_index('ix_app_string_translations_published_at', 'app_string_translations', ['published_at'])


def downgrade() -> None:
    op.drop_index('ix_app_string_translations_published_at', table_name='app_string_translations')
    op.drop_index('ix_app_string_translations_language_id', table_name='app_string_translations')
    op.drop_index('ix_app_string_translations_string_id', table_name='app_string_translations')
    op.drop_table('app_string_translations')
    op.drop_table('app_strings')
