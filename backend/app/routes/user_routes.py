from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session # Import Session
from datetime import timedelta

# Models & Schemas
from app.models.user_models import User, UserCreate, Token # UserInDB Pydantic model not directly used by routes now
# DB related
from app.database import get_db
from app.crud import crud_user
from app.models.user_models import DBUser # SQLAlchemy model for type hint

# Services
from app.services.auth_service import (
    create_access_token,
    authenticate_user, # Use the new DB-aware authenticate_user
    ACCESS_TOKEN_EXPIRE_MINUTES,
    # get_password_hash, verify_password are now used within crud_user or authenticate_user
    get_current_active_user, # Import this
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# No more in-memory DBs needed here for users
# _fake_users_db_user_routes: Dict[str, UserInDB] = {}
# _next_user_id = 1

@router.post("/register", response_model=User) # Returns Pydantic User model
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user_by_username = crud_user.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    db_user_by_email = crud_user.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    created_db_user = crud_user.create_user(db=db, user=user)
    # Convert SQLAlchemy model (DBUser) to Pydantic model (User) for response
    return User.model_validate(created_db_user)


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # authenticate_user now handles fetching from DB and password verification
    user = authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Fetch the current logged in user.
    """
    # get_current_active_user already returns the Pydantic User model
    return current_user

# For testing purposes - this reset function is no longer needed here
# as user data is in the database. Test setup will need to manage test DB state.
# def reset_user_db_and_ids_for_test():
#     global _next_user_id, _fake_users_db_user_routes
#     _fake_users_db_user_routes.clear()
#     _next_user_id = 1
