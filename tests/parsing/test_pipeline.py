"""Tests for resume_roast.parsing.pipeline.parse_resume/extract_resume."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from resume_roast.parsing import BBox, Bullet, Extraction, Line, Style
from resume_roast.parsing.errors import UnsupportedFormatError
from resume_roast.parsing.pdf import PyMuPdfExtractor
from resume_roast.parsing.pipeline import extract_resume, parse_resume

PdfFactory = Callable[..., Path]


def test_parse_resume_returns_document_for_single_column_pdf(
    canonical_resume_pdf: Path,
) -> None:
    doc = parse_resume(canonical_resume_pdf)

    assert doc.source == "resume.pdf"
    assert doc.page_count == 1
    assert [s.heading for s in doc.sections] == ["Jordan Diaz", "EXPERIENCE"]
    entries = doc.sections[1].entries

    first_entry = entries[0]
    assert first_entry.heading is None
    assert first_entry.blocks[0].text == "Software Engineer - Acme Corp"
    bullets = [b for b in first_entry.blocks if isinstance(b, Bullet)]
    assert [b.marker for b in bullets] == ["-", "-"]
    assert [b.text for b in bullets] == [
        "Shipped the roasting pipeline",
        "Cut parse latency by 40%",
    ]

    second_entry = entries[1]
    assert second_entry.heading == "Senior Engineer - Beta Corp"
    second_bullets = [b for b in second_entry.blocks if isinstance(b, Bullet)]
    assert [b.text for b in second_bullets] == ["Mentored two junior engineers"]


@pytest.mark.parametrize("name", ["resume.docx", "resume"], ids=["docx", "no-suffix"])
def test_parse_resume_rejects_unregistered_extension(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"whatever")

    with pytest.raises(UnsupportedFormatError):
        parse_resume(path)


class _StubExtractor:
    def extract(self, path: Path) -> Extraction:  # noqa: ARG002
        heading = Line(
            text="Stub Heading",
            style=Style(font="Helvetica-Bold", size=14.0, bold=True, italic=False),
            bbox=BBox(x0=72.0, y0=100.0, x1=200.0, y1=116.0),
            page=1,
        )
        body = Line(
            text="Stub body line here.",
            style=Style(font="Helvetica", size=11.0, bold=False, italic=False),
            bbox=BBox(x0=72.0, y0=120.0, x1=250.0, y1=132.0),
            page=1,
        )
        return Extraction(lines=(heading, body), page_count=1)


def test_parse_resume_uses_injected_extractor(tmp_path: Path) -> None:
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"irrelevant -- extractor is stubbed")

    doc = parse_resume(path, extractor=_StubExtractor())

    assert doc.sections[0].heading == "Stub Heading"
    assert doc.sections[0].entries[0].blocks[0].text == "Stub body line here."


def test_extract_resume_returns_raw_extraction_for_pdf(canonical_resume_pdf: Path) -> None:
    extraction = extract_resume(canonical_resume_pdf)

    assert extraction == PyMuPdfExtractor().extract(canonical_resume_pdf)


@pytest.mark.parametrize("name", ["resume.docx", "resume"], ids=["docx", "no-suffix"])
def test_extract_resume_rejects_unregistered_extension(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"whatever")

    with pytest.raises(UnsupportedFormatError):
        extract_resume(path)


def test_extract_resume_uses_injected_extractor(tmp_path: Path) -> None:
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"irrelevant -- extractor is stubbed")

    extraction = extract_resume(path, extractor=_StubExtractor())

    assert extraction == _StubExtractor().extract(path)
