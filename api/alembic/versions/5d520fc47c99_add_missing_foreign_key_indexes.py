"""Add missing foreign key indexes

Revision ID: 5d520fc47c99
Revises: 525db585ac79
Create Date: 2026-07-22 21:03:23.271467

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d520fc47c99'
down_revision = '525db585ac79'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add indexes for relationships heavily queried during API reads (e.g., getting a single case)
    op.create_index('ix_accused_case_master_id', 'accused', ['case_master_id'], unique=False)
    op.create_index('ix_properties_case_master_id', 'properties', ['case_master_id'], unique=False)
    op.create_index('ix_vehicles_case_master_id', 'vehicles', ['case_master_id'], unique=False)
    op.create_index('ix_victims_case_master_id', 'victims', ['case_master_id'], unique=False)
    op.create_index('ix_cases_police_station_id', 'cases', ['police_station_id'], unique=False)
    op.create_index('ix_units_district_id', 'units', ['district_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_units_district_id', table_name='units')
    op.drop_index('ix_cases_police_station_id', table_name='cases')
    op.drop_index('ix_victims_case_master_id', table_name='victims')
    op.drop_index('ix_vehicles_case_master_id', table_name='vehicles')
    op.drop_index('ix_properties_case_master_id', table_name='properties')
    op.drop_index('ix_accused_case_master_id', table_name='accused')
