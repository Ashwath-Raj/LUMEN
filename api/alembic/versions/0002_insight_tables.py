"""Session 8 — intelligence tables (§3.6: lumen_insight, lumen_model_registry)

Adds the two §3.6 platform tables Session 8 (§8–§10) requires:
  * `lumen_insight` — persisted InsightContract v1 rows (§8 model, §10
    lifecycle, §10 approval record).
  * `lumen_model_registry` — required by §8 invariant 5
    ("lineage.model_version exists in lumen_model_registry"); the registry
    MODULE remains Session 22, only the table lands here.

Revision ID: 0002_insight_tables
Revises: 0001_canonical_baseline
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_insight_tables"
down_revision = "0001_canonical_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_insight",
        sa.Column("insight_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=True),
        sa.Column("subject_type", sa.String(length=20), nullable=True),
        sa.Column("subject_id", sa.String(length=60), nullable=True),
        sa.Column("headline", sa.String(length=400), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("confidence_components", sa.JSON(), nullable=True),
        sa.Column("factors", sa.JSON(), nullable=True),
        sa.Column("counterfactuals", sa.JSON(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("limitations", sa.JSON(), nullable=True),
        sa.Column("lineage", sa.JSON(), nullable=True),
        sa.Column("contract_version", sa.String(length=10), nullable=True),
        sa.Column("lifecycle_state", sa.String(length=20), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.String(length=120), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("insight_id", name=op.f("pk_lumen_insight")),
    )
    op.create_table(
        "lumen_model_registry",
        sa.Column("model_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=True),
        sa.Column("version", sa.String(length=40), nullable=True),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("trained_at", sa.DateTime(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("model_id", name=op.f("pk_lumen_model_registry")),
    )


def downgrade() -> None:
    op.drop_table("lumen_model_registry")
    op.drop_table("lumen_insight")
