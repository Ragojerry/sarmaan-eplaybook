"""The inline True/False quiz statement (content type TRUE_FALSE).

content = {
  "statement":   "AZM is delivered through door to door approach",
  "answer":      true,                # the correct answer
  "explanation": "..." | null,        # optional, shown after answering
  "audience":    "HFW" | "CDD",       # which curriculum's quiz it belongs to (reports, editor)
  "quiz_ref":    "1.2" | null,        # where it came from in the programme's quiz table
}
The module's own audience decides who sees it; `audience` labels it for staff.
Statements are never indexed for Ask/search (app/ai/indexer.py).
"""
AUDIENCES = ("HFW", "CDD")
MAX_STATEMENT = 500
MAX_EXPLANATION = 1000


def clean_true_false(content: dict) -> dict:
    """The stored shape, or ValueError with a message an editor can act on."""
    if not isinstance(content, dict):
        raise ValueError("content must be an object")
    statement = content.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise ValueError("a True/False statement needs its text")
    if len(statement) > MAX_STATEMENT:
        raise ValueError(f"the statement is longer than {MAX_STATEMENT} characters")
    answer = content.get("answer")
    if not isinstance(answer, bool):
        raise ValueError("choose whether the statement is True or False")
    explanation = content.get("explanation")
    if explanation is not None and not isinstance(explanation, str):
        raise ValueError("the explanation must be text")
    explanation = (explanation or "").strip() or None
    if explanation and len(explanation) > MAX_EXPLANATION:
        raise ValueError(f"the explanation is longer than {MAX_EXPLANATION} characters")
    audience = content.get("audience")
    if audience not in AUDIENCES:
        raise ValueError(f"audience must be one of {', '.join(AUDIENCES)}")
    out = {"statement": statement.strip(), "answer": answer, "explanation": explanation, "audience": audience}
    if content.get("quiz_ref"):
        out["quiz_ref"] = str(content["quiz_ref"])[:20]
    return out
