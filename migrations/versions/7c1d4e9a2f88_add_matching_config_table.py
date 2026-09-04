"""add matching_config table

Revision ID: 7c1d4e9a2f88
Revises: 3f7a9c2e1b44
Create Date: 2026-09-04 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1d4e9a2f88'
down_revision: Union[str, Sequence[str], None] = '3f7a9c2e1b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'matching_config',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('gstin_weight', sa.Float(), server_default='0.60', nullable=False),
        sa.Column('pan_weight', sa.Float(), server_default='0.55', nullable=False),
        sa.Column('name_weight', sa.Float(), server_default='0.42', nullable=False),
        sa.Column('address_weight', sa.Float(), server_default='0.28', nullable=False),
        sa.Column('pin_weight', sa.Float(), server_default='0.12', nullable=False),
        sa.Column('pin_requires_name_sim', sa.Float(), server_default='0.35', nullable=False),
        sa.Column('auto_link_threshold', sa.Float(), server_default='0.92', nullable=False),
        sa.Column('review_threshold', sa.Float(), server_default='0.70', nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('matching_config')
