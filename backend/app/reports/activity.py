"""
User activity reporting. One function builds a row per user (completion, quiz,
activity categories, area); everything else (rollups by area, per-module
tables, CSV, Power BI) is derived from those rows so every screen and export
agrees with every other.

Date range: when date_from/date_to are given, activity counts are limited to
that period and "modules completed" counts completions that happened in it.
Without dates everything is all-time.

Activity categories (columns on every row):
  training   MODULE_OPEN + MODULE_COMPLETE events
  video      VIDEO_OPEN / VIDEO_COMPLETE / VIDEO_PLAYBACK_FAILURE
  quiz       quiz attempts
  qa         questions asked in the Ask screen (and how many went unanswered)
  technical  DOWNLOAD_STARTED/FAILED, SYNC_FAILED, APPLICATION_ERROR, STORAGE_ERROR
  session    DEVICE_HEARTBEAT, UPDATE_INSTALLED
"""
from __future__ import annotations

import csv
import io
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    AdminBoundary,
    AiQuestionLog,
    AnalyticsEvent,
    GeneralTestAttempt,
    Module,
    QuizAttempt,
    User,
    UserModuleProgress,
)
from app.learning.access import module_visible_to
from app.devices import registry as device_registry
from app.learning.rules import general_passes
from app.models.enums import AnalyticsEventType as ET, BoundaryLevel, LearnerRole, ModuleStatus, RoleName, TestType

CATEGORY_EVENTS = {
    "training": (ET.MODULE_OPEN, ET.MODULE_COMPLETE),
    "video": (ET.VIDEO_OPEN, ET.VIDEO_COMPLETE, ET.VIDEO_PLAYBACK_FAILURE),
    "technical": (ET.DOWNLOAD_STARTED, ET.DOWNLOAD_FAILED, ET.SYNC_FAILED, ET.APPLICATION_ERROR, ET.STORAGE_ERROR),
    "session": (ET.DEVICE_HEARTBEAT, ET.UPDATE_INSTALLED),
}
# Not training activity: never counted in these reports, not even as "last activity"
# (the Support deck and the Tools repository are separate from training).
NON_TRAINING_EVENTS = (ET.SUPPORT_CONTACT_TAP, ET.TOOL_OPEN)
LEVELS = ["country", "state", "lga", "ward", "facility"]
ACTIVE_WINDOW_DAYS = 30


@dataclass
class Filters:
    country_id: uuid.UUID | None = None
    state_id: uuid.UUID | None = None
    lga_id: uuid.UUID | None = None
    ward_id: uuid.UUID | None = None
    facility_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    role: RoleName | None = RoleName.CDD
    learner_role: LearnerRole | None = None
    team_code: str | None = None
    date_from: date | None = None
    date_to: date | None = None

    @property
    def narrowed(self) -> bool:
        """True when the user population is restricted (area, session, team or role other than the default)."""
        return bool(self.country_id or self.state_id or self.lga_id or self.ward_id or self.facility_id
                    or self.session_id or self.team_code or self.learner_role or self.role != RoleName.CDD)

    @property
    def start(self):
        return datetime.combine(self.date_from, time.min, tzinfo=timezone.utc) if self.date_from else None

    @property
    def end(self):
        return datetime.combine(self.date_to + timedelta(days=1), time.min, tzinfo=timezone.utc) if self.date_to else None


def _in_range(col, f: Filters):
    conds = []
    if f.start is not None:
        conds.append(col >= f.start)
    if f.end is not None:
        conds.append(col < f.end)
    return conds


def user_rows(db: Session, f: Filters) -> list[dict]:
    q = db.query(User)
    for level in LEVELS:
        v = getattr(f, f"{level}_id")
        if v:
            q = q.filter(getattr(User, f"{level}_id") == v)
    if f.session_id:
        q = q.filter(User.training_session_id == f.session_id)
    if f.role:
        q = q.filter(User.role == f.role)
    if f.learner_role:
        q = q.filter(User.learner_role == f.learner_role)
    if f.team_code:
        q = q.filter(User.team_code == f.team_code)
    users = q.order_by(User.last_name, User.first_name).all()
    ids = [u.id for u in users]
    devices = device_registry.report_fields(db, ids)
    modules = db.query(Module).filter(Module.status == ModuleStatus.PUBLISHED).all()
    # Each person is measured against the modules they can see (general + their learner role's).
    visible_to = {u.id: {m.id for m in modules if module_visible_to(m, u)} for u in users}

    completed = defaultdict(int)
    started = defaultdict(int)
    completion_times = defaultdict(list)
    last_progress = {}
    seconds = defaultdict(int)
    if ids:
        for uid, mid, done, completed_at, updated, secs in db.query(
            UserModuleProgress.user_id, UserModuleProgress.module_id, UserModuleProgress.completed,
            UserModuleProgress.completed_at, UserModuleProgress.updated_at, UserModuleProgress.seconds_spent,
        ).filter(UserModuleProgress.user_id.in_(ids)):
            if mid not in visible_to[uid]:
                continue
            seconds[uid] += secs or 0
            ts = completed_at or updated
            if f.start or f.end:
                ok = (f.start is None or (ts and ts >= f.start)) and (f.end is None or (ts and ts < f.end))
                if not ok:
                    continue
            started[uid] += 1
            if done:
                completed[uid] += 1
                completion_times[uid].append(completed_at or updated)
            if updated and (uid not in last_progress or updated > last_progress[uid]):
                last_progress[uid] = updated

    cat = defaultdict(lambda: defaultdict(int))
    last_event = {}
    if ids:
        ev = db.query(AnalyticsEvent.user_id, AnalyticsEvent.event_type, func.count(), func.max(AnalyticsEvent.occurred_at)).join(
            User, User.id == AnalyticsEvent.user_id
        ).filter(
            AnalyticsEvent.user_id.in_(ids), *_in_range(AnalyticsEvent.occurred_at, f),
            AnalyticsEvent.event_type.notin_(NON_TRAINING_EVENTS),
            or_(User.training_restarted_at.is_(None), AnalyticsEvent.occurred_at >= User.training_restarted_at),
        ).group_by(AnalyticsEvent.user_id, AnalyticsEvent.event_type)
        by_type = {t: c for c, types in CATEGORY_EVENTS.items() for t in types}
        for uid, et, n, last in ev:
            c = by_type.get(et)
            if c:
                cat[uid][c] += n
            if et == ET.MODULE_OPEN:
                cat[uid]["module_opens"] += n
            if et == ET.VIDEO_OPEN:
                cat[uid]["video_opens"] += n
            if last and (uid not in last_event or last > last_event[uid]):
                last_event[uid] = last

    quiz = defaultdict(lambda: {"attempts": 0, "best": {}, "last": None})
    module_quiz = defaultdict(lambda: {"attempts": 0, "passed": set()})
    if ids:
        for uid, mid, score, passed, taken, test_type, valid in db.query(
            QuizAttempt.user_id, QuizAttempt.module_id, QuizAttempt.score_percent, QuizAttempt.passed,
            QuizAttempt.taken_at, QuizAttempt.test_type, QuizAttempt.valid,
        ).filter(QuizAttempt.user_id.in_(ids), *_in_range(QuizAttempt.taken_at, f)):
            if test_type == TestType.MODULE_QUIZ:
                module_quiz[uid]["attempts"] += 1
                if valid and passed:
                    module_quiz[uid]["passed"].add(mid)
            d = quiz[uid]
            d["attempts"] += 1
            prev = d["best"].get(mid)
            if prev is None or score > prev[0]:
                d["best"][mid] = (score, passed)
            elif passed and not prev[1]:
                d["best"][mid] = (prev[0], True)
            if d["last"] is None or taken > d["last"]:
                d["last"] = taken

    general = defaultdict(dict)  # uid -> {PRE: first valid attempt, POST: ...}
    if ids:
        for g in db.query(GeneralTestAttempt).filter(GeneralTestAttempt.user_id.in_(ids), GeneralTestAttempt.valid.is_(True)
                                                     ).order_by(GeneralTestAttempt.taken_at):
            general[g.user_id].setdefault(g.test_type, g)

    qa = defaultdict(lambda: [0, 0, None])
    if ids:
        for uid, n, unanswered, last in db.query(
            AiQuestionLog.user_id, func.count(), func.count().filter(AiQuestionLog.matched.is_(False)), func.max(AiQuestionLog.asked_at)
        ).join(User, User.id == AiQuestionLog.user_id).filter(
            AiQuestionLog.user_id.in_(ids), *_in_range(AiQuestionLog.asked_at, f),
            or_(User.training_restarted_at.is_(None), AiQuestionLog.asked_at >= User.training_restarted_at),
        ).group_by(AiQuestionLog.user_id):
            qa[uid] = [n, unanswered, last]

    rows = []
    for u in users:
        total_modules = len(visible_to[u.id])
        best = quiz[u.id]["best"]
        scores = [s for s, _ in best.values()]
        last_candidates = [x for x in (last_progress.get(u.id), last_event.get(u.id), quiz[u.id]["last"], qa[u.id][2]) if x]
        c = cat[u.id]
        rows.append(
            {
                "user_id": str(u.id),
                "username": u.username,
                "full_name": f"{u.first_name} {u.last_name}",
                "role": u.role.value,
                "learner_role": u.learner_role.value if u.learner_role else None,
                "status": u.status.value,
                "deactivated_at": u.deactivated_at.isoformat() if u.deactivated_at else None,
                "team_code": u.team_code,
                "country": u.country_name,
                "state": u.state_name,
                "lga": u.lga_name,
                "ward": u.ward_name,
                "facility": u.facility_name,
                "session": u.session_name,
                "session_start": u.session_start_date.isoformat() if u.session_start_date else None,
                "session_end": u.session_end_date.isoformat() if u.session_end_date else None,
                "session_status": u.session_status,
                "training_attempt": u.training_attempt,
                "restarted_at": u.training_restarted_at.isoformat() if u.training_restarted_at else None,
                "modules_total": total_modules,
                "modules_started": started[u.id],
                "modules_completed": completed[u.id],
                "completed_all_at": (
                    max(completion_times[u.id]).isoformat()
                    if total_modules and completed[u.id] >= total_modules and completion_times[u.id]
                    else None
                ),
                "completion_rate": round(100 * completed[u.id] / total_modules, 1) if total_modules else 0.0,
                "quiz_attempts": quiz[u.id]["attempts"],
                "quizzes_passed": sum(1 for _, p in best.values() if p),
                "avg_best_quiz_score": round(sum(scores) / len(scores), 1) if scores else None,
                # since 2026-11: inline module quizzes, active time and the General pre/post test
                "learner_group": "CDD" if u.learner_role == LearnerRole.CDD else "HFW & others",
                "module_quiz_attempts": module_quiz[u.id]["attempts"],
                "module_quizzes_passed": len(module_quiz[u.id]["passed"] & visible_to[u.id]),
                "seconds_spent_total": seconds[u.id],
                **_general_fields(general[u.id]),
                "training_events": c["training"],
                "module_opens": c["module_opens"],
                "video_events": c["video"],
                "video_opens": c["video_opens"],
                "questions_asked": qa[u.id][0],
                "questions_unanswered": qa[u.id][1],
                "technical_events": c["technical"],
                "session_events": c["session"],
                "last_activity": max(last_candidates).isoformat() if last_candidates else None,
                "last_login": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                # since 2026-11-13: devices (app 0.1.16+; older apps have none)
                **devices[u.id],
            }
        )
    return rows


def _general_fields(mine: dict) -> dict:
    pre, post = mine.get(TestType.PRE), mine.get(TestType.POST)
    return {
        "general_pre_points": pre.correct_count if pre else None,
        "general_pre_total": pre.total_count if pre else None,
        "general_pre_percent": pre.score_percent if pre else None,
        "general_post_points": post.correct_count if post else None,
        "general_post_total": post.total_count if post else None,
        "general_post_percent": post.score_percent if post else None,
        "general_change_points": post.correct_count - pre.correct_count if pre and post else None,
        # since 2026-11-13: the pass mark stored with each attempt (none before) and the verdict
        "general_change_percent": post.score_percent - pre.score_percent if pre and post else None,
        "general_pre_pass_mark": pre.pass_mark if pre else None,
        "general_pre_passed": _verdict(pre),
        "general_post_pass_mark": post.pass_mark if post else None,
        "general_post_passed": _verdict(post),
    }


def _verdict(a) -> str | None:
    """PASSED / NOT_PASSED against the stored mark; None without an attempt or a stored mark."""
    if a is None or a.pass_mark is None:
        return None
    return "PASSED" if general_passes(a.correct_count, a.total_count, a.pass_mark) else "NOT_PASSED"


SUM_FIELDS = [
    "modules_completed", "quiz_attempts", "quizzes_passed", "training_events", "video_events",
    "questions_asked", "questions_unanswered", "technical_events", "session_events",
]
UNASSIGNED = "(not assigned)"


def boundary_rollup(rows: list[dict], level: str) -> list[dict]:
    """Group the user rows by the chosen area level (state, lga, ...). Each group
    carries its parent areas so a table or Power BI can slice the hierarchy."""
    if level not in LEVELS:
        raise ValueError("level")
    parents = LEVELS[: LEVELS.index(level)]
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = tuple(r[p] or UNASSIGNED for p in parents) + (r[level] or UNASSIGNED,)
        groups[key].append(r)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)).isoformat()
    out = []
    for key, members in sorted(groups.items()):
        n = len(members)
        scores = [m["avg_best_quiz_score"] for m in members if m["avg_best_quiz_score"] is not None]
        item = {p: key[i] for i, p in enumerate(parents)}
        item.update(
            {
                "level": level,
                "area": key[-1],
                "users": n,
                "active_users_30d": sum(1 for m in members if m["last_activity"] and m["last_activity"] >= cutoff),
                "users_completed_all": sum(1 for m in members if m["modules_total"] and m["modules_completed"] >= m["modules_total"]),
                "avg_completion_rate": round(sum(m["completion_rate"] for m in members) / n, 1),
                "avg_best_quiz_score": round(sum(scores) / len(scores), 1) if scores else None,
            }
        )
        for fld in SUM_FIELDS:
            item[fld] = sum(m[fld] for m in members)
        out.append(item)
    return out


def session_rollup(db: Session, rows: list[dict], include_empty: bool = True) -> list[dict]:
    """One row per training session (each monitored on its own): dates, status,
    enrolment, completion, quizzes, activity categories, and how many finished
    every module by the session's end date. Users with no session are grouped
    under (no session)."""
    from app.models import TrainingSession

    meta = {s_.name: s_ for s_ in db.query(TrainingSession).all()}
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["session"] or "(no session)"].append(r)
    if include_empty:  # on an unfiltered report, sessions with nobody enrolled yet still appear
        for name in meta:
            groups.setdefault(name, [])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)).isoformat()
    out = []
    for name in sorted(groups, key=lambda n: (meta[n].start_date if n in meta else date.max, n)):
        members = groups[name]
        n = len(members)
        info = meta.get(name)
        end_exclusive = datetime.combine(info.end_date + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat() if info else None
        scores = [m["avg_best_quiz_score"] for m in members if m["avg_best_quiz_score"] is not None]
        item = {
            "session": name,
            "start_date": info.start_date.isoformat() if info else None,
            "end_date": info.end_date.isoformat() if info else None,
            "status": info.status if info else None,
            "days_remaining": max((info.end_date - date.today()).days, 0) if info and info.status != "ENDED" else 0 if info else None,
            "users": n,
            "not_started": sum(1 for m in members if m["modules_started"] == 0),
            "active_users_30d": sum(1 for m in members if m["last_activity"] and m["last_activity"] >= cutoff),
            "users_completed_all": sum(1 for m in members if m["modules_total"] and m["modules_completed"] >= m["modules_total"]),
            "completed_all_by_end_date": sum(
                1 for m in members if m["completed_all_at"] and end_exclusive and m["completed_all_at"] < end_exclusive
            ),
            "avg_completion_rate": round(sum(m["completion_rate"] for m in members) / n, 1) if n else 0.0,
            "avg_best_quiz_score": round(sum(scores) / len(scores), 1) if scores else None,
        }
        for fld in SUM_FIELDS:
            item[fld] = sum(m[fld] for m in members)
        out.append(item)
    return out


def module_rows(db: Session, f: Filters, level: str | None = None) -> list[dict]:
    """Completion and quiz results per module, overall or (with `level`) per
    module and area, for the same user filters."""
    users = db.query(User)
    for lv in LEVELS:
        v = getattr(f, f"{lv}_id")
        if v:
            users = users.filter(getattr(User, f"{lv}_id") == v)
    if f.session_id:
        users = users.filter(User.training_session_id == f.session_id)
    if f.role:
        users = users.filter(User.role == f.role)
    if f.learner_role:
        users = users.filter(User.learner_role == f.learner_role)
    if f.team_code:
        users = users.filter(User.team_code == f.team_code)
    users = users.all()
    ids = [u.id for u in users]
    area_of = {}
    parents = LEVELS[: LEVELS.index(level)] if level in LEVELS else []
    for u in users:
        names = {"country": u.country_name, "state": u.state_name, "lga": u.lga_name, "ward": u.ward_name,
                 "facility": u.facility_name, "session": u.session_name}
        area_of[u.id] = tuple(names[p] or UNASSIGNED for p in parents) + ((names[level] or UNASSIGNED,) if level else ())
    mods = db.query(Module).filter(Module.status == ModuleStatus.PUBLISHED).order_by(Module.sort_order).all()
    prog = defaultdict(dict)
    quiz_best = defaultdict(dict)
    if ids:
        for uid, mid, done, cat, upd in db.query(
            UserModuleProgress.user_id, UserModuleProgress.module_id, UserModuleProgress.completed,
            UserModuleProgress.completed_at, UserModuleProgress.updated_at,
        ).filter(UserModuleProgress.user_id.in_(ids)):
            ts = cat or upd
            if (f.start and (not ts or ts < f.start)) or (f.end and (not ts or ts >= f.end)):
                continue
            prog[mid][uid] = done
        for uid, mid, score, passed in db.query(
            QuizAttempt.user_id, QuizAttempt.module_id, QuizAttempt.score_percent, QuizAttempt.passed
        ).filter(QuizAttempt.user_id.in_(ids), *_in_range(QuizAttempt.taken_at, f)):
            prev = quiz_best[mid].get(uid)
            if prev is None or score > prev[0]:
                quiz_best[mid][uid] = (score, passed)
    groups = defaultdict(list)
    by_id = {u.id: u for u in users}
    for u in users:
        groups[area_of[u.id] if level else ()].append(u.id)
    out = []
    for m in mods:
        for key, everyone in sorted(groups.items()):
            members = [uid for uid in everyone if module_visible_to(m, by_id[uid])]  # only people the module is for
            started = [uid for uid in members if uid in prog[m.id]]
            done = [uid for uid in members if prog[m.id].get(uid)]
            q = [quiz_best[m.id][uid] for uid in members if uid in quiz_best[m.id]]
            row = {"module_code": m.module_code, "module_title": m.title}
            row.update({p: key[i] for i, p in enumerate(parents)})
            if level:
                row.update({"level": level, "area": key[-1]})
            row.update(
                {
                    "users": len(members),
                    "started": len(started),
                    "completed": len(done),
                    "completion_rate": round(100 * len(done) / len(members), 1) if members else 0.0,
                    "quiz_takers": len(q),
                    "quiz_passed": sum(1 for _, p in q if p),
                    "avg_best_quiz_score": round(sum(s for s, _ in q) / len(q), 1) if q else None,
                }
            )
            out.append(row)
    return out


def _csv_safe(value):
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def to_csv(rows: list[dict]) -> str:
    """UTF-8 CSV with a BOM so Excel opens accents correctly; text cells that
    start like a formula are neutralised."""
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (v if isinstance(v, (int, float)) and not isinstance(v, bool) else _csv_safe(v)) for k, v in r.items()})
    return "﻿" + buf.getvalue()
