"""Session 14 — prompt registry table (§3.6: lumen_prompt_registry)

§16.3's registry: versioned prompt files hashed in at startup.

Revision ID: 0007_prompt_registry
Revises: 0006_kb_tables
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_prompt_registry"
down_revision = "0006_kb_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_prompt_registry",
        sa.Column("prompt_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("template_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("prompt_id", name=op.f("pk_lumen_prompt_registry")),
    )


def downgrade() -> None:
    op.drop_table("lumen_prompt_registry")
