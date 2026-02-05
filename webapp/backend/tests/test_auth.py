"""
Tests for authentication endpoints.
"""

import pytest
from app.models.user import User


def test_register_user(client, db_session):
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "name": "newuser",
            "password": "securepass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "newuser"
    assert "id" in data

    # Verify user in database
    user = db_session.query(User).filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.is_verified is False
    assert user.credits == 0


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",  # Already exists
            "name": "anotheruser",
            "password": "securepass123"
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with nonexistent user."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
    )

    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user with valid token."""
    response = client.get("/api/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "testuser"
    assert data["credits"] == 10


def test_get_current_user_no_token(client):
    """Test getting current user without token."""
    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401


def test_password_reset_request(client, test_user):
    """Test password reset request."""
    response = client.post(
        "/api/auth/password-reset-request",
        json={"email": "test@example.com"}
    )

    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()


def test_get_user_credits(client, auth_headers):
    """Test getting user credits."""
    response = client.get("/api/users/credits", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["credits"] == 10
    assert "pending_jobs" in data
