"""Tree-string rendering for a parsed Document."""

from __future__ import annotations

import re

from resume_roast.parsing.models import Document, Entry, Node, Paragraph, Section
from resume_roast.parsing.tree import walk

TEXT_PREVIEW_LENGTH = 60


def _clean(text: str) -> str:
    text = text.rstrip()
    return re.sub(r"  +", " ", text)


def _truncate(text: str, max_length: int = TEXT_PREVIEW_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"


def _heading_or_untitled(
    heading: str | None,
    truncate: bool = False,
    max_length: int = TEXT_PREVIEW_LENGTH,
) -> str:
    if heading is not None:
        text = _clean(heading)
        if truncate and len(text) > max_length:
            return text[: max_length - 1] + "…"
        return text
    return "(untitled)"


def _depth(node: Node) -> int:
    if isinstance(node, Document):
        return 0
    if isinstance(node, Section):
        return 1
    if isinstance(node, Entry):
        return 2
    return 3


def _page_of(node: Node) -> int | None:
    if isinstance(node, Document):
        return None
    return node.page


def _render_line(
    node: Node,
    truncate: bool = False,
    max_length: int = TEXT_PREVIEW_LENGTH,
) -> str:
    indent = "  " * _depth(node)
    if isinstance(node, Document):
        line = (
            f"{indent}{node.id} [document] {node.source} — {node.page_count} page(s), "
            f"{len(node.sections)} section(s)"
        )
    elif isinstance(node, Section):
        line = f"{indent}{node.id} [section] {_heading_or_untitled(node.heading, truncate=truncate, max_length=max_length)}"
    elif isinstance(node, Entry):
        line = f"{indent}{node.id} [entry] {_heading_or_untitled(node.heading, truncate=truncate, max_length=max_length)}"
    elif isinstance(node, Paragraph):
        text = _clean(node.text)
        if truncate:
            text = _truncate(text, max_length)
        line = f"{indent}{node.id} [paragraph] {text}"
    else:
        text = _clean(node.text)
        if truncate:
            text = _truncate(text, max_length)
        line = f"{indent}{node.id} [bullet] {text}"

    page = _page_of(node)
    if page is not None:
        line = f"{line} (p{page})"
    return line


def render_tree(
    document: Document,
    *,
    truncate: bool = False,
    max_length: int = TEXT_PREVIEW_LENGTH,
) -> list[str]:
    """Render a Document tree as a list of formatted node lines."""
    return [_render_line(node, truncate=truncate, max_length=max_length) for node in walk(document)]
