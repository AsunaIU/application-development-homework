"""add timestamps to orders

Revision ID: 453659de82b0
Revises: 453659de82b0
Create Date: 2025-12-12 17:32:58.553654
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '453659de82b0'
down_revision: Union[str, Sequence[str], None] = 'a3853528df4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.add_column('orders', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'updated_at')
    op.drop_column('orders', 'created_at')
