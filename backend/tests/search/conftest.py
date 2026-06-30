import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.search.schemas import SearchResponse, SearchResult
from app.modules.search.service import SearchService
from app.modules.auth.models import User
from app.common.dependencies import get_current_user, get_db_session


@pytest.fixture
def test_client():
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_current_user():
    """Create a mock current user"""
    user = AsyncMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_search_service(test_client, mock_db_session, mock_current_user):
    """Create mock search service and override dependencies"""
    with patch("app.modules.search.router.SearchService") as mock:
        service_instance = AsyncMock(spec=SearchService)
        mock.return_value = service_instance
        
        # Override get_db_session dependency
        async def override_get_db_session():
            yield mock_db_session
        
        # Override get_current_user dependency
        async def override_get_current_user():
            return mock_current_user
        
        test_client.app.dependency_overrides[get_db_session] = override_get_db_session
        test_client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        yield service_instance
        
        # Clean up
        test_client.app.dependency_overrides.clear()


@pytest.fixture
def sample_search_result():
    return SearchResult(
        chunk_id="chunk_123",
        document_id=str(uuid4()),
        file_name="test.pdf",
        page=1,
        text="This is a <mark>test</mark> search result",
        score=0.95
    )


@pytest.fixture
def sample_search_response(sample_search_result):
    return SearchResponse(
        query="test search",
        document_id=None,
        items=[sample_search_result],
        total=1,
        limit=10,
        offset=0
    )


@pytest.fixture
def valid_document_id():
    return "550e8400-e29b-41d4-a716-446655440000"