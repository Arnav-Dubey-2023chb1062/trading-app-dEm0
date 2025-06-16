from fastapi.testclient import TestClient
from fastapi import status
import pytest # For pytest.fixture if needed locally, or just use conftest
from decimal import Decimal # Import Decimal

# client and get_test_user_token fixtures are from conftest.py

@pytest.fixture(scope="function")
def setup_portfolio_for_trades(client: TestClient, get_test_user_token: str) -> tuple[str, int]:
    """
    Creates a portfolio for the test user and returns the token and portfolio_id.
    """
    token = get_test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    portfolio_data = {"portfolio_name": "Trade Test Portfolio"}
    response = client.post("/portfolios/", json=portfolio_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    portfolio_id = response.json()["portfolio_id"]
    return token, portfolio_id

def test_create_trade_success(client: TestClient, setup_portfolio_for_trades: tuple[str, int]):
    token, portfolio_id = setup_portfolio_for_trades
    headers = {"Authorization": f"Bearer {token}"}

    trade_data = {
        "ticker_symbol": "AAPL",
        "trade_type": "BUY",
        "quantity": 10,
        "price": 150.25
    }
    response = client.post(f"/portfolios/{portfolio_id}/trades/", json=trade_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["ticker_symbol"] == trade_data["ticker_symbol"]
    assert response_data["portfolio_id"] == portfolio_id
    assert "trade_id" in response_data
    assert "timestamp" in response_data

def test_list_trades_for_portfolio(client: TestClient, setup_portfolio_for_trades: tuple[str, int]):
    token, portfolio_id = setup_portfolio_for_trades
    headers = {"Authorization": f"Bearer {token}"}

    # Create some trades
    client.post(f"/portfolios/{portfolio_id}/trades/", json={"ticker_symbol": "MSFT", "trade_type": "BUY", "quantity": 5, "price": 300.00}, headers=headers)
    client.post(f"/portfolios/{portfolio_id}/trades/", json={"ticker_symbol": "GOOG", "trade_type": "SELL", "quantity": 2, "price": 2500.50}, headers=headers)

    response = client.get(f"/portfolios/{portfolio_id}/trades/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    trades = response.json()
    assert isinstance(trades, list)
    assert len(trades) >= 2 # >= because other tests might add trades if IDs are not perfectly isolated
    assert trades[0]["ticker_symbol"] == "MSFT"
    assert trades[1]["ticker_symbol"] == "GOOG"


def test_get_specific_trade(client: TestClient, setup_portfolio_for_trades: tuple[str, int]):
    token, portfolio_id = setup_portfolio_for_trades
    headers = {"Authorization": f"Bearer {token}"}

    create_trade_resp = client.post(f"/portfolios/{portfolio_id}/trades/", json={"ticker_symbol": "TSLA", "trade_type": "BUY", "quantity": 3, "price": 700.00}, headers=headers)
    assert create_trade_resp.status_code == status.HTTP_201_CREATED
    trade_id = create_trade_resp.json()["trade_id"]

    response = client.get(f"/portfolios/{portfolio_id}/trades/{trade_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    trade = response.json()
    assert trade["trade_id"] == trade_id
    assert trade["ticker_symbol"] == "TSLA"


def test_update_trade_success(client: TestClient, setup_portfolio_for_trades: tuple[str, int]):
    token, portfolio_id = setup_portfolio_for_trades
    headers = {"Authorization": f"Bearer {token}"}

    create_trade_resp = client.post(f"/portfolios/{portfolio_id}/trades/", json={"ticker_symbol": "NVDA", "trade_type": "BUY", "quantity": 10, "price": 200.00}, headers=headers)
    trade_id = create_trade_resp.json()["trade_id"]

    update_data = {"ticker_symbol": "NVDA", "trade_type": "SELL", "quantity": 5, "price": 210.00}
    response = client.put(f"/portfolios/{portfolio_id}/trades/{trade_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    updated_trade = response.json()
    assert updated_trade["quantity"] == 5
    assert updated_trade["trade_type"] == "SELL"
    assert Decimal(updated_trade["price"]) == Decimal("210.00") # Compare as Decimal

def test_delete_trade_success(client: TestClient, setup_portfolio_for_trades: tuple[str, int]):
    token, portfolio_id = setup_portfolio_for_trades
    headers = {"Authorization": f"Bearer {token}"}

    create_trade_resp = client.post(f"/portfolios/{portfolio_id}/trades/", json={"ticker_symbol": "AMZN", "trade_type": "BUY", "quantity": 1, "price": 3000.00}, headers=headers)
    trade_id = create_trade_resp.json()["trade_id"]

    delete_response = client.delete(f"/portfolios/{portfolio_id}/trades/{trade_id}", headers=headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    get_response = client.get(f"/portfolios/{portfolio_id}/trades/{trade_id}", headers=headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_access_trades_for_unowned_portfolio(client: TestClient, get_test_user_token: str, setup_portfolio_for_trades: tuple[str, int]):
    # setup_portfolio_for_trades creates a portfolio for "testuser_conftest" (User 1)
    token_user1, portfolio_id_user1 = setup_portfolio_for_trades

    # Create a second user (User 2)
    user2_data = {"username": "user2_trade_test", "email": "user2_trade@example.com", "password": "password_user2_trade"}
    reg_response = client.post("/users/register", json=user2_data)
    # It's possible this user already exists if test_portfolio_api created it and db wasn't fully cleared for it
    # For robustness, we should handle this or ensure unique usernames across test files for such multi-user tests.
    # For now, assume it's fine or the conftest clears users well enough.
    assert reg_response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST] # Allow if already exists from other test

    login_payload_user2 = {"username": user2_data["username"], "password": user2_data["password"]}
    login_response_user2 = client.post("/users/login", data=login_payload_user2)
    assert login_response_user2.status_code == status.HTTP_200_OK
    token_user2 = login_response_user2.json()["access_token"]
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}

    # User 2 tries to list trades for User 1's portfolio
    response = client.get(f"/portfolios/{portfolio_id_user1}/trades/", headers=headers_user2)
    # This should fail at the portfolio ownership check level
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Portfolio not found or not owned by user" in response.json()["detail"]

    # User 2 tries to create a trade in User 1's portfolio
    trade_data_user2 = {"ticker_symbol": "HACK", "trade_type": "BUY", "quantity": 1, "price": 1.00}
    response_create_user2 = client.post(f"/portfolios/{portfolio_id_user1}/trades/", json=trade_data_user2, headers=headers_user2)
    assert response_create_user2.status_code == status.HTTP_404_NOT_FOUND
    assert "Portfolio not found or not owned by user" in response_create_user2.json()["detail"]
