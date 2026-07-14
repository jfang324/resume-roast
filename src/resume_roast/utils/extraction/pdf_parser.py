"""PDF -> `ParsedResume` extraction built on PyMuPDF."""

# PyMuPDF ships partial annotations; unknown-member noise is expected at this
# boundary, and every value we keep is narrowed with an explicit cast below.
# pyright: reportUnknownMemberType=false

from pathlib import Path
from typing import Any, cast

import pymupdf
import pymupdf4llm

from resume_roast.utils.extraction._helpers import none_when_blank
from resume_roast.utils.extraction.errors import UnreadableDocumentError
from resume_roast.utils.extraction.types import BBox, DocumentMetadata, PageMetadata, ParsedResume

_TEXT_BLOCK_TYPE = 0


def _page_metadata(page: pymupdf.Page) -> PageMetadata:
    """Snapshot one page's plain-value facts."""
    words = cast(list[tuple[Any, ...]], page.get_text("words"))
    blocks = cast(list[tuple[Any, ...]], page.get_text("blocks"))
    text_blocks: tuple[BBox, ...] = tuple(
        (float(block[0]), float(block[1]), float(block[2]), float(block[3]))
        for block in blocks
        if block[6] == _TEXT_BLOCK_TYPE
    )
    return PageMetadata(
        width=page.rect.width,
        height=page.rect.height,
        word_count=len(words),
        text_blocks=text_blocks,
        image_count=len(cast(list[Any], page.get_images())),
    )


def _page_links(page: pymupdf.Page) -> tuple[str, ...]:
    """Collect the URI targets of one page's links."""
    links = cast(list[dict[str, Any]], page.get_links())
    return tuple(link["uri"] for link in links if "uri" in link)


def _document_metadata(doc: pymupdf.Document) -> DocumentMetadata:
    """Snapshot document-level facts while the handle is still open."""
    pages: list[PageMetadata] = []
    links: list[str] = []
    for page in doc:
        pages.append(_page_metadata(page))
        links.extend(_page_links(page))
    info = cast(dict[str, str | None], doc.metadata or {})
    return DocumentMetadata(
        page_count=cast(int, doc.page_count),
        creator=none_when_blank(info.get("creator")),
        producer=none_when_blank(info.get("producer")),
        created=none_when_blank(info.get("creationDate")),
        modified=none_when_blank(info.get("modDate")),
        links=tuple(links),
        pages=tuple(pages),
    )


class PdfParser:
    """Implements `DocumentParser` for PDF files."""

    def parse(self, path: Path) -> ParsedResume:
        """Extract a PDF's content as layout-aware Markdown plus metadata.

        The PyMuPDF handle lives and dies inside this call; the returned
        dataclasses hold only plain values.
        """
        try:
            doc = pymupdf.open(path)
        except (OSError, RuntimeError, ValueError) as exc:
            raise UnreadableDocumentError(f"Could not open {path}") from exc
        with doc:
            if doc.is_encrypted:
                raise UnreadableDocumentError(f"{path} is encrypted")
            markdown = cast(str, pymupdf4llm.to_markdown(doc))
            metadata = _document_metadata(doc)
        return ParsedResume(markdown=markdown, metadata=metadata)
