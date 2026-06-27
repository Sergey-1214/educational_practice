from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.history.models import SearchHistory
from app.modules.history.schemas import SearchHistoryCreate


class SearchHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_history_item(
        self,
        data: SearchHistoryCreate,
    ) -> SearchHistory:
        history_item = SearchHistory(**data.model_dump())
        self.session.add(history_item)
        await self.session.flush()
        await self.session.refresh(history_item)
        return history_item

    async def get_history_item_by_id(
        self,
        history_item_id: UUID,
    ) -> SearchHistory | None:
        stmt = select(SearchHistory).where(SearchHistory.id == history_item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_history(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SearchHistory]:
        stmt = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_user_history(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(SearchHistory)
            .where(SearchHistory.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_history_item(
        self,
        history_item_id: UUID,
        user_id: UUID,
    ) -> bool:
        history_item = await self.get_history_item_by_id(history_item_id)
        if history_item is None or history_item.user_id != user_id:
            return False

        await self.session.delete(history_item)
        await self.session.flush()
        return True

    async def clear_user_history(self, user_id: UUID) -> int:
        stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0
