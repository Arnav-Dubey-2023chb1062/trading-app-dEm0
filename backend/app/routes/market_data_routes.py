from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from pydantic import BaseModel, condecimal # Import condecimal for Pydantic model

from app.database import get_db
from app.services import market_data_service
# Assuming get_current_active_user can be used if routes need to be protected
# from app.services.auth_service import get_current_active_user
# from app.models.user_models import User as PydanticUser

router = APIRouter(
    prefix="/marketdata",
    tags=["marketdata"],
    # dependencies=[Depends(get_current_active_user)] # Uncomment if these routes need auth
)

class TickerPriceResponse(BaseModel):
    ticker_symbol: str
    price: condecimal(max_digits=12, decimal_places=2) # Use condecimal for validated Decimal
    source: str # e.g., "realtime_finnhub", "cached", "mock_fixed", "mock_random", or error string from service

@router.get("/{ticker_symbol}", response_model=TickerPriceResponse)
async def get_ticker_price(
    ticker_symbol: str,
    db: Session = Depends(get_db)
):
    """
    Fetches the current price for a given ticker symbol.
    The price can come from a real-time API (Finnhub), cache, or a mock source if real data fails.
    The 'source' field in the response indicates where the price data originated.
    """
    price, source = market_data_service.get_current_price_with_source_info(db, ticker_symbol=ticker_symbol)

    if price is None: # Should ideally not happen if mock fallback always provides a price
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price data ultimately not available for ticker {ticker_symbol}. Source: {source}"
        )

    return TickerPriceResponse(
        ticker_symbol=ticker_symbol.upper(),
        price=price, # Pydantic condecimal will handle Decimal
        source=source
    )
