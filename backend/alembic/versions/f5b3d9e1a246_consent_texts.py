"""editable, translatable consent text

Revision ID: f5b3d9e1a246
Revises: e2a7c5d83f14
Create Date: 2026-11-04 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f5b3d9e1a246'
down_revision: Union[str, None] = 'e2a7c5d83f14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The text the app has shown so far (mobile/lib/screens/consent_screen.dart).
ENGLISH = {
    "language": "en",
    "title": "Before you start",
    "body": (
        "This app is used to deliver AZM training content to Community Drug Distributors. "
        "Your training progress and the questions you ask in the app are linked to your account and "
        "uploaded when you are online, so your supervisor and the programme team can support you. "
        "Module content is downloaded to this device so you can keep working without an internet connection."
    ),
    "usage_label": "Also share anonymous usage statistics (optional)",
    "button_label": "Agree and continue",
    "version": 1,
}


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'CONSENT_UPDATE'")
    table = op.create_table(
        'consent_texts',
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('usage_label', sa.String(length=255), nullable=False),
        sa.Column('button_label', sa.String(length=60), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('source_version', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('language'),
    )
    op.bulk_insert(table, [ENGLISH])


def downgrade() -> None:
    op.drop_table('consent_texts')
