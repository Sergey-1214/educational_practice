import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.auth.schemas import TokenResponse
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
def tokens():
    return TokenResponse(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_type="bearer"
    )


@pytest.fixture
def valid_data():
    return {"email": "test@example.com", "password": "TestPassword123"}


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, mock_service, tokens, valid_data):
        """Should return 200 with tokens when credentials are valid"""
        mock_service.login.return_value = tokens

        response = client.post("/api/v1/auth/login", json=valid_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == tokens.access_token
        assert data["refresh_token"] == tokens.refresh_token
        mock_service.login.assert_called_once()

    def test_login_invalid_credentials(self, client, mock_service, valid_data):
        """Should return 401 when credentials are invalid"""
        from fastapi import HTTPException
        mock_service.login.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

        response = client.post("/api/v1/auth/login", json=valid_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_inactive_user(self, client, mock_service, valid_data):
        """Should return 403 when user is inactive"""
        from fastapi import HTTPException
        mock_service.login.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive."
        )

        response = client.post("/api/v1/auth/login", json=valid_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in response.json()["detail"].lower()

    def test_login_invalid_email_format(self, client, mock_service):
        """Should return 422 for invalid email format"""
        invalid_data = {"email": "invalid", "password": "TestPassword123"}

        response = client.post("/api/v1/auth/login", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.login.assert_not_called()

    def test_login_short_password(self, client, mock_service):
        """Should return 422 for password shorter than 8 chars"""
        invalid_data = {"email": "test@example.com", "password": "short"}

        response = client.post("/api/v1/auth/login", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.login.assert_not_called()

    def test_login_missing_fields(self, client, mock_service):
        """Should return 422 when required fields are missing"""
        response = client.post("/api/v1/auth/login", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.login.assert_not_called()