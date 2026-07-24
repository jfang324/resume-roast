"""`interview` command: bare handler function, wired by the registry."""

import logging
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from resume_roast.cli.input_provider import ConsoleInputProvider
from resume_roast.cli.interview.rendering import ConsoleInterviewRenderer
from resume_roast.cli.interview.report import (
    REPORTS_DIRNAME,
    build_report_markdown,
    report_filename,
)
from resume_roast.cli.utils import build_client, storage_dir
from resume_roast.services.interview.service import run


def interview(
    path: Path,
    report: bool = typer.Option(
        False,
        "--report",
        help="Save a Markdown report of the interview under "
        "~/.resume-roast/interview-reports/, named by timestamp and resume.",
    ),
) -> None:
    """Run an agentic behavioral interview on a PDF or DOCX resume."""
    reports_dir = storage_dir() / REPORTS_DIRNAME
    if report:
        _ensure_reports_dir(reports_dir)

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

    if not report:
        return

    if result is None:
        console.print("[dim]No answers were evaluated; report not written.[/dim]")

        return

    destination = reports_dir / report_filename(path, datetime.now())
    try:
        destination.write_text(build_report_markdown(result, settings.model), encoding="utf-8")
    except OSError as exc:
        typer.echo(f"Error: could not write report: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    console.print(f"Report written to {destination}")


def _ensure_reports_dir(reports_dir: Path) -> None:
    """Create the reports directory before any API spend.

    The report is written only after the whole interview has run; a directory
    that can't be created, discovered then, would cost the session's entire
    output. Fail here, before the first token, instead.
    """
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        typer.echo(f"Error: could not create report directory: {exc}", err=True)
        raise typer.Exit(code=1) from exc
