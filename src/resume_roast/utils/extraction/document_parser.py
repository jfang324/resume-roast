"""Generic parser interface every document-format parser implements."""

from pathlib import Path
from typing import Protocol

from resume_roast.utils.extraction.types import ParsedResume


class DocumentParser(Protocol):
    """Converts a document file into Markdown content plus metadata."""

    def parse(self, path: Path) -> ParsedResume:
        """Extract a file's content and metadata."""
        ...
