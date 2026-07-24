"""Session 16 — policy/access tables (§3.6: lumen_audit, lumen_user_role)

The §20/§21 access-control store: the append-only audit log and the user-role
scope table. `lumen_policy` has no §3.6 DDL and is deliberately not created
(the §20.1 role policy is code-defined).

Revision ID: 0009_policy_tables
Revises: 0008_ai_eval
Create Date: 2026-07-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0009_policy_tables"
down_revision = "0008_ai_eval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lumen_audit",
        sa.Column("audit_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=60), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=True),
        sa.Column("resource", sa.String(length=120), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("reason", sa.String(length=300), nullable=True),
        sa.Column("ip", sa.String(length=60), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("audit_id", name=op.f("pk_lumen_audit")),
    )
    op.create_table(
        "lumen_user_role",
        sa.Column("user_id", sa.String(length=60), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=True),
        sa.Column("district_scope", sa.JSON(), nullable=True),
        sa.Column("unit_scope", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_lumen_user_role")),
    )


def downgrade() -> None:
    op.drop_table("lumen_user_role")
    op.drop_table("lumen_audit")
