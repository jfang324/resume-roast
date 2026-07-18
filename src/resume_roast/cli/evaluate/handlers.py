"""`evaluate` command: bare handler function, wired by the registry."""

from pathlib import Path

from rich.console import Console

from resume_roast.cli.evaluate.constants import SPINNER_MESSAGES
from resume_roast.cli.evaluate.rendering import show_report
from resume_roast.cli.utils import build_client, spinner
from resume_roast.services.evaluate.service import run


def evaluate(path: Path) -> None:
    """Roast a PDF or DOCX resume with the configured model and print the report."""
    client, settings = build_client()
    console = Console(highlight=False)

    with spinner(*SPINNER_MESSAGES):
        result = run(client, path, settings.persona, settings.level)

    show_report(console, result, settings.model)
