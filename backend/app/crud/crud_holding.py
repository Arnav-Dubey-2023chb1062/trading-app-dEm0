from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.holding_models import DBHolding
from decimal import Decimal # For type hinting and ensuring precision

def get_holding_by_portfolio_and_ticker(
    db: Session, portfolio_id: int, ticker_symbol: str
) -> Optional[DBHolding]:
    """
    Fetches a specific holding for a given portfolio and ticker.
    """
    return (
        db.query(DBHolding)
        .filter(DBHolding.portfolio_id == portfolio_id, DBHolding.ticker_symbol == ticker_symbol)
        .first()
    )

def create_holding(
    db: Session, portfolio_id: int, ticker_symbol: str, quantity: int, average_buy_price: Decimal
) -> DBHolding:
    """
    Creates a new DBHolding record.
    average_buy_price should be passed as Decimal.
    """
    db_holding = DBHolding(
        portfolio_id=portfolio_id,
        ticker_symbol=ticker_symbol,
        quantity=quantity,
        average_buy_price=average_buy_price # SQLAlchemy DECIMAL type handles Decimal objects
    )
    db.add(db_holding)
    # db.commit() # Commit handled by calling function
    # db.refresh(db_holding) # Refresh handled by calling function if needed after commit
    return db_holding

def update_holding(
    db: Session, holding: DBHolding, new_quantity: int, new_average_buy_price: Optional[Decimal] = None
) -> DBHolding:
    """
    Updates the given DBHolding object's quantity.
    If new_average_buy_price is provided (as Decimal), updates that too.
    Commit is handled by the calling function.
    """
    holding.quantity = new_quantity
    if new_average_buy_price is not None:
        holding.average_buy_price = new_average_buy_price
    db.add(holding) # Ensure changes are staged
    # db.commit() # Commit handled by calling function
    # db.refresh(holding) # Refresh handled by calling function if needed after commit
    return holding

def delete_holding(db: Session, holding_id: int) -> Optional[DBHolding]:
    """
    Deletes a holding by its ID.
    Commit is handled by the calling function.
    Returns the holding object if found and marked for deletion, else None.
    """
    db_holding = db.query(DBHolding).filter(DBHolding.holding_id == holding_id).first()
    if db_holding:
        db.delete(db_holding)
        # db.commit() # Commit handled by calling function
        return db_holding
    return None


def get_holdings_by_portfolio(
    db: Session, portfolio_id: int, skip: int = 0, limit: int = 100
) -> List[DBHolding]:
    """
    Retrieves a list of holdings for a specific portfolio with pagination.
    (Original function, kept for listing purposes)
    """
    return (
        db.query(DBHolding)
        .filter(DBHolding.portfolio_id == portfolio_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
