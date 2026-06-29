import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.auth.schemas import UserRead, RegisterResponse
from app.modules.auth.router import get_auth_service


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def mock_service(client):
    with patch("app.modules.auth.router.AuthService") as mock:
        service = AsyncMock()
        mock.return_value = service
        
        async def override():
            return service
        
        client.app.dependency_overrides[get_auth_service] = override
        yield service
        client.app.dependency_overrides.clear()


@pytest.fixture
def user_data():
    return UserRead(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
        created_at=datetime.now()
    )


@pytest.fixture
def valid_data():
    return {"email": "test@example.com", "password": "TestPassword123"}


class TestRegister:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client, mock_service, user_data, valid_data):
        """Should return 201 when registration is successful"""
        mock_service.register.return_value = RegisterResponse(user=user_data)

        response = client.post("/api/v1/auth/register", json=valid_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user"]["email"] == valid_data["email"]
        assert data["user"]["id"] == str(user_data.id)
        mock_service.register.assert_called_once()

    def test_register_conflict(self, client, mock_service, valid_data):
        """Should return 409 when email already exists"""
        from fastapi import HTTPException
        mock_service.register.side_effect = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists."
        )

        response = client.post("/api/v1/auth/register", json=valid_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]

    def test_register_invalid_email(self, client, mock_service):
        """Should return 422 for invalid email format"""
        invalid_data = {"email": "invalid", "password": "TestPassword123"}

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.register.assert_not_called()

    def test_register_short_password(self, client, mock_service):
        """Should return 422 for password shorter than 8 chars"""
        invalid_data = {"email": "test@example.com", "password": "short"}

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.register.assert_not_called()

    def test_register_missing_fields(self, client, mock_service):
        """Should return 422 when required fields are missing"""
        response = client.post("/api/v1/auth/register", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.register.assert_not_called()