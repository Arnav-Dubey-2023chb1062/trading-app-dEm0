import pytest
from fastapi.testclient import TestClient
from typing import Generator, Any

# Import the main FastAPI app
from main import app # Corrected import path

# Import the main FastAPI app
from main import app # Corrected import path

# Import reset functions
from app.routes.user_routes import reset_user_db_and_ids_for_test
from app.services.auth_service import reset_auth_service_db_for_test
from app.routes.portfolio_routes import reset_portfolio_db_and_ids_for_test
from app.routes.trade_routes import reset_trade_db_and_ids_for_test


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, Any, None]:
    # Reset all data stores and ID counters before each test
    reset_user_db_and_ids_for_test()
    reset_auth_service_db_for_test()
    reset_portfolio_db_and_ids_for_test()
    reset_trade_db_and_ids_for_test()

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def get_test_user_token(client: TestClient) -> str:
    """
    Registers a test user and returns their auth token.
    Relies on the main 'client' fixture to have already reset relevant DBs including user IDs.
    """
    # The main 'client' fixture (which runs before this one if both are used by a test)
    # has already called all reset functions, including user DBs and ID counters.

    user_data = {
        "username": "testuser_conftest",
        "email": "test_conftest@example.com",
        "password": "testpassword_conftest"
    }
    response = client.post("/users/register", json=user_data)
    assert response.status_code == 200 # Assuming User model is returned on register

    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    # Use data= for form encoding with OAuth2PasswordRequestForm
    response = client.post("/users/login", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    return token_data["access_token"]
