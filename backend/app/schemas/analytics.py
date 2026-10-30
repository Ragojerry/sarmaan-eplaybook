from pydantic import BaseModel


class ModuleEngagement(BaseModel):
    module_id: str
    module_code: str
    title: str
    opens: int
    completions: int


class LanguageUsage(BaseModel):
    language_code: str
    count: int


class DashboardResponse(BaseModel):
    """Every field here is a real query result — never a literal, per master
    prompt §49 ("Do not use permanent prototype numbers"). Fields legitimately
    read 0 until the mobile app is actually emitting analytics events
    (Phase 7+) — a true zero is honest; a fabricated nonzero number is not."""

    active_devices_7d: int
    published_modules: int
    draft_modules: int
    total_modules: int
    ai_questions_total: int
    ai_questions_unmatched: int
    update_adoption_percent: float | None
    module_engagement: list[ModuleEngagement]
    language_usage: list[LanguageUsage]
    download_failures_7d: int
    sync_failures_7d: int


# ---------- Phase 13: usage reports ----------


class DeviceActivity(BaseModel):
    active_1d: int
    active_7d: int
    active_30d: int


class DailyUsage(BaseModel):
    date: str  # YYYY-MM-DD (UTC)
    events: int
    devices: int


class EventTypeCount(BaseModel):
    event_type: str
    count: int


class ModuleUsage(BaseModel):
    module_id: str
    module_code: str
    title: str
    opens: int
    completions: int
    cdds_started: int  # from synced progress (account-based, not opt-in analytics)
    cdds_completed: int


class VideoUsage(BaseModel):
    video_id: str
    title: str
    opens: int
    completions: int
    playback_failures: int


class TechnicalCounts(BaseModel):
    download_failures: int
    sync_failures: int
    app_errors: int
    storage_errors: int
    playback_failures: int


class ReleaseAdoption(BaseModel):
    release_code: str
    devices: int


class UsageResponse(BaseModel):
    days: int
    since: str
    devices: DeviceActivity
    daily: list[DailyUsage]
    events_by_type: list[EventTypeCount]
    modules: list[ModuleUsage]
    videos: list[VideoUsage]
    technical: TechnicalCounts
    current_release_code: str | None
    current_release_devices: int
    release_adoption_percent: float | None
    release_adoption: list[ReleaseAdoption]
    languages: list[LanguageUsage]
    note: str


class QuestionCount(BaseModel):
    question: str
    count: int
    last_asked: str


class QuestionsReport(BaseModel):
    days: int
    total: int
    matched: int
    unmatched: int
    answer_rate_percent: float | None
    top_unanswered: list[QuestionCount]
    top_answered: list[QuestionCount]
