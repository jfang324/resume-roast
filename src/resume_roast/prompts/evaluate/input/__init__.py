"""The resume document input: system-side description, user-side rendering."""

from resume_roast.utils.extraction.stats import average_ink_coverage, average_words_per_page
from resume_roast.utils.extraction.types import DocumentMetadata, ParsedResume

RESUME_INPUT = """\
## Input

The user message contains the resume as Markdown extracted from a PDF,
inside <resume> tags, then document statistics computed from the PDF's
layout, and closes with your task.

The Markdown extraction preserves text content and section order, but
discards all visual layout — positioning, centering, fonts, colors,
spacing, and visual hierarchy. You can see what text exists and its
rough order; you cannot see how it was arranged on the page. Judge
fullness and density from the statistics, not from blank lines. Section
headings can also be detached from their content, demoted to plain text,
or moved out of order.

Statistics calibration: a full one-page resume typically runs 400-700
words. Well under that reads as thin; well over reads as cramped. Low
text coverage with few words means unused space the candidate could
fill; high coverage with many words means a wall of text."""


def render_resume_input(parsed: ParsedResume) -> str:
    """Render the user-message counterpart of RESUME_INPUT: tagged Markdown plus stats."""
    return "\n\n".join(
        [
            f"<resume>\n{parsed.markdown.strip()}\n</resume>",
            _stats_block(parsed.metadata),
        ]
    )


def _stats_block(metadata: DocumentMetadata) -> str:
    """Render the document statistics the model should ground density claims in."""
    return "\n".join(
        [
            "## Document Statistics",
            "",
            f"- Pages: {metadata.page_count}",
            f"- Average words per page: {average_words_per_page(metadata):.0f}",
            f"- Text coverage: {average_ink_coverage(metadata):.0%} of page area",
            f"- Images: {sum(page.image_count for page in metadata.pages)}",
            f"- Links: {', '.join(metadata.links) if metadata.links else 'none'}",
        ]
    )
