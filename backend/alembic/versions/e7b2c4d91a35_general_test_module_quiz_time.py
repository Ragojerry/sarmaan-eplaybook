"""General pre/post test, inline module quizzes and time per module; per-module tests archived

Revision ID: e7b2c4d91a35
Revises: d2a6f1c84e57
Create Date: 2026-11-10 21:00:00.000000

Adds (nothing is deleted):
  - enum values: content_type TRUE_FALSE (inline quiz statement), test_type MODULE_QUIZ,
    audit_action GENERAL_TEST_UPDATE and SETTING_CHANGE;
  - tables general_test_questions, general_test_attempts and platform_settings
    (module_min_seconds = 180, general_test_active = false);
  - user_module_progress.seconds_spent (0 for existing rows) and quiz_questions.archived_at.

Archives every active per-module pre/post question: is_active = false and archived_at = now.
The rows and every old attempt stay; one audit entry lists the archived question ids.

Rollback: `alembic downgrade d2a6f1c84e57` re-activates the questions this migration archived
and drops the new tables and columns (General test results and time spent are lost).
Postgres cannot drop enum values; unused values are harmless.
"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'e7b2c4d91a35'
down_revision: Union[str, None] = 'd2a6f1c84e57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE content_type ADD VALUE IF NOT EXISTS 'TRUE_FALSE'")
        op.execute("ALTER TYPE test_type ADD VALUE IF NOT EXISTS 'MODULE_QUIZ'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'GENERAL_TEST_UPDATE'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'SETTING_CHANGE'")

    op.add_column("user_module_progress",
                  sa.Column("seconds_spent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("quiz_questions", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "general_test_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("number", sa.Integer(), nullable=False, unique=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=True),
        sa.Column("cdd_specific", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "general_test_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("client_id", sa.String(80), nullable=False),
        sa.Column("test_type", postgresql.ENUM(name="test_type", create_type=False), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("score_percent", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("invalid_reason", sa.String(120), nullable=True),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "client_id", name="uq_general_test_attempt_client"),
    )
    settings = op.create_table(
        "platform_settings",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.bulk_insert(settings, [
        {"key": "module_min_seconds", "value": 180, "note": "Minimum active time in a module before it can be completed"},
        {"key": "general_test_active", "value": False, "note": "General pre-test gate and post-test (off until the answer key is loaded)"},
    ])

    conn = op.get_bind()
    ids = [str(r[0]) for r in conn.execute(sa.text(
        "UPDATE quiz_questions SET is_active = false, archived_at = now() "
        "WHERE is_active AND archived_at IS NULL RETURNING id"))]
    if ids:
        conn.execute(sa.text(
            "INSERT INTO audit_logs (id, action, entity_type, details, created_at) "
            "VALUES (gen_random_uuid(), 'CONTENT_EDIT', 'quiz_questions_archived', CAST(:d AS jsonb), now())"),
            {"d": json.dumps({"reason": "per-module pre/post tests replaced by the General test and inline module quizzes",
                              "via": "alembic e7b2c4d91a35", "count": len(ids), "question_ids": ids})})


def downgrade() -> None:
    op.execute("UPDATE quiz_questions SET is_active = true WHERE archived_at IS NOT NULL")
    op.drop_table("platform_settings")
    op.drop_table("general_test_attempts")
    op.drop_table("general_test_questions")
    op.drop_column("quiz_questions", "archived_at")
    op.drop_column("user_module_progress", "seconds_spent")
