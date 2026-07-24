"""Session 12 — event store table (§3.6: lumen_event)

The §3.6 append-only event store. Every event lands here (the replay log)
and on the bus (§19.2). §21: append-only, enforced in the repository layer.

Revision ID: 0005_event_table
Revises: 0004_prediction_tables
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_event_table"
down_revision = "0004_prediction_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_event",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=True),
        sa.Column("event_version", sa.String(length=10), nullable=True),
        sa.Column("actor_id", sa.String(length=60), nullable=True),
        sa.Column("subject_type", sa.String(length=20), nullable=True),
        sa.Column("subject_id", sa.String(length=60), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("trace_id", sa.String(length=36), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk_lumen_event")),
    )


def downgrade() -> None:
    op.drop_table("lumen_event")
