from pydantic import BaseModel, ConfigDict, condecimal
from typing import Optional
from datetime import datetime # Though not used in this specific model, good for consistency

from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

# --- SQLAlchemy Model ---
class DBHolding(Base):
    __tablename__ = "holdings"

    holding_id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.portfolio_id"), nullable=False)
    ticker_symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    average_buy_price = Column(DECIMAL(12, 2), nullable=False)

    # Relationship
    portfolio = relationship("DBPortfolio", back_populates="holdings")

    # Constraints
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'ticker_symbol', name='uq_portfolio_ticker'),
    )

# --- Pydantic Schemas ---
class HoldingBase(BaseModel):
    ticker_symbol: str
    quantity: int
    average_buy_price: condecimal(max_digits=12, decimal_places=2)

class HoldingCreate(HoldingBase):
    # portfolio_id will likely be a path parameter or determined from context (e.g. user)
    # If needed in body: portfolio_id: int
    pass

class Holding(HoldingBase): # For reading/returning holding data
    holding_id: int
    portfolio_id: int
    # Potentially add other fields like current_value if calculated

    model_config = ConfigDict(from_attributes=True)
