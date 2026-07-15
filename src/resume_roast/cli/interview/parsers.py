"""Document-parser registry for the interview subcommand.

Keeps the parser instance map in a single place so both ``handlers.py``
and the document processing pipeline can reference it without duplication.
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


def parser_for(path: str | os.PathLike[str]) -> DocumentParser:
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
