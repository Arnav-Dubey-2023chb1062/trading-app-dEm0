from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models.portfolio_models import Portfolio, PortfolioCreate
from app.models.user_models import User
from app.services.auth_service import get_current_active_user

router = APIRouter(
    prefix="/portfolios",
    tags=["portfolios"],
    dependencies=[Depends(get_current_active_user)] # Protect all routes in this router
)

# In-memory storage for portfolios
# Structure: {user_id: {portfolio_id: Portfolio_data_dict}}
# Or simpler: List[Portfolio_data_dict] and filter by user_id, add portfolio_id sequentially.
# Let's use a list of Portfolio objects for now.
_fake_portfolios_db: List[Portfolio] = []
_next_portfolio_id: int = 1

@router.post("/", response_model=Portfolio, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_active_user)
):
    global _next_portfolio_id
    new_portfolio = Portfolio(
        portfolio_id=_next_portfolio_id,
        user_id=current_user.user_id, # user_id from the token via get_current_active_user
        portfolio_name=portfolio_in.portfolio_name
    )
    _fake_portfolios_db.append(new_portfolio)
    _next_portfolio_id += 1
    return new_portfolio

@router.get("/", response_model=List[Portfolio])
async def list_portfolios(
    current_user: User = Depends(get_current_active_user)
):
    user_portfolios = [
        p for p in _fake_portfolios_db if p.user_id == current_user.user_id
    ]
    return user_portfolios

@router.get("/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
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

@router.put("/{portfolio_id}", response_model=Portfolio)
async def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioCreate, # Can also make a PortfolioUpdate model
    current_user: User = Depends(get_current_active_user)
):
    portfolio_idx = -1
    for idx, p in enumerate(_fake_portfolios_db):
        if p.portfolio_id == portfolio_id and p.user_id == current_user.user_id:
            portfolio_idx = idx
            break

    if portfolio_idx == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )

    # Update the portfolio name
    _fake_portfolios_db[portfolio_idx].portfolio_name = portfolio_update.portfolio_name
    return _fake_portfolios_db[portfolio_idx]

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_active_user)
):
    global _fake_portfolios_db
    original_len = len(_fake_portfolios_db)
    _fake_portfolios_db = [
        p for p in _fake_portfolios_db
        if not (p.portfolio_id == portfolio_id and p.user_id == current_user.user_id)
    ]
    if len(_fake_portfolios_db) == original_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )
    return None # For 204 No Content

# For testing purposes
def reset_portfolio_db_and_ids_for_test():
    global _next_portfolio_id, _fake_portfolios_db
    _fake_portfolios_db.clear()
    _next_portfolio_id = 1
