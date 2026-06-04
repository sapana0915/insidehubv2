from unittest.mock import MagicMock, patch

import pytest

from app.users.schemas import UserCreate
from app.users.services import UserService


def test_health_check(client):
    with patch("redis.from_url") as mock_redis:
        mock_redis.return_value.ping.return_value = True
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"] is True
    assert data["checks"]["redis"] is True


def test_user_registration(db):
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User",
    )
    user = UserService.create(db, user_data)

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password is not None
    assert user.updated_at is None


def test_register_endpoint(client):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "newuser@example.com"
    assert body["updated_at"] is None
