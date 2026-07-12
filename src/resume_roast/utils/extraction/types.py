"""Dataclasses describing a parsed document and its extracted metadata."""

from dataclasses import dataclass

type BBox = tuple[float, float, float, float]
"""A rectangle as ``(x0, y0, x1, y1)`` in page coordinates."""


@dataclass(frozen=True)
class PageMetadata:
    """Plain-value facts about one page, captured while the document is open."""

    width: float
    height: float
    word_count: int

    text_blocks: tuple[BBox, ...]
    """Bounding boxes of text blocks only; image blocks are excluded."""

    image_count: int


@dataclass(frozen=True)
class DocumentMetadata:
    """Format-neutral facts about the whole document.

    Formats without fixed pages (e.g. a future DOCX parser) leave ``pages``
    empty; every other field still applies.
    """

    page_count: int
    creator: str | None
    producer: str | None

    created: str | None
    """Raw date string as the source format stores it, not normalized."""

    modified: str | None
    """Raw date string as the source format stores it, not normalized."""

    links: tuple[str, ...]
    """URI link targets found anywhere in the document."""

    pages: tuple[PageMetadata, ...]


@dataclass(frozen=True)
class ParsedResume:
    """What every document parser returns: content plus extracted metadata."""

    markdown: str
    metadata: DocumentMetadata
