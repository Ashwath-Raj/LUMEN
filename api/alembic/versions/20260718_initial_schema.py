from alembic import op
import sqlalchemy as sa

revision = '20260718_initial_schema'
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        'operators',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('clearance', sa.String(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('rank', sa.String(), nullable=False),
        sa.Column('date_of_entry', sa.String(), nullable=False),
        sa.Column('biometric_hash', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('operator_id', sa.String(), nullable=False),
        sa.Column('assigned_unit', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_operators_id'), 'operators', ['id'], unique=False)
    op.create_unique_constraint(None, 'operators', ['operator_id'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('operator_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_unique_constraint(None, 'refresh_tokens', ['token_hash'])


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('operators')
