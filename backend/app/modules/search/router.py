from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_current_user, get_db_session
from app.modules.auth.models import User
from app.modules.search.schemas import SearchParams, SearchResponse
from app.modules.search.service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=SearchResponse,
    responses={
        200: {"description": "Search completed successfully."},
        401: {"description": "Invalid or missing access token."},
        403: {"description": "Search inside a document that belongs to another user."},
        404: {"description": "Document filter points to a missing document."},
        422: {"description": "Invalid search query, document id, limit, or offset."},
        500: {"description": "Elasticsearch search failed."},
    },
)
async def search_documents(
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=300,
            description="Search query text entered by the user.",
            examples=["учебная практика"],
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_id: Annotated[
        UUID | None,
        Query(
            description="Search only inside this document when provided.",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
            description="Maximum number of search results to return.",
            examples=[10],
        ),
    ] = 10,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of search results to skip for pagination.",
            examples=[0],
        ),
    ] = 0,
) -> SearchResponse:
    service = SearchService(session)
    return await service.search(
        SearchParams(
            query=q,
            document_id=document_id,
            limit=limit,
            offset=offset,
        ),
        current_user.id,
    )
