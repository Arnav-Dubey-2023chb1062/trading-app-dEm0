"""create_initial_tables

Revision ID: 43a5088b1774
Revises:
Create Date: YYYY-MM-DD HH:MM:SS.MS

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43a5088b1774'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE users (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)
    op.execute("""
    CREATE TABLE portfolios (
        portfolio_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        portfolio_name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    op.execute("""
    CREATE TABLE market_data_cache (
        ticker_symbol VARCHAR(20) PRIMARY KEY,
        last_price DECIMAL(12, 2) NOT NULL,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """)
    op.execute("""
    CREATE TABLE holdings (
        holding_id SERIAL PRIMARY KEY,
        portfolio_id INTEGER NOT NULL,
        ticker_symbol VARCHAR(20) NOT NULL,
        quantity INTEGER NOT NULL,
        average_buy_price DECIMAL(12, 2) NOT NULL,
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
    );
    """)
    op.execute("""
    CREATE TABLE trades (
        trade_id SERIAL PRIMARY KEY,
        portfolio_id INTEGER NOT NULL,
        ticker_symbol VARCHAR(20) NOT NULL,
        trade_type VARCHAR(4) NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
        quantity INTEGER NOT NULL,
        price DECIMAL(12, 2) NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
    );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE trades;")
    op.execute("DROP TABLE holdings;")
    op.execute("DROP TABLE market_data_cache;")
    op.execute("DROP TABLE portfolios;")
    op.execute("DROP TABLE users;")
