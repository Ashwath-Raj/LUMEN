"""Session 19 — feature store table (§3.6: lumen_feature)

§12's single feature table. §3.6 declares no PK; composite
(entity_type, entity_id, feature_name, version) per the §3.3 precedent.

Revision ID: 0011_feature_table
Revises: 0010_service_registry
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0011_feature_table"
down_revision = "0010_service_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_feature",
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.String(length=60), nullable=False),
        sa.Column("feature_name", sa.String(length=60), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("entity_type", "entity_id", "feature_name",
                                "version", name=op.f("pk_lumen_feature")),
    )


def downgrade() -> None:
    op.drop_table("lumen_feature")
