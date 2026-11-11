"""
Phase 12: synchronisation endpoints (master prompt §54-56).

Uploads (phone -> server) are batched, IDEMPOTENT and report a result per item:
  GET  /sync/progress        this account's saved progress (restore on a new phone)
  POST /sync/progress        merge module progress and active time (latest wins; time only grows;
                             completed never un-completes; completion needs the quiz and the time)
  POST /sync/quiz-attempts   inline module-quiz attempts (old per-module pre/post tests: kept, never count)
  GET  /sync/learning        per-module state, quiz attempts, the General test state and the rules
  GET  /sync/general-test    the General test questions (with answers, graded on the phone too)
  POST /sync/general-test-attempts  General pre-/post-test results, graded again here
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
from app.config import get_settings
from app.database import get_db
from app.models import (
    AiQuestionLog,
    AnalyticsEvent,
    ContentRelease,
    GeneralTestAttempt,
    GeneralTestQuestion,
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
from app.learning.state import READING_PERCENT, ModuleState, learning_overview, module_state
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
    GeneralAttemptBatch,
    GeneralTestOut,
    GeneralTestState,
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
from app.learning.settings import training_settings
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


REPLACED = "per-module pre/post tests were replaced (2026-11)"


def _quiz_problem(state: ModuleState | None) -> str | None:
    """Why a module-quiz attempt cannot count (None = it counts). The phone enforces
    the same rules offline; this is the server's own check."""
    if state is None:
        return "module is not published"
    if not state.has_quiz:
        return "this module has no quiz"
    if not state.unlocked:
        return state.lock_reason
    if state.completed:
        return "module already completed"  # review only: the result and status stay as they are
    return None


@router.post("/quiz-attempts", response_model=BatchResult)
def sync_quiz_attempts(payload: QuizAttemptBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Idempotent upload of inline module-quiz attempts graded on the phone. The
    pass decision is recomputed here from the reported counts (exact 90% rule);
    the client's own `passed` flag is never trusted. Every attempt is kept as
    history; one that cannot count is stored with valid=false and the reason.
    Completion itself arrives with /sync/progress, which checks the quiz and the time.
    Attempts of the old per-module pre/post tests (older apps) are kept, never counted."""
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
                if item.test_type != TestType.MODULE_QUIZ:
                    test_type, problem = item.test_type or TestType.POST, REPLACED
                else:
                    test_type, problem = TestType.MODULE_QUIZ, _quiz_problem(module_state(db, user, module.id))
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
            results.append(ItemResult(key=item.client_id, status="ok", detail=problem))
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


def _general_state(general) -> GeneralTestState:
    return GeneralTestState(active=general.active, questions=general.questions, pre_test=_score(general.pre),
                            post_test=_score(general.post), post_unlocked=general.post_unlocked,
                            modules_total=general.modules_total, modules_completed=general.modules_completed)


@router.get("/learning", response_model=LearningState)
def get_learning_state(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The account's own state per visible module, its module-quiz attempts (so a new
    phone restores them), the General test state and the training rules. Never
    anyone else's. Fields of the retired per-module tests stay, empty, for older apps."""
    states, general = learning_overview(db, user)
    visible = {s.module.id for s in states}
    modules = [
        ModuleLearning(
            module_id=st.module.id, status=st.status, unlocked=st.unlocked, completed=st.completed,
            has_tests=False, has_quiz=st.has_quiz, quiz_statements=st.quiz_statements, quiz_passed=st.quiz_passed,
            quiz_attempts=len(st.quiz_attempts), seconds_spent=st.seconds_spent, lock_reason=st.lock_reason,
        )
        for st in states
    ]
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.module_id.in_(visible),
                QuizAttempt.test_type == TestType.MODULE_QUIZ)
        .order_by(QuizAttempt.taken_at)
        .all()
        if visible else []
    )
    return LearningState(
        learner_role=user.learner_role.value if user.learner_role else None,
        auto_approve_percent=auto_approve_percent(),
        min_app_version=get_settings().min_app_version,
        module_min_seconds=training_settings(db).module_min_seconds,
        general_test=_general_state(general),
        modules=modules,
        attempts=[AttemptOut.model_validate(a) for a in attempts],
    )


@router.get("/general-test", response_model=GeneralTestOut)
def get_general_test(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The General test questions with their answers (the phone grades offline; the
    server grades again on upload). Nothing is served until the test is switched on."""
    active = training_settings(db).general_test_active
    rows = (db.query(GeneralTestQuestion).filter_by(is_active=True).order_by(GeneralTestQuestion.number).all()
            if active else [])
    return GeneralTestOut(active=active, questions=[
        {"id": q.id, "number": q.number, "prompt": q.prompt, "options": q.options, "correct_index": q.correct_index}
        for q in rows
    ])


def _general_problem(general, test_type: TestType, taken_at: datetime) -> str | None:
    """Why a General test upload cannot count (None = it counts). Each test counts once."""
    if not general.active:
        return "the General test is not switched on"
    if test_type == TestType.PRE:
        return "pre-test already taken" if general.pre is not None else None
    if test_type != TestType.POST:
        return "unknown test type"
    if general.pre is None:
        return "no pre-test yet"
    if general.post is not None:
        return "post-test already taken"
    if _aware(general.pre.taken_at) > _aware(taken_at):
        return "taken before the pre-test"
    if not general.all_modules_completed:
        return "complete all your modules first"
    return None


@router.post("/general-test-attempts", response_model=BatchResult)
def sync_general_test_attempts(payload: GeneralAttemptBatch, db: Session = Depends(get_db),
                               user: User = Depends(get_current_user)):
    """Idempotent upload of General pre-/post-tests. Graded here from the chosen options
    against the answer key (unanswered = wrong), out of every active question. Each test
    counts once: the first valid one is the learner's result; later ones are kept, invalid."""
    key = sorted(db.query(GeneralTestQuestion).filter_by(is_active=True), key=lambda q: q.number)
    results: list[ItemResult] = []
    for item in sorted(payload.items, key=lambda i: _aware(i.taken_at)):  # a pre-test before its post-test
        try:
            with db.begin_nested():
                if is_stale(user, item.taken_at):
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="before training restart"))
                    continue
                if db.query(GeneralTestAttempt.id).filter_by(user_id=user.id, client_id=item.client_id).first():
                    results.append(ItemResult(key=item.client_id, status="duplicate"))
                    continue
                chosen = {a.question_id: a.choice for a in item.answers}
                graded = [{"question_id": str(q.id), "choice": chosen.get(q.id),
                           "correct": q.correct_index is not None and chosen.get(q.id) == q.correct_index}
                          for q in key]
                correct = sum(1 for g in graded if g["correct"])
                problem = _general_problem(learning_overview(db, user)[1], item.test_type, item.taken_at)
                db.add(GeneralTestAttempt(
                    user_id=user.id, client_id=item.client_id, test_type=item.test_type,
                    correct_count=correct, total_count=len(graded), score_percent=score_percent(correct, len(graded)),
                    answers=graded, valid=problem is None, invalid_reason=problem,
                    device_id=payload.device_id, taken_at=item.taken_at,
                ))
                db.flush()
            results.append(ItemResult(key=item.client_id, status="ok",
                                      detail=problem or f"score {correct}/{len(graded)}"))
        except IntegrityError:
            results.append(ItemResult(key=item.client_id, status="duplicate"))
        except Exception as exc:  # noqa: BLE001
            results.append(ItemResult(key=item.client_id, status="error", detail=type(exc).__name__))
    db.commit()
    return BatchResult(results=results)


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
    """Per-module pre/post test questions, for apps older than 0.1.12. Those tests were
    retired in 2026-11 (archived questions are never served), so this is normally
    empty; the inline module quizzes travel as TRUE_FALSE content sections instead."""
    visible = visible_module_ids(db, user)
    rows = (
        db.query(QuizQuestion)
        .join(Module, Module.id == QuizQuestion.module_id)
        .filter(QuizQuestion.is_active.is_(True), QuizQuestion.archived_at.is_(None),
                Module.status == ModuleStatus.PUBLISHED, Module.id.in_(visible))
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
    """Why completing a module from the phone is refused (None = allowed): it must be
    unlocked, its inline quiz passed (if it has one) and the minimum time spent."""
    if state is None:
        return "module is not published"
    return state.completion_problem()


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
                row = (
                    db.query(UserModuleProgress)
                    .filter_by(user_id=user.id, module_id=item.module_id)
                    .with_for_update()
                    .one_or_none()
                )
                if row is None:
                    row = UserModuleProgress(user_id=user.id, module_id=item.module_id, progress_percent=0,
                                             seconds_spent=0)
                    db.add(row)
                    incoming_is_newer = True
                else:
                    incoming_is_newer = (
                        row.last_opened_at is None
                        or item.last_opened_at is None
                        or item.last_opened_at >= row.last_opened_at
                    )
                # Active time only grows (the larger value wins), so a retried or older upload is harmless.
                if item.seconds_spent is not None and item.seconds_spent > (row.seconds_spent or 0):
                    row.seconds_spent = item.seconds_spent
                db.flush()
                state = module_state(db, user, module.id)
                refused = _completion_problem(state) if item.completed else None
                locked = state is not None and not state.unlocked
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
