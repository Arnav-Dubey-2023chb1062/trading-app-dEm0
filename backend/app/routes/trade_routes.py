from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List

from app.models.trade_models import Trade, TradeCreate
from app.models.user_models import User
from app.services.auth_service import get_current_active_user
# We need access to the portfolio "DB" to check ownership
from app.routes.portfolio_routes import _fake_portfolios_db

router = APIRouter(
    # Prefix will be defined in main.py when including the router
    tags=["trades"],
    dependencies=[Depends(get_current_active_user)]
)

# In-memory storage for trades
# List of Trade objects. portfolio_id is part of Trade model.
_fake_trades_db: List[Trade] = []
_next_trade_id: int = 1

# Helper function to check portfolio ownership
async def get_portfolio_for_user(
    portfolio_id: int,
    current_user: User = Depends(get_current_active_user)
):
    portfolio = next((
        p for p in _fake_portfolios_db
        if p.portfolio_id == portfolio_id and p.user_id == current_user.user_id
    ), None)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )
    return portfolio

@router.post("/", response_model=Trade, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_in: TradeCreate, # Body parameter first
    portfolio_id: int = Path(..., title="The ID of the portfolio to add trade to"),
    current_user: User = Depends(get_current_active_user)
    # portfolio = Depends(get_portfolio_for_user) # Alternative way to inject and check ownership
):
    # Ensure the portfolio exists and belongs to the user
    # current_user is resolved by Depends, portfolio_id from path
    portfolio = await get_portfolio_for_user(portfolio_id, current_user)
    # If we reach here, portfolio is valid and owned by current_user

    global _next_trade_id
    from datetime import datetime, timezone # Import here or globally

    new_trade = Trade(
        trade_id=_next_trade_id,
        portfolio_id=portfolio.portfolio_id, # Use ID from path, validated by get_portfolio_for_user
        ticker_symbol=trade_in.ticker_symbol,
        trade_type=trade_in.trade_type,
        quantity=trade_in.quantity,
        price=trade_in.price,
        timestamp=datetime.now(timezone.utc)
    )
    _fake_trades_db.append(new_trade)
    _next_trade_id += 1
    return new_trade

@router.get("/", response_model=List[Trade])
async def list_trades_for_portfolio(
    portfolio_id: int = Path(..., title="The ID of the portfolio"),
    current_user: User = Depends(get_current_active_user)
):
    # Ensure the portfolio exists and belongs to the user
    await get_portfolio_for_user(portfolio_id, current_user)

    trades_in_portfolio = [
        t for t in _fake_trades_db if t.portfolio_id == portfolio_id
    ]
    return trades_in_portfolio

@router.get("/{trade_id}", response_model=Trade)
async def get_trade(
    portfolio_id: int = Path(..., title="The ID of the portfolio"),
    trade_id: int = Path(..., title="The ID of the trade"),
    current_user: User = Depends(get_current_active_user)
):
    # Ensure portfolio ownership first
    await get_portfolio_for_user(portfolio_id, current_user)

    trade = next((
        t for t in _fake_trades_db
        if t.trade_id == trade_id and t.portfolio_id == portfolio_id
    ), None)

    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found in this portfolio"
        )
    return trade

@router.put("/{trade_id}", response_model=Trade)
async def update_trade(
    trade_update: TradeCreate, # Body parameter first
    portfolio_id: int = Path(..., title="The ID of the portfolio"),
    trade_id: int = Path(..., title="The ID of the trade"),
    current_user: User = Depends(get_current_active_user)
):
    # Ensure portfolio ownership
    await get_portfolio_for_user(portfolio_id, current_user)

    trade_idx = -1
    for idx, t in enumerate(_fake_trades_db):
        if t.trade_id == trade_id and t.portfolio_id == portfolio_id:
            trade_idx = idx
            break

    if trade_idx == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found in this portfolio"
        )

    # Update fields
    updated_trade = _fake_trades_db[trade_idx]
    updated_trade.ticker_symbol = trade_update.ticker_symbol
    updated_trade.trade_type = trade_update.trade_type
    updated_trade.quantity = trade_update.quantity
    updated_trade.price = trade_update.price
    # Timestamp could be updated or kept as original creation, depends on requirements
    # For now, let's assume it's not updated here. It's the original trade time.

    _fake_trades_db[trade_idx] = updated_trade
    return updated_trade

@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(
    portfolio_id: int = Path(..., title="The ID of the portfolio"),
    trade_id: int = Path(..., title="The ID of the trade"),
    current_user: User = Depends(get_current_active_user)
):
    # Ensure portfolio ownership
    await get_portfolio_for_user(portfolio_id, current_user)

    global _fake_trades_db
    original_len = len(_fake_trades_db)
    _fake_trades_db = [
        t for t in _fake_trades_db
        if not (t.trade_id == trade_id and t.portfolio_id == portfolio_id)
    ]

    if len(_fake_trades_db) == original_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found in this portfolio"
        )
    return None

# For testing purposes
def reset_trade_db_and_ids_for_test():
    global _next_trade_id, _fake_trades_db
    _fake_trades_db.clear()
    _next_trade_id = 1
