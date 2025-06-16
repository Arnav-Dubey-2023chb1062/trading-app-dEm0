from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.trade_models import DBTrade, TradeCreate # Pydantic TradeCreate
# from app.models.portfolio_models import DBPortfolio # Not strictly needed for these operations

def create_portfolio_trade(db: Session, trade: TradeCreate, portfolio_id: int) -> DBTrade:
    """
    Creates a new trade for a specific portfolio.
    """
    db_trade = DBTrade(**trade.model_dump(), portfolio_id=portfolio_id)
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
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
