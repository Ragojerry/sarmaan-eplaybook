"""Shared enums, matching the master prompt's field lists exactly (§6-10, §15, §41, §61)."""
import enum


class RoleName(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    CONTENT_ADMIN = "CONTENT_ADMIN"
    PROGRAM_REVIEWER = "PROGRAM_REVIEWER"
    LOCALISATION_REVIEWER = "LOCALISATION_REVIEWER"
    TECHNICAL_REVIEWER = "TECHNICAL_REVIEWER"
    SUPERVISOR = "SUPERVISOR"
    CDD = "CDD"
    READ_ONLY = "READ_ONLY"


class BoundaryLevel(str, enum.Enum):
    """Administrative hierarchy, top to bottom. Each level's parent is the level above."""
    COUNTRY = "COUNTRY"
    STATE = "STATE"
    LGA = "LGA"
    WARD = "WARD"
    FACILITY = "FACILITY"


BOUNDARY_ORDER = [BoundaryLevel.COUNTRY, BoundaryLevel.STATE, BoundaryLevel.LGA, BoundaryLevel.WARD, BoundaryLevel.FACILITY]


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class LanguageStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    BETA = "BETA"
    IN_REVIEW = "IN_REVIEW"
    NOT_STARTED = "NOT_STARTED"


class CampaignStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class ModuleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


# Content governance workflow, per master prompt §15 exactly:
# Draft -> Programme Review -> Localisation Review -> Technical QA -> Published
class ContentReviewStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROGRAMME_REVIEW = "PROGRAMME_REVIEW"
    LOCALISATION_REVIEW = "LOCALISATION_REVIEW"
    TECHNICAL_QA = "TECHNICAL_QA"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


class ContentType(str, enum.Enum):
    TEXT = "TEXT"
    HEADING = "HEADING"
    IMAGE = "IMAGE"
    TABLE = "TABLE"
    CALLOUT = "CALLOUT"
    WARNING = "WARNING"
    JOB_AID = "JOB_AID"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    LIST = "LIST"


class MediaAssetType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class VideoStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class FaqStatus(str, enum.Enum):
    """Curated answers: only APPROVED ones are used by the Ask assistant."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


class ReferenceStatus(str, enum.Enum):
    """Reference library documents: only APPROVED ones are searched."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


class ReleaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ROLLED_BACK = "ROLLED_BACK"


class AnalyticsEventType(str, enum.Enum):
    """Covers every metric master prompt §50 lists, grouped by its own headers."""
    # Training
    MODULE_OPEN = "MODULE_OPEN"
    MODULE_COMPLETE = "MODULE_COMPLETE"
    # Videos
    VIDEO_OPEN = "VIDEO_OPEN"
    VIDEO_COMPLETE = "VIDEO_COMPLETE"
    VIDEO_PLAYBACK_FAILURE = "VIDEO_PLAYBACK_FAILURE"
    # Technical
    DOWNLOAD_STARTED = "DOWNLOAD_STARTED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    SYNC_FAILED = "SYNC_FAILED"
    APPLICATION_ERROR = "APPLICATION_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    # Device/session
    DEVICE_HEARTBEAT = "DEVICE_HEARTBEAT"
    UPDATE_INSTALLED = "UPDATE_INSTALLED"


class AuditAction(str, enum.Enum):
    SESSION_CHANGE = "SESSION_CHANGE"
    TRAINING_RESTART = "TRAINING_RESTART"
    BOUNDARY_CHANGE = "BOUNDARY_CHANGE"
    API_KEY_CREATE = "API_KEY_CREATE"
    API_KEY_REVOKE = "API_KEY_REVOKE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CONTENT_CREATE = "CONTENT_CREATE"
    CONTENT_EDIT = "CONTENT_EDIT"
    CONTENT_REVIEW = "CONTENT_REVIEW"
    CONTENT_APPROVE = "CONTENT_APPROVE"
    CONTENT_REJECT = "CONTENT_REJECT"
    RELEASE_CREATE = "RELEASE_CREATE"
    RELEASE_PUBLISH = "RELEASE_PUBLISH"
    RELEASE_ROLLBACK = "RELEASE_ROLLBACK"
    USER_CREATE = "USER_CREATE"
    ROLE_CHANGE = "ROLE_CHANGE"
    LANGUAGE_APPROVE = "LANGUAGE_APPROVE"
    LOGIN_FAILED = "LOGIN_FAILED"
    VIDEO_UPLOAD = "VIDEO_UPLOAD"
    VIDEO_UPDATE = "VIDEO_UPDATE"
    USER_UPDATE = "USER_UPDATE"
    REFERENCE_UPLOAD = "REFERENCE_UPLOAD"
    REFERENCE_UPDATE = "REFERENCE_UPDATE"
    FAQ_CREATE = "FAQ_CREATE"
    FAQ_UPDATE = "FAQ_UPDATE"
    CONSENT_UPDATE = "CONSENT_UPDATE"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    MATCHING = "MATCHING"
    ORDERING = "ORDERING"
    IMAGE_CHOICE = "IMAGE_CHOICE"
    NUMERIC = "NUMERIC"
