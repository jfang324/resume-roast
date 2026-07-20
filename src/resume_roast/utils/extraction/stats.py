"""Pure statistics computed on demand from extracted document metadata."""

from resume_roast.utils.extraction.types import DocumentMetadata, PageMetadata


def total_words(metadata: DocumentMetadata) -> int:
    """Sum the word counts of every page."""
    return sum(page.word_count for page in metadata.pages)


def average_words_per_page(metadata: DocumentMetadata) -> float:
    """Compute the mean word count per page; 0.0 for a document without pages."""
    if not metadata.pages:
        return 0.0

    return total_words(metadata) / len(metadata.pages)


def ink_coverage(page: PageMetadata) -> float:
    """Compute the fraction (0.0-1.0) of the page area covered by text blocks.

    An approximation: overlapping blocks are counted twice and images are
    not counted at all.
    """
    area = page.width * page.height
    if area == 0:
        return 0.0

    covered = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in page.text_blocks)

    return covered / area


def average_ink_coverage(metadata: DocumentMetadata) -> float:
    """Compute the mean ink coverage across pages; 0.0 for a document without pages."""
    if not metadata.pages:
        return 0.0

    return sum(ink_coverage(page) for page in metadata.pages) / len(metadata.pages)
