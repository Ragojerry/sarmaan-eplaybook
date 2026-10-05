"""Stub router — audit log endpoints land alongside auth/RBAC (Phase 4)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/_stub")
def stub():
    return {"note": "Audit log endpoints implemented alongside Phase 4."}
