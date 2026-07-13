"""`evaluate` command: bare handler function, wired by the registry."""

import random
import time
from pathlib import Path

import typer
from rich.console import Console

from resume_roast.cli.utils import print_highlighted_lines, spinner
from resume_roast.integrations.errors import AuthenticationError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.integrations.nvidia.pricing import estimate_cost
from resume_roast.integrations.structured import structured_completion
from resume_roast.integrations.types import Message, Usage
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.evaluate.builder import build_evaluate_prompt
from resume_roast.prompts.evaluate.parser import RoastReportParser
from resume_roast.prompts.evaluate.rendering import (
    DIFF_ADDITION_PREFIX,
    DIFF_REMOVAL_PREFIX,
    render_report,
)
from resume_roast.prompts.types import Prompt
from resume_roast.utils.extraction.pdf_parser import PdfParser

_SPINNER_MESSAGES = (
    "roasting your resume...",
    "summoning the resume wizard...",
    "counting the buzzwords...",
    "judging your font choices...",
    "consulting the hiring gods...",
    "searching for measurable impact...",
    "composing something devastating...",
)

_DIFF_STYLES = {
    DIFF_REMOVAL_PREFIX: "on #3a0000",
    DIFF_ADDITION_PREFIX: "on #003a00",
}
"""Full-width background colors for the removal/addition lines of a rewrite."""


def evaluate(path: Path) -> None:
    """Roast a PDF resume with the configured model and print the report."""
    api_key = _require_api_key()
    settings = SettingsStore(storage_dir()).load_or_create()
    parsed = PdfParser().parse(path)
    prompt = build_evaluate_prompt(parsed, persona=settings.persona, level=settings.level)

    client: LlmClient = NvidiaClient(api_key=api_key, model=settings.model)
    started = time.perf_counter()
    shuffled = random.sample(_SPINNER_MESSAGES, len(_SPINNER_MESSAGES))
    with spinner(*shuffled):
        report, usage = structured_completion(
            client, _to_messages(prompt), RoastReportParser().parse
        )
    latency_seconds = time.perf_counter() - started

    console = Console(highlight=False)
    print_highlighted_lines(render_report(report), console, _DIFF_STYLES)
    typer.echo()
    console.print(_summary_line(settings.model, usage, latency_seconds), style="dim")


def _require_api_key() -> str:
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )
    return credentials.nvidia_api_key


def _to_messages(prompt: Prompt) -> list[Message]:
    messages = [Message(role="system", content=prompt.system)]
    if prompt.user is not None:
        messages.append(Message(role="user", content=prompt.user))
    return messages


def _summary_line(model: str, usage: Usage | None, latency_seconds: float) -> str:
    parts: list[str] = []
    if usage is not None:
        parts.append(f"{usage.prompt_tokens:,} input tokens")
        parts.append(f"{usage.completion_tokens:,} output tokens")
        cost = estimate_cost(usage, model)
        if cost is not None:
            parts.append(f"~${cost:.4f}")
    parts.append(f"{latency_seconds:.1f}s")
    return " · ".join(parts)
