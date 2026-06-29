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
from app.modules.documents.schemas import DocumentRead, DocumentsListResponse, DocumentStatus
from app.modules.documents.router import get_documents_service  # Changed to plural
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
    return user


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_documents_service():
    """Mock the DocumentsService class"""
    with patch("app.modules.documents.router.DocumentsService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def client_with_overrides(client, mock_current_user, mock_db_session, mock_documents_service):
    """Client with all dependencies overridden"""
    async def override_get_current_user():
        return mock_current_user
    
    async def override_get_db_session():
        yield mock_db_session
    
    async def override_get_documents_service():
        return mock_documents_service
    
    client.app.dependency_overrides[get_current_user] = override_get_current_user
    client.app.dependency_overrides[get_db_session] = override_get_db_session
    client.app.dependency_overrides[get_documents_service] = override_get_documents_service
    
    yield client, mock_documents_service
    
    client.app.dependency_overrides.clear()


@pytest.fixture
def sample_document():
    return DocumentRead(
        id=uuid4(),
        user_id=uuid4(),
        file_name="test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        status=DocumentStatus.PROCESSED,
        chunks_count=10,
        error_message=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def document_list(sample_document):
    return DocumentsListResponse(
        items=[sample_document],
        total=1
    )


class TestGetDocuments:
    """Tests for GET /api/v1/documents"""

    def test_get_documents_success(self, client_with_overrides, document_list):
        """Should return 200 with list of documents"""
        client, mock_service = client_with_overrides
        mock_service.list_documents.return_value = document_list  # Changed method name

        response = client.get("/api/v1/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["file_name"] == "test.pdf"
        assert data["items"][0]["status"] == "processed"
        mock_service.list_documents.assert_called_once()  # Changed method name

    def test_get_documents_with_pagination(self, client_with_overrides, document_list):
        """Should return 200 with paginated documents"""
        client, mock_service = client_with_overrides
        mock_service.list_documents.return_value = document_list  # Changed method name

        response = client.get("/api/v1/documents?limit=10&offset=5")

        assert response.status_code == status.HTTP_200_OK
        mock_service.list_documents.assert_called_once()  # Changed method name

    def test_get_documents_invalid_limit(self, client_with_overrides):
        """Should return 422 when limit exceeds max (100)"""
        client, mock_service = client_with_overrides
        response = client.get("/api/v1/documents?limit=200")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.list_documents.assert_not_called()

    def test_get_documents_invalid_offset(self, client_with_overrides):
        """Should return 422 when offset is negative"""
        client, mock_service = client_with_overrides
        response = client.get("/api/v1/documents?offset=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.list_documents.assert_not_called()

    def test_get_documents_empty_list(self, client_with_overrides):
        """Should return 200 with empty list when no documents exist"""
        client, mock_service = client_with_overrides
        empty_response = DocumentsListResponse(items=[], total=0)
        mock_service.list_documents.return_value = empty_response  # Changed method name

        response = client.get("/api/v1/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0