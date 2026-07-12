"""`evaluate` command: bare handler function, wired by the registry."""

from pathlib import Path

import typer

from resume_roast.cli.utils import NOT_SET
from resume_roast.utils.extraction.pdf_parser import PdfParser
from resume_roast.utils.extraction.types import DocumentMetadata


def evaluate(path: Path) -> None:
    """Print a PDF's extracted Markdown and metadata.

    For now this only shows extraction output; the roast pipeline will
    take over this command later.
    """
    result = PdfParser().parse(path)
    typer.echo(result.markdown)
    typer.echo("--- metadata ---")
    _echo_metadata(result.metadata)


def _echo_metadata(metadata: DocumentMetadata) -> None:
    """Render every extracted document- and page-level fact, one per line."""
    typer.echo(f"Pages: {metadata.page_count}")
    typer.echo(f"Creator: {metadata.creator or NOT_SET}")
    typer.echo(f"Producer: {metadata.producer or NOT_SET}")
    typer.echo(f"Created: {metadata.created or NOT_SET}")
    typer.echo(f"Modified: {metadata.modified or NOT_SET}")
    typer.echo(f"Links: {', '.join(metadata.links) if metadata.links else NOT_SET}")
    for number, page in enumerate(metadata.pages, start=1):
        typer.echo(
            f"Page {number}: {page.width:g}x{page.height:g} pt, "
            f"{page.word_count} words, {len(page.text_blocks)} text blocks, "
            f"{page.image_count} images"
        )
