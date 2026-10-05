import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.models.enums import RoleName, UserStatus
from app.auth.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validates the access token and loads the corresponding, still-active
    user. Every protected endpoint depends on this — never trust a token's
    claims alone without re-checking the user's current status (a suspended
    account must be locked out immediately, not just at its next login)."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise unauthorized

    if payload.get("type") != "access":
        raise unauthorized

    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized

    try:
        user = db.get(User, uuid.UUID(user_id))
    except (ValueError, TypeError):
        raise unauthorized

    if user is None or user.status != UserStatus.ACTIVE:
        raise unauthorized

    return user


def require_roles(*allowed: RoleName):
    """Dependency factory for RBAC: `Depends(require_roles(RoleName.SUPER_ADMIN, RoleName.CONTENT_ADMIN))`.
    SUPER_ADMIN always passes regardless of the allowed list — it's the one
    role every governance action (§15) and admin endpoint must permit."""

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == RoleName.SUPER_ADMIN:
            return current_user
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted to perform this action.",
            )
        return current_user

    return _check
