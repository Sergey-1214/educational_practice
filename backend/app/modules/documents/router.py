from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_current_user, get_db_session
from app.modules.auth.models import User
from app.modules.documents.schemas import DocumentUploadResponse
from app.modules.documents.service import DocumentsService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_documents_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentsService:
    return DocumentsService(session)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[UploadFile, File()],
    documents_service: Annotated[DocumentsService, Depends(get_documents_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DocumentUploadResponse:
    return await documents_service.upload_document(
        file=file,
        user_id=current_user.id,
    )
