"""add_cash_balance_to_portfolios

Revision ID: 20ba6222e479
Revises: 43a5088b1774
Create Date: YYYY-MM-DD HH:MM:SS.MS # Will be filled by Alembic

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20ba6222e479'
down_revision: Union[str, None] = '43a5088b1774' # Should point to the previous migration (initial_tables)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('portfolios',
                  sa.Column('cash_balance',
                            sa.DECIMAL(precision=15, scale=2),
                            nullable=False,
                            server_default=sa.text('0.00'))
                 )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('portfolios', 'cash_balance')
    # ### end Alembic commands ###
