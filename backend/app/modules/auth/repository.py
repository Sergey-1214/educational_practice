from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken, User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def create_refresh_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_refresh_token_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_refresh_token(
        self,
        token_hash: str,
        current_time: datetime | None = None,
    ) -> RefreshToken | None:
        current_time = current_time or datetime.now(UTC)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > current_time,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(
        self,
        token_hash: str,
        revoked_at: datetime | None = None,
    ) -> RefreshToken | None:
        refresh_token = await self.get_refresh_token_by_hash(token_hash)
        if refresh_token is None:
            return None

        refresh_token.revoked_at = revoked_at or datetime.now(UTC)
        await self.session.flush()
        return refresh_token

    async def revoke_user_refresh_tokens(
        self,
        user_id: UUID,
        revoked_at: datetime | None = None,
    ) -> list[RefreshToken]:
        revoked_at = revoked_at or datetime.now(UTC)
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        refresh_tokens = list(result.scalars().all())

        for refresh_token in refresh_tokens:
            refresh_token.revoked_at = revoked_at

        await self.session.flush()
        return refresh_tokens
