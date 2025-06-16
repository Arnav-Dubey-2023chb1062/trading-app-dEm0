import pytest
from fastapi.testclient import TestClient
from typing import Generator, Any

# Import the main FastAPI app
from main import app # Corrected import path

# Import the main FastAPI app
from main import app # Corrected import path

# Import reset functions
# from app.routes.user_routes import reset_user_db_and_ids_for_test # This function is now removed
# from app.services.auth_service import reset_auth_service_db_for_test # This function is now removed
# from app.routes.portfolio_routes import reset_portfolio_db_and_ids_for_test # This function is now removed
# from app.routes.trade_routes import reset_trade_db_and_ids_for_test # This function is now removed


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, Any, None]:
    # Reset all data stores and ID counters before each test
    # reset_user_db_and_ids_for_test() # Removed
    # reset_auth_service_db_for_test() # Removed
    # reset_portfolio_db_and_ids_for_test() # Removed
    # reset_trade_db_and_ids_for_test() # Removed

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def get_test_user_token(client: TestClient) -> str:
    """
    Registers a test user and returns their auth token.
    Relies on the main 'client' fixture to have already reset relevant DBs including user IDs.
    """
    # The main 'client' fixture (which runs before this one if both are used by a test)
    # has already called reset functions for portfolio and trade in-memory DBs.
    # User creation will now hit the database.

    user_data = {
        "username": "testuser_conftest",
        "email": "test_conftest@example.com",
        "password": "testpassword_conftest"
    }
    # This registration will now write to the database.
    # For tests to be repeatable, the database state needs to be managed (e.g., test DB, transactions, cleanup).
    # If the user already exists from a previous test run (without cleanup), this will fail.
    # This fixture might need adjustment for robust DB testing (e.g., try-except for creation or ensure cleanup).
    response = client.post("/users/register", json=user_data)

    # If user already exists (e.g. from a previous unclean test run), registration might fail.
    # For this fixture to be robust, it should handle this, or tests need proper DB cleanup.
    # A simple approach for now: if registration fails with 400 (already exists), try to login directly.
    if response.status_code == 400 and "already registered" in response.text:
        pass # User likely exists, proceed to login
    else:
        assert response.status_code == 200 # Expect 200 if new user or other non-conflict error

    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    # Use data= for form encoding with OAuth2PasswordRequestForm
    response = client.post("/users/login", data=login_data)
    assert response.status_code == 200, f"Login failed for testuser_conftest: {response.text}"
    token_data = response.json()
    return token_data["access_token"]
