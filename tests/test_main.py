import pytest
from fastapi.testclient import TestClient
from app.main import app  

client = TestClient(app)


def test_root_redirects_to_login():
    response = client.get("/")
    if response.status_code == 303:
        assert response.headers["location"].endswith("/login")
    else:
        assert response.status_code == 200



def test_home_redirects_without_login():
    response = client.get("/home")
    # Update according to the application's actual behavior
    assert response.status_code in [401, 307, 303]

def test_create_user_valid_user():
    response = client.post("/users", json={"username": "unique_testuser", "password": "testpassword"})
    assert response.status_code == 201, f"Response data: {response.json()}"


def test_create_user_duplicate_username():
    # Trying to register the same user again should raise a 400 error
    client.post("/users", json={"username": "unique_user", "password": "testpassword"})
    response = client.post("/users", json={"username": "unique_user", "password": "testpassword"})
    assert response.status_code == 400


def test_get_token_with_valid_credentials():
    # Assume 'valid_user' was created before with password 'valid_password'
    client.post("/users", json={"username": "valid_user", "password": "valid_password"})
    response = client.get("/get-token?username=valid_user&password=valid_password")
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_get_token_with_invalid_credentials():
    response = client.get("/get-token?username=invalid_user&password=invalid_password")
    assert response.status_code == 401


def test_login_get_page():
    response = client.get("/login")
    assert response.status_code == 200


