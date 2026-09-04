"""add job table

Revision ID: 3f7a9c2e1b44
Revises: ee4fd47dbd34
Create Date: 2026-09-04 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f7a9c2e1b44'
down_revision: Union[str, Sequence[str], None] = 'ee4fd47dbd34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'job',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'job_type',
            sa.Enum('status_run_all', 'process_pending', 'csv_match', name='jobtypeenum', native_enum=False),
            nullable=True,
        ),
        sa.Column(
            'status',
            sa.Enum('pending', 'running', 'succeeded', 'failed', name='jobstatusenum', native_enum=False),
            nullable=True,
        ),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(length=2000), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_job_job_type'), 'job', ['job_type'], unique=False)
    op.create_index(op.f('ix_job_status'), 'job', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_job_status'), table_name='job')
    op.drop_index(op.f('ix_job_job_type'), table_name='job')
    op.drop_table('job')
