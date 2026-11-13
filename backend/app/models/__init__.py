"""Import every model here so Base.metadata (and therefore Alembic autogenerate)
sees the full schema. Order matters only for readability, not for correctness —
SQLAlchemy resolves relationships lazily via string references."""
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.language import Language
from app.models.campaign import Campaign
from app.models.module import Module, ModuleTranslation
from app.models.content_section import ContentSection
from app.models.section_translation import SectionTranslation
from app.models.quiz import QuizAttempt, QuizQuestion
from app.models.general_test import GeneralTestAttempt, GeneralTestQuestion, PlatformSetting
from app.models.media_asset import MediaAsset
from app.models.video import Video
from app.models.user_module_progress import UserModuleProgress
from app.models.content_release import ContentRelease
from app.models.ai_question_log import AiQuestionLog
from app.models.analytics_event import AnalyticsEvent
from app.models.content_chunk import ContentChunk
from app.models.reference_document import ReferenceDocument, ReferencePassage
from app.models.faq_entry import FaqEntry
from app.models.consent_text import ConsentText
from app.models.app_string import AppString, AppStringTranslation
from app.models.support_contact import SupportContact
from app.models.tool import ToolItem, ToolModule
from app.models.audit_log import AuditLog
from app.models.boundary import AdminBoundary
from app.models.api_key import ApiKey
from app.models.training_session import TrainingSession

__all__ = [
    "User",
    "RefreshToken",
    "Language",
    "Campaign",
    "Module",
    "ModuleTranslation",
    "ContentSection",
    "SectionTranslation",
    "QuizAttempt",
    "QuizQuestion",
    "GeneralTestQuestion",
    "GeneralTestAttempt",
    "PlatformSetting",
    "MediaAsset",
    "Video",
    "UserModuleProgress",
    "ContentRelease",
    "AiQuestionLog",
    "AnalyticsEvent",
    "ContentChunk",
    "ReferenceDocument",
    "ReferencePassage",
    "FaqEntry",
    "ConsentText",
    "AppString",
    "AppStringTranslation",
    "SupportContact",
    "ToolModule",
    "ToolItem",
    "AuditLog",
    "AdminBoundary",
    "ApiKey",
    "TrainingSession",
]
