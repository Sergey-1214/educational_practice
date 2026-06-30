import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.history.schemas import SearchHistoryDeleteResponse
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


@pytest.fixture
def history_item_id():
    return "550e8400-e29b-41d4-a716-446655440000"


class TestDeleteHistoryItem:
    """Tests for DELETE /api/v1/history/{history_item_id}"""

    def test_delete_history_item_success(self, client, mock_service, mock_current_user, history_item_id):
        """Should return 200 when history item is deleted successfully"""
        mock_service.delete_history_item.return_value = SearchHistoryDeleteResponse(
            deleted=True
        )

        response = client.delete(f"/api/v1/history/{history_item_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted"] is True
        
        mock_service.delete_history_item.assert_called_once_with(
            history_item_id=history_item_id,
            user_id=mock_current_user.id
        )

    def test_delete_history_item_not_found(self, client, mock_service, history_item_id):
        """Should return 404 when history item does not exist"""
        from fastapi import HTTPException
        mock_service.delete_history_item.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History item not found."
        )

        response = client.delete(f"/api/v1/history/{history_item_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_delete_history_item_invalid_id(self, client, mock_service):
        """Should return 422 when history_item_id is invalid UUID format"""
        response = client.delete("/api/v1/history/invalid-id")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.delete_history_item.assert_not_called()