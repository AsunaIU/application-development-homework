"""create order_reports view

Revision ID: 4159f8afee9f
Revises: a3853528df4f
Create Date: 2025-12-12 05:05:35.408287
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4159f8afee9f'
down_revision: Union[str, Sequence[str], None] = '453659de82b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE VIEW order_reports AS
        SELECT 
            o.created_at::DATE as report_at,
            o.id as order_id,
            COUNT(oi.product_id) as count_product,
            o.total_amount as total_amount
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.created_at::DATE, o.id, o.total_amount
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP VIEW IF EXISTS order_reports")
