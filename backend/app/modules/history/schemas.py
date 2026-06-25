from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchHistoryCreate(BaseModel):
    user_id: UUID
    query: str = Field(min_length=1, max_length=300)
    results_count: int = Field(ge=0)
    document_id: UUID | None = None


class SearchHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    document_id: UUID | None
    query: str
    results_count: int
    created_at: datetime


class SearchHistoryListResponse(BaseModel):
    items: list[SearchHistoryRead]
    total: int


class SearchHistoryDeleteResponse(BaseModel):
    deleted: bool


class SearchHistoryClearResponse(BaseModel):
    deleted_count: int
