"""
Phase 5: real database-driven dashboard statistics, per master prompt §49
("Do not use permanent prototype numbers") and §50 (analytics categories).

Every number here comes from an actual query. Metrics that depend on data
the mobile app doesn't emit yet (Phase 7+) legitimately return 0 — that's
honest, unlike the prototype's hardcoded non-zero placeholders
(docs/prototype-analysis.md §2, §8).
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models import (
    User,
    Module,
    AiQuestionLog,
    AnalyticsEvent,
    ContentRelease,
    Language,
    UserModuleProgress,
    Video,
)
from app.models.enums import ModuleStatus, AnalyticsEventType, ReleaseStatus, RoleName
from app.schemas.analytics import (
    DashboardResponse,
    DailyUsage,
    DeviceActivity,
    EventTypeCount,
    LanguageUsage,
    ModuleEngagement,
    ModuleUsage,
    QuestionCount,
    QuestionsReport,
    ReleaseAdoption,
    TechnicalCounts,
    UsageResponse,
    VideoUsage,
)

# Everyone who works on the programme can read aggregates; field staff (CDD) cannot.
REPORT_VIEWERS = tuple(r for r in RoleName if r not in (RoleName.CDD,))
ET = AnalyticsEventType


def _distinct_devices(db: Session, since: datetime, *filters) -> int:
    return (
        db.query(func.count(distinct(AnalyticsEvent.device_id)))
        .filter(AnalyticsEvent.occurred_at >= since, AnalyticsEvent.device_id.isnot(None), *filters)
        .scalar()
        or 0
    )


def _release_adoption(db: Session, since: datetime):
    """-> (current release code, devices that installed it, % of active devices, per-release counts).
    Counts DISTINCT devices from UPDATE_INSTALLED events, not raw event counts."""
    current = (
        db.query(ContentRelease)
        .filter(ContentRelease.status == ReleaseStatus.PUBLISHED, ContentRelease.checksum.isnot(None))
        .order_by(ContentRelease.published_at.desc())
        .first()
    )
    code_col = AnalyticsEvent.payload["release_code"].astext
    rows = (
        db.query(code_col, func.count(distinct(AnalyticsEvent.device_id)))
        .filter(AnalyticsEvent.event_type == ET.UPDATE_INSTALLED, AnalyticsEvent.device_id.isnot(None))
        .group_by(code_col)
        .order_by(func.count(distinct(AnalyticsEvent.device_id)).desc())
        .all()
    )
    per_release = [ReleaseAdoption(release_code=c, devices=n) for c, n in rows if c]
    current_code = current.release_code if current else None
    current_devices = next((r.devices for r in per_release if r.release_code == current_code), 0)
    active = _distinct_devices(db, since)
    pct = round(100.0 * current_devices / active, 1) if current_code and active > 0 else None
    return current_code, current_devices, pct, per_release

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

    _, _, update_adoption_percent, _ = _release_adoption(db, datetime.now(timezone.utc) - timedelta(days=30))

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


@router.get("/usage", response_model=UsageResponse)
def usage(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*REPORT_VIEWERS)),
):
    """Aggregated usage for the admin portal (master prompt §49-50). Aggregates
    only — no per-person data. Event-based figures come from devices that opted
    in to usage statistics; the CDD progress columns come from synced progress."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    devices = DeviceActivity(
        active_1d=_distinct_devices(db, now - timedelta(days=1)),
        active_7d=_distinct_devices(db, now - timedelta(days=7)),
        active_30d=_distinct_devices(db, now - timedelta(days=30)),
    )

    day = func.date_trunc("day", func.timezone("UTC", AnalyticsEvent.occurred_at))
    by_day = {
        d.date().isoformat(): (n, dev)
        for d, n, dev in db.query(day, func.count(AnalyticsEvent.id), func.count(distinct(AnalyticsEvent.device_id)))
        .filter(AnalyticsEvent.occurred_at >= since)
        .group_by(day)
        .all()
    }
    start = since.date()
    daily = []
    for i in range(days + 1):
        key = (start + timedelta(days=i)).isoformat()
        n, dev = by_day.get(key, (0, 0))
        daily.append(DailyUsage(date=key, events=n, devices=dev))

    events_by_type = [
        EventTypeCount(event_type=t.value, count=n)
        for t, n in db.query(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.occurred_at >= since)
        .group_by(AnalyticsEvent.event_type)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .all()
    ]

    def _count(event_type):
        return func.count(AnalyticsEvent.id).filter(AnalyticsEvent.event_type == event_type)

    mod_rows = (
        db.query(Module.id, Module.module_code, Module.title, _count(ET.MODULE_OPEN), _count(ET.MODULE_COMPLETE))
        .outerjoin(
            AnalyticsEvent,
            (AnalyticsEvent.module_id == Module.id) & (AnalyticsEvent.occurred_at >= since),
        )
        .group_by(Module.id, Module.module_code, Module.title, Module.sort_order)
        .order_by(Module.sort_order)
        .all()
    )
    prog = {
        mid: (started, completed)
        for mid, started, completed in db.query(
            UserModuleProgress.module_id,
            func.count(distinct(UserModuleProgress.user_id)),
            func.count(distinct(UserModuleProgress.user_id)).filter(UserModuleProgress.completed.is_(True)),
        )
        .group_by(UserModuleProgress.module_id)
        .all()
    }
    modules = [
        ModuleUsage(
            module_id=str(mid),
            module_code=code,
            title=title,
            opens=opens or 0,
            completions=comps or 0,
            cdds_started=prog.get(mid, (0, 0))[0],
            cdds_completed=prog.get(mid, (0, 0))[1],
        )
        for mid, code, title, opens, comps in mod_rows
    ]

    vid_rows = (
        db.query(
            Video.id,
            Video.title,
            _count(ET.VIDEO_OPEN),
            _count(ET.VIDEO_COMPLETE),
            _count(ET.VIDEO_PLAYBACK_FAILURE),
        )
        .outerjoin(
            AnalyticsEvent,
            (AnalyticsEvent.video_id == Video.id) & (AnalyticsEvent.occurred_at >= since),
        )
        .group_by(Video.id, Video.title)
        .order_by(Video.title)
        .all()
    )
    videos = [
        VideoUsage(video_id=str(vid), title=t, opens=o or 0, completions=c or 0, playback_failures=f or 0)
        for vid, t, o, c, f in vid_rows
    ]

    counts = dict(
        db.query(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.occurred_at >= since)
        .group_by(AnalyticsEvent.event_type)
        .all()
    )
    technical = TechnicalCounts(
        download_failures=counts.get(ET.DOWNLOAD_FAILED, 0),
        sync_failures=counts.get(ET.SYNC_FAILED, 0),
        app_errors=counts.get(ET.APPLICATION_ERROR, 0),
        storage_errors=counts.get(ET.STORAGE_ERROR, 0),
        playback_failures=counts.get(ET.VIDEO_PLAYBACK_FAILURE, 0),
    )

    current_code, current_devices, pct, per_release = _release_adoption(db, now - timedelta(days=30))

    languages = [
        LanguageUsage(language_code=code, count=n)
        for code, n in db.query(AnalyticsEvent.language, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.language.isnot(None), AnalyticsEvent.occurred_at >= since)
        .group_by(AnalyticsEvent.language)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .all()
    ]

    return UsageResponse(
        days=days,
        since=since.date().isoformat(),
        devices=devices,
        daily=daily,
        events_by_type=events_by_type,
        modules=modules,
        videos=videos,
        technical=technical,
        current_release_code=current_code,
        current_release_devices=current_devices,
        release_adoption_percent=pct,
        release_adoption=per_release,
        languages=languages,
        note="Event figures cover devices that opted in to usage statistics. Days are UTC.",
    )


@router.get("/questions", response_model=QuestionsReport)
def questions(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*REPORT_VIEWERS)),
):
    """Master prompt §42-43: what learners ask that the materials don't answer
    (content gaps) and what they ask most. Questions are grouped case-insensitively."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    base = db.query(AiQuestionLog).filter(AiQuestionLog.asked_at >= since)
    total = base.count()
    matched = base.filter(AiQuestionLog.matched.is_(True)).count()

    norm = func.lower(func.trim(AiQuestionLog.question))

    def _top(is_matched: bool) -> list[QuestionCount]:
        rows = (
            db.query(norm, func.count(AiQuestionLog.id), func.max(AiQuestionLog.asked_at))
            .filter(AiQuestionLog.asked_at >= since, AiQuestionLog.matched.is_(is_matched))
            .group_by(norm)
            .order_by(func.count(AiQuestionLog.id).desc(), func.max(AiQuestionLog.asked_at).desc())
            .limit(limit)
            .all()
        )
        return [QuestionCount(question=q, count=n, last_asked=last.isoformat()) for q, n, last in rows]

    return QuestionsReport(
        days=days,
        total=total,
        matched=matched,
        unmatched=total - matched,
        answer_rate_percent=round(100.0 * matched / total, 1) if total else None,
        top_unanswered=_top(False),
        top_answered=_top(True),
    )
