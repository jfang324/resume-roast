"""PyMuPDF-backed Extractor -- the sole ingestion seam for raw PDF payloads."""

from __future__ import annotations

import itertools
import unicodedata
from pathlib import Path
from typing import Any, cast

import pymupdf

from resume_roast.parsing.errors import InvalidPdfError, NoTextLayerError, UnsupportedLayoutError
from resume_roast.parsing.models import BBox, Extraction, Line, Style

GUTTER_MIN_WIDTH = 24.0
MIN_SIDE_FRACTION = 0.30
MIN_SIDE_LINES = 5
MIN_LINES_FOR_COLUMN_CHECK = 10
ROW_OVERLAP_FRACTION = 0.5

_BOLD_FLAG = 1 << 4
_ITALIC_FLAG = 1 << 1


class PyMuPdfExtractor:
    """Extractor implementation backed by PyMuPDF."""

    def extract(self, path: Path) -> Extraction:
        """Extract styled Lines from a PDF, rejecting unsupported input loudly."""
        try:
            document = pymupdf.open(path)
        except Exception as exc:
            raise InvalidPdfError(f"cannot open {path} as a PDF: {exc}") from exc

        if document.needs_pass:  # pyright: ignore[reportUnknownMemberType]
            raise InvalidPdfError(f"{path} is password-protected")

        page_count = cast(int, document.page_count)  # pyright: ignore[reportUnknownMemberType]
        all_lines: list[Line] = []
        for page_index in range(page_count):
            page = document[page_index]
            raw = cast(
                dict[str, Any],
                page.get_text("dict"),  # pyright: ignore[reportUnknownMemberType]
            )
            page_lines = _page_lines(raw, page_index + 1)
            _check_column_layout(page_lines, page_index + 1)
            all_lines.extend(page_lines)

        if not all_lines:
            raise NoTextLayerError(f"{path} has no extractable text (it may be a scan)")

        all_lines.sort(key=lambda line: (line.page, line.bbox.y0, line.bbox.x0))
        merged = _merge_same_row_fragments(all_lines)

        return Extraction(lines=tuple(merged), page_count=page_count)


def _page_lines(raw: dict[str, Any], page: int) -> list[Line]:
    lines: list[Line] = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = cast(list[dict[str, Any]], line.get("spans", []))
            if not spans:
                continue
            text = unicodedata.normalize(
                "NFKC", "".join(str(span.get("text", "")) for span in spans)
            )
            if not text.strip():
                continue
            dominant = max(spans, key=lambda span: len(str(span.get("text", ""))))
            flags = int(cast(int, dominant.get("flags", 0)))
            font = str(dominant.get("font", ""))
            style = Style(
                font=font,
                size=float(cast(float, dominant.get("size", 0.0))),
                bold=bool(flags & _BOLD_FLAG) or "bold" in font.lower(),
                italic=bool(flags & _ITALIC_FLAG),
            )
            raw_bbox = cast(tuple[float, float, float, float], line["bbox"])
            bbox = BBox(x0=raw_bbox[0], y0=raw_bbox[1], x1=raw_bbox[2], y1=raw_bbox[3])
            lines.append(Line(text=text, style=style, bbox=bbox, page=page))
    return lines


def _check_column_layout(lines: list[Line], page: int) -> None:
    if len(lines) < MIN_LINES_FOR_COLUMN_CHECK:
        return

    intervals = sorted((line.bbox.x0, line.bbox.x1) for line in lines)
    coverage: list[list[float]] = []
    for x0, x1 in intervals:
        if coverage and x0 <= coverage[-1][1]:
            coverage[-1][1] = max(coverage[-1][1], x1)
        else:
            coverage.append([x0, x1])

    total = len(lines)
    for (_, gap_start), (gap_end, _) in itertools.pairwise(coverage):
        if gap_end - gap_start < GUTTER_MIN_WIDTH:
            continue
        left = sum(1 for line in lines if line.bbox.x1 <= gap_start)
        right = sum(1 for line in lines if line.bbox.x0 >= gap_end)
        if (
            left >= MIN_SIDE_LINES
            and right >= MIN_SIDE_LINES
            and left / total >= MIN_SIDE_FRACTION
            and right / total >= MIN_SIDE_FRACTION
        ):
            raise UnsupportedLayoutError(
                f"page {page} appears to use a multi-column layout, which is not supported"
            )


def _row_overlap_fraction(a: Line, b: Line) -> float:
    overlap = min(a.bbox.y1, b.bbox.y1) - max(a.bbox.y0, b.bbox.y0)
    if overlap <= 0:
        return 0.0
    shorter = min(a.bbox.y1 - a.bbox.y0, b.bbox.y1 - b.bbox.y0)
    if shorter <= 0:
        return 0.0
    return overlap / shorter


def _union_bbox(a: BBox, b: BBox) -> BBox:
    return BBox(
        x0=min(a.x0, b.x0),
        y0=min(a.y0, b.y0),
        x1=max(a.x1, b.x1),
        y1=max(a.y1, b.y1),
    )


def _merge_same_row_fragments(lines: list[Line]) -> list[Line]:
    merged: list[Line] = []
    for line in lines:
        if (
            merged
            and merged[-1].page == line.page
            and _row_overlap_fraction(merged[-1], line) >= ROW_OVERLAP_FRACTION
        ):
            prev = merged[-1]
            dominant = prev if len(prev.text) >= len(line.text) else line
            merged[-1] = Line(
                text=f"{prev.text}  {line.text}",
                style=dominant.style,
                bbox=_union_bbox(prev.bbox, line.bbox),
                page=prev.page,
            )
        else:
            merged.append(line)
    return merged
