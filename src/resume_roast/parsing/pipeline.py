"""Facade: dispatch to the registered Extractor, then build the tree."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from resume_roast.parsing.errors import UnsupportedFormatError
from resume_roast.parsing.models import Document, Extractor
from resume_roast.parsing.pdf import PyMuPdfExtractor
from resume_roast.parsing.treeify import build_tree

EXTRACTORS: Mapping[str, Extractor] = {".pdf": PyMuPdfExtractor()}


def parse_resume(path: Path, *, extractor: Extractor | None = None) -> Document:
    """Parse a resume file into an addressable Document tree."""
    if extractor is None:
        suffix = path.suffix.lower()
        if suffix not in EXTRACTORS:
            raise UnsupportedFormatError(
                f"no extractor registered for {suffix or '(no extension)'} files"
            )
        extractor = EXTRACTORS[suffix]

    extraction = extractor.extract(path)
    return build_tree(extraction.lines, source=path.name, page_count=extraction.page_count)
