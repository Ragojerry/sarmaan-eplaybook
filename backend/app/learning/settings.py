"""Training rules an administrator can change in the portal (table platform_settings).

module_min_seconds        active time a learner must spend in a module before completing it
general_test_active       the General pre-test gate and post-test are switched on
general_pass_mark_cdd     General pre/post-test pass mark (%) for CDD learners (60)
general_pass_mark_other   the same for every other learner role and staff accounts (80)
                          (each attempt stores the mark that applied: a change never alters old results)

Phones receive both with GET /sync/learning. A missing row means the default.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import AuditLog, GeneralTestQuestion, PlatformSetting, User
from app.models.enums import AuditAction, LearnerRole

DEFAULTS = {"module_min_seconds": 180, "general_test_active": False, "general_pass_mark_cdd": 60, "general_pass_mark_other": 80}
PASS_MARK_KEYS = ("general_pass_mark_cdd", "general_pass_mark_other")
MAX_MODULE_SECONDS = 3600


class SettingError(ValueError):
    pass


@dataclass(frozen=True)
class TrainingSettings:
    module_min_seconds: int
    general_test_active: bool
    general_pass_mark_cdd: int = 60
    general_pass_mark_other: int = 80

    def pass_mark_for(self, user: User) -> int:
        """CDD learners use the CDD mark; every other learner role (Health Worker,
        Logistician, Monitor/Supervisor, Others) and staff accounts the other one."""
        return self.general_pass_mark_cdd if user.learner_role == LearnerRole.CDD else self.general_pass_mark_other


def training_settings(db: Session) -> TrainingSettings:
    stored = {r.key: r.value for r in db.query(PlatformSetting).filter(PlatformSetting.key.in_(DEFAULTS))}
    values = {**DEFAULTS, **stored}
    return TrainingSettings(module_min_seconds=int(values["module_min_seconds"]),
                            general_test_active=bool(values["general_test_active"]),
                            general_pass_mark_cdd=int(values["general_pass_mark_cdd"]),
                            general_pass_mark_other=int(values["general_pass_mark_other"]))


def general_test_ready(db: Session) -> str | None:
    """Why the General test cannot be switched on (None = it can)."""
    questions = db.query(GeneralTestQuestion).filter_by(is_active=True).all()
    if not questions:
        return "no active General test question"
    missing = sorted(q.number for q in questions if q.correct_index is None)
    if missing:
        return f"questions without a correct answer: {', '.join(map(str, missing))}"
    return None


def change_setting(db: Session, key: str, value, user: User) -> None:
    if key not in DEFAULTS:
        raise SettingError(f"unknown setting {key}")
    if key == "module_min_seconds":
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_MODULE_SECONDS:
            raise SettingError(f"module_min_seconds must be a whole number of seconds from 0 to {MAX_MODULE_SECONDS}")
    if key in PASS_MARK_KEYS:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise SettingError(f"{key} must be a whole number from 1 to 100")
    if key == "general_test_active":
        if not isinstance(value, bool):
            raise SettingError("general_test_active must be true or false")
        problem = general_test_ready(db) if value else None
        if problem:
            raise SettingError(f"the General test cannot be switched on: {problem}")
    row = db.get(PlatformSetting, key)
    before = row.value if row else DEFAULTS[key]
    if row is None:
        row = PlatformSetting(key=key, value=value)
        db.add(row)
    row.value, row.updated_by = value, user.id
    db.add(AuditLog(user_id=user.id, action=AuditAction.SETTING_CHANGE, entity_type="platform_setting",
                    details={"key": key, "before": before, "after": value}))
