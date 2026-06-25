from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AuthRepository(session)

    async def register(self, data: RegisterRequest) -> RegisterResponse:
        email = data.email.lower()
        existing_user = await self.repository.get_user_by_email(email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        try:
            user = await self.repository.create_user(
                email=email,
                hashed_password=hash_password(data.password),
            )
            await self.session.commit()
            await self.session.refresh(user)
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            ) from exc

        return RegisterResponse(user=user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        email = data.email.lower()
        user = await self.repository.get_user_by_email(email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        token_response = await self._create_token_pair(user.id)
        await self.session.commit()
        return token_response

    async def refresh_token(self, data: RefreshTokenRequest) -> TokenResponse:
        token_hash = hash_token(data.refresh_token)
        refresh_token = await self.repository.get_active_refresh_token(token_hash)
        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await self.repository.get_user_by_id(refresh_token.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        await self.repository.revoke_refresh_token(token_hash)
        token_response = await self._create_token_pair(user.id)
        await self.session.commit()
        return token_response

    async def logout(self, data: LogoutRequest) -> LogoutResponse:
        token_hash = hash_token(data.refresh_token)
        await self.repository.revoke_refresh_token(token_hash)
        await self.session.commit()
        return LogoutResponse()

    async def _create_token_pair(self, user_id: UUID) -> TokenResponse:
        access_token = create_access_token(user_id)
        refresh_token, expires_at = create_refresh_token()
        await self.repository.create_refresh_token(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
