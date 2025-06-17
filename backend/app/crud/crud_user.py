from sqlalchemy.orm import Session
from app.models.user_models import DBUser, UserCreate # Pydantic UserCreate for input type hint
from app.services.auth_service import get_password_hash # For hashing password

def get_user_by_username(db: Session, username: str) -> DBUser | None:
    """
    Retrieves a user from the database by their username.
    """
    return db.query(DBUser).filter(DBUser.username == username).first()

def get_user_by_email(db: Session, email: str) -> DBUser | None:
    """
    Retrieves a user from the database by their email.
    """
    return db.query(DBUser).filter(DBUser.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> DBUser | None:
    """
    Retrieves a user from the database by their user ID.
    """
    return db.query(DBUser).filter(DBUser.user_id == user_id).first()

def create_user(db: Session, user: UserCreate) -> DBUser:
    """
    Creates a new user in the database.
    - Hashes the plain password from the UserCreate schema.
    - Adds the new user to the session, commits, and refreshes.
    """
    hashed_password = get_password_hash(user.password)
    db_user = DBUser(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # To get the auto-generated user_id and created_at
    return db_user
