from fastapi.testclient import TestClient
from fastapi import status

# client fixture from conftest.py
# get_test_user_token fixture from conftest.py

def test_create_portfolio_success(client: TestClient, get_test_user_token: str):
    token = get_test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    portfolio_data = {"portfolio_name": "My First Portfolio"}
    response = client.post("/portfolios/", json=portfolio_data, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["portfolio_name"] == portfolio_data["portfolio_name"]
    assert "portfolio_id" in response_data
    assert "user_id" in response_data # user_id should match the test user's ID

def test_list_portfolios_for_user(client: TestClient, get_test_user_token: str):
    token = get_test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    # Create a portfolio first
    client.post("/portfolios/", json={"portfolio_name": "Portfolio 1"}, headers=headers)
    client.post("/portfolios/", json={"portfolio_name": "Portfolio 2"}, headers=headers)

    response = client.get("/portfolios/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    portfolios = response.json()
    assert isinstance(portfolios, list)
    assert len(portfolios) >= 2 # Could be more if other tests ran and didn't clean up perfectly for user_id association
                               # The conftest clear should handle this for this specific user.
                               # If user_id is predictable (e.g. always 1 for get_test_user_token due to reset), this is more robust.
    assert portfolios[0]["portfolio_name"] == "Portfolio 1"
    assert portfolios[1]["portfolio_name"] == "Portfolio 2"

def test_get_specific_portfolio_owned_by_user(client: TestClient, get_test_user_token: str):
    token = get_test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/portfolios/", json={"portfolio_name": "Specific Portfolio"}, headers=headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    portfolio_id = create_response.json()["portfolio_id"]

    response = client.get(f"/portfolios/{portfolio_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    portfolio_data = response.json()
    assert portfolio_data["portfolio_id"] == portfolio_id
    assert portfolio_data["portfolio_name"] == "Specific Portfolio"

def test_get_portfolio_not_owned_forbidden_or_not_found(client: TestClient, get_test_user_token: str):
    # This test requires two users.
    # User 1 (get_test_user_token) creates a portfolio.
    # User 2 tries to access it.

    # User 1 setup
    token_user1 = get_test_user_token
    headers_user1 = {"Authorization": f"Bearer {token_user1}"}
    portfolio_name_user1 = "User1_Portfolio"
    create_resp_user1 = client.post("/portfolios/", json={"portfolio_name": portfolio_name_user1}, headers=headers_user1)
    assert create_resp_user1.status_code == status.HTTP_201_CREATED
    portfolio_id_user1 = create_resp_user1.json()["portfolio_id"]

    # User 2 setup (register and login a new user)
    user2_data = {"username": "user2_portfolio_test", "email": "user2_pt@example.com", "password": "password_user2"}
    client.post("/users/register", json=user2_data) # User ID counter in user_routes will increment
    login_resp_user2 = client.post("/users/login", data={"username": user2_data["username"], "password": user2_data["password"]})
    token_user2 = login_resp_user2.json()["access_token"]
    headers_user2 = {"Authorization": f"Bearer {token_user2}"}

    # User 2 tries to get User 1's portfolio
    response_user2_get = client.get(f"/portfolios/{portfolio_id_user1}", headers=headers_user2)
    assert response_user2_get.status_code == status.HTTP_404_NOT_FOUND # As per current implementation
    assert "Portfolio not found or not owned by user" in response_user2_get.json()["detail"]


def test_update_portfolio_success(client: TestClient, get_test_user_token: str):
    token = get_test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/portfolios/", json={"portfolio_name": "Original Name"}, headers=headers)
    portfolio_id = create_response.json()["portfolio_id"]

    update_data = {"portfolio_name": "Updated Name"}
    response = client.put(f"/portfolios/{portfolio_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["portfolio_name"] == "Updated Name"
    assert response_data["portfolio_id"] == portfolio_id

def test_delete_portfolio_success(client: TestClient, get_test_user_token: str):
    token = get_test_user_token
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post("/portfolios/", json={"portfolio_name": "To Be Deleted"}, headers=headers)
    portfolio_id = create_response.json()["portfolio_id"]

    delete_response = client.delete(f"/portfolios/{portfolio_id}", headers=headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's actually deleted
    get_response = client.get(f"/portfolios/{portfolio_id}", headers=headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
