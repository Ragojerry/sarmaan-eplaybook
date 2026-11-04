"""
Turns an uploaded reference document (PDF, Word .docx, or plain text /
Markdown) into searchable passages: [(heading, text)]. A passage is a few
paragraphs, cut at paragraph boundaries, labelled with the page ("Page 3")
or the nearest heading so an answer can say where it came from.

The file type is decided from the bytes, not the name or declared type.
"""
import io
import re
import zipfile

MAX_PASSAGE_CHARS = 900
MAX_HEADING_CHARS = 255

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TEXT = "text/plain"


class UnreadableDocument(ValueError):
    """The upload is not a supported type, or no text could be read from it."""


def sniff(data: bytes) -> str:
    if data[:5] == b"%PDF-":
        return PDF
    if data[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if "word/document.xml" in z.namelist():
                    return DOCX
        except zipfile.BadZipFile:
            pass
        raise UnreadableDocument("Only Word .docx files are supported among Office formats.")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise UnreadableDocument("Please upload a PDF, a Word .docx file, or a UTF-8 text file.") from None
    return TEXT


_SPACES = re.compile(r"[ \t ]+")
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")


def _clean(text: str) -> str:
    return _SPACES.sub(" ", text).strip()


def _paragraphs(raw: str) -> list[str]:
    """Blank lines separate paragraphs; single line breaks inside one are
    just wrapping (PDFs break every line), so they become spaces."""
    raw = _HYPHEN_BREAK.sub(r"\1\2", raw.replace("\r\n", "\n"))
    out = []
    for block in re.split(r"\n\s*\n", raw):
        p = _clean(block.replace("\n", " "))
        if p:
            out.append(p)
    return out


def _pack(sections: list[tuple[str | None, list[str]]]) -> list[tuple[str | None, str]]:
    """Group each section's paragraphs into passages of at most
    MAX_PASSAGE_CHARS (a single longer paragraph stays whole)."""
    passages = []
    for heading, paras in sections:
        heading = heading[:MAX_HEADING_CHARS] if heading else None
        current = ""
        for p in paras:
            if current and len(current) + 1 + len(p) > MAX_PASSAGE_CHARS:
                passages.append((heading, current))
                current = p
            else:
                current = f"{current} {p}".strip()
        if current:
            passages.append((heading, current))
    return passages


def _pdf_sections(data: bytes):
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    sections = []
    for n, page in enumerate(reader.pages, start=1):
        paras = _paragraphs(page.extract_text() or "")
        if paras:
            sections.append((f"Page {n}", paras))
    return sections


def _docx_sections(data: bytes):
    import docx

    document = docx.Document(io.BytesIO(data))
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    for p in document.paragraphs:
        text = _clean(p.text)
        if not text:
            continue
        style = (p.style.name or "") if p.style is not None else ""
        if style.lower().startswith(("heading", "title")):
            sections.append((text, []))
        else:
            sections[-1][1].append(text)
    for table in document.tables:
        rows = []
        for row in table.rows:
            cells = [_clean(c.text) for c in row.cells]
            cells = [c for i, c in enumerate(cells) if c and c not in cells[:i]]  # merged cells repeat
            if cells:
                rows.append("; ".join(cells) + ".")
        if rows:
            sections.append(("Table", rows))
    return [s for s in sections if s[1]]


def _text_sections(data: bytes):
    sections: list[tuple[str | None, list[str]]] = [(None, [])]
    body: list[str] = []

    def flush():
        if body:
            sections[-1][1].extend(_paragraphs("\n".join(body)))
            body.clear()

    for line in data.decode("utf-8").splitlines():
        if line.lstrip().startswith("#"):
            flush()
            sections.append((_clean(line.strip().lstrip("#")) or None, []))
        else:
            body.append(line)
    flush()
    return [s for s in sections if s[1]]


def extract_passages(data: bytes) -> tuple[str, list[tuple[str | None, str]]]:
    """-> (mime_type, [(heading, passage_text)]). Raises UnreadableDocument."""
    mime = sniff(data)
    try:
        if mime == PDF:
            sections = _pdf_sections(data)
        elif mime == DOCX:
            sections = _docx_sections(data)
        else:
            sections = _text_sections(data)
    except UnreadableDocument:
        raise
    except Exception as exc:  # noqa: BLE001 - a corrupt file must not become a 500
        raise UnreadableDocument(f"The file could not be read: {exc}") from exc
    passages = _pack(sections)
    if not passages:
        raise UnreadableDocument(
            "No text could be read from this file. Scanned PDFs (pictures of pages) are not supported."
        )
    return mime, passages
