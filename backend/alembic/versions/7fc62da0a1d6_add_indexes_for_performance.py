"""add_indexes_for_performance

Revision ID: 7fc62da0a1d6
Revises: 5d520fc47c99
Create Date: 2026-07-22 23:49:24.893908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fc62da0a1d6'
down_revision = '5d520fc47c99'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add indexes for performance optimization in analytics and dashboard
    op.create_index('ix_cases_crime_registered_date', 'cases', ['crime_registered_date'], unique=False)
    op.create_index('ix_cases_status', 'cases', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cases_status', table_name='cases')
    op.drop_index('ix_cases_crime_registered_date', table_name='cases')
