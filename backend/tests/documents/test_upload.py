import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime
from uuid import uuid4
from io import BytesIO

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.documents.schemas import DocumentRead, DocumentUploadResponse, DocumentStatus
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


class TestUploadDocument:
    """Tests for POST /api/v1/documents/upload"""

    def test_upload_success(self, client_with_overrides, sample_document):
        """Should return 201 when document upload is successful"""
        client, mock_service = client_with_overrides
        mock_service.upload_document.return_value = DocumentUploadResponse(
            document=sample_document
        )

        files = {"file": ("test.pdf", BytesIO(b"test content"), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["document"]["id"] == str(sample_document.id)
        assert data["document"]["file_name"] == "test.pdf"
        assert data["document"]["status"] == "processed"
        mock_service.upload_document.assert_called_once()

    def test_upload_empty_file(self, client_with_overrides):
        """Should return 400 when file is empty"""
        from fastapi import HTTPException
        client, mock_service = client_with_overrides
        mock_service.upload_document.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file is not allowed."
        )

        files = {"file": ("empty.pdf", BytesIO(b""), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Empty file" in response.json()["detail"]

    def test_upload_unsupported_type(self, client_with_overrides):
        """Should return 400 when file type is unsupported"""
        from fastapi import HTTPException
        client, mock_service = client_with_overrides
        mock_service.upload_document.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type."
        )

        files = {"file": ("test.exe", BytesIO(b"test"), "application/x-msdownload")}
        response = client.post("/api/v1/documents/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported" in response.json()["detail"]

    def test_upload_file_too_large(self, client_with_overrides):
        """Should return 400 when file exceeds 20 MB"""
        from fastapi import HTTPException
        client, mock_service = client_with_overrides
        mock_service.upload_document.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 20 MB limit."
        )

        large_content = b"x" * (21 * 1024 * 1024)
        files = {"file": ("large.pdf", BytesIO(large_content), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds" in response.json()["detail"]

    def test_upload_missing_file(self, client_with_overrides):
        """Should return 422 when file is missing from request"""
        client, mock_service = client_with_overrides
        response = client.post("/api/v1/documents/upload", files={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.upload_document.assert_not_called()