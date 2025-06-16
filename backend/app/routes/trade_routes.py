from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from sqlalchemy.orm import Session

from app.models.trade_models import Trade, TradeCreate # Pydantic models
from app.models.user_models import User as PydanticUser # Pydantic User for current_user
from app.services.auth_service import get_current_active_user
from app.database import get_db
from app.crud import crud_trade, crud_portfolio # Import portfolio CRUD for ownership check
from app.models.portfolio_models import DBPortfolio # SQLAlchemy model for type hint

router = APIRouter(
    # Prefix is defined in main.py: /portfolios/{portfolio_id}/trades
    tags=["trades"],
    dependencies=[Depends(get_current_active_user)]
)

# In-memory DB and ID counter are removed
# _fake_trades_db: List[Trade] = []
# _next_trade_id: int = 1

# Helper function to check portfolio ownership using DB
async def get_portfolio_for_user_from_db(
    portfolio_id: int,
    current_user: PydanticUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DBPortfolio: # Return SQLAlchemy DBPortfolio
    db_portfolio = crud_portfolio.get_portfolio_by_id(db, portfolio_id=portfolio_id)
    if not db_portfolio or db_portfolio.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or not owned by user"
        )
    return db_portfolio

@router.post("/", response_model=Trade, status_code=status.HTTP_201_CREATED)
async def create_trade(
    trade_in: TradeCreate,
    portfolio_id: int = Path(..., description="The ID of the portfolio to add this trade to"),
    # current_user is available from router dependencies, but get_portfolio_for_user_from_db also resolves it
    db_portfolio: DBPortfolio = Depends(get_portfolio_for_user_from_db), # Handles ownership check
    db: Session = Depends(get_db)
):
    # db_portfolio (from Depends) confirms ownership and existence
    db_trade = crud_trade.create_portfolio_trade(
        db=db, trade=trade_in, portfolio_id=db_portfolio.portfolio_id
    )
    return Trade.model_validate(db_trade)

@router.get("/", response_model=List[Trade])
async def list_trades_for_portfolio(
    portfolio_id: int = Path(..., description="The ID of the portfolio"),
    db_portfolio: DBPortfolio = Depends(get_portfolio_for_user_from_db), # Handles ownership check
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    db_trades = crud_trade.get_trades_by_portfolio(
        db=db, portfolio_id=db_portfolio.portfolio_id, skip=skip, limit=limit
    )
    return [Trade.model_validate(t) for t in db_trades]

@router.get("/{trade_id}", response_model=Trade)
async def get_trade(
    trade_id: int,
    db_portfolio: DBPortfolio = Depends(get_portfolio_for_user_from_db), # Handles ownership check
    db: Session = Depends(get_db)
):
    db_trade = crud_trade.get_trade_by_id(db=db, trade_id=trade_id)
    if db_trade is None or db_trade.portfolio_id != db_portfolio.portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found in this portfolio"
        )
    return Trade.model_validate(db_trade)

@router.put("/{trade_id}", response_model=Trade)
async def update_trade(
    trade_update: TradeCreate,
    trade_id: int,
    db_portfolio: DBPortfolio = Depends(get_portfolio_for_user_from_db), # Handles ownership check
    db: Session = Depends(get_db)
):
    # First, check if the trade exists and belongs to the specified portfolio (which is owned by user)
    db_trade_to_update = crud_trade.get_trade_by_id(db=db, trade_id=trade_id)
    if db_trade_to_update is None or db_trade_to_update.portfolio_id != db_portfolio.portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found for update in this portfolio"
        )

    updated_db_trade = crud_trade.update_trade(
        db=db, trade_id=trade_id, trade_update=trade_update
    )
    return Trade.model_validate(updated_db_trade)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(
    trade_id: int,
    db_portfolio: DBPortfolio = Depends(get_portfolio_for_user_from_db), # Handles ownership check
    db: Session = Depends(get_db)
):
    # First, check if the trade exists and belongs to the specified portfolio
    db_trade_to_delete = crud_trade.get_trade_by_id(db=db, trade_id=trade_id)
    if db_trade_to_delete is None or db_trade_to_delete.portfolio_id != db_portfolio.portfolio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found for deletion in this portfolio"
        )

    deleted_trade = crud_trade.delete_trade(db=db, trade_id=trade_id)
    if not deleted_trade: # Should ideally not happen if previous check passed
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade deletion failed")

    return None

# The reset function is no longer needed.
# def reset_trade_db_and_ids_for_test():
#     global _next_trade_id, _fake_trades_db
#     _fake_trades_db.clear()
#     _next_trade_id = 1
