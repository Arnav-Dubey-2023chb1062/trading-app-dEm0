from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings # Import the settings instance

# SQLALCHEMY_DATABASE_URL is now sourced from settings.SQLALCHEMY_DATABASE_URL
# The load_dotenv() call is now in config.py

# Create the SQLAlchemy engine
# For PostgreSQL, no special connect_args are typically needed like for SQLite.
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
# Each instance of SessionLocal will be a database session.
# autocommit=False and autoflush=False are standard for web apps with ORMs.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define Base
# This Base will be used by all SQLAlchemy models to inherit from.
Base = declarative_base()

# --- Database Session Dependency ---
def get_db():
    """
    FastAPI dependency to get a database session.
    Ensures the database session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
