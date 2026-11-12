"""
Training completion certificates.

A learner earns the certificate with a valid General post-test at the pass mark
(90%, the same as the module quizzes: app.quiz.grading.passed). The phone makes
the PDF offline, so the certificate number is derived, not stored: both sides
compute it from the account id and the post-test attempt's client id

    SII-<year taken, UTC>-<first 10 hex digits of sha256("<user_id>:<client_id>"), upper case>

and the admin portal checks a number by recomputing it for every passing
post-test (mobile/lib/learning/certificate.dart is the phone's copy of this rule).
"""
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import GeneralTestAttempt, User
from app.models.enums import TestType
from app.quiz.grading import passed


def certificate_number(user_id: uuid.UUID | str, client_id: str, taken_at: datetime) -> str:
    year = (taken_at if taken_at.tzinfo else taken_at.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).year
    digest = hashlib.sha256(f"{user_id}:{client_id}".encode("utf-8")).hexdigest()[:10].upper()
    return f"SII-{year}-{digest}"


def find_certificate(db: Session, number: str) -> dict | None:
    number = number.strip().upper()
    parts = number.split("-")
    if len(parts) != 3 or parts[0] != "SII" or not parts[1].isdigit():
        return None
    attempts = (db.query(GeneralTestAttempt)
                .filter(GeneralTestAttempt.test_type == TestType.POST, GeneralTestAttempt.valid.is_(True))
                .order_by(GeneralTestAttempt.taken_at).all())
    for a in attempts:
        if not passed(a.correct_count, a.total_count):
            continue
        if certificate_number(a.user_id, a.client_id, a.taken_at) != number:
            continue
        user = db.get(User, a.user_id)
        return {
            "number": number,
            "valid": True,
            "name": f"{user.first_name} {user.last_name}".strip() if user else None,
            "username": user.username if user else None,
            "completed_at": a.taken_at.isoformat(),
            "correct": a.correct_count,
            "total": a.total_count,
            "percent": a.score_percent,
        }
    return None
