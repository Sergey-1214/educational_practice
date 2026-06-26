from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import async_session_factory
from app.modules.documents.models import Document
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
    DocumentDeleteResponse,
    DocumentRead,
    DocumentsListResponse,
    DocumentUploadResponse,
)
from app.modules.search.elastic_repository import ElasticsearchRepository


MAX_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = {PDF_CONTENT_TYPE, DOCX_CONTENT_TYPE}


class DocumentsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DocumentsRepository(session)
        self.elasticsearch_repository = ElasticsearchRepository()

    async def upload_document(
        self,
        file: UploadFile,
        background_tasks: BackgroundTasks,
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
        document = await self.repository.mark_as_processing(document.id)
        await self.session.commit()
        await self.session.refresh(document)

        background_tasks.add_task(process_document, document.id, content)

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

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> DocumentRead:
        document = await self.repository.get_document_by_id(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this document",
            )

        return DocumentRead.model_validate(document)

    async def delete_document(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> DocumentDeleteResponse:
        document = await self.repository.get_document_by_id(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this document",
            )

        try:
            await self.elasticsearch_repository.delete_document_chunks(
                document_id=str(document.id),
                user_id=str(user_id),
            )
            await self.repository.delete_document(document)
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document",
            ) from exc

        return DocumentDeleteResponse(deleted=True)

    @staticmethod
    def _build_chunks(
        document: Document,
        content: bytes,
    ) -> list[dict[str, str | int | None]]:
        pages = parse_document(content, document.content_type)
        chunks: list[dict[str, str | int | None]] = []

        for page in pages:
            page_chunks = split_text_into_chunks(page.text)
            for index, text in enumerate(page_chunks, start=1):
                chunk_id = f"{document.id}:{page.page_number}:{index}"
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": str(document.id),
                        "user_id": str(document.user_id) if document.user_id else None,
                        "file_name": document.file_name,
                        "page_number": page.page_number,
                        "chunk_number": index,
                        "text": text,
                    },
                )

        if not chunks:
            raise ValueError("Document does not contain extractable text")

        return chunks

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


async def process_document(document_id: UUID, content: bytes) -> None:
    async with async_session_factory() as session:
        service = DocumentsService(session)
        document = await service.repository.get_document_by_id(document_id)
        if document is None:
            return

        try:
            chunks = service._build_chunks(document, content)
            await service.elasticsearch_repository.index_document_chunks(chunks)
            await service.repository.mark_as_processed(
                document.id,
                chunks_count=len(chunks),
            )
            await session.commit()
        except (UnsupportedDocumentTypeError, ValueError) as exc:
            await service.repository.mark_as_failed(document.id, str(exc))
            await session.commit()
        except Exception:
            await service.repository.mark_as_failed(
                document.id,
                "Failed to process document",
            )
            await session.commit()
