from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal, InvalidOperation # For precise calculations and handling conversion errors
from fastapi import HTTPException, status # For raising business logic errors
import logging # For logging

from app.models.trade_models import DBTrade, TradeCreate, TradeTypeEnum
from app.crud import crud_holding
from app.services.market_data_service import get_mock_current_price # Import mock price service

logger = logging.getLogger(__name__)

def create_portfolio_trade(db: Session, trade: TradeCreate, portfolio_id: int) -> DBTrade:
    """
    Creates a new trade for a specific portfolio and updates/creates a holding.
    """
    # Create the trade record first
    # Note: Pydantic's condecimal is already Decimal, no need to cast trade.price to Decimal here
    # if it's coming directly from a Pydantic model that uses condecimal.
    # The DBTrade model's price field is SQLAlchemy DECIMAL, which handles Python Decimal.

    trade_execution_price: Decimal
    if trade.price is not None:
        trade_execution_price = trade.price
        logger.info(f"Using client-provided price for trade: {trade_execution_price}")
    else:
        trade_execution_price = get_mock_current_price(trade.ticker_symbol)
        logger.info(f"Using mock price for trade: {trade_execution_price}")

    db_trade = DBTrade(
        portfolio_id=portfolio_id,
        ticker_symbol=trade.ticker_symbol,
        trade_type=trade.trade_type.value, # Use enum's value
        quantity=trade.quantity,
        price=trade_execution_price # Use determined execution price
    )
    db.add(db_trade)
    # db.commit() # Commit later after holding update or handle as one transaction

    # Update holdings
    existing_holding = crud_holding.get_holding_by_portfolio_and_ticker(
        db, portfolio_id=portfolio_id, ticker_symbol=trade.ticker_symbol
    )

    # trade_price_decimal = trade.price # Now use trade_execution_price

    if trade.trade_type == TradeTypeEnum.BUY:
        if existing_holding:
            # Ensure existing_holding.average_buy_price is Decimal for calculation
            current_avg_price = Decimal(str(existing_holding.average_buy_price))

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
            crud_holding.delete_holding(db, holding_id=existing_holding.holding_id)
        else:
            # Average buy price does not change on sell
            crud_holding.update_holding(db, holding=existing_holding, new_quantity=new_quantity)

    # Commit all changes (trade and holding) together if individual commits are removed from above
    db.commit()
    db.refresh(db_trade) # Refresh to get trade_id and other DB-generated values
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
