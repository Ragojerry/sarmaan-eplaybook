import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

settings = get_settings()


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(subject: str, extra_claims: dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    # jti guarantees uniqueness even when the same user logs in twice within
    # the same second — iat truncates to whole seconds, so without a jti,
    # two such logins would produce byte-identical JWTs and collide on the
    # refresh_tokens.token unique constraint (a real bug hit during Phase 5
    # test development, not hypothetical).
    payload = {"sub": subject, "iat": now, "exp": now + expires_delta, "jti": str(uuid.uuid4()), **extra_claims}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: str) -> str:
    return create_token(
        subject=user_id,
        extra_claims={"role": role, "type": "access"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    return create_token(
        subject=user_id,
        extra_claims={"type": "refresh"},
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Raises jose.JWTError on invalid/expired tokens — callers translate that
    into a 401, never leak the raw exception."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

