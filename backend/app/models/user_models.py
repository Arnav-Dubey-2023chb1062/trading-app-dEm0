from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDBBase(UserBase):
    user_id: Optional[int] = None # Or int, if always present after fetch

    class Config:
        from_attributes = True

class User(UserInDBBase): # For returning user data, without password
    pass

class UserInDB(UserInDBBase): # For representing user in database
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
