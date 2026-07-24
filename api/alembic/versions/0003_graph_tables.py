"""Session 9 — graph tables (§3.6: lumen_graph_edge, lumen_person_metrics,
lumen_community)

Adds the three §3.6 graph platform tables §14's projection pipeline writes
("write lumen_graph_edge / lumen_person_metrics / lumen_community") and the
ten §14.4 queries read. §3.6 declares no PK for lumen_graph_edge — a composite
key over the five identity columns is used (§3.3 precedent).

Revision ID: 0003_graph_tables
Revises: 0002_insight_tables
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_graph_tables"
down_revision = "0002_insight_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_graph_edge",
        sa.Column("src_type", sa.String(length=20), nullable=False),
        sa.Column("src_id", sa.String(length=60), nullable=False),
        sa.Column("dst_type", sa.String(length=20), nullable=False),
        sa.Column("dst_id", sa.String(length=60), nullable=False),
        sa.Column("rel", sa.String(length=30), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("props", sa.JSON(), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("src_type", "src_id", "dst_type", "dst_id", "rel",
                                name=op.f("pk_lumen_graph_edge")),
    )
    op.create_table(
        "lumen_person_metrics",
        sa.Column("person_id", sa.String(length=36), nullable=False),
        sa.Column("degree", sa.Integer(), nullable=True),
        sa.Column("betweenness", sa.Float(), nullable=True),
        sa.Column("eigenvector", sa.Float(), nullable=True),
        sa.Column("community_id", sa.Integer(), nullable=True),
        sa.Column("district_span", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["lumen_person.person_id"],
                                name=op.f("fk_lumen_person_metrics_person_id_lumen_person")),
        sa.PrimaryKeyConstraint("person_id", name=op.f("pk_lumen_person_metrics")),
    )
    op.create_table(
        "lumen_community",
        sa.Column("community_id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("district_ids", sa.JSON(), nullable=True),
        sa.Column("broker_person_id", sa.String(length=60), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("community_id", name=op.f("pk_lumen_community")),
    )


def downgrade() -> None:
    op.drop_table("lumen_community")
    op.drop_table("lumen_person_metrics")
    op.drop_table("lumen_graph_edge")
