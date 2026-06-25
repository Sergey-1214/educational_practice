from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.repository import DocumentsRepository
from app.modules.history.repository import SearchHistoryRepository
from app.modules.history.schemas import SearchHistoryCreate
from app.modules.search.elastic_repository import ElasticsearchRepository
from app.modules.search.schemas import SearchParams, SearchResponse, SearchResult


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents_repository = DocumentsRepository(session)
        self.history_repository = SearchHistoryRepository(session)
        self.repository = ElasticsearchRepository()

    async def search(self, params: SearchParams, user_id: UUID) -> SearchResponse:
        if params.document_id is not None:
            await self._check_document_access(params.document_id, user_id)

        try:
            response = await self.repository.search_documents(
                query=params.query,
                user_id=str(user_id),
                document_id=str(params.document_id) if params.document_id else None,
                limit=params.limit,
                offset=params.offset,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search documents",
            ) from exc

        hits = response.get("hits", {})
        total = self._extract_total(hits.get("total"))
        items = [
            self._build_result(hit)
            for hit in hits.get("hits", [])
        ]
        await self.history_repository.create_history_item(
            SearchHistoryCreate(
                user_id=user_id,
                query=params.query,
                document_id=params.document_id,
                results_count=total,
            ),
        )
        await self.session.commit()

        return SearchResponse(
            query=params.query,
            document_id=params.document_id,
            items=items,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    @staticmethod
    def _extract_total(total: object) -> int:
        if isinstance(total, dict):
            value = total.get("value", 0)
            return value if isinstance(value, int) else 0
        if isinstance(total, int):
            return total
        return 0

    @staticmethod
    def _build_result(hit: dict) -> SearchResult:
        source = hit.get("_source", {})
        highlight = hit.get("highlight", {})
        highlighted_text = highlight.get("text", [None])[0]

        return SearchResult(
            chunk_id=source["chunk_id"],
            document_id=source["document_id"],
            file_name=source["file_name"],
            page=source["page_number"],
            text=highlighted_text or source["text"],
            score=float(hit.get("_score") or 0),
        )

    async def _check_document_access(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> None:
        document = await self.documents_repository.get_document_by_id(document_id)
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
