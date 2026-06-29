import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.history.schemas import SearchHistoryClearResponse
from app.modules.history.router import get_history_service
from app.common.dependencies import get_current_user


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    user = AsyncMock()
    user.id = uuid4()
    return user


@pytest.fixture
def mock_service(client, mock_current_user):
    with patch("app.modules.history.router.SearchHistoryService") as mock:
        service = AsyncMock()
        mock.return_value = service
        
        async def override_service():
            return service
        
        async def override_user():
            return mock_current_user
        
        client.app.dependency_overrides[get_history_service] = override_service
        client.app.dependency_overrides[get_current_user] = override_user
        
        yield service
        
        client.app.dependency_overrides.clear()


class TestClearHistory:
    """Tests for DELETE /api/v1/history"""

    def test_clear_history_success(self, client, mock_service, mock_current_user):
        """Should return 200 when history is cleared successfully"""
        mock_service.clear_user_history.return_value = SearchHistoryClearResponse(
            deleted_count=5
        )

        response = client.delete("/api/v1/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 5
        
        mock_service.clear_user_history.assert_called_once_with(
            mock_current_user.id
        )

    def test_clear_history_no_items(self, client, mock_service, mock_current_user):
        """Should return 200 with deleted_count=0 when no history to clear"""
        mock_service.clear_user_history.return_value = SearchHistoryClearResponse(
            deleted_count=0
        )

        response = client.delete("/api/v1/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0
        
        mock_service.clear_user_history.assert_called_once_with(
            mock_current_user.id
        )