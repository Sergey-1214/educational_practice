import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from io import BytesIO
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.modules.documents.schemas import DocumentStatus
from app.common.dependencies import get_current_user, get_db_session
from app.modules.auth.models import User


class TestDocumentUploadE2E:
    """End-to-end tests for document upload flow"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.dependency_overrides.clear()
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock authenticated user"""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def authenticated_client(self, client, mock_current_user, mock_db_session):
        """Client with authentication overrides"""
        async def override_get_current_user():
            return mock_current_user
        
        async def override_get_db_session():
            yield mock_db_session
        
        client.app.dependency_overrides[get_current_user] = override_get_current_user
        client.app.dependency_overrides[get_db_session] = override_get_db_session
        
        yield client, mock_current_user, mock_db_session
        
        client.app.dependency_overrides.clear()

    def test_upload_pdf_success(self, authenticated_client):
        """Test successful PDF upload"""
        client, mock_user, mock_session = authenticated_client
        
        document_id = uuid4()

        # Mock the DocumentsService
        with patch("app.modules.documents.router.DocumentsService") as MockService:
            mock_service = AsyncMock()
            mock_service.upload_document.return_value = MagicMock(
                document=MagicMock(
                    id=document_id,
                    user_id=mock_user.id,
                    file_name="test_document.pdf",
                    content_type="application/pdf",
                    size_bytes=1024,
                    status=DocumentStatus.UPLOADED,
                    chunks_count=0,
                    error_message=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            MockService.return_value = mock_service
            
            # Upload file
            file_content = b"%PDF-1.4\n%Test PDF content"
            files = {
                "file": ("test_document.pdf", BytesIO(file_content), "application/pdf")
            }
            
            response = client.post("/api/v1/documents/upload", files=files)
            
            # Assertions
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["document"]["file_name"] == "test_document.pdf"
            assert data["document"]["content_type"] == "application/pdf"
            assert data["document"]["status"] == DocumentStatus.UPLOADED.value
            assert data["document"]["id"] == str(document_id)
            
            # Verify service was called
            mock_service.upload_document.assert_called_once()

    def test_upload_docx_success(self, authenticated_client):
        """Test successful DOCX upload"""
        client, mock_user, mock_session = authenticated_client
        
        document_id = uuid4()
        
        with patch("app.modules.documents.router.DocumentsService") as MockService:
            mock_service = AsyncMock()
            mock_service.upload_document.return_value = MagicMock(
                document=MagicMock(
                    id=document_id,
                    user_id=mock_user.id,
                    file_name="test_document.docx",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    size_bytes=2048,
                    status=DocumentStatus.UPLOADED,
                    chunks_count=0,
                    error_message=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            MockService.return_value = mock_service
            
            file_content = b"PK\x03\x04Test DOCX content"
            files = {
                "file": ("test_document.docx", BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            }
            
            response = client.post("/api/v1/documents/upload", files=files)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["document"]["file_name"] == "test_document.docx"
            assert data["document"]["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            assert data["document"]["status"] == DocumentStatus.UPLOADED.value

    def test_upload_txt_success(self, authenticated_client):
        """Test successful TXT upload"""
        client, mock_user, mock_session = authenticated_client
        
        document_id = uuid4()
        
        with patch("app.modules.documents.router.DocumentsService") as MockService:
            mock_service = AsyncMock()
            mock_service.upload_document.return_value = MagicMock(
                document=MagicMock(
                    id=document_id,
                    user_id=mock_user.id,
                    file_name="test_document.txt",
                    content_type="text/plain",
                    size_bytes=512,
                    status=DocumentStatus.UPLOADED,
                    chunks_count=0,
                    error_message=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            MockService.return_value = mock_service
            
            file_content = b"This is a test text document"
            files = {
                "file": ("test_document.txt", BytesIO(file_content), "text/plain")
            }
            
            response = client.post("/api/v1/documents/upload", files=files)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["document"]["file_name"] == "test_document.txt"
            assert data["document"]["content_type"] == "text/plain"
            assert data["document"]["status"] == DocumentStatus.UPLOADED.value

    def test_upload_empty_file_error(self, authenticated_client):
        """Test upload empty file - should return 400"""
        client, _, _ = authenticated_client
        
        files = {
            "file": ("empty.pdf", BytesIO(b""), "application/pdf")
        }
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "empty" in response.json()["detail"].lower() or "Empty" in response.json()["detail"]

    def test_upload_unsupported_file_type_error(self, authenticated_client):
        """Test upload unsupported file type - should return 400"""
        client, _, _ = authenticated_client
        
        files = {
            "file": ("test.exe", BytesIO(b"test content"), "application/x-msdownload")
        }
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unsupported" in response.json()["detail"].lower() or "Unsupported" in response.json()["detail"]

    def test_upload_file_too_large_error(self, authenticated_client):
        """Test upload file exceeding 20 MB - should return 400"""
        client, _, _ = authenticated_client
        
        # Create 21 MB file (20 MB = 20,971,520 bytes)
        large_content = b"x" * (21 * 1024 * 1024)
        files = {
            "file": ("large.pdf", BytesIO(large_content), "application/pdf")
        }
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds" in response.json()["detail"].lower() or "Exceeds" in response.json()["detail"]

    def test_upload_without_file_error(self, authenticated_client):
        """Test upload without file - should return 422"""
        client, _, _ = authenticated_client
        
        response = client.post("/api/v1/documents/upload", files={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_unauthorized(self, client):
        """Test upload without authentication - should return 401"""
        async def override_get_current_user():
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing access token."
            )
        
        client.app.dependency_overrides[get_current_user] = override_get_current_user
        
        files = {
            "file": ("test.pdf", BytesIO(b"test content"), "application/pdf")
        }
        
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access token" in response.json()["detail"].lower()
        
        client.app.dependency_overrides.clear()

    def test_upload_with_background_processing(self, authenticated_client):
        """Test that background processing is triggered"""
        client, mock_user, mock_session = authenticated_client
        
        document_id = uuid4()
        
        with patch("app.modules.documents.router.DocumentsService") as MockService:
            mock_service = AsyncMock()
            mock_service.upload_document.return_value = MagicMock(
                document=MagicMock(
                    id=document_id,
                    user_id=mock_user.id,
                    file_name="test_document.pdf",
                    content_type="application/pdf",
                    size_bytes=1024,
                    status=DocumentStatus.UPLOADED,
                    chunks_count=0,
                    error_message=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            MockService.return_value = mock_service
            
            files = {
                "file": ("test_document.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")
            }
            
            response = client.post("/api/v1/documents/upload", files=files)
            
            assert response.status_code == status.HTTP_201_CREATED
            # Background tasks should be added - verify service received background_tasks parameter
            call_args = mock_service.upload_document.call_args
            assert "background_tasks" in call_args.kwargs or "background_tasks" in call_args.args

    def test_upload_multiple_files_sequential(self, authenticated_client):
        """Test uploading multiple files sequentially"""
        client, mock_user, mock_session = authenticated_client
        
        document_id1 = uuid4()
        document_id2 = uuid4()
        
        with patch("app.modules.documents.router.DocumentsService") as MockService:
            mock_service = AsyncMock()
            
            # Return different documents for each call
            def side_effect(file, background_tasks, user_id):
                if "test1.pdf" in file.filename:
                    return MagicMock(
                        document=MagicMock(
                            id=document_id1,
                            user_id=mock_user.id,
                            file_name="test1.pdf",
                            content_type="application/pdf",
                            size_bytes=1024,
                            status=DocumentStatus.UPLOADED,
                            chunks_count=0,
                            error_message=None,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                    )
                else:
                    return MagicMock(
                        document=MagicMock(
                            id=document_id2,
                            user_id=mock_user.id,
                            file_name="test2.pdf",
                            content_type="application/pdf",
                            size_bytes=2048,
                            status=DocumentStatus.UPLOADED,
                            chunks_count=0,
                            error_message=None,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                    )
            
            mock_service.upload_document.side_effect = side_effect
            MockService.return_value = mock_service
            
            # Upload first file
            files1 = {"file": ("test1.pdf", BytesIO(b"%PDF-1.4 file1"), "application/pdf")}
            response1 = client.post("/api/v1/documents/upload", files=files1)
            
            # Upload second file
            files2 = {"file": ("test2.pdf", BytesIO(b"%PDF-1.4 file2"), "application/pdf")}
            response2 = client.post("/api/v1/documents/upload", files=files2)
            
            assert response1.status_code == status.HTTP_201_CREATED
            assert response2.status_code == status.HTTP_201_CREATED
            
            data1 = response1.json()
            data2 = response2.json()
            assert data1["document"]["file_name"] == "test1.pdf"
            assert data2["document"]["file_name"] == "test2.pdf"
            
            assert mock_service.upload_document.call_count == 2

    def test_upload_then_get_document(self, authenticated_client):
        """Test full flow: upload document then retrieve it"""
        client, mock_user, mock_session = authenticated_client
        
        document_id = uuid4()
        
        with patch("app.modules.documents.router.DocumentsService") as MockService:
            mock_service = AsyncMock()
            
            # Mock upload response
            mock_service.upload_document.return_value = MagicMock(
                document=MagicMock(
                    id=document_id,
                    user_id=mock_user.id,
                    file_name="test_document.pdf",
                    content_type="application/pdf",
                    size_bytes=1024,
                    status=DocumentStatus.UPLOADED,
                    chunks_count=0,
                    error_message=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            
            # Mock get document response
            mock_service.get_document.return_value = MagicMock(
                id=document_id,
                user_id=mock_user.id,
                file_name="test_document.pdf",
                content_type="application/pdf",
                size_bytes=1024,
                status=DocumentStatus.PROCESSED,  # Status changed after processing
                chunks_count=5,
                error_message=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            MockService.return_value = mock_service
            
            # Step 1: Upload document
            files = {"file": ("test_document.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")}
            upload_response = client.post("/api/v1/documents/upload", files=files)
            
            assert upload_response.status_code == status.HTTP_201_CREATED
            upload_data = upload_response.json()
            assert upload_data["document"]["id"] == str(document_id)
            
            # Step 2: Get the document
            get_response = client.get(f"/api/v1/documents/{document_id}")
            
            assert get_response.status_code == status.HTTP_200_OK
            get_data = get_response.json()
            assert get_data["id"] == str(document_id)
            assert get_data["file_name"] == "test_document.pdf"
            assert get_data["status"] == DocumentStatus.PROCESSED.value
            assert get_data["chunks_count"] == 5


class TestDocumentUploadIntegration:
    """Integration tests with real service (requires database)"""

    @pytest.mark.skip(reason="Requires real database connection")
    def test_real_upload_flow(self):
        """Test actual upload flow with real services"""
        # This would test with real database, file storage, etc.
        # Uncomment and implement when needed
        pass
