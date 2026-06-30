from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.history.repository import SearchHistoryRepository
from app.modules.history.schemas import (
    SearchHistoryClearResponse,
    SearchHistoryCreate,
    SearchHistoryDeleteResponse,
    SearchHistoryListResponse,
    SearchHistoryRead,
)


class SearchHistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SearchHistoryRepository(session)

    async def save_search_query(
        self,
        user_id: UUID,
        query: str,
        results_count: int,
        document_id: UUID | None = None,
    ) -> SearchHistoryRead:
        history_item = await self.repository.create_history_item(
            SearchHistoryCreate(
                user_id=user_id,
                query=query,
                document_id=document_id,
                results_count=results_count,
            ),
        )
        await self.session.commit()
        await self.session.refresh(history_item)
        return SearchHistoryRead.model_validate(history_item)

    async def list_user_history(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchHistoryListResponse:
        items = await self.repository.list_user_history(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        total = await self.repository.count_user_history(user_id)
        return SearchHistoryListResponse(items=items, total=total)

    async def delete_history_item(
        self,
        history_item_id: UUID | str,
        user_id: UUID,
    ) -> SearchHistoryDeleteResponse:
        if isinstance(history_item_id, str):
            history_item_id = UUID(history_item_id)

        deleted = await self.repository.delete_history_item(
            history_item_id=history_item_id,
            user_id=user_id,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History item not found",
            )

        await self.session.commit()
        return SearchHistoryDeleteResponse(deleted=True)

    async def clear_user_history(self, user_id: UUID) -> SearchHistoryClearResponse:
        deleted_count = await self.repository.clear_user_history(user_id)
        await self.session.commit()
        return SearchHistoryClearResponse(deleted_count=deleted_count)
