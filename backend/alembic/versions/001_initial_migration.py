"""Initial migration creating users, docking_jobs, and binding_affinity_predictions tables.

Revision ID: 001_initial
Revises: 
Create Date: 2026-07-13 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. Create docking_jobs table
    op.create_table(
        'docking_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('protein_path', sa.String(), nullable=False),
        sa.Column('ligand_path', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('output_directory', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_docking_jobs_id'), 'docking_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_docking_jobs_user_id'), 'docking_jobs', ['user_id'], unique=False)

    # 3. Create binding_affinity_predictions table
    op.create_table(
        'binding_affinity_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('smiles', sa.String(), nullable=False),
        sa.Column('protein_sequence', sa.String(), nullable=False),
        sa.Column('predicted_affinity', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_binding_affinity_predictions_id'), 'binding_affinity_predictions', ['id'], unique=False)
    op.create_index(op.f('ix_binding_affinity_predictions_user_id'), 'binding_affinity_predictions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_binding_affinity_predictions_user_id'), table_name='binding_affinity_predictions')
    op.drop_index(op.f('ix_binding_affinity_predictions_id'), table_name='binding_affinity_predictions')
    op.drop_table('binding_affinity_predictions')
    
    op.drop_index(op.f('ix_docking_jobs_user_id'), table_name='docking_jobs')
    op.drop_index(op.f('ix_docking_jobs_id'), table_name='docking_jobs')
    op.drop_table('docking_jobs')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
