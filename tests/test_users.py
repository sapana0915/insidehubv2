import pytest
from app.users.services import UserService
from app.users.schemas import UserCreate


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_user_registration(db):
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User",
    )
    user = await UserService.create(db, user_data)

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password is not None


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
    assert response.json()["email"] == "newuser@example.com"
