"""
Reference library: supporting documents (guidelines, SOPs, job aids) that
the online Ask assistant may quote beside the training modules. Upload ->
DRAFT -> a reviewer checks the extracted text -> APPROVED (searched) ->
ARCHIVED (no longer searched). Only approved documents ever reach an
answer, and every change lands in the audit log.
"""
import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.reference_text import UnreadableDocument, extract_passages
from app.auth.dependencies import require_roles
from app.config import get_settings
from app.database import get_db
from app.models import ReferenceDocument, ReferencePassage, User
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, ReferenceStatus, RoleName

router = APIRouter()
settings = get_settings()

EDITORS = (RoleName.CONTENT_ADMIN,)
# Approving a document puts its text in front of every CDD, so reviewers may
# approve too (as with content); SUPER_ADMIN always passes require_roles.
APPROVERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.TECHNICAL_REVIEWER)
VIEWERS = APPROVERS + (RoleName.LOCALISATION_REVIEWER,)


class ReferenceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ReferenceStatus | None = None


def _serialize(doc: ReferenceDocument, passage_count: int) -> dict:
    return {
        "id": str(doc.id),
        "title": doc.title,
        "description": doc.description,
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "file_size": doc.file_size,
        "language": doc.language,
        "status": doc.status.value,
        "passage_count": passage_count,
        "uploaded_by": str(doc.uploaded_by) if doc.uploaded_by else None,
        "approved_by": str(doc.approved_by) if doc.approved_by else None,
        "approved_at": doc.approved_at.isoformat() if doc.approved_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _passage_count(db: Session, doc_id: uuid.UUID) -> int:
    return db.query(func.count(ReferencePassage.id)).filter_by(document_id=doc_id).scalar() or 0


def _get(db: Session, doc_id: uuid.UUID) -> ReferenceDocument:
    doc = db.get(ReferenceDocument, doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def _audit(db: Session, user: User, action: AuditAction, doc: ReferenceDocument, details: dict) -> None:
    db.add(AuditLog(user_id=user.id, action=action, entity_type="reference_document", entity_id=doc.id,
                    details={"title": doc.title, **details}))


@router.get("")
def list_references(db: Session = Depends(get_db), current_user: User = Depends(require_roles(*VIEWERS))):
    counts = dict(
        db.query(ReferencePassage.document_id, func.count(ReferencePassage.id))
        .group_by(ReferencePassage.document_id)
        .all()
    )
    docs = db.query(ReferenceDocument).order_by(ReferenceDocument.created_at.desc()).all()
    return [_serialize(d, counts.get(d.id, 0)) for d in docs]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_reference(
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(None),
    language: str = Form("en", min_length=2, max_length=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*EDITORS)),
):
    limit = settings.max_reference_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"The file is larger than {settings.max_reference_upload_mb} MB.")
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The file is empty.")
    try:
        mime, passages = extract_passages(data)
    except UnreadableDocument as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    doc = ReferenceDocument(
        title=title.strip(),
        description=(description or "").strip() or None,
        filename=(file.filename or "document")[:255],
        mime_type=mime,
        file_size=len(data),
        checksum=hashlib.sha256(data).hexdigest(),
        file_data=data,
        language=language,
        status=ReferenceStatus.DRAFT,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.flush()
    for i, (heading, text) in enumerate(passages):
        db.add(ReferencePassage(document_id=doc.id, position=i, heading=heading, text=text))
    _audit(db, current_user, AuditAction.REFERENCE_UPLOAD, doc,
           {"filename": doc.filename, "passages": len(passages), "checksum": doc.checksum})
    db.commit()
    db.refresh(doc)
    return _serialize(doc, len(passages))


@router.get("/{doc_id}/passages")
def list_passages(doc_id: uuid.UUID, db: Session = Depends(get_db),
                  current_user: User = Depends(require_roles(*VIEWERS))):
    """The exact text the assistant would search — what a reviewer approves."""
    doc = _get(db, doc_id)
    return [{"position": p.position, "heading": p.heading, "text": p.text} for p in doc.passages]


@router.get("/{doc_id}/file")
def download_reference(doc_id: uuid.UUID, db: Session = Depends(get_db),
                       current_user: User = Depends(require_roles(*VIEWERS))):
    doc = _get(db, doc_id)
    safe_name = "".join(ch for ch in doc.filename if ch.isalnum() or ch in "._- ") or "document"
    return Response(content=doc.file_data, media_type=doc.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{safe_name}"'})


@router.patch("/{doc_id}")
def update_reference(
    doc_id: uuid.UUID,
    payload: ReferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*APPROVERS)),
):
    doc = _get(db, doc_id)
    changes = payload.model_dump(exclude_unset=True)
    if ("title" in changes or "description" in changes) and current_user.role not in (
        RoleName.CONTENT_ADMIN, RoleName.SUPER_ADMIN
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only content admins can edit details.")
    if changes.get("title") is not None:
        doc.title = changes["title"].strip()
    if "description" in changes:
        doc.description = (changes["description"] or "").strip() or None
    new_status = changes.get("status")
    if new_status is not None and new_status != doc.status:
        doc.status = new_status
        if new_status == ReferenceStatus.APPROVED:
            doc.approved_by = current_user.id
            doc.approved_at = datetime.now(timezone.utc)
    _audit(db, current_user, AuditAction.REFERENCE_UPDATE, doc,
           {k: (v.value if isinstance(v, ReferenceStatus) else v) for k, v in changes.items()})
    db.commit()
    db.refresh(doc)
    return _serialize(doc, _passage_count(db, doc.id))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference(doc_id: uuid.UUID, db: Session = Depends(get_db),
                     current_user: User = Depends(require_roles(*EDITORS))):
    doc = _get(db, doc_id)
    if doc.status == ReferenceStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Archive the document before deleting it.")
    _audit(db, current_user, AuditAction.REFERENCE_UPDATE, doc, {"deleted": True, "checksum": doc.checksum})
    db.delete(doc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
