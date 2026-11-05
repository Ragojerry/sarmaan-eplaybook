"""
Phase 12: synchronisation endpoints (master prompt §54-56).

Uploads (phone -> server) are batched, IDEMPOTENT and report a result per item:
  GET  /sync/progress        this account's saved progress (restore on a new phone)
  POST /sync/progress        merge module progress (latest wins; completed never un-completes)
  POST /sync/quiz-attempts   pre-/post-test attempts; a qualifying post-test completes the module
  GET  /sync/learning        per-module test state, attempt history and the auto-approval threshold
  POST /sync/ai-questions    keyed by (user, client_id)
  POST /sync/analytics       keyed by (device, client_id); only the §50 event types
Downloads (server -> phone), filtered to the modules the account may see
(app/learning/access.py):
  GET  /sync/release/current           newest PUBLISHED release + whether the phone needs it
  GET  /sync/release/{code}/package    the account's copy of the frozen package, checksum-verifiable

A retried upload (lost response, killed app, flaky network) therefore never
double-counts: the server answers "duplicate" and the phone marks it synced.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import (
    AiQuestionLog,
    AnalyticsEvent,
    ContentRelease,
    ContentSection,
    Language,
    Module,
    ModuleTranslation,
    QuizAttempt,
    QuizQuestion,
    SectionTranslation,
    User,
    UserModuleProgress,
)
from app.learning.access import module_visible_to, visible_module_ids
from app.learning.rules import auto_approve_percent
from app.learning.state import READING_PERCENT, ModuleState, complete, learning_states, module_state
from app.models.enums import AnalyticsEventType, ContentReviewStatus, ModuleStatus, ReleaseStatus, TestType
from app.releases.packager import package_path
from app.releases.variants import variant_for
from app.quiz.grading import passed as quiz_passed, score_percent
from app.schemas.sync import (
    AiQuestionBatch,
    AnalyticsBatch,
    BatchResult,
    AttemptOut,
    CurrentReleaseResponse,
    ItemResult,
    LearningState,
    ModuleLearning,
    ProgressBatch,
    ProgressOut,
    QuizAttemptBatch,
    ReleaseInfo,
    TestScore,
    TrainingRestartBatch,
    TrainingState,
)
from app.training.restart import is_stale, restart_training

router = APIRouter()


def _latest_published(db: Session) -> ContentRelease | None:
    return (
        db.query(ContentRelease)
        .filter(ContentRelease.status == ReleaseStatus.PUBLISHED, ContentRelease.checksum.isnot(None))
        .order_by(ContentRelease.published_at.desc())
        .first()
    )


# ---------- uploads ----------


NOT_YOURS = "not available for your learner role"


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _sequence_problem(state: ModuleState | None, test_type: TestType, taken_at: datetime) -> str | None:
    """Why this attempt cannot count (None = it counts). The phone enforces the
    same order offline; this is the server's own check."""
    if state is None:
        return "module is not published"
    if not state.has_tests:
        return "this module has no test"
    if not state.unlocked:
        return "module is locked: complete the previous module first"
    taken_at = _aware(taken_at)
    reading = state.progress.reading_completed_at if state.progress else None
    legacy = bool(state.progress and state.progress.legacy_reading)
    if test_type == TestType.PRE:
        if state.completed:
            return "module already completed"
        if state.pre is not None:
            return "pre-test already taken"
        if state.posts:
            return "post-test already taken"
        if reading is not None and not legacy and _aware(reading) < taken_at:
            return "pre-test must be taken before reading"
        return None
    if state.completed:
        return "module already completed"  # review only: the result and status stay as they are
    if state.pre is None:
        return "no pre-test yet"
    if _aware(state.pre.taken_at) > taken_at:
        return "taken before the pre-test"
    if reading is None:
        return "reading not finished"
    if not legacy and _aware(reading) > taken_at:
        return "taken before reading was finished"
    return None


@router.post("/quiz-attempts", response_model=BatchResult)
def sync_quiz_attempts(payload: QuizAttemptBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Idempotent upload of pre-/post-test attempts graded on the phone. The
    pass decision is recomputed here from the reported counts (exact 90%
    rule); the client's own `passed` flag is never trusted. Every attempt is
    kept as history; one that breaks the sequence is stored with valid=false
    and the reason. A post-test that meets the rule (app/learning/rules.py)
    completes the module here, which unlocks the next one."""
    results: list[ItemResult] = []
    for item in sorted(payload.items, key=lambda i: _aware(i.taken_at)):  # a pre-test before its post-test
        try:
            with db.begin_nested():
                if item.correct_count > item.total_count:
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="correct exceeds total"))
                    continue
                module = db.get(Module, item.module_id)
                if module is None:
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="unknown module"))
                    continue
                if not module_visible_to(module, user):
                    results.append(ItemResult(key=item.client_id, status="rejected", detail=NOT_YOURS))
                    continue
                if is_stale(user, item.taken_at):
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="before training restart"))
                    continue
                if db.query(QuizAttempt.id).filter_by(user_id=user.id, client_id=item.client_id).first():
                    results.append(ItemResult(key=item.client_id, status="duplicate"))
                    continue
                if item.test_type is None:
                    test_type, problem = TestType.POST, "sent by an app without pre/post tests"
                else:
                    test_type = item.test_type
                    problem = _sequence_problem(module_state(db, user, module.id), test_type, item.taken_at)
                db.add(
                    QuizAttempt(
                        user_id=user.id, module_id=item.module_id, client_id=item.client_id,
                        correct_count=item.correct_count, total_count=item.total_count,
                        score_percent=score_percent(item.correct_count, item.total_count),
                        passed=quiz_passed(item.correct_count, item.total_count),
                        results=[{"question_id": str(r.question_id), "correct": r.correct} for r in item.results],
                        device_id=payload.device_id, taken_at=item.taken_at,
                        test_type=test_type, valid=problem is None, invalid_reason=problem,
                    )
                )
                db.flush()
                detail = problem
                if problem is None and test_type == TestType.POST:
                    state = module_state(db, user, module.id)
                    if state and not state.completed and state.completing_post() is not None:
                        complete(db, user, module.id, when=_aware(item.taken_at))
                        detail = "completed"
            results.append(ItemResult(key=item.client_id, status="ok", detail=detail))
        except IntegrityError:
            results.append(ItemResult(key=item.client_id, status="duplicate"))
        except Exception as exc:  # noqa: BLE001
            results.append(ItemResult(key=item.client_id, status="error", detail=type(exc).__name__))
    db.commit()
    return BatchResult(results=results)


def _score(a) -> TestScore | None:
    if a is None:
        return None
    return TestScore(client_id=a.client_id, correct_count=a.correct_count, total_count=a.total_count,
                     score_percent=a.score_percent, taken_at=a.taken_at)


@router.get("/learning", response_model=LearningState)
def get_learning_state(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The account's own test state per visible module and its attempt
    history (so a new phone restores pre-test baselines), plus the
    auto-approval threshold for 100% pre-tests. Never anyone else's."""
    states = learning_states(db, user)
    visible = {s.module.id for s in states}
    modules = []
    for st in states:
        best = max(st.posts, key=lambda a: (a.correct_count / a.total_count, a.taken_at), default=None)
        modules.append(ModuleLearning(
            module_id=st.module.id, status=st.status, unlocked=st.unlocked, completed=st.completed,
            has_tests=st.has_tests, pre_test=_score(st.pre), best_post_test=_score(best),
            post_test_attempts=len(st.posts),
        ))
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.module_id.in_(visible))
        .order_by(QuizAttempt.taken_at)
        .all()
        if visible else []
    )
    return LearningState(
        learner_role=user.learner_role.value if user.learner_role else None,
        auto_approve_percent=auto_approve_percent(),
        modules=modules,
        attempts=[AttemptOut.model_validate(a) for a in attempts],
    )


@router.get("/translations")
def get_translations(language: str = Query(..., min_length=2, max_length=10), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Everything the phone needs to show published modules in one language:
    the module title/body/audio text and the translated sections. Only
    translations that have passed the whole review chain (PUBLISHED) are
    returned, so a draft translation never reaches a learner. Anything not
    returned falls back to English on the phone."""
    lang = db.query(Language).filter_by(code=language).one_or_none()
    if lang is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown language")
    visible = visible_module_ids(db, user)
    rows = (
        db.query(ModuleTranslation)
        .join(Module, Module.id == ModuleTranslation.module_id)
        .filter(
            ModuleTranslation.language_id == lang.id,
            ModuleTranslation.status == ContentReviewStatus.PUBLISHED,
            Module.status == ModuleStatus.PUBLISHED,
            Module.id.in_(visible),
        )
        .all()
    )
    out = []
    for t in rows:
        secs = (
            db.query(SectionTranslation)
            .join(ContentSection, ContentSection.id == SectionTranslation.section_id)
            .filter(ContentSection.module_id == t.module_id, SectionTranslation.language_id == lang.id)
            .all()
        )
        out.append(
            {
                "module_id": str(t.module_id),
                "title": t.title,
                "description": t.description,
                "body": t.body,
                "audio_text": t.audio_text,
                "sections": [{"section_id": str(x.section_id), "title": x.title, "content": x.content} for x in secs],
            }
        )
    return {"language": lang.code, "modules": out}


@router.get("/quiz-questions")
def get_quiz_questions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Active quiz questions (with answers, graded on the phone) for every
    published module this account may see. This is how Home sync gets
    quizzes; the release package carries the same data for the release
    installer. `usage` says whether a question is in the pre-test, the
    post-test or both."""
    visible = visible_module_ids(db, user)
    rows = (
        db.query(QuizQuestion)
        .join(Module, Module.id == QuizQuestion.module_id)
        .filter(QuizQuestion.is_active.is_(True), Module.status == ModuleStatus.PUBLISHED, Module.id.in_(visible))
        .order_by(Module.sort_order, QuizQuestion.sort_order, QuizQuestion.created_at)
        .all()
    )
    return [
        {
            "id": str(q.id),
            "module_id": str(q.module_id),
            "question_type": q.question_type.value,
            "prompt": q.prompt,
            "content": q.content,
            "explanation": q.explanation,
            "sort_order": q.sort_order,
            "usage": q.usage.value,
        }
        for q in rows
    ]


@router.post("/training-restart", response_model=BatchResult)
def sync_training_restart(payload: TrainingRestartBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The learner chose to start the training over. Replaces this account's
    progress and quiz attempts; a retried upload answers "duplicate"."""
    results: list[ItemResult] = []
    for item in sorted(payload.items, key=lambda i: i.restarted_at):
        try:
            changed = restart_training(db, user, item.restarted_at, user, via="mobile")
            results.append(ItemResult(key=item.client_id, status="ok" if changed else "duplicate"))
        except Exception as exc:  # noqa: BLE001
            results.append(ItemResult(key=item.client_id, status="error", detail=type(exc).__name__))
    db.commit()
    return BatchResult(results=results)


@router.get("/training", response_model=TrainingState)
def get_training_state(user: User = Depends(get_current_user)):
    """Lets a phone notice a restart done elsewhere (another device or an admin)."""
    return TrainingState(attempt=user.training_attempt, restarted_at=user.training_restarted_at)


@router.get("/progress", response_model=list[ProgressOut])
def get_my_progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The signed-in account's own progress, so a new phone, a reinstall or a
    second device resumes where the learner stopped. Never returns anyone else's."""
    return db.query(UserModuleProgress).filter_by(user_id=user.id).all()


def _completion_problem(state: ModuleState | None) -> str | None:
    """Why "Mark as complete" from the phone is refused (None = allowed). A
    module with tests is completed by its qualifying post-test instead
    (sync_quiz_attempts), so this only lets an already-qualified one through."""
    if state is None:
        return "module is not published"
    if state.completed:
        return None
    if not state.unlocked:
        return "module is locked: complete the previous module first"
    if state.has_tests and state.completing_post() is None:
        return "post-test not passed yet"
    return None


@router.post("/progress", response_model=BatchResult)
def sync_progress(payload: ProgressBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results: list[ItemResult] = []
    for item in payload.items:
        key = str(item.module_id)
        try:
            with db.begin_nested():
                module = db.get(Module, item.module_id)
                if module is None:
                    results.append(ItemResult(key=key, status="rejected", detail="unknown module"))
                    continue
                if not module_visible_to(module, user):
                    results.append(ItemResult(key=key, status="rejected", detail=NOT_YOURS))
                    continue
                if is_stale(user, item.last_opened_at):
                    results.append(ItemResult(key=key, status="rejected", detail="before training restart"))
                    continue
                state = module_state(db, user, module.id)
                refused = _completion_problem(state) if item.completed else None
                locked = state is not None and not state.unlocked
                row = (
                    db.query(UserModuleProgress)
                    .filter_by(user_id=user.id, module_id=item.module_id)
                    .with_for_update()
                    .one_or_none()
                )
                if row is None:
                    row = UserModuleProgress(user_id=user.id, module_id=item.module_id, progress_percent=0)
                    db.add(row)
                    incoming_is_newer = True
                else:
                    incoming_is_newer = (
                        row.last_opened_at is None
                        or item.last_opened_at is None
                        or item.last_opened_at >= row.last_opened_at
                    )
                percent = min(item.progress_percent, 99) if refused else item.progress_percent
                if incoming_is_newer:
                    row.progress_percent = percent
                    row.last_section = item.last_section
                    row.last_opened_at = item.last_opened_at or row.last_opened_at
                    row.device_id = payload.device_id
                # Reading a locked module does not count (the phone does not open one).
                if not locked and row.reading_completed_at is None and (
                        item.reading_completed_at or percent >= READING_PERCENT):
                    row.reading_completed_at = (
                        item.reading_completed_at or item.last_opened_at or datetime.now(timezone.utc)
                    )
                # A completed module never un-completes, whichever write is newer.
                if item.completed and not refused and not row.completed:
                    row.completed = True
                    row.progress_percent = 100
                    row.completed_at = item.completed_at or datetime.now(timezone.utc)
                elif row.completed:
                    row.progress_percent = 100
                db.flush()
            if refused:
                results.append(ItemResult(key=key, status="ok", detail=f"not completed: {refused}"))
            else:
                results.append(ItemResult(key=key, status="ok" if incoming_is_newer or item.completed else "duplicate"))
        except IntegrityError:
            results.append(ItemResult(key=key, status="error", detail="conflict, retry"))
        except Exception as exc:  # noqa: BLE001 - never let one item sink the batch
            results.append(ItemResult(key=key, status="error", detail=type(exc).__name__))
    db.commit()
    return BatchResult(results=results)


@router.post("/ai-questions", response_model=BatchResult)
def sync_ai_questions(payload: AiQuestionBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results: list[ItemResult] = []
    now = datetime.now(timezone.utc)
    for item in payload.items:
        try:
            with db.begin_nested():
                exists = db.query(AiQuestionLog.id).filter_by(user_id=user.id, client_id=item.client_id).first()
                if exists:
                    results.append(ItemResult(key=item.client_id, status="duplicate"))
                    continue
                db.add(
                    AiQuestionLog(
                        client_id=item.client_id,
                        question=item.question.strip(),
                        answer=item.answer if item.matched else None,
                        matched=item.matched,
                        confidence=item.confidence,
                        source_module_id=item.module_id,
                        source_section_id=item.section_id,
                        language=item.language,
                        user_id=user.id,
                        device_id=payload.device_id,
                        asked_at=item.asked_at,
                        synced_at=now,
                    )
                )
                db.flush()
            results.append(ItemResult(key=item.client_id, status="ok"))
        except IntegrityError as exc:
            # Unique violation = a concurrent retry beat us to it (fine); an FK violation = bad module/section id (permanent).
            msg = str(exc.orig).lower()
            if "uq_ai_question_user_client" in msg:
                results.append(ItemResult(key=item.client_id, status="duplicate"))
            else:
                results.append(ItemResult(key=item.client_id, status="rejected", detail="unknown module or section"))
        except Exception as exc:  # noqa: BLE001
            results.append(ItemResult(key=item.client_id, status="error", detail=type(exc).__name__))
    db.commit()
    return BatchResult(results=results)


_ALLOWED_EVENTS = {e.value for e in AnalyticsEventType}


@router.post("/analytics", response_model=BatchResult)
def sync_analytics(payload: AnalyticsBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results: list[ItemResult] = []
    for item in payload.items:
        if item.event_type not in _ALLOWED_EVENTS:
            results.append(ItemResult(key=item.client_id, status="rejected", detail="unsupported event_type"))
            continue
        try:
            with db.begin_nested():
                exists = db.query(AnalyticsEvent.id).filter_by(device_id=payload.device_id, client_id=item.client_id).first()
                if exists:
                    results.append(ItemResult(key=item.client_id, status="duplicate"))
                    continue
                db.add(
                    AnalyticsEvent(
                        client_id=item.client_id,
                        event_type=AnalyticsEventType(item.event_type),
                        user_id=user.id,
                        device_id=payload.device_id,
                        module_id=item.module_id,
                        video_id=item.video_id,
                        language=item.language,
                        payload=item.payload,
                        occurred_at=item.occurred_at,
                    )
                )
                db.flush()
            results.append(ItemResult(key=item.client_id, status="ok"))
        except IntegrityError as exc:
            msg = str(exc.orig).lower()
            if "uq_analytics_device_client" in msg:
                results.append(ItemResult(key=item.client_id, status="duplicate"))
            else:
                results.append(ItemResult(key=item.client_id, status="rejected", detail="unknown module or video"))
        except Exception as exc:  # noqa: BLE001
            results.append(ItemResult(key=item.client_id, status="error", detail=type(exc).__name__))
    db.commit()
    return BatchResult(results=results)


# ---------- release distribution ----------


@router.get("/release/current", response_model=CurrentReleaseResponse)
def current_release(
    installed: str | None = Query(default=None, description="release_code the phone currently has"),
    installed_variant: str | None = Query(default=None, max_length=64, description="variant the phone currently has"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    release = _latest_published(db)
    if release is None:
        return CurrentReleaseResponse(release=None, installed=installed, update_available=False)
    if package_path(release.release_code).exists():
        _, variant, size, checksum = variant_for(db, release, user)
    else:  # the download will answer 404; report what the release row holds
        variant, size, checksum = None, release.package_size, release.checksum
    info = ReleaseInfo(
        release_code=release.release_code,
        version=release.version,
        mandatory=release.mandatory,
        description=release.description,
        package_size=size,
        checksum=checksum,
        published_at=release.published_at,
        variant=variant,
    )
    # Phones from 0.1.8 send the variant they hold, so a learner-role or
    # audience change triggers a fresh download of the same release.
    stale_variant = installed_variant is not None and installed_variant != variant
    return CurrentReleaseResponse(
        release=info, installed=installed, update_available=installed != release.release_code or stale_variant
    )


@router.get("/release/{release_code}/package")
def download_package(release_code: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    release = db.query(ContentRelease).filter_by(release_code=release_code).one_or_none()
    if release is None or release.status != ReleaseStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not available")
    if not package_path(release.release_code).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release package file missing")
    path, variant, _, checksum = variant_for(db, release, user)
    return FileResponse(
        path, media_type="application/json", headers={"X-Package-SHA256": checksum, "X-Package-Variant": variant}
    )
