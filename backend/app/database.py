import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file (optional, but good practice)
# Create a .env file in the backend directory with your DATABASE_URL
# e.g., DATABASE_URL=postgresql://your_user:your_password@localhost/trading_app_db
load_dotenv()

# Define SQLALCHEMY_DATABASE_URL
# It should be read from an environment variable for security and flexibility.
# Default to the placeholder if the environment variable is not set.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://your_db_user:your_db_password@localhost/trading_app_db"
)
# IMPORTANT: Users need to configure their actual database URL here,
# preferably via a .env file or system environment variables.

# Create the SQLAlchemy engine
# For PostgreSQL, no special connect_args are typically needed like for SQLite.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
