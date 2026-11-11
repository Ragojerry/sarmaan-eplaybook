"""
CDD flipbook: scripts/migrate_cdd_content.py on top of the HFW curriculum.

Each test runs the real HFW changeover and then the CDD migration inside the
`sandbox` session from test_hfw_migration (an outer transaction that is rolled back),
so the development database is left exactly as it was.

    cd backend && python -m pytest tests/test_cdd_content.py -v
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.learning.access import visible_modules
from app.models import AuditLog, ContentChunk, ContentRelease, ContentSection, MediaAsset, Module, QuizAttempt, UserModuleProgress
from app.models.enums import AuditAction, LearnerRole, ModuleAudience, ModuleStatus, ReleaseStatus, TestType
from app.releases.packager import build_package
from app.releases.variants import filter_package
from app.routers.ai import answer
from scripts import cutover_hfw, migrate_cdd_content
from tests.test_hfw_migration import _people, sandbox  # noqa: F401  (sandbox is a fixture)

CONTENT = Path(__file__).resolve().parents[2] / "content" / "cdd_flipbook"
CDD_CODES = [f"CDD-{i:02d}" for i in range(1, 7)]
SPEC = json.loads((CONTENT / "content_sections.json").read_text(encoding="utf-8"))
IMAGES = {r["file"]: r for r in json.loads((CONTENT / "images_build.json").read_text(encoding="utf-8"))}
N_SECTIONS = sum(len(m["sections"]) for m in SPEC)
EVERYONE = (LearnerRole.CDD, LearnerRole.HEALTH_WORKER, LearnerRole.LOGISTICIAN, LearnerRole.MONITOR_SUPERVISOR,
            LearnerRole.OTHER)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture()
def hfw(sandbox, tmp_path):  # noqa: F811
    """The production state: HFW is the only curriculum, plus one learner of every role
    with some training history on HFW modules."""
    db = sandbox
    cutover_hfw.run(dry_run=False, db=db, media_root=tmp_path, env="development", cutover_date="")
    people = dict(zip(EVERYONE, _people(db, *EVERYONE)))
    mods = {m.module_code: m for m in db.query(Module).filter(Module.module_code.like("HFW-%"))}
    now = datetime.now(timezone.utc)
    for role, code in ((LearnerRole.CDD, "HFW-01"), (LearnerRole.HEALTH_WORKER, "HFW-05")):
        db.add(UserModuleProgress(user_id=people[role].id, module_id=mods[code].id, progress_percent=100,
                                  completed=True, completed_at=now, reading_completed_at=now))
        db.add(QuizAttempt(user_id=people[role].id, module_id=mods[code].id, client_id=str(uuid.uuid4()),
                           correct_count=10, total_count=10, score_percent=100, passed=True, results=[],
                           taken_at=now, test_type=TestType.POST, valid=True))
    db.commit()
    return db, people, tmp_path


def _counts(db):
    cdd = [m.id for m in db.query(Module).filter(Module.module_code.like("CDD-%"))]
    return {"modules": db.query(Module).count(), "sections": db.query(ContentSection).count(),
            "media": db.query(MediaAsset).count(), "chunks": db.query(ContentChunk).count(),
            "audit": db.query(AuditLog).count(), "cdd sections": db.query(ContentSection).filter(
                ContentSection.module_id.in_(cdd)).count() if cdd else 0}


def test_content_files_are_complete():
    """Every image the sections use was exported, with the checksum the build recorded."""
    assert [m["module_code"] for m in SPEC] == CDD_CODES
    assert all(m["title"].startswith(f"CDD - Module {i}:") for i, m in enumerate(SPEC, 1))
    used = [s["content"]["image_file"] for m in SPEC for s in m["sections"] if s["content_type"] == "IMAGE"]
    assert sorted(used) == sorted(IMAGES) and len(used) == 34
    for f in used:
        assert _sha((CONTENT / "images" / f).read_bytes()) == IMAGES[f]["sha256"], f
    pages = {p for m in SPEC for s in m["sections"] for p in s["pdf_pages"]}
    assert pages == set(range(1, 69)), "every PDF page has content"
    ids = [s["id"] for m in SPEC for s in m["sections"]]
    assert len(ids) == len(set(ids))


def test_dry_run_changes_nothing(hfw):
    db, people, media = hfw
    before = (_counts(db), migrate_cdd_content.hfw_audiences(db))
    rep = migrate_cdd_content.run(CONTENT, dry_run=True, media_root=media, db=db)
    assert rep.counts["modules created (PUBLISHED)"] == 6 and rep.counts["sections created"] == N_SECTIONS
    assert rep.counts["HFW modules re-tagged (audience only)"] == 13
    db.expire_all()
    assert (_counts(db), migrate_cdd_content.hfw_audiences(db)) == before
    assert not (media / "images" / "cdd").exists(), "a dry run copies no picture"


def test_cdd_added_and_hfw_untouched(hfw):
    db, people, media = hfw
    seen_before = {r: [m.module_code for m in visible_modules(db, u)] for r, u in people.items()}
    progress_before = sorted((str(p.user_id), str(p.module_id), p.completed) for p in db.query(UserModuleProgress))

    rep = migrate_cdd_content.run(CONTENT, dry_run=False, media_root=media, db=db)
    db.expire_all()

    # the script's own before/after proof: everything identical except the audience tags
    assert rep.fingerprint and all(b == a for b, a in rep.fingerprint.values())
    assert rep.fingerprint["content_sections"][0]["rows"] == 254
    assert rep.fingerprint["quiz_questions"][0]["rows"] == 170
    assert rep.fingerprint["user_module_progress"][0]["rows"] == 2
    assert sorted((str(p.user_id), str(p.module_id), p.completed) for p in db.query(UserModuleProgress)) == progress_before
    hfw_mods = db.query(Module).filter(Module.module_code.like("HFW-%")).all()
    assert len(hfw_mods) == 17 and {m.status for m in hfw_mods} == {ModuleStatus.PUBLISHED}
    assert not any("CDD" in (m.learner_roles or []) for m in hfw_mods)
    assert {m.module_code: m.learner_roles for m in hfw_mods if m.module_code in ("HFW-03", "HFW-07")} == \
        {"HFW-03": ["HEALTH_WORKER"], "HFW-07": ["HEALTH_WORKER"]}

    # the CDD modules: published, CDD only, every section and picture
    cdd = db.query(Module).filter(Module.module_code.like("CDD-%")).order_by(Module.sort_order).all()
    assert [m.module_code for m in cdd] == CDD_CODES
    for m in cdd:
        assert m.status == ModuleStatus.PUBLISHED
        assert (m.audience, m.learner_roles) == (ModuleAudience.ROLE_SPECIFIC, ["CDD"])
    ids = [m.id for m in cdd]
    assert db.query(ContentSection).filter(ContentSection.module_id.in_(ids)).count() == N_SECTIONS
    images = db.query(ContentSection).filter(ContentSection.module_id.in_(ids), ContentSection.content_type == "IMAGE").all()
    assert len(images) == 34
    for s in images:
        asset = db.get(MediaAsset, uuid.UUID(s.content["media_asset_id"]))
        data = (media / asset.storage_path).read_bytes()
        assert _sha(data) == asset.checksum == IMAGES[s.content["image_file"]]["sha256"]
        assert asset.size_bytes == len(data) and s.content["alt"] and s.content["caption"]
    audits = db.query(AuditLog).filter(AuditLog.action == AuditAction.CONTENT_CREATE, AuditLog.entity_id.in_(ids)).all()
    assert len(audits) == 6 and all(a.details["source"] == "content/source/CDD-flipbook.pdf" for a in audits)
    assert db.query(AuditLog).filter(AuditLog.action == AuditAction.AUDIENCE_CHANGE).count() == 13
    assert db.query(ContentRelease).filter(ContentRelease.release_code.like("CDD%")).count() == 0, "no release is made"

    # who sees what: CDD learners only the CDD modules; every other role exactly as before,
    # except Health Workers, who now also get HFW-03 and HFW-07
    seen = {r: [m.module_code for m in visible_modules(db, u)] for r, u in people.items()}
    assert seen[LearnerRole.CDD] == CDD_CODES
    assert set(seen[LearnerRole.HEALTH_WORKER]) == set(seen_before[LearnerRole.HEALTH_WORKER]) | {"HFW-03", "HFW-07"}
    for r in (LearnerRole.LOGISTICIAN, LearnerRole.MONITOR_SUPERVISOR, LearnerRole.OTHER):
        assert seen[r] == seen_before[r], r
    assert not any(c.startswith("CDD-") for r, codes in seen.items() if r != LearnerRole.CDD for c in codes)


def test_search_answers_come_from_the_learners_own_modules(hfw):
    db, people, media = hfw
    migrate_cdd_content.run(CONTENT, dry_run=False, media_root=media, db=db)
    db.expire_all()
    for question in ("How do I mark a house?", "What is the dose for a child 1-2 months?", "When should I refer a sick child?"):
        cdd = answer(db, question, "en", people[LearnerRole.CDD])
        hw = answer(db, question, "en", people[LearnerRole.HEALTH_WORKER])
        assert cdd["matched"] and hw["matched"], question
        assert {s["module_code"][:4] for s in cdd["sources"]} == {"CDD-"}, question
        assert {s["module_code"][:4] for s in hw["sources"]} == {"HFW-"}, question


def test_phone_packages_hold_each_roles_modules_and_pictures(hfw):
    db, people, media = hfw
    migrate_cdd_content.run(CONTENT, dry_run=False, media_root=media, db=db)
    db.expire_all()
    release = ContentRelease(release_code=f"TEST-CDD-{uuid.uuid4().hex[:8]}", version="test", status=ReleaseStatus.DRAFT)
    db.add(release)
    db.flush()
    package = build_package(db, release)
    for role, expect in ((LearnerRole.CDD, set(CDD_CODES)), (LearnerRole.LOGISTICIAN, None)):
        visible = {str(m.id): m for m in visible_modules(db, people[role])}
        audiences = {i: {"audience": m.audience.value, "learner_roles": sorted(m.learner_roles)} for i, m in visible.items()}
        variant = filter_package(package, set(visible), audiences)
        codes = {m["module_code"] for m in variant["modules"]}
        if expect:
            assert codes == expect
            assert variant["counts"]["media"] == 34 and variant["counts"]["sections"] == N_SECTIONS
            for a in variant["media"]:  # what the phone checks after downloading each picture
                assert _sha((media / db.get(MediaAsset, uuid.UUID(a["id"])).storage_path).read_bytes()) == a["checksum"]
            assert variant["curriculum"] == "hfw-2026", "no 'new curriculum' notice on CDD phones"
        else:
            assert codes and not any(c.startswith("CDD-") for c in codes)


def test_rerun_changes_nothing(hfw):
    db, people, media = hfw
    migrate_cdd_content.run(CONTENT, dry_run=False, media_root=media, db=db)
    db.expire_all()
    first = (_counts(db), migrate_cdd_content.hfw_audiences(db))
    again = migrate_cdd_content.run(CONTENT, dry_run=False, media_root=media, db=db)
    db.expire_all()
    assert (_counts(db), migrate_cdd_content.hfw_audiences(db)) == first
    assert again.counts["sections unchanged"] == N_SECTIONS and not again.audience
    assert again.counts["pictures already present (matched by SHA-256)"] == 34
    assert "audit entries for CDD modules" not in again.counts


def test_a_change_to_hfw_content_rolls_everything_back(hfw, monkeypatch):
    """The safety net: if anything but an audience tag changed on HFW, nothing is written."""
    db, people, media = hfw
    real = migrate_cdd_content.retag_hfw

    def retag_and_break(db, rep):
        real(db, rep)
        sec = db.query(ContentSection).join(Module).filter(Module.module_code == "HFW-01").first()
        sec.title = (sec.title or "") + " (changed)"
        db.flush()

    monkeypatch.setattr(migrate_cdd_content, "retag_hfw", retag_and_break)
    with pytest.raises(migrate_cdd_content.Refused, match="content_sections"):
        migrate_cdd_content.run(CONTENT, dry_run=False, media_root=media, db=db)
    db.expire_all()
    assert db.query(Module).filter(Module.module_code.like("CDD-%")).count() == 0


def test_production_needs_permission_and_a_backup(monkeypatch, capsys):
    monkeypatch.setattr(migrate_cdd_content, "get_settings", lambda: SimpleNamespace(environment="production"))
    assert migrate_cdd_content.main([]) == 2
    assert "--allow-production" in capsys.readouterr().out
    assert migrate_cdd_content.main(["--allow-production"]) == 2
    assert "no --backup given" in capsys.readouterr().out
