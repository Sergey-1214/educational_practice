import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.search.schemas import SearchResponse, SearchResult
from app.modules.search.service import SearchService
from app.common.dependencies import get_current_user, get_db_session


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    user = AsyncMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_search_service():
    """Mock the SearchService class"""
    with patch("app.modules.search.router.SearchService") as mock:
        service_instance = AsyncMock(spec=SearchService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def client_with_overrides(client, mock_current_user, mock_db_session, mock_search_service):
    """Client with all dependencies overridden"""
    async def override_get_current_user():
        return mock_current_user
    
    async def override_get_db_session():
        yield mock_db_session
    
    client.app.dependency_overrides[get_current_user] = override_get_current_user
    client.app.dependency_overrides[get_db_session] = override_get_db_session
    
    yield client
    
    client.app.dependency_overrides.clear()


@pytest.fixture
def search_result():
    return SearchResult(
        chunk_id="chunk_123",
        document_id=str(uuid4()),
        file_name="test.pdf",
        page=1,
        text="This is a <mark>test</mark> search result",
        score=0.95
    )


@pytest.fixture
def search_response(search_result):
    return SearchResponse(
        query="test",
        document_id=None,
        items=[search_result],
        total=1,
        limit=10,
        offset=0
    )


class TestSearch:
    """Tests for GET /api/v1/search"""

    def test_search_success(self, client_with_overrides, mock_search_service, search_response):
        """Should return 200 with search results"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=test")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "test"
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["file_name"] == "test.pdf"
        assert data["items"][0]["text"] == "This is a <mark>test</mark> search result"
        
        # Verify SearchService was instantiated and called correctly
        mock_search_service.search.assert_called_once()

    def test_search_with_document_filter(self, client_with_overrides, mock_search_service, search_response):
        """Should return 200 when searching within specific document"""
        mock_search_service.search.return_value = search_response

        document_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client_with_overrides.get(f"/api/v1/search?q=test&document_id={document_id}")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify the search was called with document_id
        call_args = mock_search_service.search.call_args
        assert call_args[0][0].document_id is not None
        assert str(call_args[0][0].document_id) == document_id

    def test_search_with_pagination(self, client_with_overrides, mock_search_service, search_response):
        """Should return 200 with paginated search results"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=test&limit=5&offset=10")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify pagination params
        call_args = mock_search_service.search.call_args
        assert call_args[0][0].limit == 5
        assert call_args[0][0].offset == 10

    def test_search_with_default_pagination(self, client_with_overrides, mock_search_service, search_response):
        """Should use default pagination values when not specified"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=test")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify default pagination params
        call_args = mock_search_service.search.call_args
        assert call_args[0][0].limit == 10  # default
        assert call_args[0][0].offset == 0  # default

    def test_search_empty_query(self, client_with_overrides, mock_search_service):
        """Should return 422 when query is empty (min_length=1)"""
        response = client_with_overrides.get("/api/v1/search?q=")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_query_too_long(self, client_with_overrides, mock_search_service):
        """Should return 422 when query exceeds 300 characters"""
        long_query = "a" * 301
        response = client_with_overrides.get(f"/api/v1/search?q={long_query}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_missing_query(self, client_with_overrides, mock_search_service):
        """Should return 422 when query parameter is missing"""
        response = client_with_overrides.get("/api/v1/search")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_invalid_limit_above_max(self, client_with_overrides, mock_search_service):
        """Should return 422 when limit exceeds max (50)"""
        response = client_with_overrides.get("/api/v1/search?q=test&limit=51")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_invalid_limit_below_min(self, client_with_overrides, mock_search_service):
        """Should return 422 when limit is less than min (1)"""
        response = client_with_overrides.get("/api/v1/search?q=test&limit=0")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_invalid_offset_negative(self, client_with_overrides, mock_search_service):
        """Should return 422 when offset is negative"""
        response = client_with_overrides.get("/api/v1/search?q=test&offset=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_invalid_document_id_format(self, client_with_overrides, mock_search_service):
        """Should return 422 when document_id is invalid UUID format"""
        response = client_with_overrides.get("/api/v1/search?q=test&document_id=invalid-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_search_service.search.assert_not_called()

    def test_search_document_not_found(self, client_with_overrides, mock_search_service):
        """Should return 404 when document filter points to missing document"""
        from fastapi import HTTPException
        mock_search_service.search.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document filter points to a missing document."
        )

        document_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client_with_overrides.get(f"/api/v1/search?q=test&document_id={document_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "missing document" in response.json()["detail"]

    def test_search_document_forbidden(self, client_with_overrides, mock_search_service):
        """Should return 403 when searching inside document belonging to another user"""
        from fastapi import HTTPException
        mock_search_service.search.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Search inside a document that belongs to another user."
        )

        document_id = "550e8400-e29b-41d4-a716-446655440000"
        response = client_with_overrides.get(f"/api/v1/search?q=test&document_id={document_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "belongs to another user" in response.json()["detail"]

    def test_search_unauthorized(self, client, mock_search_service):
        """Should return 401 when authentication is missing"""
        from fastapi import HTTPException
        from app.common.dependencies import get_current_user
        
        async def override_get_current_user():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing access token."
            )
        
        client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        response = client.get("/api/v1/search?q=test")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access token" in response.json()["detail"].lower()
        
        client.app.dependency_overrides.clear()

    def test_search_elasticsearch_error(self, client_with_overrides, mock_search_service):
        """Should return 500 when Elasticsearch search fails"""
        from fastapi import HTTPException
        mock_search_service.search.side_effect = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Elasticsearch search failed."
        )

        response = client_with_overrides.get("/api/v1/search?q=test")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Elasticsearch" in response.json()["detail"]

    def test_search_with_unicode_characters(self, client_with_overrides, mock_search_service, search_response):
        """Should handle search queries with unicode characters"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=учебная%20практика")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify the query was decoded correctly
        call_args = mock_search_service.search.call_args
        assert call_args[0][0].query == "учебная практика"

    def test_search_with_special_characters(self, client_with_overrides, mock_search_service, search_response):
        """Should handle search queries with special characters"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=test%20%26%20search")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify the query was decoded correctly
        call_args = mock_search_service.search.call_args
        assert "test & search" in call_args[0][0].query

    def test_search_with_document_id_as_none(self, client_with_overrides, mock_search_service, search_response):
        """Should handle document_id=None (search all documents)"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=test")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify document_id is None
        call_args = mock_search_service.search.call_args
        assert call_args[0][0].document_id is None

    def test_search_verifies_user_id_passed(self, client_with_overrides, mock_search_service, 
                                            search_response, mock_current_user):
        """Should verify that user_id is passed to the search service"""
        mock_search_service.search.return_value = search_response

        response = client_with_overrides.get("/api/v1/search?q=test")

        assert response.status_code == status.HTTP_200_OK
        mock_search_service.search.assert_called_once()
        
        # Verify user_id was passed correctly
        call_args = mock_search_service.search.call_args
        assert call_args[0][1] == mock_current_user.id  # user_id is the second argument