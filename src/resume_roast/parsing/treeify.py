"""Builds an addressable Document tree from styled Lines via style clustering."""

from __future__ import annotations

import itertools
import statistics
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field

from resume_roast.parsing.models import (
    BBox,
    Bullet,
    Document,
    Entry,
    Line,
    Paragraph,
    Section,
    Style,
)

STYLE_SIZE_BIN = 0.5
SECTION_SIZE_DELTA = 1.0
PARAGRAPH_GAP_FACTOR = 0.75
BULLET_X_TOLERANCE = 2.0
BULLET_MARKERS = ("•", "◦", "▪", "‣", "·", "●", "-", "–", "*")  # noqa: RUF001

_StyleKey = tuple[float, bool]


@dataclass
class _MutableBlock:
    kind: str
    text: str
    marker: str
    style: Style
    dominant_len: int
    bbox: BBox
    page: int
    last_bbox: BBox
    bullet_x0: float


@dataclass
class _MutableEntry:
    heading: str | None
    style: Style | None
    bbox: BBox | None
    page: int | None
    blocks: list[_MutableBlock] = field(default_factory=list[_MutableBlock])


@dataclass
class _MutableSection:
    heading: str | None
    style: Style | None
    bbox: BBox | None
    page: int | None
    entries: list[_MutableEntry] = field(default_factory=list[_MutableEntry])


def _style_key(style: Style) -> _StyleKey:
    return (round(style.size / STYLE_SIZE_BIN) * STYLE_SIZE_BIN, style.bold)


def _is_invisible_boundary(char: str) -> bool:
    return char.isspace() or unicodedata.category(char) == "Cf"


def _split_bullet(text: str) -> tuple[str, str] | None:
    for marker in BULLET_MARKERS:
        if not text.startswith(marker):
            continue
        rest = text[len(marker) :]
        if not rest or not _is_invisible_boundary(rest[0]):
            continue
        index = 0
        while index < len(rest) and _is_invisible_boundary(rest[index]):
            index += 1
        return marker, rest[index:]
    return None


def _classify(line: Line, body_size: float, body_bold: bool) -> tuple[str, tuple[str, str] | None]:
    split = _split_bullet(line.text)
    if split is not None:
        return "bullet", split

    size_bin = _style_key(line.style)[0]
    if size_bin >= body_size + SECTION_SIZE_DELTA:
        return "section", None
    if line.style.bold and not body_bold and size_bin >= body_size:
        return "entry", None
    return "body", None


def _join_text(prev: str, nxt: str) -> str:
    if prev.endswith("-") and nxt[:1].islower():
        words = prev.split()
        last_token = words[-1] if words else prev
        stem = last_token[:-1]
        if "-" in stem:
            return prev + nxt
        return prev[:-1] + nxt
    return f"{prev} {nxt}"


def _union_bbox(a: BBox, b: BBox) -> BBox:
    return BBox(
        x0=min(a.x0, b.x0),
        y0=min(a.y0, b.y0),
        x1=max(a.x1, b.x1),
        y1=max(a.y1, b.y1),
    )


def _try_merge(block: _MutableBlock, line: Line, median_height: float) -> bool:
    if block.page != line.page:
        return False
    gap = line.bbox.y0 - block.last_bbox.y1
    if gap >= PARAGRAPH_GAP_FACTOR * median_height:
        return False
    if block.kind == "bullet" and line.bbox.x0 < block.bullet_x0 - BULLET_X_TOLERANCE:
        return False

    block.text = _join_text(block.text, line.text)
    if len(line.text) > block.dominant_len:
        block.style = line.style
        block.dominant_len = len(line.text)
    block.bbox = _union_bbox(block.bbox, line.bbox)
    block.last_bbox = line.bbox
    return True


def _freeze(sections: list[_MutableSection], source: str, page_count: int) -> Document:
    counter = itertools.count(2)
    frozen_sections: list[Section] = []
    for section in sections:
        section_id = f"n{next(counter)}"
        frozen_entries: list[Entry] = []
        for entry in section.entries:
            entry_id = f"n{next(counter)}"
            frozen_blocks: list[Paragraph | Bullet] = []
            for block in entry.blocks:
                block_id = f"n{next(counter)}"
                if block.kind == "bullet":
                    frozen_blocks.append(
                        Bullet(
                            id=block_id,
                            text=block.text,
                            marker=block.marker,
                            style=block.style,
                            bbox=block.bbox,
                            page=block.page,
                        )
                    )
                else:
                    frozen_blocks.append(
                        Paragraph(
                            id=block_id,
                            text=block.text,
                            style=block.style,
                            bbox=block.bbox,
                            page=block.page,
                        )
                    )
            frozen_entries.append(
                Entry(
                    id=entry_id,
                    heading=entry.heading,
                    style=entry.style,
                    bbox=entry.bbox,
                    page=entry.page,
                    blocks=tuple(frozen_blocks),
                )
            )
        frozen_sections.append(
            Section(
                id=section_id,
                heading=section.heading,
                style=section.style,
                bbox=section.bbox,
                page=section.page,
                entries=tuple(frozen_entries),
            )
        )
    return Document(id="n1", source=source, page_count=page_count, sections=tuple(frozen_sections))


def build_tree(lines: Sequence[Line], *, source: str, page_count: int) -> Document:
    """Classify and group styled Lines into an addressable Document tree."""
    if not lines:
        return Document(id="n1", source=source, page_count=page_count, sections=())

    style_totals: dict[_StyleKey, int] = {}
    for line in lines:
        key = _style_key(line.style)
        style_totals[key] = style_totals.get(key, 0) + len(line.text)
    body_size, body_bold = max(style_totals, key=lambda key: style_totals[key])

    body_heights = [
        line.bbox.y1 - line.bbox.y0
        for line in lines
        if _style_key(line.style) == (body_size, body_bold)
    ]
    median_height = statistics.median(body_heights)

    sections: list[_MutableSection] = []
    cur_section: _MutableSection | None = None
    cur_entry: _MutableEntry | None = None
    cur_block: _MutableBlock | None = None

    for line in lines:
        kind, split = _classify(line, body_size, body_bold)

        if kind == "section":
            cur_section = _MutableSection(line.text, line.style, line.bbox, line.page)
            sections.append(cur_section)
            cur_entry = None
            cur_block = None
            continue

        if kind == "entry":
            if cur_section is None:
                cur_section = _MutableSection(None, None, None, None)
                sections.append(cur_section)
            cur_entry = _MutableEntry(line.text, line.style, line.bbox, line.page)
            cur_section.entries.append(cur_entry)
            cur_block = None
            continue

        if cur_section is None:
            cur_section = _MutableSection(None, None, None, None)
            sections.append(cur_section)
        if cur_entry is None:
            cur_entry = _MutableEntry(None, None, None, None)
            cur_section.entries.append(cur_entry)

        if split is not None:
            marker, text = split
            block = _MutableBlock(
                kind="bullet",
                text=text,
                marker=marker,
                style=line.style,
                dominant_len=len(text),
                bbox=line.bbox,
                page=line.page,
                last_bbox=line.bbox,
                bullet_x0=line.bbox.x0,
            )
            cur_entry.blocks.append(block)
            cur_block = block
            continue

        if cur_block is not None and _try_merge(cur_block, line, median_height):
            continue

        block = _MutableBlock(
            kind="paragraph",
            text=line.text,
            marker="",
            style=line.style,
            dominant_len=len(line.text),
            bbox=line.bbox,
            page=line.page,
            last_bbox=line.bbox,
            bullet_x0=line.bbox.x0,
        )
        cur_entry.blocks.append(block)
        cur_block = block

    return _freeze(sections, source, page_count)
