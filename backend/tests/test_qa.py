"""
Revised Phases 10/11 tests: the offline extractive Q&A engine, against real
migrated content, plus the HTTP API and its logging. The engine/vector tests
are the Python half of the Python<->Dart parity contract (the Dart half is
mobile/test/qa_engine_test.dart, replaying the same qa_vectors.json).
"""
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai import qa_engine as qa
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AiQuestionLog, AuditLog, ContentChunk, Language, RefreshToken, User
from app.models.content_release import ContentRelease
from app.models.enums import RoleName, UserStatus
from scripts import build_content_index

client = TestClient(app)
VECTORS = json.loads((Path(__file__).parent / "qa_vectors.json").read_text(encoding="utf-8"))


# ---------- helpers ----------
def _chunks_from_db():
    db = SessionLocal()
    try:
        rows = db.query(ContentChunk).filter_by(language="en").all()
        return [
            {
                "id": str(c.id), "module_id": str(c.module_id),
                "section_id": str(c.section_id) if c.section_id else None,
                "module_code": c.module_code, "source_title": c.source_title,
                "section_title": c.section_title, "chunk_text": c.chunk_text,
            }
            for c in rows
        ]
    finally:
        db.close()


@pytest.fixture(scope="module")
def real_chunks():
    build_content_index.run()
    chunks = _chunks_from_db()
    assert len(chunks) >= 10, "content index should contain the migrated AZM modules"
    return chunks


def _make_user(db, role, language_id):
    username = f"test_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username, email=f"{username}@sarmaan-eplaybook.app",
        password_hash=hash_password("TestPass123!"), first_name="Test", last_name=role.value,
        role=role, language_id=language_id, status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(username):
    resp = client.post("/auth/login", json={"username": username, "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def cdd_user():
    db = SessionLocal()
    english = db.query(Language).filter_by(code="en").one()
    user = _make_user(db, RoleName.CDD, english.id)
    yield user
    db.query(AiQuestionLog).filter_by(user_id=user.id).delete()
    db.query(ContentRelease).filter_by(created_by=user.id).update({"created_by": None})
    db.query(RefreshToken).filter_by(user_id=user.id).delete()
    db.query(AuditLog).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()
    db.close()


# ---------- parity contract (Python half) ----------
def test_stopwords_and_synonyms_match_vectors():
    assert sorted(qa.STOPWORDS) == VECTORS["stopwords"]
    assert qa.SYNONYM_GROUPS == VECTORS["synonym_groups"]


@pytest.mark.parametrize("case", VECTORS["tokenize"])
def test_tokenize_vectors(case):
    assert qa.tokenize(case["input"]) == case["expected"]


@pytest.mark.parametrize("case", VECTORS["stem"])
def test_stem_vectors(case):
    assert qa.stem(case["input"]) == case["expected"]


@pytest.mark.parametrize("case", VECTORS["content_terms"])
def test_content_terms_vectors(case):
    assert qa.content_terms(case["input"]) == case["expected"]


@pytest.mark.parametrize("case", VECTORS["answers"], ids=lambda c: c["question"][:40])
def test_answer_vectors(case):
    result = qa.answer_question(case["question"], VECTORS["chunks"])
    exp = case["expected"]
    assert result["matched"] == exp["matched"]
    assert result["confidence"] == exp["confidence"]
    assert result["answer"] == exp["answer"]
    assert [s["chunk_id"] for s in result["sources"]] == exp["source_ids"]


# ---------- real migrated content ----------
GOOD = [
    ("What age group is eligible for azithromycin?", {"M1", "M2"}, ["1–59 months"], []),
    ("What should I do if the child vomits after the medicine?", {"M4"}, ["re-dose", "5 minutes"], []),
    ("How much AZM should I give to a 3 month old?", {"M4"}, ["3–4 months", "3 ml"], ["5–11 months"]),
    # A 4-month-old must get the 3-4 month row, NOT the "5-11 months: 4 ml" row.
    ("How much AZM should I give to a 4 month old?", {"M4"}, ["3–4 months", "3 ml"], ["5–11 months"]),
    ("How much AZM should I give to a 8 month old?", {"M4"}, ["5–11 months", "4 ml"], ["3–4 months"]),
    ("How do I mix the powder?", {"M4"}, ["15 ml"], []),
    ("What is the MUAC measurement for severe acute malnutrition?", {"M2"}, ["< 11.5 cm", "Severe Acute Malnutrition"], ["Moderate"]),
    ("Who do I report safeguarding concerns to?", {"M6"}, ["concerns@malariaconsortium.org"], []),
    ("What are the signs of an allergic reaction?", {"M3"}, ["Swelling"], []),
    ("How do I mark a house after visiting?", {"M4"}, ["chalk"], []),
]


@pytest.mark.parametrize("question,modules,must_have,must_not", GOOD, ids=[g[0][:45] for g in GOOD])
def test_real_questions_get_correct_cited_answers(real_chunks, question, modules, must_have, must_not):
    r = qa.answer_question(question, real_chunks)
    assert r["matched"] is True, r
    assert r["sources"], "every answer must carry a citation"
    assert r["sources"][0]["module_code"] in modules, (r["sources"][0]["module_code"], r["answer"])
    for phrase in must_have:
        assert phrase.lower() in r["answer"].lower(), (phrase, r["answer"])
    for phrase in must_not:
        assert phrase.lower() not in r["answer"].lower(), (phrase, r["answer"])
    assert 0.5 <= r["confidence"] <= 1.0


@pytest.mark.parametrize("question", ["What is the capital of France?", "pizza recipe", "what is it?", "   ??  "])
def test_unsupported_questions_get_strict_fallback_not_a_guess(real_chunks, question):
    r = qa.answer_question(question, real_chunks)
    assert r["matched"] is False
    assert r["answer"] == qa.FALLBACK_MESSAGE
    assert r["sources"] == []
    assert r["suggestions"], "fallback should offer topics the materials do cover"


def test_answers_are_verbatim_from_the_materials(real_chunks):
    """No generation: every sentence in an answer must be copied from a chunk."""
    all_text = " ".join(c["chunk_text"] for c in real_chunks)
    for question, *_ in GOOD:
        r = qa.answer_question(question, real_chunks)
        for sentence in qa.split_sentences(r["answer"]):
            assert sentence in all_text, ("not verbatim", sentence)


def test_engine_is_deterministic(real_chunks):
    a = qa.answer_question("What should I do if the child vomits after the medicine?", real_chunks)
    b = qa.answer_question("What should I do if the child vomits after the medicine?", list(reversed(real_chunks)))
    assert a == b, "result must not depend on chunk ordering"


# ---------- HTTP API ----------
def test_ask_requires_auth():
    assert client.post("/ai/ask", json={"question": "who is eligible?"}).status_code == 401
    assert client.get("/ai/chunks").status_code == 401


def test_ask_returns_cited_answer_and_logs_it(real_chunks, cdd_user):
    headers = _login(cdd_user.username)
    resp = client.post("/ai/ask", json={"question": "What should I do if the child vomits after the medicine?"}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["matched"] is True and body["offline"] is False
    assert "re-dose" in body["answer"].lower()
    assert body["sources"][0]["module_code"] == "M4"

    db = SessionLocal()
    row = db.query(AiQuestionLog).filter_by(user_id=cdd_user.id).one()
    assert row.matched is True and row.answer and row.source_module_id is not None
    db.close()


def test_unanswerable_question_is_logged_as_unmatched(real_chunks, cdd_user):
    headers = _login(cdd_user.username)
    resp = client.post("/ai/ask", json={"question": "What is the capital of France?"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["matched"] is False
    db = SessionLocal()
    row = db.query(AiQuestionLog).filter_by(user_id=cdd_user.id).one()
    assert row.matched is False and row.answer is None
    db.close()


def test_chunks_endpoint_serves_what_the_phone_needs(real_chunks, cdd_user):
    headers = _login(cdd_user.username)
    resp = client.get("/ai/chunks?language=en", headers=headers)
    assert resp.status_code == 200
    chunks = resp.json()
    assert len(chunks) == len(real_chunks)
    for key in ("id", "module_id", "module_code", "section_title", "source_title", "chunk_text", "language"):
        assert key in chunks[0]


def test_ask_validates_input(cdd_user):
    headers = _login(cdd_user.username)
    assert client.post("/ai/ask", json={"question": "x"}, headers=headers).status_code == 422


# ---------- synonym coverage pass ----------
# SYNTHETIC paraphrases written by the team to probe vocabulary gaps. They are
# NOT real user questions. Once phones report unanswered questions, replace
# these with real ones from GET /analytics/questions.
PARAPHRASES = [
    ("My baby threw up the medicine, what now?", "M4", "re-dose"),
    ("child spits out the drug", "M4", "re-dose"),
    ("how much AZM for a 2 year old", "M4", "12–59 months"),
    ("how to prepare the suspension", "M4", "15 ml"),
    ("child protection contact", "M6", "escalate"),
    ("swollen face after medicine", "M3", "swelling"),
    ("how do I mark the compound", "M4", "chalk"),
    ("how do I take a photo of the child", "M6", "photograph"),
]


@pytest.mark.parametrize("question,module,phrase", PARAPHRASES, ids=[p[0][:40] for p in PARAPHRASES])
def test_paraphrased_questions_reach_the_right_module(real_chunks, question, module, phrase):
    r = qa.answer_question(question, real_chunks)
    assert r["matched"] is True, r
    assert r["sources"][0]["module_code"] == module
    assert phrase.lower() in r["answer"].lower()


def test_years_are_read_as_months_so_a_toddler_never_gets_an_infant_dose(real_chunks):
    assert qa.normalize_ages("dose for a 2 year old") == "dose for a 24 months old"
    r = qa.answer_question("how much AZM for a 2 year old", real_chunks)
    assert "1–2 months" not in r["answer"]
