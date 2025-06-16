from pydantic import BaseModel, ConfigDict, condecimal
from typing import Optional
from datetime import datetime

from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, func
# No relationships needed for this model as per current design
from app.database import Base

# --- SQLAlchemy Model ---
class DBMarketDataCache(Base): # Prefixed with DB for consistency
    __tablename__ = "market_data_cache"

    ticker_symbol = Column(String(20), primary_key=True, index=True)
    last_price = Column(DECIMAL(12, 2), nullable=False)
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

# --- Pydantic Schemas ---
class MarketDataBase(BaseModel):
    ticker_symbol: str
    last_price: condecimal(max_digits=12, decimal_places=2)

class MarketDataCreate(MarketDataBase): # For creating or updating cache entries
    pass

class MarketData(MarketDataBase): # For reading/returning cache data
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)
