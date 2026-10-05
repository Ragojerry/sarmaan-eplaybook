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
