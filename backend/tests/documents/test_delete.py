import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.documents.schemas import DocumentDeleteResponse
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
    with patch("app.modules.documents.router.DocumentsService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def client_with_overrides(client, mock_current_user, mock_db_session, mock_documents_service):
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


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/{document_id}"""

    def test_delete_document_success(self, client_with_overrides):
        """Should return 200 when document is deleted successfully"""
        client, mock_service = client_with_overrides
        mock_service.delete_document.return_value = DocumentDeleteResponse(
            deleted=True
        )

        document_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted"] is True
        mock_service.delete_document.assert_called_once()

    def test_delete_document_not_found(self, client_with_overrides):
        """Should return 404 when document does not exist"""
        from fastapi import HTTPException
        client, mock_service = client_with_overrides
        document_id = "00000000-0000-0000-0000-000000000000"
        mock_service.delete_document.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

        response = client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_delete_document_forbidden(self, client_with_overrides):
        """Should return 403 when user has no access to document"""
        from fastapi import HTTPException
        client, mock_service = client_with_overrides
        document_id = "00000000-0000-0000-0000-000000000000"
        mock_service.delete_document.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user has no access to this document."
        )

        response = client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "no access" in response.json()["detail"]

    def test_delete_document_internal_error(self, client_with_overrides):
        """Should return 500 when deletion fails"""
        from fastapi import HTTPException
        client, mock_service = client_with_overrides
        document_id = "00000000-0000-0000-0000-000000000000"
        mock_service.delete_document.side_effect = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document or its Elasticsearch chunks."
        )

        response = client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete" in response.json()["detail"]

    def test_delete_document_invalid_id(self, client_with_overrides):
        """Should return 422 when document_id is invalid UUID"""
        client, mock_service = client_with_overrides
        response = client.delete("/api/v1/documents/invalid-id")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.delete_document.assert_not_called()