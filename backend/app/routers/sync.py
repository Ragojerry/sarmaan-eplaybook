"""
Phase 12: synchronisation endpoints (master prompt §54-56).

Uploads (phone -> server) are batched, IDEMPOTENT and report a result per item:
  GET  /sync/progress        this account's saved progress (restore on a new phone)
  POST /sync/progress        merge module progress (latest wins; completed never un-completes)
  POST /sync/ai-questions    keyed by (user, client_id)
  POST /sync/analytics       keyed by (device, client_id); only the §50 event types
Downloads (server -> phone):
  GET  /sync/release/current           newest PUBLISHED release + whether the phone needs it
  GET  /sync/release/{code}/package    the frozen package, checksum-verifiable

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
from app.models.enums import AnalyticsEventType, ContentReviewStatus, ModuleStatus, ReleaseStatus
from app.releases.packager import package_path
from app.quiz.grading import passed as quiz_passed, score_percent
from app.schemas.sync import (
    AiQuestionBatch,
    AnalyticsBatch,
    BatchResult,
    CurrentReleaseResponse,
    ItemResult,
    ProgressBatch,
    ProgressOut,
    QuizAttemptBatch,
    ReleaseInfo,
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


def _quiz_gate_open(db: Session, user_id, module_id) -> bool:
    """A module with a quiz can only be completed by someone who passed it.
    Modules without active questions can still be completed directly."""
    has_quiz = db.query(QuizQuestion.id).filter_by(module_id=module_id, is_active=True).first() is not None
    if not has_quiz:
        return True
    return db.query(QuizAttempt.id).filter_by(user_id=user_id, module_id=module_id, passed=True).first() is not None


@router.post("/quiz-attempts", response_model=BatchResult)
def sync_quiz_attempts(payload: QuizAttemptBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Idempotent upload of quiz attempts graded on the phone. The pass decision
    is recomputed here from the reported counts (exact 90% rule); the client's
    own `passed` flag is never trusted."""
    results: list[ItemResult] = []
    for item in payload.items:
        try:
            with db.begin_nested():
                if item.correct_count > item.total_count:
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="correct exceeds total"))
                    continue
                if db.get(Module, item.module_id) is None:
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="unknown module"))
                    continue
                if is_stale(user, item.taken_at):
                    results.append(ItemResult(key=item.client_id, status="rejected", detail="before training restart"))
                    continue
                if db.query(QuizAttempt.id).filter_by(user_id=user.id, client_id=item.client_id).first():
                    results.append(ItemResult(key=item.client_id, status="duplicate"))
                    continue
                db.add(
                    QuizAttempt(
                        user_id=user.id, module_id=item.module_id, client_id=item.client_id,
                        correct_count=item.correct_count, total_count=item.total_count,
                        score_percent=score_percent(item.correct_count, item.total_count),
                        passed=quiz_passed(item.correct_count, item.total_count),
                        results=[{"question_id": str(r.question_id), "correct": r.correct} for r in item.results],
                        device_id=payload.device_id, taken_at=item.taken_at,
                    )
                )
                db.flush()
            results.append(ItemResult(key=item.client_id, status="ok"))
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
    rows = (
        db.query(ModuleTranslation)
        .join(Module, Module.id == ModuleTranslation.module_id)
        .filter(
            ModuleTranslation.language_id == lang.id,
            ModuleTranslation.status == ContentReviewStatus.PUBLISHED,
            Module.status == ModuleStatus.PUBLISHED,
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
    published module. This is how Home sync gets quizzes; the release package
    carries the same data for the release installer."""
    rows = (
        db.query(QuizQuestion)
        .join(Module, Module.id == QuizQuestion.module_id)
        .filter(QuizQuestion.is_active.is_(True), Module.status == ModuleStatus.PUBLISHED)
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


@router.post("/progress", response_model=BatchResult)
def sync_progress(payload: ProgressBatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    results: list[ItemResult] = []
    for item in payload.items:
        key = str(item.module_id)
        try:
            with db.begin_nested():
                if db.get(Module, item.module_id) is None:
                    results.append(ItemResult(key=key, status="rejected", detail="unknown module"))
                    continue
                if is_stale(user, item.last_opened_at):
                    results.append(ItemResult(key=key, status="rejected", detail="before training restart"))
                    continue
                if item.completed and not _quiz_gate_open(db, user.id, item.module_id):
                    results.append(ItemResult(key=key, status="rejected", detail="quiz not passed"))
                    continue
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
                if incoming_is_newer:
                    row.progress_percent = item.progress_percent
                    row.last_section = item.last_section
                    row.last_opened_at = item.last_opened_at or row.last_opened_at
                    row.device_id = payload.device_id
                # A completed module never un-completes, whichever write is newer.
                if item.completed and not row.completed:
                    row.completed = True
                    row.progress_percent = 100
                    row.completed_at = item.completed_at or datetime.now(timezone.utc)
                elif row.completed:
                    row.progress_percent = 100
                db.flush()
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
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    release = _latest_published(db)
    if release is None:
        return CurrentReleaseResponse(release=None, installed=installed, update_available=False)
    info = ReleaseInfo(
        release_code=release.release_code,
        version=release.version,
        mandatory=release.mandatory,
        description=release.description,
        package_size=release.package_size,
        checksum=release.checksum,
        published_at=release.published_at,
    )
    return CurrentReleaseResponse(
        release=info, installed=installed, update_available=installed != release.release_code
    )


@router.get("/release/{release_code}/package")
def download_package(release_code: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    release = db.query(ContentRelease).filter_by(release_code=release_code).one_or_none()
    if release is None or release.status != ReleaseStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not available")
    path = package_path(release.release_code)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release package file missing")
    return FileResponse(
        path, media_type="application/json", headers={"X-Package-SHA256": release.checksum or ""}
    )
