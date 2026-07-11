"""The root-level `evaluate` command."""

from __future__ import annotations

from pathlib import Path

import typer

from resume_roast.parsing import ParsingError, parse_resume
from resume_roast.parsing.render import render_tree

evaluate_cli = typer.Typer()


@evaluate_cli.command("evaluate")
def evaluate(path: Path) -> None:
    """Parse a resume and display its node tree."""
    try:
        document = parse_resume(path)
    except ParsingError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    for line in render_tree(document):
        typer.echo(line)
