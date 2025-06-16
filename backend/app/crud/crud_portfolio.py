from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.portfolio_models import DBPortfolio, PortfolioCreate # Pydantic PortfolioCreate
from app.models.user_models import DBUser # For type hinting if needed, not directly used here

def create_user_portfolio(db: Session, portfolio: PortfolioCreate, user_id: int) -> DBPortfolio:
    """
    Creates a new portfolio for a specific user.
    """
    db_portfolio = DBPortfolio(**portfolio.model_dump(), user_id=user_id)
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

def get_portfolio_by_id(db: Session, portfolio_id: int) -> Optional[DBPortfolio]:
    """
    Retrieves a portfolio by its ID.
    """
    return db.query(DBPortfolio).filter(DBPortfolio.portfolio_id == portfolio_id).first()

def get_portfolios_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[DBPortfolio]:
    """
    Retrieves a list of portfolios for a specific user with pagination.
    """
    return (
        db.query(DBPortfolio)
        .filter(DBPortfolio.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_portfolio(
    db: Session, portfolio_id: int, portfolio_update: PortfolioCreate
) -> Optional[DBPortfolio]:
    """
    Updates an existing portfolio.
    Only updates portfolio_name.
    """
    db_portfolio = get_portfolio_by_id(db, portfolio_id=portfolio_id)
    if db_portfolio:
        # Only update fields present in PortfolioCreate (i.e., portfolio_name)
        db_portfolio.portfolio_name = portfolio_update.portfolio_name
        db.commit()
        db.refresh(db_portfolio)
    return db_portfolio

def delete_portfolio(db: Session, portfolio_id: int) -> Optional[DBPortfolio]:
    """
    Deletes a portfolio from the database.
    Returns the deleted portfolio object if found and deleted, otherwise None.
    """
    db_portfolio = get_portfolio_by_id(db, portfolio_id=portfolio_id)
    if db_portfolio:
        db.delete(db_portfolio)
        db.commit()
        # After deletion, the object's session is expired.
        # It's common to return the object as it was before deletion, or just a success status.
        # For consistency, if we return the object, it's now detached.
        # Some prefer to return True/False or the ID.
        # Let's return the object (though its state regarding session might be tricky if accessed later).
        # Or, for simplicity, let's return it as is, understanding it's now transient.
    return db_portfolio
