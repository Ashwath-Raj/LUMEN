"""Session 10 — prediction tables (§3.6: lumen_hotspot, lumen_district_risk)

The two §3.6 "geo / prediction" tables §13's batch scorers write and the API
reads. §3.6 declares no PK for lumen_district_risk — composite
(district_id, window_start) per the §3.3 precedent.

Revision ID: 0004_prediction_tables
Revises: 0003_graph_tables
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_prediction_tables"
down_revision = "0003_graph_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_hotspot",
        sa.Column("cluster_id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=True),
        sa.Column("centroid_lng", sa.Float(), nullable=True),
        sa.Column("radius_m", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("district_id", sa.Integer(), nullable=True),
        sa.Column("crime_head_id", sa.Integer(), nullable=True),
        sa.Column("window_start", sa.Date(), nullable=True),
        sa.Column("window_end", sa.Date(), nullable=True),
        sa.Column("method", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(["district_id"], ["District.DistrictID"],
                                name=op.f("fk_lumen_hotspot_district_id_District")),
        sa.ForeignKeyConstraint(["crime_head_id"], ["CrimeHead.CrimeHeadID"],
                                name=op.f("fk_lumen_hotspot_crime_head_id_CrimeHead")),
        sa.PrimaryKeyConstraint("cluster_id", name=op.f("pk_lumen_hotspot")),
    )
    op.create_table(
        "lumen_district_risk",
        sa.Column("district_id", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.Date(), nullable=False),
        sa.Column("band", sa.String(length=20), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("factors", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(["district_id"], ["District.DistrictID"],
                                name=op.f("fk_lumen_district_risk_district_id_District")),
        sa.PrimaryKeyConstraint("district_id", "window_start",
                                name=op.f("pk_lumen_district_risk")),
    )


def downgrade() -> None:
    op.drop_table("lumen_district_risk")
    op.drop_table("lumen_hotspot")
