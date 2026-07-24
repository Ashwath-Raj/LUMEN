"""Session 15 — AI evaluation table (§3.6: lumen_ai_eval)

§17.4's scorecard store: one row per evaluated question per `make eval` run.

Revision ID: 0008_ai_eval
Revises: 0007_prompt_registry
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008_ai_eval"
down_revision = "0007_prompt_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_ai_eval",
        sa.Column("eval_id", sa.String(length=80), nullable=False),
        sa.Column("run_id", sa.String(length=80), nullable=True),
        sa.Column("question_id", sa.String(length=80), nullable=True),
        sa.Column("groundedness", sa.Float(), nullable=True),
        sa.Column("correctness", sa.Float(), nullable=True),
        sa.Column("hallucinated_ids", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("prompt_version", sa.String(length=20), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("eval_id", name=op.f("pk_lumen_ai_eval")),
    )


def downgrade() -> None:
    op.drop_table("lumen_ai_eval")
