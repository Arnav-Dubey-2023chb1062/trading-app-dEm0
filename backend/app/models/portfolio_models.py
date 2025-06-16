from pydantic import BaseModel, ConfigDict
from typing import Optional

class PortfolioBase(BaseModel):
    portfolio_name: str

class PortfolioCreate(PortfolioBase):
    pass

class Portfolio(PortfolioBase):
    portfolio_id: int
    user_id: int # Assuming username is used as user_id for now from TokenData

    model_config = ConfigDict(from_attributes=True)
