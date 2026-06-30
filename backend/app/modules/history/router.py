from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_current_user, get_db_session
from app.modules.auth.models import User
from app.modules.history.schemas import (
    SearchHistoryClearResponse,
    SearchHistoryDeleteResponse,
    SearchHistoryListResponse,
)
from app.modules.history.service import SearchHistoryService

router = APIRouter(prefix="/history", tags=["history"])

AUTH_RESPONSES = {
    401: {"description": "Invalid or missing access token."},
}


def get_history_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SearchHistoryService:
    return SearchHistoryService(session)


@router.get(
    "",
    response_model=SearchHistoryListResponse,
    responses={
        200: {"description": "Current user's search history returned successfully."},
        **AUTH_RESPONSES,
        422: {"description": "Invalid pagination query parameters."},
    },
)
async def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    history_service: Annotated[SearchHistoryService, Depends(get_history_service)],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of history items to return.",
            examples=[20],
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of history items to skip for pagination.",
            examples=[0],
        ),
    ] = 0,
) -> SearchHistoryListResponse:
    return await history_service.list_user_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/{history_item_id}",
    response_model=SearchHistoryDeleteResponse,
    responses={
        200: {"description": "History item deleted successfully."},
        **AUTH_RESPONSES,
        404: {"description": "History item not found."},
        422: {"description": "Invalid history item id."},
    },
)
async def delete_history_item(
    history_item_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    history_service: Annotated[SearchHistoryService, Depends(get_history_service)],
) -> SearchHistoryDeleteResponse:
    return await history_service.delete_history_item(
        history_item_id=str(history_item_id),
        user_id=current_user.id,
    )


@router.delete(
    "",
    response_model=SearchHistoryClearResponse,
    responses={
        200: {"description": "Current user's search history cleared successfully."},
        **AUTH_RESPONSES,
    },
)
async def clear_history(
    current_user: Annotated[User, Depends(get_current_user)],
    history_service: Annotated[SearchHistoryService, Depends(get_history_service)],
) -> SearchHistoryClearResponse:
    return await history_service.clear_user_history(current_user.id)
