from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal, InvalidOperation # For precise calculations and handling conversion errors
from fastapi import HTTPException, status
import logging

from app.models.trade_models import DBTrade, TradeCreate, TradeTypeEnum
from app.models.portfolio_models import DBPortfolio # Import DBPortfolio
from app.crud import crud_holding
from app.services.market_data_service import get_price_for_trade

logger = logging.getLogger(__name__)

def create_portfolio_trade(db: Session, trade: TradeCreate, portfolio_id: int) -> DBTrade:
    """
    Creates a new trade for a specific portfolio and updates/creates a holding.
    """
    # Create the trade record first
    # Note: Pydantic's condecimal is already Decimal, no need to cast trade.price to Decimal here
    # if it's coming directly from a Pydantic model that uses condecimal.
    # The DBTrade model's price field is SQLAlchemy DECIMAL, which handles Python Decimal.

    # 1. Determine trade execution price
    trade_execution_price: Decimal
    if trade.price is not None:
        trade_execution_price = trade.price # This is already Decimal from Pydantic model
        logger.info(f"Using client-provided price for trade: {trade_execution_price}")
    else:
        trade_execution_price = get_price_for_trade(db, trade.ticker_symbol)
        logger.info(f"Using server-determined price for trade: {trade_execution_price} (source logged in market_data_service)")

    # 2. Fetch the portfolio to access/update cash_balance
    # Ownership of portfolio_id should be checked by the calling route using a dependency.
    db_portfolio = db.query(DBPortfolio).filter(DBPortfolio.portfolio_id == portfolio_id).first()
    if not db_portfolio:
        # This should ideally not happen if routes check portfolio existence and ownership first.
        # No db.rollback() needed here as no changes made yet.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found for trade operation.")

    # 3. Perform trade-specific logic (BUY or SELL)
    if trade.trade_type == TradeTypeEnum.BUY:
        trade_cost = trade_execution_price * trade.quantity
        if db_portfolio.cash_balance < trade_cost:
            # No db.rollback() needed here as no changes made yet to this session for this operation
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash balance.")

        # Debit cash balance before creating trade and updating holdings
        db_portfolio.cash_balance -= trade_cost
        db.add(db_portfolio) # Stage portfolio update

    # 4. Create the DBTrade object (staged for commit)
    db_trade = DBTrade(
        portfolio_id=portfolio_id,
        ticker_symbol=trade.ticker_symbol,
        trade_type=trade.trade_type.value,
        quantity=trade.quantity,
        price=trade_execution_price
    )
    db.add(db_trade) # Stage trade creation

    # 5. Process holding update (staged for commit by crud_holding functions if they don't commit themselves)
    existing_holding = crud_holding.get_holding_by_portfolio_and_ticker(
        db, portfolio_id=portfolio_id, ticker_symbol=trade.ticker_symbol
    )

    if trade.trade_type == TradeTypeEnum.BUY:
        if existing_holding:
            current_avg_price = Decimal(str(existing_holding.average_buy_price)) # Ensure Decimal
            new_total_cost = (current_avg_price * existing_holding.quantity) + \
                             (trade_execution_price * trade.quantity)
            new_total_quantity = existing_holding.quantity + trade.quantity
            new_average_buy_price = new_total_cost / new_total_quantity

            crud_holding.update_holding(
                db,
                holding=existing_holding,
                new_quantity=new_total_quantity,
                new_average_buy_price=new_average_buy_price
            )
        else:
            crud_holding.create_holding(
                db,
                portfolio_id=portfolio_id,
                ticker_symbol=trade.ticker_symbol,
                quantity=trade.quantity,
                average_buy_price=trade_execution_price # Use determined execution price
            )
    elif trade.trade_type == TradeTypeEnum.SELL:
        if not existing_holding or existing_holding.quantity < trade.quantity:
            # Rollback the trade addition if handling as one transaction (requires taking out individual commits)
            # For now, with individual commits, this state is problematic.
            # Ideally, this check happens before even creating DBTrade or the route manages transaction.
            db.rollback() # Rollback trade if holding logic fails (requires no prior commit for trade)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient quantity to sell or holding does not exist."
            )

        new_quantity = existing_holding.quantity - trade.quantity
        if new_quantity == 0:
            crud_holding.delete_holding(db, holding_id=existing_holding.holding_id) # This stages delete
        else:
            crud_holding.update_holding(db, holding=existing_holding, new_quantity=new_quantity) # This stages update

        # Credit cash balance after processing sell and holding update
        trade_proceeds = trade_execution_price * trade.quantity
        db_portfolio.cash_balance += trade_proceeds
        db.add(db_portfolio) # Stage portfolio update again if not already (though it should be fine)

    # 6. Commit the transaction (includes trade, portfolio cash_balance, and holding changes)
    try:
        db.commit()
    except Exception as e: # Catch potential commit errors (e.g. DB constraints if any not caught before)
        db.rollback()
        logger.error(f"Error during commit for trade {trade.ticker_symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save trade and update holdings.")

    # 7. Refresh instances to get DB-generated values
    db.refresh(db_trade)
    db.refresh(db_portfolio)
    # If existing_holding was updated, it's already part of the session and its state will be updated on commit.
    # If a new holding was created by crud_holding.create_holding, it should also be refreshed if its ID is needed.
    # crud_holding.create_holding returns the new holding, so it's already refreshed if that was called.

    return db_trade

def get_trade_by_id(db: Session, trade_id: int) -> Optional[DBTrade]:
    """
    Retrieves a trade by its ID.
    """
    return db.query(DBTrade).filter(DBTrade.trade_id == trade_id).first()

def get_trades_by_portfolio(
    db: Session, portfolio_id: int, skip: int = 0, limit: int = 100
) -> List[DBTrade]:
    """
    Retrieves a list of trades for a specific portfolio with pagination.
    """
    return (
        db.query(DBTrade)
        .filter(DBTrade.portfolio_id == portfolio_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_trade(
    db: Session, trade_id: int, trade_update: TradeCreate
) -> Optional[DBTrade]:
    """
    Updates an existing trade.
    Updates all fields from TradeCreate: ticker_symbol, trade_type, quantity, price.
    Timestamp is not updated.
    """
    db_trade = get_trade_by_id(db, trade_id=trade_id)
    if db_trade:
        update_data = trade_update.model_dump(exclude_unset=True) # Only update provided fields
        for key, value in update_data.items():
            setattr(db_trade, key, value)
        db.commit()
        db.refresh(db_trade)
    return db_trade

def delete_trade(db: Session, trade_id: int) -> Optional[DBTrade]:
    """
    Deletes a trade from the database.
    Returns the deleted trade object if found and deleted, otherwise None.
    """
    db_trade = get_trade_by_id(db, trade_id=trade_id)
    if db_trade:
        db.delete(db_trade)
        db.commit()
    return db_trade
