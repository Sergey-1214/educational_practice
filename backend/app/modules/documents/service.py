from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.chunker import split_text_into_chunks
from app.modules.documents.parser import (
    DOCX_CONTENT_TYPE,
    PDF_CONTENT_TYPE,
    UnsupportedDocumentTypeError,
    parse_document,
)
from app.modules.documents.repository import DocumentsRepository
from app.modules.documents.schemas import (
    DocumentCreate,
    DocumentsListResponse,
    DocumentUploadResponse,
)


MAX_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = {PDF_CONTENT_TYPE, DOCX_CONTENT_TYPE}


class DocumentsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DocumentsRepository(session)

    async def upload_document(
        self,
        file: UploadFile,
        user_id: UUID | None = None,
    ) -> DocumentUploadResponse:
        self._validate_content_type(file.content_type)

        content = await file.read()
        self._validate_file_content(content)

        document = await self.repository.create_document(
            DocumentCreate(
                file_name=file.filename or "document",
                content_type=file.content_type or "",
                size_bytes=len(content),
                user_id=user_id,
            ),
        )
        await self.repository.mark_as_processing(document.id)

        try:
            chunks_count = self._count_chunks(content, document.content_type)
            document = await self.repository.mark_as_processed(
                document.id,
                chunks_count=chunks_count,
            )
            await self.session.commit()
            await self.session.refresh(document)
        except (UnsupportedDocumentTypeError, ValueError) as exc:
            document = await self.repository.mark_as_failed(document.id, str(exc))
            await self.session.commit()
            await self.session.refresh(document)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            document = await self.repository.mark_as_failed(
                document.id,
                "Failed to process document",
            )
            await self.session.commit()
            await self.session.refresh(document)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document",
            ) from exc

        return DocumentUploadResponse(document=document)

    async def list_documents(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> DocumentsListResponse:
        documents = await self.repository.list_documents(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        total = await self.repository.count_documents(user_id=user_id)
        return DocumentsListResponse(items=documents, total=total)

    @staticmethod
    def _count_chunks(content: bytes, content_type: str) -> int:
        pages = parse_document(content, content_type)
        chunks_count = sum(
            len(split_text_into_chunks(page.text))
            for page in pages
        )
        if chunks_count == 0:
            raise ValueError("Document does not contain extractable text")

        return chunks_count

    @staticmethod
    def _validate_content_type(content_type: str | None) -> None:
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and DOCX files are supported",
            )

    @staticmethod
    def _validate_file_content(content: bytes) -> None:
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )
        if len(content) > MAX_DOCUMENT_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must not exceed 20 MB",
            )
