"""Tests for extraction stats."""

from resume_roast.utils.extraction.stats import (
    average_ink_coverage,
    average_words_per_page,
    ink_coverage,
    total_words,
)
from resume_roast.utils.extraction.types import BBox, DocumentMetadata, PageMetadata


def _page(
    word_count: int = 0,
    text_blocks: tuple[BBox, ...] = (),
    width: float = 100.0,
    height: float = 100.0,
) -> PageMetadata:
    return PageMetadata(
        width=width,
        height=height,
        word_count=word_count,
        text_blocks=text_blocks,
        image_count=0,
    )


def _document(*pages: PageMetadata) -> DocumentMetadata:
    return DocumentMetadata(
        page_count=len(pages),
        creator=None,
        producer=None,
        created=None,
        modified=None,
        links=(),
        pages=pages,
    )


def test_total_words_sums_pages() -> None:
    assert total_words(_document(_page(word_count=20), _page(word_count=5))) == 25


def test_average_words_per_page() -> None:
    assert average_words_per_page(_document(_page(word_count=20), _page(word_count=5))) == 12.5


def test_average_words_per_page_without_pages_is_zero() -> None:
    assert average_words_per_page(_document()) == 0.0


def test_ink_coverage_sums_block_areas() -> None:
    page = _page(text_blocks=((0.0, 0.0, 50.0, 50.0), (50.0, 50.0, 100.0, 100.0)))
    assert ink_coverage(page) == 0.5


def test_ink_coverage_of_zero_area_page_is_zero() -> None:
    assert ink_coverage(_page(width=0.0, height=0.0)) == 0.0


def test_average_ink_coverage() -> None:
    full = _page(text_blocks=((0.0, 0.0, 100.0, 100.0),))
    empty = _page()
    assert average_ink_coverage(_document(full, empty)) == 0.5


def test_average_ink_coverage_without_pages_is_zero() -> None:
    assert average_ink_coverage(_document()) == 0.0
