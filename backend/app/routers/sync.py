"""Stub router — offline sync endpoints (progress, AI questions, analytics) land in a later phase."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/_stub")
def stub():
    return {"note": "Sync endpoints implemented in the mobile/sync phase."}
