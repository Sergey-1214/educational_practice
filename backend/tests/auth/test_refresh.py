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
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer"
    )


@pytest.fixture
def valid_data():
    return {"refresh_token": "valid_refresh_token"}


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh"""

    def test_refresh_success(self, client, mock_service, tokens, valid_data):
        """Should return 200 with new token pair when refresh is valid"""
        mock_service.refresh_token.return_value = tokens

        response = client.post("/api/v1/auth/refresh", json=valid_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == tokens.access_token
        assert data["refresh_token"] == tokens.refresh_token
        mock_service.refresh_token.assert_called_once()

    def test_refresh_invalid_token(self, client, mock_service, valid_data):
        """Should return 401 when refresh token is invalid"""
        from fastapi import HTTPException
        mock_service.refresh_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token."
        )

        response = client.post("/api/v1/auth/refresh", json=valid_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_inactive_user(self, client, mock_service, valid_data):
        """Should return 403 when user is inactive"""
        from fastapi import HTTPException
        mock_service.refresh_token.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is inactive or forbidden."
        )

        response = client.post("/api/v1/auth/refresh", json=valid_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_refresh_missing_token(self, client, mock_service):
        """Should return 422 when refresh_token is missing"""
        response = client.post("/api/v1/auth/refresh", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.refresh_token.assert_not_called()

    def test_refresh_empty_token(self, client, mock_service):
        """Should return 422 when refresh_token is empty"""
        invalid_data = {"refresh_token": ""}

        response = client.post("/api/v1/auth/refresh", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.refresh_token.assert_not_called()