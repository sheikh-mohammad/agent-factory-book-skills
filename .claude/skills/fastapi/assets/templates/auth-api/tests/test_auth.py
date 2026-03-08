import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_session
from app.models import User
from app.auth.security import get_password_hash

# Test client
client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data

def test_login_user():
    response = client.post("/auth/token", data={
        "username": "testuser",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user_unauthorized():
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_get_current_user_authorized():
    # First register a user
    client.post("/auth/register", json={
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "password123"
    })

    # Then login to get token
    login_response = client.post("/auth/token", data={
        "username": "testuser2",
        "password": "password123"
    })

    token = login_response.json()["access_token"]

    # Use token to access protected endpoint
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser2"