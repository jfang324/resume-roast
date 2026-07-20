"""`interview` command: bare handler function, wired by the registry."""

import logging
from pathlib import Path

from rich.console import Console

from resume_roast.cli.input_provider import ConsoleInputProvider
from resume_roast.cli.interview.rendering import ConsoleInterviewRenderer
from resume_roast.cli.utils import build_client
from resume_roast.services.interview.service import run


def interview(path: Path) -> None:
    """Run an agentic behavioral interview on a PDF or DOCX resume."""
    client, settings = build_client()
    debug = logging.getLogger().isEnabledFor(logging.DEBUG)
    renderer = ConsoleInterviewRenderer(
        Console(highlight=False),
        settings.model,
        debug=debug,
    )
    input_provider = ConsoleInputProvider()

    run(client, path, renderer, input_provider)
