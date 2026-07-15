"""Suffix-to-parser registry.

Lives next to the parser implementations it dispatches to so the
table and the implementations evolve together.
"""

import os

from resume_roast.utils.extraction.document_parser import DocumentParser
from resume_roast.utils.extraction.docx_parser import DocxParser
from resume_roast.utils.extraction.errors import UnreadableDocumentError
from resume_roast.utils.extraction.pdf_parser import PdfParser

PARSERS: dict[str, DocumentParser] = {
    ".pdf": PdfParser(),
    ".docx": DocxParser(),
}


def get_parser(path: str | os.PathLike[str]) -> DocumentParser:
    """Return the parser registered for *path*'s suffix.

    Raises:
        UnreadableDocumentError: if no parser is registered.
    """
    from pathlib import Path

    suffix = Path(path).suffix.lower()
    parser = PARSERS.get(suffix)
    if parser is None:
        raise UnreadableDocumentError(
            f"Unsupported file type: {Path(path).suffix or '(no extension)'}"
        )
    return parser
