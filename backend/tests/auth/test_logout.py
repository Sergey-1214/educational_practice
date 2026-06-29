import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.auth.schemas import LogoutResponse
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
def valid_data():
    return {"refresh_token": "valid_refresh_token"}


class TestLogout:
    """Tests for POST /api/v1/auth/logout"""

    def test_logout_success(self, client, mock_service, valid_data):
        """Should return 200 when logout is successful"""
        mock_service.logout.return_value = LogoutResponse(
            detail="Logged out successfully"
        )

        response = client.post("/api/v1/auth/logout", json=valid_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["detail"] == "Logged out successfully"
        mock_service.logout.assert_called_once()

    def test_logout_invalid_token(self, client, mock_service, valid_data):
        """Should return 401 when refresh token is invalid"""
        from fastapi import HTTPException
        mock_service.logout.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token."
        )

        response = client.post("/api/v1/auth/logout", json=valid_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_inactive_user(self, client, mock_service, valid_data):
        """Should return 403 when user is inactive"""
        from fastapi import HTTPException
        mock_service.logout.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is inactive or forbidden."
        )

        response = client.post("/api/v1/auth/logout", json=valid_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_logout_missing_token(self, client, mock_service):
        """Should return 422 when refresh_token is missing"""
        response = client.post("/api/v1/auth/logout", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.logout.assert_not_called()

    def test_logout_empty_token(self, client, mock_service):
        """Should return 422 when refresh_token is empty"""
        invalid_data = {"refresh_token": ""}

        response = client.post("/api/v1/auth/logout", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.logout.assert_not_called()