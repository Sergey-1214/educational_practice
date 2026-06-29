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
from app.modules.history.schemas import SearchHistoryRead, SearchHistoryListResponse
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
    user.email = "test@example.com"
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
def history_item(mock_current_user):
    return SearchHistoryRead(
        id=uuid4(),
        user_id=mock_current_user.id,
        document_id=uuid4(),
        query="test search",
        results_count=5,
        created_at=datetime.now()
    )


@pytest.fixture
def history_list(history_item):
    return SearchHistoryListResponse(
        items=[history_item],
        total=1
    )


class TestGetHistory:
    """Tests for GET /api/v1/history"""

    def test_get_history_success(self, client, mock_service, history_list, mock_current_user):
        """Should return 200 with list of history items"""
        mock_service.list_user_history.return_value = history_list

        response = client.get("/api/v1/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["query"] == "test search"
        assert data["items"][0]["user_id"] == str(mock_current_user.id)
        
        mock_service.list_user_history.assert_called_once_with(
            user_id=mock_current_user.id,
            limit=20,
            offset=0
        )

    def test_get_history_with_pagination(self, client, mock_service, history_list, mock_current_user):
        """Should return 200 with paginated history"""
        mock_service.list_user_history.return_value = history_list

        response = client.get("/api/v1/history?limit=10&offset=5")

        assert response.status_code == status.HTTP_200_OK
        mock_service.list_user_history.assert_called_once_with(
            user_id=mock_current_user.id,
            limit=10,
            offset=5
        )

    def test_get_history_invalid_limit(self, client, mock_service):
        """Should return 422 when limit exceeds max (100)"""
        response = client.get("/api/v1/history?limit=200")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.list_user_history.assert_not_called()

    def test_get_history_invalid_offset(self, client, mock_service):
        """Should return 422 when offset is negative"""
        response = client.get("/api/v1/history?offset=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.list_user_history.assert_not_called()