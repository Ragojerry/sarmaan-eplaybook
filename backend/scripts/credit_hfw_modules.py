"""
Gives learners credit for the new HFW modules from the current modules they
already completed (migration_plan.md). Re-runnable; never edits or deletes the
old progress or test records.

For each learner who completed an old module, and for each matching new module
that the learner's role can see:
  - a ModuleCompletionCredit row records "credited from <old module>" with the
    old completion date and the score of the post-test that completed it;
  - the learner's progress row for the new module is marked completed (with the
    old date), so the phone and the module lock order treat it as done.
Skipped: learners already credited (re-run), learners who already completed the
new module themselves (earned), and modules outside the learner's role.

Mapping: content/hfw_flipbook/content_sections.json, field credit_from (the old
module codes). When a new module lists several old modules, ALL of them must be
completed; the latest completion date and the lowest score are copied.

Usage (from backend/):
    python -m scripts.credit_hfw_modules --dry-run --report ../content/hfw_flipbook/credit_dry_run_report.md
    python -m scripts.credit_hfw_modules                 # writes (refused when ENVIRONMENT=production
                                                         #   unless --allow-production is given)
    python -m scripts.credit_hfw_modules --undo <run_id> # removes one run's credits
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.learning.rules import post_test_completes  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    Module,
    ModuleCompletionCredit,
    QuizAttempt,
    User,
    UserModuleProgress,
)
from app.models.enums import AuditAction, ModuleAudience, RoleName, TestType  # noqa: E402

DEFAULT_MAP = Path(__file__).resolve().parents[2] / "content" / "hfw_flipbook" / "content_sections.json"


def role_sees(module: Module, user: User) -> bool:
    """Audience only (the new modules may still be DRAFT when credit is given)."""
    if module.audience == ModuleAudience.GENERAL:
        return True
    return user.learner_role is not None and user.learner_role.value in (module.learner_roles or [])


def completing_score(attempts: list[QuizAttempt]) -> int | None:
    """Score of the post-test that completed the module: the first valid
    post-test meeting the rule against the latest valid pre-test before it.
    None when the module was completed without one (e.g. before tests existed)."""
    pre = None
    for a in sorted(attempts, key=lambda a: a.taken_at):
        if a.test_type == TestType.PRE:
            pre = a
        elif pre is not None and post_test_completes(a.correct_count, a.total_count, pre.correct_count, pre.total_count):
            return a.score_percent
    return None


def run(dry_run: bool, map_path: Path = DEFAULT_MAP, db=None, run_id: str | None = None) -> dict:
    own = db is None
    db = db or SessionLocal()
    run_id = run_id or "credit-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = {"run_id": run_id, "dry_run": dry_run, "modules": [], "warnings": []}
    try:
        mapping = [(m["module_code"], m["credit_from"]) for m in json.loads(map_path.read_text(encoding="utf-8")) if m["credit_from"]]
        codes = {c for _, olds in mapping for c in olds} | {n for n, _ in mapping}
        mods = {m.module_code: m for m in db.query(Module).filter(Module.module_code.in_(codes))}
        learners = {u.id: u for u in db.query(User).filter(User.role == RoleName.CDD)}
        old_ids = [mods[c].id for c in codes if c in mods and not c.startswith("HFW-")]
        done = defaultdict(dict)  # old module id -> {user id: progress}
        for p in db.query(UserModuleProgress).filter(UserModuleProgress.module_id.in_(old_ids),
                                                    UserModuleProgress.completed.is_(True)):
            if p.user_id in learners and p.completed_at is not None:
                done[p.module_id][p.user_id] = p
        attempts = defaultdict(list)
        for a in db.query(QuizAttempt).filter(QuizAttempt.module_id.in_(old_ids), QuizAttempt.valid.is_(True)):
            attempts[(a.user_id, a.module_id)].append(a)
        credits = {(c.user_id, c.module_id) for c in db.query(ModuleCompletionCredit)}

        for new_code, old_codes in mapping:
            row = {"module": new_code, "credit_from": old_codes, "credited_learners": 0, "records": 0, "skipped": Counter()}
            out["modules"].append(row)
            new = mods.get(new_code)
            missing = [c for c in old_codes if c not in mods]
            if new is None or missing:
                out["warnings"].append(f"{new_code}: skipped, module(s) not in the database: {', '.join(([new_code] if new is None else []) + missing)}")
                continue
            olds = [mods[c] for c in old_codes]
            eligible = set.intersection(*(set(done[o.id]) for o in olds))  # every listed old module completed
            for uid in sorted(eligible, key=str):
                u = learners[uid]
                if not role_sees(new, u):
                    row["skipped"]["new module is not for the learner's role"] += 1
                    continue
                if (uid, new.id) in credits:
                    row["skipped"]["already credited (earlier run)"] += 1
                    continue
                prog = db.query(UserModuleProgress).filter_by(user_id=uid, module_id=new.id).one_or_none()
                if prog is not None and prog.completed:
                    row["skipped"]["already completed in the new module (earned)"] += 1
                    continue
                sources = [(done[o.id][uid], o) for o in olds]
                last_p, last_o = max(sources, key=lambda t: t[0].completed_at)
                scores = [completing_score(attempts[(uid, o.id)]) for _, o in sources]
                score = None if any(s is None for s in scores) else min(scores)
                row["credited_learners"] += 1
                row["records"] += 1
                if dry_run:
                    continue
                credit = ModuleCompletionCredit(
                    user_id=uid, module_id=new.id, source_module_id=last_o.id, source_module_code=last_o.module_code,
                    source_completed_at=last_p.completed_at, source_score_percent=score, run_id=run_id,
                    progress_existed=prog is not None, previous_progress_percent=prog.progress_percent if prog else None,
                )
                if prog is None:
                    prog = UserModuleProgress(user_id=uid, module_id=new.id, progress_percent=0, device_id="credit")
                    db.add(prog)
                prog.completed, prog.completed_at, prog.progress_percent = True, last_p.completed_at, 100
                db.add(credit)
                credits.add((uid, new.id))
            row["skipped"] = dict(row["skipped"])
        out["total_records"] = sum(r["records"] for r in out["modules"])
        if dry_run:
            db.rollback()
        else:
            db.add(AuditLog(action=AuditAction.CONTENT_EDIT,
                            entity_type="module_completion_credit", entity_id=None,
                            details={"run_id": run_id, "records": out["total_records"],
                                     "per_module": {r["module"]: r["records"] for r in out["modules"]}}))
            db.commit()
        out["distinct_learners"] = len({uid for o in old_ids for uid in done[o]})
        return out
    except Exception:
        db.rollback()
        raise
    finally:
        if own:
            db.close()


def undo(run_id: str, dry_run: bool, db=None) -> dict:
    """Removes the credits of one run and puts the new-module progress back as it was.
    Progress the learner earned afterwards in the new module (a valid post-test) is kept."""
    own = db is None
    db = db or SessionLocal()
    try:
        rows = db.query(ModuleCompletionCredit).filter_by(run_id=run_id).all()
        n = Counter()
        for c in rows:
            prog = db.query(UserModuleProgress).filter_by(user_id=c.user_id, module_id=c.module_id).one_or_none()
            earned_since = db.query(QuizAttempt).filter_by(user_id=c.user_id, module_id=c.module_id, valid=True,
                                                          test_type=TestType.POST).count()
            if prog is not None and not earned_since:
                if c.progress_existed:
                    prog.completed, prog.completed_at = False, None
                    prog.progress_percent = c.previous_progress_percent or 0
                    n["progress restored"] += 1
                else:
                    db.delete(prog)
                    n["progress rows removed"] += 1
            elif earned_since:
                n["kept: learner took the new module's post-test since"] += 1
            db.delete(c)
            n["credits removed"] += 1
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return {"run_id": run_id, "dry_run": dry_run, **n}
    finally:
        if own:
            db.close()


def markdown(res: dict, env: str) -> str:
    lines = [f"# Credit report ({'DRY RUN, nothing changed' if res['dry_run'] else 'real run'}, environment {env})", "",
             f"Run id: `{res['run_id']}`. Learners with at least one completed old module: {res.get('distinct_learners', 0)}. "
             f"Credit records {'that would be' if res['dry_run'] else ''} created: **{res['total_records']}**.", "",
             "| New module | Credited from | Learners credited | Records | Skipped (reason: count) |", "|---|---|---|---|---|"]
    for r in res["modules"]:
        sk = "; ".join(f"{k}: {v}" for k, v in (r["skipped"] or {}).items()) or "none"
        lines.append(f"| {r['module']} | {', '.join(r['credit_from'])} | {r['credited_learners']} | {r['records']} | {sk} |")
    if res["warnings"]:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in res["warnings"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="change nothing; report counts per module")
    ap.add_argument("--map", type=Path, default=DEFAULT_MAP)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--undo", metavar="RUN_ID")
    ap.add_argument("--allow-production", action="store_true", help="required when ENVIRONMENT=production")
    a = ap.parse_args(argv)
    env = get_settings().environment
    if env == "production" and not a.allow_production:
        print("Refusing to run against ENVIRONMENT=production without --allow-production (run on staging first).")
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    if a.undo:
        print(json.dumps(undo(a.undo, a.dry_run), indent=1))
        return 0
    res = run(a.dry_run, a.map)
    md = markdown(res, env)
    print(md)
    if a.report:
        a.report.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
