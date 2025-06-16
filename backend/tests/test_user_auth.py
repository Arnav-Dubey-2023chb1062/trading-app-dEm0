from fastapi.testclient import TestClient
from fastapi import status # For status codes

# Assuming conftest.py provides the 'client' fixture

def test_user_registration_success(client: TestClient):
    user_data = {"username": "testuser1", "email": "test1@example.com", "password": "password123"}
    response = client.post("/users/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK # Assuming 200 from User model return
    response_data = response.json()
    assert response_data["username"] == user_data["username"]
    assert response_data["email"] == user_data["email"]
    assert "user_id" in response_data
    assert "hashed_password" not in response_data # Ensure password is not returned

def test_user_registration_existing_username(client: TestClient):
    user_data = {"username": "testuser2", "email": "test2@example.com", "password": "password123"}
    # First registration should succeed
    response1 = client.post("/users/register", json=user_data)
    assert response1.status_code == status.HTTP_200_OK

    # Second registration with the same username should fail
    user_data_conflict = {"username": "testuser2", "email": "test2_conflict@example.com", "password": "password456"}
    response2 = client.post("/users/register", json=user_data_conflict)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response2.json()["detail"]

def test_user_login_success(client: TestClient):
    # First, register a user
    user_data = {"username": "loginuser", "email": "login@example.com", "password": "loginpass"}
    reg_response = client.post("/users/register", json=user_data)
    assert reg_response.status_code == status.HTTP_200_OK

    # Attempt login
    login_payload = {"username": "loginuser", "password": "loginpass"}
    # For OAuth2PasswordRequestForm, data should be sent as form data, not JSON
    response = client.post("/users/login", data=login_payload)
    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_user_login_incorrect_password(client: TestClient):
    user_data = {"username": "loginfailuser", "email": "loginfail@example.com", "password": "correctpass"}
    reg_response = client.post("/users/register", json=user_data)
    assert reg_response.status_code == status.HTTP_200_OK

    login_payload = {"username": "loginfailuser", "password": "wrongpassword"}
    response = client.post("/users/login", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]

def test_user_login_nonexistent_user(client: TestClient):
    login_payload = {"username": "nonexistentuser", "password": "anypassword"}
    response = client.post("/users/login", data=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]

def test_access_protected_route_no_token(client: TestClient):
    # Using GET /portfolios/ as an example of a protected route
    response = client.get("/portfolios/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # FastAPI's default for missing token in OAuth2PasswordBearer is often a 403 if not handled,
    # but 401 is more standard if the scheme is processed. Let's assume 401.
    # The detail might vary based on FastAPI internals or if a custom handler is made.
    # It might also be {"detail":"Not authenticated"} or similar.
    # For now, checking status code is primary.
    # assert response.json()["detail"] == "Not authenticated"
    # The default behavior for OAuth2PasswordBearer if no token is provided is to return 401 with "Not authenticated"

def test_access_protected_route_invalid_token(client: TestClient):
    response = client.get("/portfolios/", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Detail for invalid token comes from our get_current_user function
    assert response.json()["detail"] == "Could not validate credentials"

def test_access_protected_route_valid_token(client: TestClient, get_test_user_token: str):
    # get_test_user_token fixture provides a valid token
    headers = {"Authorization": f"Bearer {get_test_user_token}"}
    response = client.get("/portfolios/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    # Expect an empty list if no portfolios created for this user yet
    assert response.json() == []
