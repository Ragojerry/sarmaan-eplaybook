"""audit actions + reporting indexes (Phase 13)

* new audit_action values: LOGIN_FAILED, VIDEO_UPLOAD, VIDEO_UPDATE
* indexes backing the audit-log filters and the usage reports

Postgres cannot drop an enum value, so downgrade leaves the three values in
place (harmless) and drops only the indexes.

Revision ID: c8e4a1f06d52
Revises: b5d2f8a91c37
"""
from alembic import op

revision = "c8e4a1f06d52"
down_revision = "b5d2f8a91c37"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for value in ("LOGIN_FAILED", "VIDEO_UPLOAD", "VIDEO_UPDATE"):
            op.execute(f"ALTER TYPE audit_action ADD VALUE IF NOT EXISTS '{value}'")
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_analytics_events_occurred_at", "analytics_events", ["occurred_at"])
    op.create_index("ix_analytics_events_type_occurred", "analytics_events", ["event_type", "occurred_at"])
    op.create_index("ix_ai_question_log_asked_at", "ai_question_log", ["asked_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_question_log_asked_at", table_name="ai_question_log")
    op.drop_index("ix_analytics_events_type_occurred", table_name="analytics_events")
    op.drop_index("ix_analytics_events_occurred_at", table_name="analytics_events")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
