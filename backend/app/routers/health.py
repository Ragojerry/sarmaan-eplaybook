from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Verifies the app can actually reach PostgreSQL, not just that the process is up."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
