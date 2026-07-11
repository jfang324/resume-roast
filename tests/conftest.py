"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

import pymupdf
import pytest

Placement = tuple[str, float, float, float, str] | tuple[str, float, float, float, str, int]
HtmlPlacement = tuple[str, float, float, float, float, int]
PdfFactory = Callable[..., Path]


@pytest.fixture
def store_dir(tmp_path: Path) -> Path:
    """Return a store directory path that does not yet exist on disk."""
    return tmp_path / "store"


@pytest.fixture
def make_pdf(tmp_path: Path) -> PdfFactory:
    """Return a factory that builds a synthetic PDF from text placements.

    Each placement is ``(text, x, y, size, fontname)`` (base-14 names like
    ``"helv"``/``"hebo"``), optionally followed by a 0-based page index for
    multi-page documents. ``html_placements`` route through an HTML/CSS box
    instead, using PyMuPDF's Unicode-capable fallback font -- base-14 fonts
    cannot encode glyphs like the "fi" ligature.
    """

    def _make(
        placements: Sequence[Placement] = (),
        *,
        filename: str = "resume.pdf",
        page_count: int = 1,
        user_pw: str | None = None,
        html_placements: Sequence[HtmlPlacement] = (),
    ) -> Path:
        doc = pymupdf.open()
        for _ in range(page_count):
            doc.new_page()

        for placement in placements:
            text, x, y, size, fontname, *rest = placement
            page_index = rest[0] if rest else 0
            doc[page_index].insert_text(  # pyright: ignore[reportUnknownMemberType]
                (x, y), text, fontsize=size, fontname=fontname
            )

        for text, x0, y0, x1, y1, page_index in html_placements:
            rect = pymupdf.Rect(x0, y0, x1, y1)
            doc[page_index].insert_htmlbox(  # pyright: ignore[reportUnknownMemberType]
                rect, f"<p>{text}</p>"
            )

        path = tmp_path / filename
        if user_pw is not None:
            doc.save(  # pyright: ignore[reportUnknownMemberType]
                path,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
                user_pw=user_pw,
                owner_pw=user_pw,
            )
        else:
            doc.save(path)  # pyright: ignore[reportUnknownMemberType]
        doc.close()
        return path

    return _make


def two_column_placements() -> list[Placement]:
    """Return placements for a two-column layout: two 8-line columns across a wide gutter.

    Shared by ``tests/parsing/test_pdf.py`` (direct extraction) and
    ``tests/cli/test_evaluate.py`` (CLI error-path parametrization) so the
    geometry that trips the column-gutter heuristic is defined once.
    """
    placements: list[Placement] = []
    y = 100.0
    for i in range(8):
        placements.append((f"Left line {i}", 72, y, 11, "helv"))
        placements.append((f"Right line {i}", 330, y, 11, "helv"))
        y += 20
    return placements


@pytest.fixture
def two_column_pdf(make_pdf: PdfFactory) -> Path:
    """Build a synthetic two-column PDF using ``two_column_placements``."""
    return make_pdf(two_column_placements())


@pytest.fixture
def canonical_resume_pdf(make_pdf: PdfFactory) -> Path:
    """Build the canonical fixture resume shared by parsing and CLI tests.

    One page: a 22pt name, an 11pt contact line, a 14pt-bold section heading,
    an 11pt-bold entry heading, and two ASCII "- " bullets.
    """
    return make_pdf(
        [
            ("Jordan Diaz", 72, 60, 22, "hebo"),
            ("jordan@example.com | 555-0100", 72, 100, 11, "helv"),
            ("EXPERIENCE", 72, 150, 14, "hebo"),
            ("Software Engineer - Acme Corp", 72, 180, 11, "hebo"),
            ("- Shipped the roasting pipeline", 72, 205, 11, "helv"),
            ("- Cut parse latency by 40%", 72, 225, 11, "helv"),
        ],
        filename="resume.pdf",
    )
