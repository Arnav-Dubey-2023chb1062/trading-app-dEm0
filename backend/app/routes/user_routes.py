from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Dict, Any

# Models (adjust path if necessary)
from app.models.user_models import User, UserCreate, UserLogin, Token, UserInDB

# Services (adjust path if necessary)
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    add_user_to_auth_service_db, # Import the new function
    get_user_from_db as get_user_from_auth_service_db # To avoid name clash if any local get_user_from_db
)
from datetime import timedelta

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# In-memory storage for users (temporary simulation for this route module)
# This stores the UserInDB model directly now.
# Note: user_id needs to be handled.
_fake_users_db_user_routes: Dict[str, UserInDB] = {}
_next_user_id = 1

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    global _next_user_id
    if user.username in _fake_users_db_user_routes: # Check local cache first
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check auth service cache too (though ideally these are perfectly synced)
    if get_user_from_auth_service_db(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered (auth store)",
        )

    hashed_password = get_password_hash(user.password)

    # Assign a user_id
    current_user_id = _next_user_id
    _next_user_id += 1

    user_in_db = UserInDB(
        **user.model_dump(),
        hashed_password=hashed_password,
        user_id=current_user_id
    )

    _fake_users_db_user_routes[user.username] = user_in_db
    add_user_to_auth_service_db(user_in_db) # Sync with auth_service's user store

    return User.model_validate(user_in_db) # Convert UserInDB to User for response


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authenticate against the auth_service's user store, as it's the source of truth for get_current_user
    user_in_db = get_user_from_auth_service_db(form_data.username)

    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # UserInDB object is already available
    if not verify_password(form_data.password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_in_db.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# For testing purposes
def reset_user_db_and_ids_for_test():
    global _next_user_id, _fake_users_db_user_routes
    _fake_users_db_user_routes.clear()
    _next_user_id = 1
