"""Session 13 — knowledge base tables (§3.6: lumen_kb_document, lumen_kb_chunk)

The §15 corpus store: documents + chunks. `embedding_ref` is nullable and
unfilled at T1 (QuickML embedding is the Session 14+ boundary).

Revision ID: 0006_kb_tables
Revises: 0005_event_table
Create Date: 2026-07-24
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_kb_tables"
down_revision = "0005_event_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_kb_document",
        sa.Column("doc_id", sa.String(length=80), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("classification", sa.String(length=20), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("doc_id", name=op.f("pk_lumen_kb_document")),
    )
    op.create_table(
        "lumen_kb_chunk",
        sa.Column("chunk_id", sa.String(length=100), nullable=False),
        sa.Column("doc_id", sa.String(length=80), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("embedding_ref", sa.String(length=120), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["doc_id"], ["lumen_kb_document.doc_id"],
                                name=op.f("fk_lumen_kb_chunk_doc_id_lumen_kb_document")),
        sa.PrimaryKeyConstraint("chunk_id", name=op.f("pk_lumen_kb_chunk")),
    )


def downgrade() -> None:
    op.drop_table("lumen_kb_chunk")
    op.drop_table("lumen_kb_document")
