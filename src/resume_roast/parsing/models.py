"""Typed models for the resume parsing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Style:
    """Font/weight metadata for a line or node."""

    font: str
    size: float
    bold: bool
    italic: bool


@dataclass(frozen=True)
class BBox:
    """A bounding box in PDF page coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class Line:
    """One styled line of text extracted from a page."""

    text: str
    style: Style
    bbox: BBox
    page: int


@dataclass(frozen=True)
class Extraction:
    """The full set of lines an Extractor produced for a document."""

    lines: tuple[Line, ...]
    page_count: int


@dataclass(frozen=True)
class Paragraph:
    """A block of merged body text."""

    id: str
    text: str
    style: Style
    bbox: BBox
    page: int


@dataclass(frozen=True)
class Bullet:
    """A block of merged bullet text."""

    id: str
    text: str
    marker: str
    style: Style
    bbox: BBox
    page: int


type Block = Paragraph | Bullet


@dataclass(frozen=True)
class Entry:
    """One resume entry (e.g. a job) within a Section."""

    id: str
    heading: str | None
    style: Style | None
    bbox: BBox | None
    page: int | None
    blocks: tuple[Block, ...]


@dataclass(frozen=True)
class Section:
    """One resume section (e.g. Experience) within a Document."""

    id: str
    heading: str | None
    style: Style | None
    bbox: BBox | None
    page: int | None
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class Document:
    """The root of a parsed resume tree."""

    id: str
    source: str
    page_count: int
    sections: tuple[Section, ...]


type Node = Document | Section | Entry | Paragraph | Bullet


class Extractor(Protocol):
    """Extraction stage for one resume file format."""

    def extract(self, path: Path) -> Extraction: ...
