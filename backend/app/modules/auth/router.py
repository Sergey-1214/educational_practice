from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_current_user, get_db_session
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

UNAUTHORIZED_RESPONSE = {401: {"description": "Invalid or missing access token."}}
FORBIDDEN_RESPONSE = {403: {"description": "Authenticated user is inactive or forbidden."}}


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    return AuthService(session)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User registered successfully."},
        409: {"description": "User with this email already exists."},
        422: {"description": "Invalid request body."},
    },
)
async def register(
    data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> RegisterResponse:
    return await auth_service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        200: {"description": "User authenticated successfully. Returns token pair."},
        401: {"description": "Invalid email or password."},
        403: {"description": "User is inactive."},
        422: {"description": "Invalid request body."},
    },
)
async def login(
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await auth_service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        200: {"description": "Token pair refreshed successfully."},
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        422: {"description": "Invalid request body."},
    },
)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TokenResponse:
    return await auth_service.refresh_token(data, current_user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        200: {"description": "Refresh token revoked successfully."},
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        422: {"description": "Invalid request body."},
    },
)
async def logout(
    data: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LogoutResponse:
    return await auth_service.logout(data, current_user)
