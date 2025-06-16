from pydantic import BaseModel, EmailStr
from typing import Optional, List # Added List for relationship typing

from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base # Import Base from the placeholder database.py
from datetime import datetime # Import datetime

# --- SQLAlchemy Model ---
class DBUser(Base): # Renamed to DBUser to avoid Pydantic User model collision
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    portfolios = relationship("DBPortfolio", back_populates="owner") # Use DBPortfolio for SQLAlchemy model

# --- Pydantic Schemas (original content) ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str # Plain password, will be hashed before storing

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDBBase(UserBase):
    user_id: int # Changed to int, as it will always be present from DB
    created_at: Optional[datetime] = None # Add created_at if it's part of response model

    class Config:
        from_attributes = True # Pydantic V2

class User(UserInDBBase): # For returning user data, without password
    pass

class UserInDB(UserInDBBase): # Used for reading from DB, includes hashed_password
    hashed_password: str # This is the Pydantic model, not SQLAlchemy

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Need datetime for Pydantic model if created_at is included
from datetime import datetime
