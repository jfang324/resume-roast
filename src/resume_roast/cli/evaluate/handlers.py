"""`evaluate` command: bare handler function, wired by the registry."""

from pathlib import Path

import typer
from rich.console import Console

from resume_roast.cli.evaluate.constants import DIFF_STYLES, SPINNER_MESSAGES
from resume_roast.cli.utils import print_highlighted_lines, spinner, summary_line
from resume_roast.integrations.errors import AuthenticationError
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.evaluate.output.rendering import render_report
from resume_roast.services.evaluate import run as run_evaluate
from resume_roast.utils.extraction.mappings import get_parser


def evaluate(path: Path) -> None:
    """Roast a PDF or DOCX resume with the configured model and print the report."""
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )
    settings = SettingsStore(storage_dir()).load_or_create()

    client = NvidiaClient(api_key=credentials.nvidia_api_key, model=settings.model)
    parsed = get_parser(path).parse(path)

    console = Console(highlight=False)
    with spinner(*SPINNER_MESSAGES):
        result = run_evaluate(client, parsed, settings.persona, settings.level)

    print_highlighted_lines(render_report(result.report), console, DIFF_STYLES)
    typer.echo()
    console.print(summary_line(settings.model, result.usage, result.latency_seconds), style="dim")
