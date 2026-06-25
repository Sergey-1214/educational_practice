from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.modules.search.schemas import SearchParams, SearchResponse
from app.modules.search.service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
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
    service = SearchService()
    return await service.search(
        SearchParams(
            query=q,
            document_id=document_id,
            limit=limit,
            offset=offset,
        ),
    )
