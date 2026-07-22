"""`interview` command: bare handler function, wired by the registry."""

import logging
from pathlib import Path

import typer
from rich.console import Console

from resume_roast.cli.input_provider import ConsoleInputProvider
from resume_roast.cli.interview.rendering import ConsoleInterviewRenderer
from resume_roast.cli.interview.report import build_report_markdown
from resume_roast.cli.utils import build_client
from resume_roast.services.interview.service import run


def interview(
    path: Path,
    report: Path | None = typer.Option(
        None,
        "--report",
        help="Write a detailed Markdown report of the interview to this file.",
    ),
) -> None:
    """Run an agentic behavioral interview on a PDF or DOCX resume."""
    if report is not None:
        _reject_unwritable(report)

    client, settings = build_client()
    debug = logging.getLogger().isEnabledFor(logging.DEBUG)
    console = Console(highlight=False)
    renderer = ConsoleInterviewRenderer(
        console,
        settings.model,
        debug=debug,
    )
    input_provider = ConsoleInputProvider()

    result = run(client, path, renderer, input_provider)

    if report is None:
        return

    if result is None:
        console.print("[dim]No answers were evaluated; report not written.[/dim]")

        return

    try:
        report.write_text(build_report_markdown(result, settings.model), encoding="utf-8")
    except OSError as exc:
        typer.echo(f"Error: could not write report: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    console.print(f"Report written to {report}")


def _reject_unwritable(report: Path) -> None:
    """Refuse a report path that cannot receive the file, before any API spend.

    The write happens only after the whole interview has run; a typo'd
    directory discovered then would cost the session's entire output.
    """
    if report.is_dir():
        typer.echo(f"Error: report path is a directory: {report}", err=True)
        raise typer.Exit(code=1)

    if not report.parent.is_dir():
        typer.echo(f"Error: report directory does not exist: {report.parent}", err=True)
        raise typer.Exit(code=1)
