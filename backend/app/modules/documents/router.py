from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_current_user, get_db_session
from app.modules.auth.models import User
from app.modules.documents.schemas import (
    DocumentDeleteResponse,
    DocumentRead,
    DocumentsListResponse,
    DocumentUploadResponse,
)
from app.modules.documents.service import DocumentsService

router = APIRouter(prefix="/documents", tags=["documents"])

AUTH_RESPONSES = {
    401: {"description": "Invalid or missing access token."},
    403: {"description": "Authenticated user has no access to this document."},
}


def get_documents_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentsService:
    return DocumentsService(session)


@router.get(
    "",
    response_model=DocumentsListResponse,
    responses={
        200: {"description": "Current user's documents returned successfully."},
        401: {"description": "Invalid or missing access token."},
        422: {"description": "Invalid pagination query parameters."},
    },
)
async def get_documents(
    documents_service: Annotated[DocumentsService, Depends(get_documents_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of documents to return.",
            examples=[20],
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of documents to skip for pagination.",
            examples=[0],
        ),
    ] = 0,
) -> DocumentsListResponse:
    return await documents_service.list_documents(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    responses={
        200: {"description": "Document metadata returned successfully."},
        **AUTH_RESPONSES,
        404: {"description": "Document not found."},
        422: {"description": "Invalid document id."},
    },
)
async def get_document(
    document_id: UUID,
    documents_service: Annotated[DocumentsService, Depends(get_documents_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentRead:
    return await documents_service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    responses={
        200: {"description": "Document and its Elasticsearch chunks deleted successfully."},
        **AUTH_RESPONSES,
        404: {"description": "Document not found."},
        422: {"description": "Invalid document id."},
        500: {"description": "Failed to delete document or its Elasticsearch chunks."},
    },
)
async def delete_document(
    document_id: UUID,
    documents_service: Annotated[DocumentsService, Depends(get_documents_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentDeleteResponse:
    return await documents_service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": (
                "Document accepted successfully. Processing continues in background."
            ),
        },
        400: {"description": "Empty file, unsupported file type, or file exceeds 20 MB."},
        401: {"description": "Invalid or missing access token."},
        422: {"description": "Invalid multipart form data."},
    },
)
async def upload_document(
    file: Annotated[UploadFile, File()],
    background_tasks: BackgroundTasks,
    documents_service: Annotated[DocumentsService, Depends(get_documents_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentUploadResponse:
    return await documents_service.upload_document(
        file=file,
        background_tasks=background_tasks,
        user_id=current_user.id,
    )
