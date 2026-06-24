from dataclasses import dataclass
from io import BytesIO

import pdfplumber
from docx import Document as DocxDocument


PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


class UnsupportedDocumentTypeError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str


def parse_document(content: bytes, content_type: str) -> list[ParsedPage]:
    if content_type == PDF_CONTENT_TYPE:
        return parse_pdf(content)
    if content_type == DOCX_CONTENT_TYPE:
        return parse_docx(content)

    raise UnsupportedDocumentTypeError("Only PDF and DOCX files are supported")


def parse_pdf(content: bytes) -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    with pdfplumber.open(BytesIO(content)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = normalize_text(text)
            if text:
                pages.append(ParsedPage(page_number=index, text=text))

    return pages


def parse_docx(content: bytes) -> list[ParsedPage]:
    document = DocxDocument(BytesIO(content))
    paragraphs = [
        normalize_text(paragraph.text)
        for paragraph in document.paragraphs
        if normalize_text(paragraph.text)
    ]
    text = "\n".join(paragraphs)
    if not text:
        return []

    return [ParsedPage(page_number=1, text=text)]


def normalize_text(text: str) -> str:
    return " ".join(text.split())
