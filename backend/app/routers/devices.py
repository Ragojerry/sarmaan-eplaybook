"""Device registry endpoint for phones (app/devices/registry.py).

  POST /sync/device   refreshes this account's row for the install; the app calls it
                      on every sync (and sends the same block with its login).
Older apps never call it; nothing else depends on it.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.devices import registry
from app.devices.registry import DeviceInfo
from app.models import User

sync_router = APIRouter()


@sync_router.post("/device")
def sync_device(payload: DeviceInfo, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = registry.touch(db, current_user, payload, "sync")
    db.commit()
    db.refresh(d)
    return {"active_days": registry.active_days(), "device": registry.serialize(d)}
