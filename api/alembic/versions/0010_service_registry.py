"""Session 17 — service registry table (§3.6: lumen_service_registry)

The §22 service registry. The other two registry tables (lumen_model_registry,
lumen_prompt_registry) already exist from Sessions 8 and 14 and are not
re-created.

Revision ID: 0010_service_registry
Revises: 0009_policy_tables
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0010_service_registry"
down_revision = "0009_policy_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_service_registry",
        sa.Column("service_id", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=True),
        sa.Column("capability", sa.String(length=120), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("endpoint", sa.String(length=200), nullable=True),
        sa.Column("depends_on", sa.JSON(), nullable=True),
        sa.Column("health_state", sa.String(length=20), nullable=True),
        sa.Column("last_check", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("service_id", name=op.f("pk_lumen_service_registry")),
    )


def downgrade() -> None:
    op.drop_table("lumen_service_registry")
