"""Stub router — RAG/AI endpoints land in the AI phase."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/_stub")
def stub():
    return {"note": "AI/RAG endpoints implemented in the AI phase."}
