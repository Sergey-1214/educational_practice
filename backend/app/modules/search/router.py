from typing import Annotated

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
            limit=limit,
            offset=offset,
        ),
    )
