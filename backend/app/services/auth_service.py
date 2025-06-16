from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session # Added for DB session
from fastapi import Depends, HTTPException, status # Depends is already here
from fastapi.security import OAuth2PasswordBearer

# --- User Models & DB ---
from app.models.user_models import TokenData, User, DBUser
from app.crud import crud_user
from app.database import get_db
from app.config import settings # Import settings

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- User Authentication ---
def authenticate_user(db: Session, username: str, password: str) -> DBUser | None:
    """
    Authenticates a user.
    - Fetches user by username from DB.
    - Verifies password.
    Returns the DBUser object if authentication is successful, otherwise None.
    """
    user = crud_user.get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# --- JWT Handling ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy() # data should contain 'sub': username
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db) # Add DB session dependency
) -> DBUser: # Return SQLAlchemy model DBUser
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        # TokenData model is for payload structure, not needed to be returned here explicitly
        # token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception # This covers invalid token format, signature, expiry

    user = crud_user.get_user_by_username(db, username=username)
    if user is None:
        # This case means the user existed when token was issued, but not anymore.
        raise credentials_exception
    return user # Return the SQLAlchemy DBUser object

async def get_current_active_user(
    current_user: DBUser = Depends(get_current_user) # Depends on the new get_current_user
) -> User: # Return Pydantic User model for API response shaping
    # Here you could add logic to check if current_user (DBUser) is active, e.g.
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    # Convert DBUser (SQLAlchemy model) to User (Pydantic model) for the response
    # This ensures that hashed_password and other sensitive DB fields are not directly returned
    # if User Pydantic model is defined correctly (e.g. inherits from UserInDBBase and does not add password_hash)
    return User.model_validate(current_user)


# Removed _fake_db_users_auth_service, get_user_from_db (local fake one),
# add_user_to_auth_service_db, and reset_auth_service_db_for_test as they are no longer needed.
# The reset function for testing will now rely on clearing actual DB or using test DB.
# For now, crud/db interaction means tests against a live (test) DB are implied.
# The conftest.py reset for auth_service can be removed.
