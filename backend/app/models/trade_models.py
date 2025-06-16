from pydantic import BaseModel, ConfigDict, condecimal
from typing import Optional
from datetime import datetime

# Assuming trade_type will be an ENUM later, for now, simple string
# from enum import Enum
# class TradeTypeEnum(str, Enum):
#     BUY = "BUY"
#     SELL = "SELL"

class TradeBase(BaseModel):
    ticker_symbol: str
    # trade_type: TradeTypeEnum
    trade_type: str # Keep simple for now, add CHECK constraint from SQL
    quantity: int
    price: condecimal(max_digits=12, decimal_places=2)

class TradeCreate(TradeBase):
    pass

class Trade(TradeBase):
    trade_id: int
    portfolio_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
