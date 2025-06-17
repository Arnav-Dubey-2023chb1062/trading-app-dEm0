from pydantic import BaseModel, ConfigDict, condecimal # Import condecimal
from typing import Optional, List
from datetime import datetime

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, func, DECIMAL # Import DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base

# --- SQLAlchemy Model ---
class DBPortfolio(Base): # Renamed to DBPortfolio
    __tablename__ = "portfolios"

    portfolio_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    portfolio_name = Column(String(100), nullable=False)
    cash_balance = Column(DECIMAL(15, 2), nullable=False) # Default set by CRUD
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("DBUser", back_populates="portfolios") # Relates to DBUser
    trades = relationship("DBTrade", back_populates="portfolio", cascade="all, delete-orphan") # Relates to DBTrade
    holdings = relationship("DBHolding", back_populates="portfolio", cascade="all, delete-orphan") # Relates to DBHolding


# --- Pydantic Schemas (original content) ---
class PortfolioBase(BaseModel):
    portfolio_name: str
    # cash_balance is part of Portfolio response, but not typically set on creation by client directly
    # It will be initialized by the server.
    # If we want to show it in responses derived from PortfolioBase (like Portfolio schema):
    cash_balance: Optional[condecimal(max_digits=15, decimal_places=2)] = None


class PortfolioCreate(BaseModel): # Modified to not inherit cash_balance from PortfolioBase for creation
    portfolio_name: str

class Portfolio(PortfolioBase): # For reading/returning portfolio data
    portfolio_id: int
    user_id: int
    created_at: Optional[datetime] = None
    cash_balance: condecimal(max_digits=15, decimal_places=2) # Make non-optional for response

    model_config = ConfigDict(from_attributes=True)

# Pydantic model for a portfolio that includes its trades and holdings (example)
# Might be useful for detailed portfolio view endpoints
class PortfolioWithDetails(Portfolio):
    trades: List['Trade'] = [] # Forward reference for Pydantic Trade schema
    holdings: List['Holding'] = [] # Forward reference for Pydantic Holding schema
    # Ensure Trade and Holding Pydantic schemas are defined elsewhere and imported if used like this

# To resolve forward references if Trade and Holding Pydantic models are in other files
# and this model is used. For now, this is illustrative.
# If Pydantic models for Trade and Holding are in their respective files,
# this would need proper imports or be defined after those.
# For now, this is mostly a placeholder to show how relationships translate to Pydantic.
# We'll need actual Pydantic `Trade` and `Holding` schemas.
# Let's assume they will be created alongside their SQLAlchemy models.
from .trade_models import Trade # Assuming Trade Pydantic schema is in trade_models
from .holding_models import Holding # Assuming Holding Pydantic schema is in holding_models

PortfolioWithDetails.model_rebuild() # Pydantic v2 way to rebuild model with forward refs
                                     # Requires Trade and Holding to be defined
                                     # This might cause issues if those files don't exist yet or
                                     # don't have those Pydantic models.
                                     # I'll keep this commented out.
# PortfolioWithDetails.model_rebuild()
