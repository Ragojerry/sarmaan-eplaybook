"""sync idempotency keys (Phase 12)

Adds the keys that make offline uploads safe to retry:
  * ai_question_log.client_id  + unique (user_id, client_id)
  * analytics_events.client_id + unique (device_id, client_id)
  * unique (user_id, module_id) on user_module_progress

NULL client_id rows (written by the online /ai/ask path) never collide,
because Postgres treats NULLs as distinct in unique constraints.

Revision ID: b5d2f8a91c37
Revises: a7c3e91d2b54
"""
from alembic import op
import sqlalchemy as sa

revision = "b5d2f8a91c37"
down_revision = "a7c3e91d2b54"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_question_log", sa.Column("client_id", sa.String(length=80), nullable=True))
    op.create_unique_constraint("uq_ai_question_user_client", "ai_question_log", ["user_id", "client_id"])

    op.add_column("analytics_events", sa.Column("client_id", sa.String(length=80), nullable=True))
    op.create_unique_constraint("uq_analytics_device_client", "analytics_events", ["device_id", "client_id"])

    # Defensive: collapse any pre-existing duplicate (user, module) rows, keeping the most recently updated.
    op.execute(
        """
        DELETE FROM user_module_progress a
        USING user_module_progress b
        WHERE a.user_id = b.user_id AND a.module_id = b.module_id
          AND (a.updated_at, a.id) < (b.updated_at, b.id)
        """
    )
    op.create_unique_constraint("uq_progress_user_module", "user_module_progress", ["user_id", "module_id"])


def downgrade() -> None:
    op.drop_constraint("uq_progress_user_module", "user_module_progress", type_="unique")
    op.drop_constraint("uq_analytics_device_client", "analytics_events", type_="unique")
    op.drop_column("analytics_events", "client_id")
    op.drop_constraint("uq_ai_question_user_client", "ai_question_log", type_="unique")
    op.drop_column("ai_question_log", "client_id")
