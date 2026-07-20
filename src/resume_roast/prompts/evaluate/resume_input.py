"""The resume document input: system-side description, user-side rendering."""

from resume_roast.utils.extraction.stats import average_ink_coverage, average_words_per_page
from resume_roast.utils.extraction.types import DocumentMetadata, ParsedResume

RESUME_INPUT = """\
## Input

The user message contains the resume as Markdown extracted from the
source document, inside <resume> tags, then — when the source format
exposes page layout — document statistics computed from it, and closes
with your task.

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
fill; high coverage with many words means a wall of text. When no
statistics block is present, the source format does not expose layout —
judge from the text alone and never treat the absence as thinness."""


def render_resume_input(parsed: ParsedResume) -> str:
    """Render the user-message counterpart of RESUME_INPUT: tagged Markdown plus stats.

    The statistics block only renders for sources with page layout (PDF);
    a paged document always has pages, so an empty ``pages`` means the
    format has none and zeros would read as an empty resume.
    """
    sections = [f"<resume>\n{parsed.markdown.strip()}\n</resume>"]
    if parsed.metadata.pages:
        sections.append(_stats_block(parsed.metadata))

    return "\n\n".join(sections)


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
