"""Admin portal pages, and which of them each portal user may open.

The portal role still decides what someone may do; a super admin can also tick
the pages a user sees (users.admin_pages). Ticks only narrow what the role
allows, never widen it. NULL means every page the role allows (all accounts
created before this existed). SUPER_ADMIN always sees every page.

Checked by require_roles and the other staff-only dependencies (portal
endpoints), never on phone endpoints, so a supervisor who also trains on the
phone is not affected by their portal ticks.
"""
from fastapi import HTTPException, Request, status

from app.models.enums import RoleName

STAFF = tuple(r for r in RoleName if r != RoleName.CDD)
REVIEWERS = (RoleName.CONTENT_ADMIN, RoleName.PROGRAM_REVIEWER, RoleName.LOCALISATION_REVIEWER,
             RoleName.TECHNICAL_REVIEWER)

# key: (label, roles that may open it). Order is the portal menu's order.
PAGES: dict[str, tuple[str, tuple[RoleName, ...]]] = {
    "dashboard": ("Dashboard", STAFF),
    "content": ("Content", STAFF),
    "videos": ("Videos", STAFF),
    "tools": ("Tools repository", STAFF),
    "learning": ("Roles & tests", STAFF),
    "general-test": ("General test", STAFF),
    "answers": ("Curated answers", REVIEWERS),
    "references": ("Reference library", REVIEWERS),
    "releases": ("Releases", STAFF),
    "languages": ("Languages", STAFF),
    "app-text": ("App interface text", REVIEWERS),
    "consent": ("Consent text", (RoleName.CONTENT_ADMIN, RoleName.LOCALISATION_REVIEWER)),
    "support-contacts": ("Support contacts", STAFF),
    "analytics": ("Analytics", STAFF),
    "reports": ("Reports", STAFF),
    "audit": ("Audit log", (RoleName.CONTENT_ADMIN, RoleName.TECHNICAL_REVIEWER)),
    "users": ("Users", ()),  # SUPER_ADMIN only
    "sessions": ("Sessions", ()),
    "areas": ("Areas", ()),
}

ANY = frozenset(PAGES)

# API prefix: (pages whose screens read it, pages whose screens change it).
# Longest prefix wins. A portal endpoint missing here is closed to a user with
# ticked pages (tests/test_admin_pages.py checks every route is listed).
API_PAGES: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "/analytics/dashboard": (frozenset({"dashboard"}), frozenset({"dashboard"})),
    "/analytics": (frozenset({"analytics"}), frozenset({"analytics"})),
    "/modules": (frozenset({"content", "videos", "answers", "learning"}), frozenset({"content", "learning"})),
    "/quiz": (frozenset({"content"}), frozenset({"content"})),
    "/media": (frozenset({"content"}), frozenset({"content"})),
    "/videos": (frozenset({"videos", "content"}), frozenset({"videos", "content"})),
    "/faqs": (frozenset({"answers"}), frozenset({"answers"})),
    "/references": (frozenset({"references"}), frozenset({"references"})),
    "/releases": (frozenset({"releases"}), frozenset({"releases"})),
    "/languages": (ANY, frozenset({"languages"})),  # every translating screen lists the languages
    "/app-strings": (frozenset({"app-text"}), frozenset({"app-text"})),
    "/consent": (frozenset({"consent"}), frozenset({"consent"})),
    "/support-contacts": (frozenset({"support-contacts"}), frozenset({"support-contacts"})),
    "/tools": (frozenset({"tools"}), frozenset({"tools"})),
    "/learning": (frozenset({"learning", "reports"}), frozenset({"learning"})),
    "/general-test": (frozenset({"general-test"}), frozenset({"general-test"})),
    "/reports": (frozenset({"reports"}), frozenset({"reports"})),
    "/bi": (frozenset({"reports"}), frozenset({"reports"})),
    "/sessions": (frozenset({"sessions", "reports", "users"}), frozenset({"sessions"})),
    "/boundaries": (frozenset({"areas", "reports", "users"}), frozenset({"areas"})),
    "/users": (frozenset({"users"}), frozenset({"users", "learning"})),
    "/audit": (frozenset({"audit"}), frozenset({"audit"})),
}

READ_METHODS = {"GET", "HEAD", "OPTIONS"}


def role_allows(role: RoleName, page: str) -> bool:
    if role == RoleName.SUPER_ADMIN:
        return True
    return role in PAGES[page][1]


def allowed_pages(role: RoleName, ticked: list[str] | None) -> list[str]:
    """The pages this account sees: those its role allows, narrowed by its ticks."""
    if role == RoleName.SUPER_ADMIN:
        return list(PAGES)
    return [p for p in PAGES if role_allows(role, p) and (ticked is None or p in ticked)]


def clean_pages(role: RoleName, ticked: list[str] | None) -> list[str] | None:
    """Validates ticks for a role. None (every page the role allows) for
    SUPER_ADMIN and learners, who have no choice to make."""
    if ticked is None or role in (RoleName.SUPER_ADMIN, RoleName.CDD):
        return None
    unknown = sorted(set(ticked) - set(PAGES))
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown page(s): {', '.join(unknown)}")
    refused = [PAGES[p][0] for p in PAGES if p in ticked and not role_allows(role, p)]
    if refused:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"The role {role.value} cannot open: {', '.join(refused)}")
    if not ticked:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Tick at least one page")
    return [p for p in PAGES if p in ticked]


def api_pages(path: str) -> tuple[frozenset[str], frozenset[str]] | None:
    best = None
    for prefix in API_PAGES:
        if (path == prefix or path.startswith(prefix + "/")) and (best is None or len(prefix) > len(best)):
            best = prefix
    return API_PAGES[best] if best else None


def check_page(request: Request, user) -> None:
    """403 when a user with ticked pages calls a portal endpoint that none of
    their pages uses."""
    if user.role == RoleName.SUPER_ADMIN or user.admin_pages is None:
        return
    # The address actually called: newer FastAPI versions give scope["route"] the
    # path without its router prefix ("/summary"), which would match nothing.
    path = request.url.path
    root = request.scope.get("root_path") or ""
    if root and path.startswith(root):
        path = path[len(root):] or "/"
    pages = api_pages(path)
    if pages is not None:
        needed = pages[0] if request.method in READ_METHODS else pages[1]
        if needed & set(allowed_pages(user.role, user.admin_pages)):
            return
    raise HTTPException(status.HTTP_403_FORBIDDEN,
                        "Your account does not include this page. Ask a super admin to add it.")
