from fastapi import APIRouter

from modules.auth.router import router as auth_router
from modules.documents.router import router as documents_router
from modules.search.router import router as search_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(search_router)
