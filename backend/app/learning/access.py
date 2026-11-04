"""Who may see which module.

Learner accounts (portal role CDD) see GENERAL modules plus the ROLE_SPECIFIC
modules listing their learner_role; a learner without a learner_role sees
GENERAL modules only. Staff accounts (every other portal role) see every
module, so reviewers can preview content on a phone. Every endpoint that hands
module content to a phone goes through here: hiding a module in the app alone
is not enough.
"""
import uuid

from sqlalchemy.orm import Session

from app.models import Module, User
from app.models.enums import ModuleAudience, ModuleStatus, RoleName


def is_learner(user: User) -> bool:
    return user.role == RoleName.CDD


def module_visible_to(module: Module, user: User) -> bool:
    if not is_learner(user):
        return True
    if module.status != ModuleStatus.PUBLISHED:
        return False
    if module.audience == ModuleAudience.GENERAL:
        return True
    return user.learner_role is not None and user.learner_role.value in (module.learner_roles or [])


def visible_modules(db: Session, user: User) -> list[Module]:
    """Published modules this user may see, in learning order."""
    rows = (
        db.query(Module)
        .filter(Module.status == ModuleStatus.PUBLISHED)
        .order_by(Module.sort_order, Module.module_number, Module.module_code)
        .all()
    )
    return [m for m in rows if module_visible_to(m, user)]


def visible_module_ids(db: Session, user: User) -> set[uuid.UUID]:
    return {m.id for m in visible_modules(db, user)}
