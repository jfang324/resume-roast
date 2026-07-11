"""Tests for resume_roast.parsing.pdf.PyMuPdfExtractor."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from resume_roast.parsing.errors import InvalidPdfError, NoTextLayerError, UnsupportedLayoutError
from resume_roast.parsing.pdf import PyMuPdfExtractor, normalize_text

PdfFactory = Callable[..., Path]


def test_extract_returns_styled_lines_in_reading_order(make_pdf: PdfFactory) -> None:
    path = make_pdf(
        [
            ("EXPERIENCE", 72, 100, 14, "hebo"),
            ("Built a parser", 72, 130, 11, "helv"),
            ("Shipped features", 72, 150, 11, "helv"),
        ]
    )

    extraction = PyMuPdfExtractor().extract(path)

    assert extraction.page_count == 1
    assert [line.text for line in extraction.lines] == [
        "EXPERIENCE",
        "Built a parser",
        "Shipped features",
    ]
    heading = extraction.lines[0]
    assert heading.style.font == "Helvetica-Bold"
    assert heading.style.size == pytest.approx(14.0, abs=0.5)
    assert heading.style.bold is True
    assert heading.page == 1

    body = extraction.lines[1]
    assert body.style.font == "Helvetica"
    assert body.style.size == pytest.approx(11.0, abs=0.5)
    assert body.style.bold is False


def test_extract_orders_lines_across_pages(make_pdf: PdfFactory) -> None:
    path = make_pdf(
        [
            ("Page one line", 72, 100, 11, "helv", 0),
            ("Page two line", 72, 100, 11, "helv", 1),
        ],
        page_count=2,
    )

    extraction = PyMuPdfExtractor().extract(path)

    assert extraction.page_count == 2
    assert [line.page for line in extraction.lines] == [1, 2]
    assert extraction.lines[0].text == "Page one line"
    assert extraction.lines[1].text == "Page two line"


def test_extract_merges_same_row_title_and_date(make_pdf: PdfFactory) -> None:
    path = make_pdf(
        [
            ("Software Engineer", 72, 100, 11, "helv"),
            ("2020 - 2023", 400, 100, 11, "helv"),
        ]
    )

    extraction = PyMuPdfExtractor().extract(path)

    assert len(extraction.lines) == 1
    assert extraction.lines[0].text == "Software Engineer  2020 - 2023"


def test_extract_normalizes_ligatures(make_pdf: PdfFactory) -> None:
    path = make_pdf(html_placements=[("efﬁcient", 72, 100, 500, 140, 0)])

    extraction = PyMuPdfExtractor().extract(path)

    assert extraction.lines[0].text == "efficient"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Remote​", "Remote"),
        ("Remote​Zone", "RemoteZone"),
        ("Plain text", "Plain text"),
    ],
    ids=["trailing-zwsp", "embedded-zwsp", "unaffected-plain-text"],
)
def test_normalize_text_strips_invisible_format_characters(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_extract_rejects_two_column_layout(two_column_pdf: Path) -> None:
    with pytest.raises(UnsupportedLayoutError, match="page 1"):
        PyMuPdfExtractor().extract(two_column_pdf)


def test_extract_rejects_pdf_without_text_layer(make_pdf: PdfFactory) -> None:
    path = make_pdf(filename="scan.pdf")

    with pytest.raises(NoTextLayerError, match=re.escape(path.name)):
        PyMuPdfExtractor().extract(path)


def _missing_path(make_pdf: PdfFactory, tmp_path: Path) -> Path:  # noqa: ARG001
    return tmp_path / "missing.pdf"


def _garbage_bytes_path(make_pdf: PdfFactory, tmp_path: Path) -> Path:  # noqa: ARG001
    path = tmp_path / "garbage.pdf"
    path.write_bytes(b"not a pdf file at all")
    return path


def _password_protected_path(make_pdf: PdfFactory, tmp_path: Path) -> Path:  # noqa: ARG001
    return make_pdf([("secret", 72, 100, 11, "helv")], filename="locked.pdf", user_pw="pw123")


@pytest.mark.parametrize(
    "build_path",
    [_missing_path, _garbage_bytes_path, _password_protected_path],
    ids=["missing", "garbage-bytes", "password-protected"],
)
def test_extract_rejects_unopenable_file(
    make_pdf: PdfFactory,
    tmp_path: Path,
    build_path: Callable[[PdfFactory, Path], Path],
) -> None:
    path = build_path(make_pdf, tmp_path)

    with pytest.raises(InvalidPdfError, match=re.escape(path.name)):
        PyMuPdfExtractor().extract(path)
