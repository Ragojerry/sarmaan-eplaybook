"""The device registry: which app installs each account uses, and which are active.

The app sends {install_id, os, os_version, model, app_version} with its login and
on every sync (POST /sync/device). install_id is the random id the app made on
first run; nothing here is a hardware identifier. A device is active when it was
seen (login or sync) within settings.active_device_days (default 30).
"""
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Device, User

_INSTALL_ID = re.compile(r"^[A-Za-z0-9-]{16,64}$")


class DeviceInfo(BaseModel):
    install_id: str = Field(min_length=16, max_length=64)
    os: str | None = Field(None, max_length=20)
    os_version: str | None = Field(None, max_length=500)
    model: str | None = Field(None, max_length=500)
    app_version: str | None = Field(None, max_length=40)

    @field_validator("install_id")
    @classmethod
    def _random_id(cls, v: str) -> str:
        if not _INSTALL_ID.match(v):
            raise ValueError("install_id must be the app's random id (letters, digits, dashes)")
        return v


def _clip(s: str | None, n: int) -> str | None:
    s = " ".join((s or "").split())
    return s[:n] or None


def active_days() -> int:
    return max(1, get_settings().active_device_days)


def active_cutoff(now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)) - timedelta(days=active_days())


def is_active(d: Device, now: datetime | None = None) -> bool:
    return d.last_seen_at is not None and d.last_seen_at >= active_cutoff(now)


def touch(db: Session, user: User, info: DeviceInfo, event: Literal["login", "sync"]) -> Device:
    """Creates or refreshes this account's row for the install (no commit)."""
    now = datetime.now(timezone.utc)
    d = db.query(Device).filter_by(user_id=user.id, install_id=info.install_id).one_or_none()
    if d is None:
        d = Device(user_id=user.id, install_id=info.install_id, first_seen_at=now)
        db.add(d)
    d.os = _clip(info.os, 20) or d.os
    d.os_version = _clip(info.os_version, 120) or d.os_version
    d.model = _clip(info.model, 120) or d.model
    d.app_version = _clip(info.app_version, 40) or d.app_version
    d.last_seen_at = now
    if event == "login":
        d.last_login_at = now
    else:
        d.last_sync_at = now
    return d


def serialize(d: Device, now: datetime | None = None) -> dict:
    iso = lambda t: t.isoformat() if t else None  # noqa: E731
    return {"id": str(d.id), "os": d.os, "os_version": d.os_version, "model": d.model, "app_version": d.app_version,
            "first_seen_at": iso(d.first_seen_at), "last_seen_at": iso(d.last_seen_at),
            "last_login_at": iso(d.last_login_at), "last_sync_at": iso(d.last_sync_at), "active": is_active(d, now)}


def devices_of(db: Session, user_id: uuid.UUID) -> list[dict]:
    rows = db.query(Device).filter_by(user_id=user_id).order_by(Device.last_seen_at.desc()).all()
    now = datetime.now(timezone.utc)
    return [serialize(d, now) for d in rows]


def report_fields(db: Session, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
    """Flat device columns for the user report (and its CSV / Power BI rows)."""
    now = datetime.now(timezone.utc)
    by_user = defaultdict(list)
    if user_ids:
        for d in db.query(Device).filter(Device.user_id.in_(user_ids)).order_by(Device.last_seen_at.desc()):
            by_user[d.user_id].append(d)
    out = {}
    for uid in user_ids:
        mine = by_user.get(uid, [])
        out[uid] = {
            "devices_active": sum(1 for d in mine if is_active(d, now)),
            "devices_total": len(mine),
            "device_last_seen": mine[0].last_seen_at.isoformat() if mine else None,
            "device_last_sync": max((d.last_sync_at for d in mine if d.last_sync_at), default=None),
            "devices_summary": " | ".join(
                f"{d.model or (d.os or 'device')} {d.os_version or ''} app {d.app_version or '?'} "
                f"({'active' if is_active(d, now) else 'inactive'}, last seen {d.last_seen_at.date().isoformat()})".replace("  ", " ")
                for d in mine) or None,
        }
        if out[uid]["device_last_sync"]:
            out[uid]["device_last_sync"] = out[uid]["device_last_sync"].isoformat()
    return out
