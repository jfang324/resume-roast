"""`evaluate` command: bare handler function, wired by the registry."""

import time
from pathlib import Path

import typer
from rich.console import Console

from resume_roast.cli.evaluate.constants import DIFF_STYLES, SPINNER_MESSAGES
from resume_roast.cli.utils import print_highlighted_lines, spinner, summary_line
from resume_roast.integrations.errors import AuthenticationError
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.integrations.structured import structured_completion
from resume_roast.integrations.types import Message
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.evaluate.builder import build_evaluate_prompt
from resume_roast.prompts.evaluate.output.parser import RoastReportParser
from resume_roast.prompts.evaluate.output.rendering import render_report
from resume_roast.utils.extraction.mappings import get_parser


def evaluate(path: Path) -> None:
    """Roast a PDF or DOCX resume with the configured model and print the report."""
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )

    settings = SettingsStore(storage_dir()).load_or_create()
    parsed = get_parser(path).parse(path)
    prompt = build_evaluate_prompt(parsed, persona=settings.persona, level=settings.level)
    messages: list[Message] = [Message(role="system", content=prompt.system)]
    if prompt.user is not None:
        messages.append(Message(role="user", content=prompt.user))

    client = NvidiaClient(api_key=credentials.nvidia_api_key, model=settings.model)
    started = time.perf_counter()
    with spinner(*SPINNER_MESSAGES):
        report, usage = structured_completion(client, messages, RoastReportParser().parse)
    latency_seconds = time.perf_counter() - started

    console = Console(highlight=False)
    print_highlighted_lines(render_report(report), console, DIFF_STYLES)
    typer.echo()
    console.print(summary_line(settings.model, usage, latency_seconds), style="dim")
