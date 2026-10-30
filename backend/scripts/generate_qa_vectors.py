"""
Generates tests/qa_vectors.json (copied to mobile/test/qa_vectors.json): the
shared contract that keeps the Python and Dart QA engines identical. Hand-
written expectations for tokenize/stem/content_terms are ASSERTED against the
engine first (so a wrong prediction fails loudly here); question->answer
expectations are then recorded from the engine over a fixed set of real
chunks. Re-run after ANY change to app/ai/qa_engine.py, and port the change
to mobile/lib/qa/qa_engine.dart.

Usage: cd backend && python3 -m scripts.generate_qa_vectors
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai import qa_engine as qa
from app.database import SessionLocal
from app.models import ContentChunk

TOKENIZE = [
    ("What should I do if the child vomits?", ["what", "should", "do", "if", "the", "child", "vomits"]),
    ("Children aged 1\u201359 months.", ["children", "aged", "1", "59", "months"]),
    ("re-dose if the child vomits within 5 minutes", ["re", "dose", "if", "the", "child", "vomits", "within", "5", "minutes"]),
    ("\u0198ananan YARA 3", ["\u0199ananan", "yara", "3"]),
    ("concerns@malariaconsortium.org", ["concerns", "malariaconsortium", "org"]),
]
STEM = [
    ("vomiting", "vomit"), ("vomited", "vomit"), ("vomits", "vomit"), ("vomit", "vomit"),
    ("medicine", "medicin"), ("medicines", "medicin"), ("dose", "dos"), ("doses", "dos"), ("dosing", "dos"),
    ("age", "age"), ("ages", "age"), ("give", "giv"), ("giving", "giv"), ("gives", "giv"),
    ("reconstitute", "reconstitut"), ("reconstituted", "reconstitut"), ("safeguarding", "safeguard"),
    ("children", "children"), ("class", "class"), ("59", "59"), ("azm", "azm"),
]
CONTENT_TERMS = [
    ("What should I do if the child vomits after the medicine?", ["child", "vomit", "medicin"]),
    ("How much AZM should I give to a 3 month old?", ["much", "azm", "giv", "3", "month", "old"]),
    ("What is the capital of France?", ["capital", "franc"]),
    ("Children aged 1\u201359 months", ["children", "aged", "1", "59", "month"]),
]
FIXTURE_TITLES = [
    ("M4", "Dosing strategy"),
    ("M3", "Possible signs of an allergic reaction to AZM"),
    ("M2", "Who is NOT eligible"),
    ("M1", "Who receives it"),
    ("M6", "During the AZM campaign"),
    ("M2", "SARMAAN-II pilot: MUAC & ANC assessment"),
    ("M4", "AZM Powdered Oral Suspension (POS)"),
]
QUESTIONS = [
    "What age group is eligible for azithromycin?",
    "What should I do if the child vomits after the medicine?",
    "How much AZM should I give to a 3 month old?",
    "How much AZM should I give to a 4 month old?",
    "How much AZM should I give to a 2 year old?",
    "My baby threw up the medicine, what now?",
    "How much AZM should I give to a 8 month old?",
    "How do I mix the powder?",
    "What is the MUAC measurement for severe acute malnutrition?",
    "When should I refer a child to the health facility?",
    "Who do I report safeguarding concerns to?",
    "What are the signs of an allergic reaction?",
    "What is the capital of France?",
    "pizza recipe",
    "what is it?",
]


def main():
    for text, expected in TOKENIZE:
        assert qa.tokenize(text) == expected, ("tokenize", text, qa.tokenize(text), expected)
    for tok, expected in STEM:
        assert qa.stem(tok) == expected, ("stem", tok, qa.stem(tok), expected)
    for text, expected in CONTENT_TERMS:
        assert qa.content_terms(text) == expected, ("content_terms", text, qa.content_terms(text), expected)

    db = SessionLocal()
    chunks = []
    for i, (code, title) in enumerate(FIXTURE_TITLES, start=1):
        row = db.query(ContentChunk).filter_by(module_code=code, section_title=title, language="en").one()
        chunks.append({
            "id": f"c{i}", "module_id": None, "section_id": None, "module_code": row.module_code,
            "source_title": row.source_title, "section_title": row.section_title, "chunk_text": row.chunk_text,
        })
    db.close()

    index = qa.build_index(chunks)
    answers = []
    for q in QUESTIONS:
        r = qa.answer_question(q, index)
        answers.append({
            "question": q,
            "expected": {
                "matched": r["matched"],
                "confidence": r["confidence"],
                "answer": r["answer"],
                "source_ids": [s["chunk_id"] for s in r["sources"]],
            },
        })

    vectors = {
        "stopwords": sorted(qa.STOPWORDS),
        "synonym_groups": qa.SYNONYM_GROUPS,
        "tokenize": [{"input": a, "expected": b} for a, b in TOKENIZE],
        "stem": [{"input": a, "expected": b} for a, b in STEM],
        "content_terms": [{"input": a, "expected": b} for a, b in CONTENT_TERMS],
        "chunks": chunks,
        "answers": answers,
    }
    out = Path(__file__).resolve().parents[1] / "tests" / "qa_vectors.json"
    out.write_text(json.dumps(vectors, ensure_ascii=False, indent=1), encoding="utf-8")
    mobile = Path(__file__).resolve().parents[2] / "mobile" / "test" / "qa_vectors.json"
    mobile.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out, mobile)
    print(f"Wrote {out} and {mobile}")
    for a in answers:
        e = a["expected"]
        print(f"- {a['question']!r}: matched={e['matched']} conf={e['confidence']} src={e['source_ids']} :: {e['answer'][:90]}")


if __name__ == "__main__":
    main()
