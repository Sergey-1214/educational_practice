from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, DocumentStatus
from app.modules.documents.schemas import DocumentCreate, DocumentStatusUpdate


class DocumentsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_document(self, data: DocumentCreate) -> Document:
        document = Document(**data.model_dump())
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_document_by_id(self, document_id: UUID) -> Document | None:
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_documents(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(Document.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _update_document_status(
        self,
        document_id: UUID,
        data: DocumentStatusUpdate,
    ) -> Document | None:
        document = await self.get_document_by_id(document_id)
        if document is None:
            return None

        document.status = data.status
        if data.chunks_count is not None:
            document.chunks_count = data.chunks_count
        document.error_message = data.error_message

        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def mark_as_uploaded(self, document_id: UUID) -> Document | None:
        return await self._update_document_status(
            document_id,
            DocumentStatusUpdate(status=DocumentStatus.UPLOADED),
        )

    async def mark_as_processing(self, document_id: UUID) -> Document | None:
        return await self._update_document_status(
            document_id,
            DocumentStatusUpdate(status=DocumentStatus.PROCESSING),
        )

    async def mark_as_processed(
        self,
        document_id: UUID,
        chunks_count: int,
    ) -> Document | None:
        return await self._update_document_status(
            document_id,
            DocumentStatusUpdate(
                status=DocumentStatus.PROCESSED,
                chunks_count=chunks_count,
                error_message=None,
            ),
        )

    async def mark_as_failed(
        self,
        document_id: UUID,
        error_message: str,
    ) -> Document | None:
        return await self._update_document_status(
            document_id,
            DocumentStatusUpdate(
                status=DocumentStatus.FAILED,
                error_message=error_message,
            ),
        )
