from pydantic import BaseModel, ConfigDict, condecimal
from typing import Optional
from datetime import datetime
import enum # Import Python's enum module for Pydantic model

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func, DECIMAL
# Removed SQLAlchemyEnum import for now as using String for DB
from sqlalchemy.orm import relationship
from app.database import Base

# --- SQLAlchemy Model ---
class DBTrade(Base): # Renamed to DBTrade
    __tablename__ = "trades"

    trade_id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.portfolio_id"), nullable=False)
    ticker_symbol = Column(String(20), nullable=False, index=True)
    trade_type = Column(String(4), nullable=False) # Matches CHECK constraint ('BUY', 'SELL')
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(12, 2), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    portfolio = relationship("DBPortfolio", back_populates="trades") # Relates to DBPortfolio


# --- Pydantic Schemas ---
class TradeTypeEnum(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeBase(BaseModel):
    ticker_symbol: str
    trade_type: TradeTypeEnum # Use the Pydantic Enum
    quantity: int
    # Pydantic v2 uses DecimalAnnotation for condecimal if from pydantic.types
    # but condecimal(max_digits=, decimal_places=) is a Pydantic v1 way.
    # For Pydantic v2, it's better to use Annotated[Decimal, Field(max_digits=, decimal_places=)]
    # or just `Decimal` and rely on db constraints / app logic for precision for schemas.
    # For simplicity with condecimal as used before:
    price: condecimal(max_digits=12, decimal_places=2)


class TradeCreate(TradeBase):
    # portfolio_id will typically be a path parameter in the route,
    # so it's not always included in the creation schema body.
    # If it were, it would be: portfolio_id: int
    pass

class Trade(TradeBase): # For reading/returning trade data
    trade_id: int
    portfolio_id: int
    timestamp: datetime # Already present from original file

    model_config = ConfigDict(from_attributes=True)
