"""Facade: dispatch to the registered Extractor, then (optionally) build the tree."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from resume_roast.parsing.errors import UnsupportedFormatError
from resume_roast.parsing.models import Document, Extraction, Extractor
from resume_roast.parsing.pdf import PyMuPdfExtractor
from resume_roast.parsing.treeify import build_tree

EXTRACTORS: Mapping[str, Extractor] = {".pdf": PyMuPdfExtractor()}


def _resolve_extractor(path: Path, extractor: Extractor | None) -> Extractor:
    if extractor is not None:
        return extractor
    suffix = path.suffix.lower()
    if suffix not in EXTRACTORS:
        raise UnsupportedFormatError(
            f"no extractor registered for {suffix or '(no extension)'} files"
        )
    return EXTRACTORS[suffix]


def extract_resume(path: Path, *, extractor: Extractor | None = None) -> Extraction:
    """Extract styled Lines from a resume file, with no classification applied.

    Nearly-raw output for a caller that wants to fit the material into the
    Document schema itself (e.g. an LLM-based structuring stage), rather
    than this package's style/whitespace heuristics.
    """
    resolved = _resolve_extractor(path, extractor)
    return resolved.extract(path)


def parse_resume(path: Path, *, extractor: Extractor | None = None) -> Document:
    """Parse a resume file into an addressable Document tree.

    Fully deterministic -- no AI, no network -- via the style/whitespace
    heuristics in build_tree.
    """
    resolved = _resolve_extractor(path, extractor)
    extraction = resolved.extract(path)
    return build_tree(extraction.lines, source=path.name, page_count=extraction.page_count)
