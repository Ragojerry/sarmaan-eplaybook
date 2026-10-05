"""
Content governance workflow (master prompt §15):

    DRAFT -> PROGRAMME_REVIEW -> LOCALISATION_REVIEW -> TECHNICAL_QA -> PUBLISHED
                                                                       -> REJECTED (from any review stage)

"Only authorized roles can advance content" and "record every transition in
audit logs" — both enforced here, in one place, so every caller (the modules
router, and later any other content type) gets the same rules rather than
each endpoint re-implementing them slightly differently.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User, ModuleTranslation
from app.models.audit_log import AuditLog
from app.models.enums import ContentReviewStatus, RoleName, AuditAction

# Which role may move content OUT of a given stage, and to where.
# SUPER_ADMIN is always allowed everywhere (checked separately) — this table
# only needs to list the specific reviewer role for each stage.
_TRANSITIONS: dict[ContentReviewStatus, tuple[RoleName, ContentReviewStatus]] = {
    ContentReviewStatus.DRAFT: (RoleName.CONTENT_ADMIN, ContentReviewStatus.PROGRAMME_REVIEW),
    ContentReviewStatus.PROGRAMME_REVIEW: (RoleName.PROGRAM_REVIEWER, ContentReviewStatus.LOCALISATION_REVIEW),
    ContentReviewStatus.LOCALISATION_REVIEW: (RoleName.LOCALISATION_REVIEWER, ContentReviewStatus.TECHNICAL_QA),
    ContentReviewStatus.TECHNICAL_QA: (RoleName.TECHNICAL_REVIEWER, ContentReviewStatus.PUBLISHED),
}

# Which role may REJECT content sitting at a given review stage (sends it
# back to DRAFT for rework, per standard review-workflow practice — the
# master prompt doesn't specify the reject destination explicitly, so DRAFT
# is the reasonable default: rejected content needs the author to revise it).
_REJECTORS: dict[ContentReviewStatus, RoleName] = {
    ContentReviewStatus.PROGRAMME_REVIEW: RoleName.PROGRAM_REVIEWER,
    ContentReviewStatus.LOCALISATION_REVIEW: RoleName.LOCALISATION_REVIEWER,
    ContentReviewStatus.TECHNICAL_QA: RoleName.TECHNICAL_REVIEWER,
}


def advance(db: Session, translation: ModuleTranslation, actor: User) -> ModuleTranslation:
    """Moves content to the next stage. Raises 403 if the actor's role isn't
    authorized for the current stage, 409 if there's no next stage (already
    PUBLISHED or REJECTED)."""
    current = translation.status
    if current not in _TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Content in status '{current.value}' cannot be advanced further.",
        )

    required_role, next_status = _TRANSITIONS[current]
    if actor.role != RoleName.SUPER_ADMIN and actor.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor.role.value}' cannot advance content out of '{current.value}' "
            f"(requires '{required_role.value}').",
        )

    translation.status = next_status
    translation.reviewed_by = actor.id
    translation.reviewed_at = datetime.now(timezone.utc)

    db.add(
        AuditLog(
            user_id=actor.id,
            action=AuditAction.CONTENT_APPROVE
            if next_status == ContentReviewStatus.PUBLISHED
            else AuditAction.CONTENT_REVIEW,
            entity_type="module_translation",
            entity_id=translation.id,
            details={"from": current.value, "to": next_status.value},
        )
    )
    db.commit()
    db.refresh(translation)
    return translation


def reject(db: Session, translation: ModuleTranslation, actor: User, reason: str | None = None) -> ModuleTranslation:
    current = translation.status
    if current not in _REJECTORS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Content in status '{current.value}' is not at a review stage that can be rejected.",
        )

    required_role = _REJECTORS[current]
    if actor.role != RoleName.SUPER_ADMIN and actor.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor.role.value}' cannot reject content at '{current.value}' "
            f"(requires '{required_role.value}').",
        )

    translation.status = ContentReviewStatus.REJECTED
    translation.reviewed_by = actor.id
    translation.reviewed_at = datetime.now(timezone.utc)

    db.add(
        AuditLog(
            user_id=actor.id,
            action=AuditAction.CONTENT_REJECT,
            entity_type="module_translation",
            entity_id=translation.id,
            details={"from": current.value, "reason": reason},
        )
    )
    db.commit()
    db.refresh(translation)
    return translation
