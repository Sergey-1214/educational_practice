from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    return create_jwt_token(
        subject=str(user_id),
        expires_at=expires_at,
        token_type="access",
    )


def create_refresh_token() -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days,
    )
    token = token_urlsafe(64)
    return token, expires_at


def create_jwt_token(
    subject: str,
    expires_at: datetime,
    token_type: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires_at,
        "type": token_type,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_jwt_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None


def get_access_token_subject(token: str) -> str | None:
    payload = decode_jwt_token(token)
    if payload is None:
        return None

    if payload.get("type") != "access":
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None

    return subject


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
