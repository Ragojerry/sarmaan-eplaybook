"""
Phase 4: real authentication. Implements exactly the four endpoints the
master prompt specifies (§52): login, refresh, logout, me.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken
from app.models.enums import UserStatus, AuditAction
from app.models.audit_log import AuditLog
from app.auth.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_current_user
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RefreshResponse,
    LogoutRequest,
    UserResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=payload.username).one_or_none()

    # Deliberately identical error for "no such user" and "wrong password" —
    # distinguishing them lets an attacker enumerate valid usernames.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
    )

    if user is None or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value.lower()}, not active.",
        )

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token_str = create_refresh_token(str(user.id))
    refresh_claims = decode_token(refresh_token_str)

    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.fromtimestamp(refresh_claims["exp"], tz=timezone.utc),
        )
    )
    user.last_login_at = datetime.now(timezone.utc)
    db.add(AuditLog(user_id=user.id, action=AuditAction.LOGIN, entity_type="user", entity_id=user.id))
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise invalid

    if claims.get("type") != "refresh":
        raise invalid

    stored = db.query(RefreshToken).filter_by(token=payload.refresh_token).one_or_none()
    if stored is None or stored.revoked:
        raise invalid
    if stored.expires_at < datetime.now(timezone.utc):
        raise invalid

    user = db.get(User, uuid.UUID(claims["sub"]))
    if user is None or user.status != UserStatus.ACTIVE:
        raise invalid

    new_access_token = create_access_token(str(user.id), user.role.value)
    return RefreshResponse(access_token=new_access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Actually revokes the refresh token server-side — not just a client-side
    "forget the token" no-op, since a still-valid refresh token could
    otherwise mint new access tokens indefinitely even after logout."""
    stored = db.query(RefreshToken).filter_by(token=payload.refresh_token, user_id=current_user.id).one_or_none()
    if stored is not None:
        stored.revoked = True
        db.add(
            AuditLog(
                user_id=current_user.id,
                action=AuditAction.LOGOUT,
                entity_type="user",
                entity_id=current_user.id,
            )
        )
        db.commit()
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
