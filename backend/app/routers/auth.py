"""
Phase 4: real authentication. Implements exactly the four endpoints the
master prompt specifies (§52): login, refresh, logout, me.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken
from app.models.enums import UserStatus, AuditAction
from app.models.audit_log import AuditLog
from app.auth.account import deactivated
from app.devices import registry as device_registry
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
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=payload.username).one_or_none()

    # Deliberately identical error for "no such user" and "wrong password" —
    # distinguishing them lets an attacker enumerate valid usernames.
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
    )

    ip = request.client.host if request.client else None

    if user is None or not verify_password(payload.password, user.password_hash):
        # Failed sign-ins are security events (master prompt §61). The password is never recorded.
        db.add(
            AuditLog(
                user_id=user.id if user else None,
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                entity_id=user.id if user else None,
                details={"username": payload.username[:100], "reason": "invalid_credentials"},
                ip_address=ip,
            )
        )
        db.commit()
        raise invalid_credentials

    if user.status != UserStatus.ACTIVE:
        db.add(
            AuditLog(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                entity_type="user",
                entity_id=user.id,
                details={"username": payload.username[:100], "reason": f"account_{user.status.value.lower()}"},
                ip_address=ip,
            )
        )
        db.commit()
        raise deactivated(status.HTTP_403_FORBIDDEN)

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
    if payload.device is not None:
        device_registry.touch(db, user, payload.device, "login")
    db.add(AuditLog(user_id=user.id, action=AuditAction.LOGIN, entity_type="user", entity_id=user.id, ip_address=ip))
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
    if stored is None:
        raise invalid
    # Checked before "revoked": deactivating an account revokes its tokens, and the
    # phone should hear "deactivated", not "sign in again".
    user = db.get(User, stored.user_id)
    if user is not None and user.status != UserStatus.ACTIVE:
        raise deactivated()
    if stored.revoked or stored.expires_at < datetime.now(timezone.utc) or user is None:
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
