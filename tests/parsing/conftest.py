"""Shared fixtures for parsing tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from resume_roast.parsing import BBox, Document, Line, Style
from resume_roast.parsing.treeify import build_tree

LineFactory = Callable[..., Line]


@pytest.fixture
def make_line() -> LineFactory:
    """Return a factory building a Line with body-style defaults (11pt, not bold)."""

    def _make(
        text: str,
        *,
        size: float = 11.0,
        bold: bool = False,
        italic: bool = False,
        font: str = "Helvetica",
        x0: float = 72.0,
        y0: float = 100.0,
        x1: float = 300.0,
        y1: float = 112.0,
        page: int = 1,
    ) -> Line:
        return Line(
            text=text,
            style=Style(font=font, size=size, bold=bold, italic=italic),
            bbox=BBox(x0=x0, y0=y0, x1=x1, y1=y1),
            page=page,
        )

    return _make


@pytest.fixture
def doc(make_line: LineFactory) -> Document:
    """Build a two-section document via ``build_tree``: SECTION A / SECTION B,
    each with one untitled entry holding one body-line Paragraph -- ids n1-n7
    in pre-order (document, section A, its entry, its block, section B, its
    entry, its block). Shared by ``test_treeify.py`` (id-assignment) and
    ``test_tree.py`` (walk/find_node/node_path/ancestors), which both need the
    exact same known tree shape.
    """
    lines = [
        make_line("SECTION A", size=14.0, bold=True, y0=100.0, y1=116.0),
        make_line("Body under A.", y0=128.0, y1=140.0),
        make_line("SECTION B", size=14.0, bold=True, y0=160.0, y1=176.0),
        make_line("Body under B.", y0=188.0, y1=200.0),
    ]
    return build_tree(lines, source="resume.pdf", page_count=1)
