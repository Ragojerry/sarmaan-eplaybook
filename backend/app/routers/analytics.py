"""
Phase 5: real database-driven dashboard statistics, per master prompt §49
("Do not use permanent prototype numbers") and §50 (analytics categories).

Every number here comes from an actual query. Metrics that depend on data
the mobile app doesn't emit yet (Phase 7+) legitimately return 0 — that's
honest, unlike the prototype's hardcoded non-zero placeholders
(docs/prototype-analysis.md §2, §8).
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Module, AiQuestionLog, AnalyticsEvent, Language
from app.models.enums import ModuleStatus, AnalyticsEventType
from app.schemas.analytics import DashboardResponse, ModuleEngagement, LanguageUsage

router = APIRouter()


@router.get("/_stub")
def stub():
    return {"note": "See GET /analytics/dashboard for the real, database-driven admin dashboard."}


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    active_devices_7d = (
        db.query(func.count(distinct(AnalyticsEvent.device_id)))
        .filter(AnalyticsEvent.occurred_at >= seven_days_ago, AnalyticsEvent.device_id.isnot(None))
        .scalar()
        or 0
    )

    published_modules = db.query(func.count(Module.id)).filter(Module.status == ModuleStatus.PUBLISHED).scalar() or 0
    draft_modules = db.query(func.count(Module.id)).filter(Module.status == ModuleStatus.DRAFT).scalar() or 0
    total_modules = db.query(func.count(Module.id)).scalar() or 0

    ai_questions_total = db.query(func.count(AiQuestionLog.id)).scalar() or 0
    ai_questions_unmatched = (
        db.query(func.count(AiQuestionLog.id)).filter(AiQuestionLog.matched.is_(False)).scalar() or 0
    )

    update_installs = (
        db.query(func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.event_type == AnalyticsEventType.UPDATE_INSTALLED)
        .scalar()
        or 0
    )
    update_adoption_percent = (
        round(100.0 * update_installs / active_devices_7d, 1) if active_devices_7d > 0 else None
    )

    engagement_rows = (
        db.query(
            Module.id,
            Module.module_code,
            Module.title,
            func.count(AnalyticsEvent.id).filter(AnalyticsEvent.event_type == AnalyticsEventType.MODULE_OPEN).label("opens"),
            func.count(AnalyticsEvent.id)
            .filter(AnalyticsEvent.event_type == AnalyticsEventType.MODULE_COMPLETE)
            .label("completions"),
        )
        .outerjoin(AnalyticsEvent, AnalyticsEvent.module_id == Module.id)
        .group_by(Module.id, Module.module_code, Module.title)
        .order_by(Module.sort_order)
        .all()
    )
    module_engagement = [
        ModuleEngagement(module_id=str(r.id), module_code=r.module_code, title=r.title, opens=r.opens or 0, completions=r.completions or 0)
        for r in engagement_rows
    ]

    language_rows = (
        db.query(AnalyticsEvent.language, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.language.isnot(None))
        .group_by(AnalyticsEvent.language)
        .all()
    )
    language_usage = [LanguageUsage(language_code=code, count=count) for code, count in language_rows]

    download_failures_7d = (
        db.query(func.count(AnalyticsEvent.id))
        .filter(
            AnalyticsEvent.event_type == AnalyticsEventType.DOWNLOAD_FAILED,
            AnalyticsEvent.occurred_at >= seven_days_ago,
        )
        .scalar()
        or 0
    )
    sync_failures_7d = (
        db.query(func.count(AnalyticsEvent.id))
        .filter(
            AnalyticsEvent.event_type == AnalyticsEventType.SYNC_FAILED,
            AnalyticsEvent.occurred_at >= seven_days_ago,
        )
        .scalar()
        or 0
    )

    return DashboardResponse(
        active_devices_7d=active_devices_7d,
        published_modules=published_modules,
        draft_modules=draft_modules,
        total_modules=total_modules,
        ai_questions_total=ai_questions_total,
        ai_questions_unmatched=ai_questions_unmatched,
        update_adoption_percent=update_adoption_percent,
        module_engagement=module_engagement,
        language_usage=language_usage,
        download_failures_7d=download_failures_7d,
        sync_failures_7d=sync_failures_7d,
    )
