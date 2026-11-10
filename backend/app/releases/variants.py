"""Per-learner-role copies of a published release package.

Publishing still freezes ONE package with every published module. A phone is
served a copy filtered to the modules its user may see NOW
(app/learning/access.py): modules, their quiz questions, search passages and
the pictures only those modules use. Each distinct set of modules is written
once next to the frozen file and reused, with its own SHA-256, so the phone's
checksum check still applies. Restricted content therefore never leaves the
server for the wrong role, on old app versions too.

The variant key is a short hash of the kept modules and their audiences, so a
role change (or an audience change) yields a new key and the phone knows to
download again.
"""
import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.learning.access import visible_modules
from app.models import ContentRelease, User
from app.releases.packager import _canonical, _sha256, package_path


def _media_ids(module: dict) -> set[str]:
    ids = set()
    for s in module.get("sections", []):
        if s.get("content_type") in ("IMAGE", "AUDIO") and (s.get("content") or {}).get("media_asset_id"):
            ids.add(str(s["content"]["media_asset_id"]))
    for q in module.get("quiz_questions", []):
        if (q.get("content") or {}).get("media_asset_id"):
            ids.add(str(q["content"]["media_asset_id"]))
    return ids


def filter_package(package: dict, allowed: set[str], audiences: dict[str, dict]) -> dict:
    """A copy of `package` holding only the modules in `allowed`. `audiences`
    (module id -> {"audience", "learner_roles"}) stamps each kept module with
    its current audience, so the phone can also hide it locally."""
    modules = []
    for m in package["modules"]:
        if m["id"] in allowed:
            modules.append({**m, **audiences.get(m["id"], {})})
    used_media = set().union(*(_media_ids(m) for m in modules)) if modules else set()
    media = [a for a in package.get("media", []) if a["id"] in used_media]
    chunks = [c for c in package.get("chunks", []) if c.get("module_id") in allowed]
    return {
        **package,
        "modules": modules,
        "media": media,
        "chunks": chunks,
        "languages": sorted({t["language_code"] for m in modules for t in m["translations"]}),
        "counts": {
            "modules": len(modules),
            "sections": sum(len(m["sections"]) for m in modules),
            "media": len(media),
            "chunks": len(chunks),
            "quiz_questions": sum(len(m.get("quiz_questions", [])) for m in modules),
        },
    }


_module_ids: dict[str, frozenset[str]] = {}
_digests: dict[Path, tuple[int, str]] = {}


def _package_module_ids(release_code: str) -> frozenset[str]:
    """Module ids in a frozen package (read once per process; packages never change)."""
    if release_code not in _module_ids:
        package = json.loads(package_path(release_code).read_bytes())
        _module_ids[release_code] = frozenset(m["id"] for m in package["modules"])
    return _module_ids[release_code]


def variant_for(db: Session, release: ContentRelease, user: User) -> tuple[Path, str, int, str]:
    """(file, variant key, size, sha256) of the package this user should get.
    Called on every update check, so the package is only parsed when a new
    variant has to be written."""
    frozen = package_path(release.release_code)
    visible = {str(m.id): m for m in visible_modules(db, user)}
    allowed = _package_module_ids(release.release_code) & set(visible)
    audiences = {
        mid: {"audience": visible[mid].audience.value, "learner_roles": sorted(visible[mid].learner_roles or [])}
        for mid in sorted(allowed)
    }
    key = hashlib.sha256(json.dumps(audiences, sort_keys=True).encode()).hexdigest()[:16]
    path = frozen.with_name(frozen.name.replace(".package.json", f".{key}.package.json"))
    if not path.exists():
        data = _canonical(filter_package(json.loads(frozen.read_bytes()), allowed, audiences))
        tmp = path.with_suffix(f".{key}.tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
        _digests[path] = (len(data), _sha256(data))
    if path not in _digests:
        data = path.read_bytes()
        _digests[path] = (len(data), _sha256(data))
    size, digest = _digests[path]
    return path, key, size, digest
