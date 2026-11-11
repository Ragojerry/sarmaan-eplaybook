"""Tiny DSL for the CDD flipbook content. Each call appends one app section to the
current module, in PDF order. `p` is always the PDF page (1-68); the printed slide
number is p - 1.

fx(p, original, corrected) records a spelling fix and returns the corrected text, so
every change to the source wording ends up in docs/cdd-content-review.md. review()
records a contradiction or question for the expert reviewers; the text is NOT changed.
"""

MODULES = []
CHANGES = []   # (pdf page, original, corrected)
REVIEW = []    # (pdf pages, topic, note)
_cur = None


def module(code, number, title, description, minutes):
    global _cur
    _cur = {"module_code": code, "learning_order": number, "title": title, "description": description,
            "estimated_minutes": minutes, "sections": []}
    MODULES.append(_cur)


def fx(p, original, corrected):
    CHANGES.append((p, original, corrected))
    return corrected


def review(pages, topic, note):
    REVIEW.append((pages if isinstance(pages, (list, tuple)) else [pages], topic, note))


def _add(kind, p, content, title=None, transcribed=False):
    _cur["sections"].append({"content_type": kind, "pdf_pages": p if isinstance(p, (list, tuple)) else [p],
                             "title": title, "content": content, "transcribed_from_image": transcribed})


def H(text, p):
    _add("HEADING", p, {"text": text})


def T(text, p, title=None):
    _add("TEXT", p, {"text": text}, title)


def L(items, p, title=None):
    _add("LIST", p, {"items": list(items)}, title)


def TB(headers, rows, p, title=None, transcribed=False):
    _add("TABLE", p, {"headers": list(headers), "rows": [list(r) for r in rows]}, title, transcribed)


def C(heading, text, p):
    _add("CALLOUT", p, {"heading": heading, "text": text}, heading)


def W(heading, text, p):
    _add("WARNING", p, {"heading": heading, "text": text}, heading)


def I(file, caption, alt, p):
    _add("IMAGE", p, {"image_file": file, "caption": caption, "alt": alt})


_QUIZ = None


def TF(ref):
    """An inline True/False quiz statement from content/learning_tests/module_quiz.json (the
    programme's module quiz), placed right after the section that teaches it. Not from the PDF,
    so it has no PDF page; its id is the fixed one the quiz build gave it."""
    global _QUIZ
    if _QUIZ is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "learning_tests", "module_quiz.json")
        with open(path, encoding="utf-8") as f:
            _QUIZ = {q["ref"]: q for q in json.load(f)}
    q = _QUIZ[ref]
    place = next(p for p in q["placements"] if p["audience"] == "CDD" and p["module_code"] == _cur["module_code"])
    _cur["sections"].append({"content_type": "TRUE_FALSE", "pdf_pages": [], "title": None, "transcribed_from_image": False,
                             "fixed_id": place["section_id"],
                             "content": {"statement": q["statement"], "answer": q["answer"], "explanation": None,
                                         "audience": "CDD", "quiz_ref": ref}})
