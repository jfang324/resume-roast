"""The root-level `evaluate` command."""

from __future__ import annotations

from pathlib import Path

import typer

from resume_roast.parsing import (
    Document,
    Entry,
    Node,
    Paragraph,
    ParsingError,
    Section,
    parse_resume,
    walk,
)

TEXT_PREVIEW_LENGTH = 60

evaluate_cli = typer.Typer()


def _truncate(text: str) -> str:
    if len(text) <= TEXT_PREVIEW_LENGTH:
        return text
    return text[: TEXT_PREVIEW_LENGTH - 1] + "…"


def _heading_or_untitled(heading: str | None) -> str:
    return _truncate(heading) if heading is not None else "(untitled)"


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


def _render_line(node: Node) -> str:
    indent = "  " * _depth(node)
    if isinstance(node, Document):
        line = (
            f"{indent}{node.id} [document] {node.source} — {node.page_count} page(s), "
            f"{len(node.sections)} section(s)"
        )
    elif isinstance(node, Section):
        line = f"{indent}{node.id} [section] {_heading_or_untitled(node.heading)}"
    elif isinstance(node, Entry):
        line = f"{indent}{node.id} [entry] {_heading_or_untitled(node.heading)}"
    elif isinstance(node, Paragraph):
        line = f"{indent}{node.id} [paragraph] {_truncate(node.text)}"
    else:
        line = f"{indent}{node.id} [bullet] {_truncate(node.text)}"

    page = _page_of(node)
    if page is not None:
        line = f"{line} (p{page})"
    return line


def _render(document: Document) -> list[str]:
    return [_render_line(node) for node in walk(document)]


@evaluate_cli.command("evaluate")
def evaluate(path: Path) -> None:
    """Parse a resume and display its node tree."""
    try:
        document = parse_resume(path)
    except ParsingError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    for line in _render(document):
        typer.echo(line)
