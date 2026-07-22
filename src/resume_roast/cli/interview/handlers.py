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

    report.write_text(build_report_markdown(result, settings.model), encoding="utf-8")
    console.print(f"Report written to {report}")
