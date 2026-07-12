"""Tests for PdfParser."""

# The fixtures drive PyMuPDF's partially annotated document-building API.
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

from pathlib import Path

import pymupdf
import pytest

from resume_roast.utils.extraction.document_parser import DocumentParser
from resume_roast.utils.extraction.errors import UnreadableDocumentError
from resume_roast.utils.extraction.pdf_parser import PdfParser
from resume_roast.utils.extraction.types import ParsedResume

_LINK_URI = "https://github.com/janedoe"

# Words inserted on each page of the sample PDF, in PyMuPDF's word-count terms.
_PAGE_ONE_WORDS = 8  # "Jane Doe" + "Experience" + "Roasted resumes at Acme Corp"
_PAGE_TWO_WORDS = 1  # "Education"


def _small_pixmap() -> pymupdf.Pixmap:
    pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 40, 40))
    pixmap.clear_with(90)
    return pixmap


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("extraction") / "sample.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 80), "Jane Doe", fontsize=20)
        page.insert_text((72, 120), "Experience", fontsize=16)
        page.insert_text((72, 150), "Roasted resumes at Acme Corp", fontsize=11)
        page.insert_image(pymupdf.Rect(400, 60, 500, 160), pixmap=_small_pixmap())
        page.insert_link(
            {
                "kind": pymupdf.LINK_URI,
                "from": pymupdf.Rect(72, 200, 200, 215),
                "uri": _LINK_URI,
            }
        )
        page_two = doc.new_page()
        page_two.insert_text((72, 80), "Education", fontsize=16)
        doc.set_metadata({"creator": "unit-test", "producer": "pymupdf"})
        doc.save(path)
    return path


@pytest.fixture(scope="module")
def parsed(sample_pdf: Path) -> ParsedResume:
    return PdfParser().parse(sample_pdf)


def test_pdf_parser_satisfies_document_parser() -> None:
    parser: DocumentParser = PdfParser()
    assert isinstance(parser, PdfParser)


def test_markdown_keeps_inserted_text(parsed: ParsedResume) -> None:
    assert "Jane Doe" in parsed.markdown
    assert "Roasted resumes at Acme Corp" in parsed.markdown
    assert "Education" in parsed.markdown


def test_metadata_counts_pages_words_and_images(parsed: ParsedResume) -> None:
    metadata = parsed.metadata
    assert metadata.page_count == 2
    assert len(metadata.pages) == 2
    assert metadata.pages[0].word_count == _PAGE_ONE_WORDS
    assert metadata.pages[1].word_count == _PAGE_TWO_WORDS
    assert metadata.pages[0].image_count == 1
    assert metadata.pages[1].image_count == 0


def test_metadata_text_blocks_fit_inside_the_page(parsed: ParsedResume) -> None:
    page = parsed.metadata.pages[0]
    assert page.text_blocks
    for x0, y0, x1, y1 in page.text_blocks:
        assert 0 <= x0 < x1 <= page.width
        assert 0 <= y0 < y1 <= page.height


def test_metadata_collects_uri_links(parsed: ParsedResume) -> None:
    assert parsed.metadata.links == (_LINK_URI,)


def test_metadata_normalizes_blank_fields_to_none(parsed: ParsedResume) -> None:
    metadata = parsed.metadata
    assert metadata.creator == "unit-test"
    assert metadata.producer == "pymupdf"
    assert metadata.created is None
    assert metadata.modified is None


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(UnreadableDocumentError):
        PdfParser().parse(tmp_path / "missing.pdf")


def test_corrupt_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"this is not a pdf")
    with pytest.raises(UnreadableDocumentError):
        PdfParser().parse(path)


def test_encrypted_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "encrypted.pdf"
    with pymupdf.open() as doc:
        doc.new_page()
        # The constant exists at runtime but is missing from PyMuPDF's stubs.
        doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret")  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(UnreadableDocumentError):
        PdfParser().parse(path)
