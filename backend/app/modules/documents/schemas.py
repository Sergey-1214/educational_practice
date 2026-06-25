from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.documents.models import DocumentStatus


class DocumentCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    user_id: UUID | None = None


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
    chunks_count: int | None = Field(default=None, ge=0)
    error_message: str | None = Field(default=None, max_length=500)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    file_name: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    chunks_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentRead


class DocumentsListResponse(BaseModel):
    items: list[DocumentRead]
    total: int
