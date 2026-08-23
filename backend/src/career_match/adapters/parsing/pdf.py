"""Extract selectable text from a PDF. Scanned pages are out of scope (no OCR)."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


class EmptyPdfError(ValueError):
    """Raised when the file has no extractable text (scan, image-only, or empty)."""


def extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n\n".join(part for part in pages if part).strip()
    if not text:
        raise EmptyPdfError(
            "No extractable text in this PDF. Scanned CVs are out of scope (no OCR)."
        )
    return text
