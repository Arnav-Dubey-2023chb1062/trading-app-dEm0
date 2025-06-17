from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.models.portfolio_models import Portfolio, PortfolioCreate # Pydantic models
from app.models.holding_models import Holding as PydanticHolding # Pydantic Holding model
from app.models.user_models import User as PydanticUser
from app.services.auth_service import get_current_active_user
from app.database import get_db
from app.crud import crud_portfolio, crud_holding # Added crud_holding

router = APIRouter(
    prefix="/portfolios",
    tags=["portfolios"],
    dependencies=[Depends(get_current_active_user)] # Protect all routes
)

# In-memory DB and ID counter are removed.
# _fake_portfolios_db: List[Portfolio] = []
# _next_portfolio_id: int = 1

@router.post("/", response_model=Portfolio, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # current_user is Pydantic User model, which has user_id
    db_portfolio = crud_portfolio.create_user_portfolio(
        db=db, portfolio=portfolio_in, user_id=current_user.user_id
    )
    return Portfolio.model_validate(db_portfolio)

@router.get("/", response_model=List[Portfolio])
async def list_portfolios(
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    db_portfolios = crud_portfolio.get_portfolios_by_user(
        db=db, user_id=current_user.user_id, skip=skip, limit=limit
    )
    return [Portfolio.model_validate(p) for p in db_portfolios]

@router.get("/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
    portfolio_id: int,
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_portfolio = crud_portfolio.get_portfolio_by_id(db=db, portfolio_id=portfolio_id)
    if db_portfolio is None or db_portfolio.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )
    return Portfolio.model_validate(db_portfolio)

@router.put("/{portfolio_id}", response_model=Portfolio)
async def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioCreate,
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_portfolio = crud_portfolio.get_portfolio_by_id(db=db, portfolio_id=portfolio_id)
    if db_portfolio is None or db_portfolio.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )

    updated_db_portfolio = crud_portfolio.update_portfolio(
        db=db, portfolio_id=portfolio_id, portfolio_update=portfolio_update
    )
    # crud_portfolio.update_portfolio itself returns the updated object or None if not found (already checked)
    return Portfolio.model_validate(updated_db_portfolio)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_portfolio_to_delete = crud_portfolio.get_portfolio_by_id(db=db, portfolio_id=portfolio_id)
    if db_portfolio_to_delete is None or db_portfolio_to_delete.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )

    deleted_portfolio = crud_portfolio.delete_portfolio(db=db, portfolio_id=portfolio_id)
    if not deleted_portfolio: # Should not happen if previous check passed, but good for safety
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio deletion failed")

    return None # Return None for 204 No Content

# The reset function is no longer needed as data is in DB.
# Test setup will manage DB state.
# def reset_portfolio_db_and_ids_for_test():
#     global _next_portfolio_id, _fake_portfolios_db
#     _fake_portfolios_db.clear()
#     _next_portfolio_id = 1

@router.get("/{portfolio_id}/holdings", response_model=List[PydanticHolding])
async def list_portfolio_holdings(
    portfolio_id: int,
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    # First, verify ownership of the portfolio
    db_portfolio = crud_portfolio.get_portfolio_by_id(db=db, portfolio_id=portfolio_id)
    if db_portfolio is None or db_portfolio.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )

    # If ownership is confirmed, fetch holdings
    db_holdings = crud_holding.get_holdings_by_portfolio(
        db=db, portfolio_id=portfolio_id, skip=skip, limit=limit
    )
    return [PydanticHolding.model_validate(h) for h in db_holdings]
