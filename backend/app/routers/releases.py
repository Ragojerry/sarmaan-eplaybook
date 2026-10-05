"""Phase 5 scope: release record CRUD + the publish transition. Actual
release-package building (bundling content into a downloadable artifact,
§11-14) is a later phase — this manages the release's metadata/status."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models import User, ContentRelease
from app.models.audit_log import AuditLog
from app.models.enums import RoleName, ReleaseStatus, AuditAction
from app.schemas.release import ContentReleaseCreate, ContentReleaseResponse

router = APIRouter()

RELEASE_MANAGERS = (RoleName.CONTENT_ADMIN, RoleName.TECHNICAL_REVIEWER)


@router.get("", response_model=list[ContentReleaseResponse])
def list_releases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ContentRelease).order_by(ContentRelease.created_at.desc()).all()


@router.post("", response_model=ContentReleaseResponse, status_code=status.HTTP_201_CREATED)
def create_release(
    payload: ContentReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*RELEASE_MANAGERS)),
):
    if db.query(ContentRelease).filter_by(release_code=payload.release_code).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="release_code already exists")
    release = ContentRelease(created_by=current_user.id, **payload.model_dump())
    db.add(release)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.RELEASE_CREATE,
            entity_type="content_release",
            entity_id=release.id,
            details={"release_code": release.release_code},
        )
    )
    db.commit()
    db.refresh(release)
    return release


@router.post("/{release_id}/publish", response_model=ContentReleaseResponse)
def publish_release(
    release_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.TECHNICAL_REVIEWER)),
):
    """Only TECHNICAL_REVIEWER (or SUPER_ADMIN) may publish — this is the
    final governance gate before content/app changes actually reach devices."""
    release = db.get(ContentRelease, release_id)
    if release is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    if release.status == ReleaseStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Release is already published")

    release.status = ReleaseStatus.PUBLISHED
    release.approved_by = current_user.id
    release.published_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.RELEASE_PUBLISH,
            entity_type="content_release",
            entity_id=release.id,
            details={"release_code": release.release_code},
        )
    )
    db.commit()
    db.refresh(release)
    return release


@router.post("/{release_id}/rollback", response_model=ContentReleaseResponse)
def rollback_release(
    release_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.TECHNICAL_REVIEWER)),
):
    release = db.get(ContentRelease, release_id)
    if release is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")
    if release.status != ReleaseStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only a published release can be rolled back")

    release.status = ReleaseStatus.ROLLED_BACK
    db.add(
        AuditLog(
            user_id=current_user.id,
            action=AuditAction.RELEASE_ROLLBACK,
            entity_type="content_release",
            entity_id=release.id,
            details={"release_code": release.release_code},
        )
    )
    db.commit()
    db.refresh(release)
    return release
