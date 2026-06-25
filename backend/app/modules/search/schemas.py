from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    chunk_id: str = Field(description="Unique identifier of the found text chunk.")
    document_id: str = Field(description="Identifier of the source document.")
    file_name: str = Field(description="Name of the source file.")
    page: int = Field(description="Page number where the match was found.")
    text: str = Field(description="Found text fragment, possibly with <mark> highlights.")
    score: float = Field(description="Elasticsearch relevance score.")


class SearchResponse(BaseModel):
    query: str = Field(description="Search query text.")
    items: list[SearchResult] = Field(description="Search results for the current page.")
    total: int = Field(description="Total number of found results.")
    limit: int = Field(description="Maximum number of results returned in this response.")
    offset: int = Field(description="Number of skipped results.")


class SearchParams(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=300,
        description="Search query text entered by the user.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of search results to return.",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of search results to skip for pagination.",
    )
