from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    language: str = Field(default="en", min_length=2, max_length=10)


class SourceOut(BaseModel):
    chunk_id: str
    module_id: str | None = None
    section_id: str | None = None
    module_code: str
    module_title: str
    section_title: str | None = None
    snippet: str
    kind: str = "module"  # "module" | "reference" (reference library; module_id is null)


class AnswerOut(BaseModel):
    answer: str
    matched: bool
    confidence: float
    offline: bool = False
    sources: list[SourceOut]
    suggestions: list[str]


class ChunkOut(BaseModel):
    id: str
    module_id: str
    module_code: str
    section_id: str | None
    section_title: str | None
    language: str
    source_title: str
    chunk_text: str
    faq_questions: list[str] | None = None  # set on curated answers: the questions they answer
