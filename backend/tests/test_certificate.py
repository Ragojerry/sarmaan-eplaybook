"""
Training certificates: only a valid General post-test at 90% or more has one, and
staff can check a number in the portal. The fixed vector below is also checked by
mobile/test/certificate_test.dart, so phone and server always agree on the number.

    cd backend && python -m pytest tests/test_certificate.py -v
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.learning.certificate import certificate_number
from app.main import app
from app.models import GeneralTestAttempt, Language
from app.models.enums import RoleName, TestType
from tests.test_content import _auth_headers, _cleanup_user, _login, _make_user

client = TestClient(app)


def test_shared_vector():
    taken = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)
    assert certificate_number("11111111-2222-3333-4444-555555555555", "general-post-1731405600000-0", taken) == "SII-2026-06E1A47048"


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


def test_only_a_valid_passing_post_test_has_a_certificate(db):
    english = db.query(Language).filter_by(code="en").one()
    learner = _make_user(db, RoleName.CDD, english.id)
    staff = _make_user(db, RoleName.PROGRAM_REVIEWER, english.id)
    taken = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)
    rows = {
        "pass": GeneralTestAttempt(user_id=learner.id, client_id="cert-pass", test_type=TestType.POST, correct_count=23,
                                   total_count=25, score_percent=92, taken_at=taken),
        "low": GeneralTestAttempt(user_id=learner.id, client_id="cert-low", test_type=TestType.POST, correct_count=22,
                                  total_count=25, score_percent=88, taken_at=taken),
        "pre": GeneralTestAttempt(user_id=learner.id, client_id="cert-pre", test_type=TestType.PRE, correct_count=25,
                                  total_count=25, score_percent=100, taken_at=taken),
        "invalid": GeneralTestAttempt(user_id=learner.id, client_id="cert-invalid", test_type=TestType.POST, correct_count=25,
                                      total_count=25, score_percent=100, taken_at=taken, valid=False, invalid_reason="test"),
    }
    db.add_all(rows.values())
    db.commit()
    try:
        h = _auth_headers(_login(staff.username))
        number = certificate_number(learner.id, "cert-pass", taken)
        r = client.get(f"/general-test/certificates/{number.lower()}", headers=h)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["valid"] and body["name"] == f"Test {RoleName.CDD.value}" and body["percent"] == 92
        for key in ("low", "pre", "invalid"):
            other = certificate_number(learner.id, rows[key].client_id, taken)
            assert client.get(f"/general-test/certificates/{other}", headers=h).status_code == 404, key
        assert client.get("/general-test/certificates/not-a-number", headers=h).status_code == 404
        learner_h = _auth_headers(_login(learner.username))
        assert client.get(f"/general-test/certificates/{number}", headers=learner_h).status_code == 403
    finally:
        db.rollback()
        db.query(GeneralTestAttempt).filter(GeneralTestAttempt.user_id == learner.id).delete()
        db.commit()
        _cleanup_user(db, learner)
        _cleanup_user(db, staff)
        db.commit()
