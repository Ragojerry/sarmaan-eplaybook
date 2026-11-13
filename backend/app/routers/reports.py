"""User activity reports for the admin portal: per user, per area, per module,
with CSV export. The same data is served to Power BI by routers/bi.py.

The per-user table and its CSV take column filters and sorting
(app/reports/column_filters.py: q./in./min./max./from./to.<column>, sort, order),
so an export always contains exactly the rows on screen."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database import get_db
from app.models import User
from app.models.enums import RoleName
from app.devices import registry as device_registry
from app.reports import activity, column_filters
from app.reports.activity import Filters
from app.reports.params import report_filters

router = APIRouter()
VIEWERS = tuple(r for r in RoleName if r != RoleName.CDD)
LEVEL = Query(default="state", pattern="^(country|state|lga|ward|facility)$")


def csv_response(rows: list[dict], name: str) -> Response:
    return Response(
        content=activity.to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}.csv"'},
    )


@router.get("/summary")
def summary(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    rows = activity.user_rows(db, f)
    n = len(rows)
    total = rows[0]["modules_total"] if rows else 0
    from datetime import datetime, timedelta, timezone

    cutoff = (datetime.now(timezone.utc) - timedelta(days=activity.ACTIVE_WINDOW_DAYS)).isoformat()
    return {
        "users": n,
        "modules_total": total,
        "avg_completion_rate": round(sum(r["completion_rate"] for r in rows) / n, 1) if n else 0.0,
        "users_completed_all": sum(1 for r in rows if r["modules_total"] and r["modules_completed"] >= r["modules_total"]),
        "users_not_started": sum(1 for r in rows if r["modules_started"] == 0),
        "active_users_30d": sum(1 for r in rows if r["last_activity"] and r["last_activity"] >= cutoff),
        "quizzes_passed": sum(r["quizzes_passed"] for r in rows),
        "questions_asked": sum(r["questions_asked"] for r in rows),
    }


def _filtered(request: Request, rows: list[dict]) -> list[dict]:
    try:
        return column_filters.apply(rows, request.query_params.multi_items())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/users")
def users(request: Request, f: Filters = Depends(report_filters), db: Session = Depends(get_db),
          user: User = Depends(require_roles(*VIEWERS))):
    return _filtered(request, activity.user_rows(db, f))


@router.get("/users.csv")
def users_csv(request: Request, f: Filters = Depends(report_filters), db: Session = Depends(get_db),
              user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(_filtered(request, activity.user_rows(db, f)), "user_activity")


@router.get("/users/{user_id}/devices")
def user_devices(user_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    """Every device this account ever used (newest first), with active or not."""
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"active_days": device_registry.active_days(), "devices": device_registry.devices_of(db, user_id)}


@router.get("/boundaries")
def boundaries(level: str = LEVEL, f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return activity.boundary_rollup(activity.user_rows(db, f), level)


@router.get("/boundaries.csv")
def boundaries_csv(level: str = LEVEL, f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(activity.boundary_rollup(activity.user_rows(db, f), level), f"activity_by_{level}")


@router.get("/sessions")
def sessions(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return activity.session_rollup(db, activity.user_rows(db, f), not f.narrowed)


@router.get("/sessions.csv")
def sessions_csv(f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(activity.session_rollup(db, activity.user_rows(db, f), not f.narrowed), "training_sessions")


@router.get("/modules")
def modules(level: str | None = Query(default=None, pattern="^(country|state|lga|ward|facility|session)$"), f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return activity.module_rows(db, f, level)


@router.get("/modules.csv")
def modules_csv(level: str | None = Query(default=None, pattern="^(country|state|lga|ward|facility|session)$"), f: Filters = Depends(report_filters), db: Session = Depends(get_db), user: User = Depends(require_roles(*VIEWERS))):
    return csv_response(activity.module_rows(db, f, level), "module_completion" + (f"_by_{level}" if level else ""))
