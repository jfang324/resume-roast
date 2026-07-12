"""`evaluate` command: bare handler function, wired by the registry."""

import random
import time
from pathlib import Path

import typer

from resume_roast.cli.utils import spinner
from resume_roast.integrations.errors import AuthenticationError
from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.integrations.nvidia.pricing import estimate_cost
from resume_roast.integrations.nvidia.types import Message, Usage
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.evaluate import build_evaluate_prompt
from resume_roast.prompts.types import Prompt
from resume_roast.utils.extraction.pdf_parser import PdfParser

_SPINNER_MESSAGES = (
    "Roasting your resume...",
    "Summoning the resume wizard...",
    "Counting the buzzwords...",
    "Judging your font choices...",
    "Consulting the hiring gods...",
    "Searching for measurable impact...",
    "Composing something devastating...",
)
"""Rotated through while the model thinks; placeholder fun until real copy lands."""


def evaluate(path: Path) -> None:
    """Roast a PDF resume with the configured model, streaming the response."""
    api_key = _require_api_key()
    settings = SettingsStore(storage_dir()).load_or_create()
    parsed = PdfParser().parse(path)
    prompt = build_evaluate_prompt(parsed, persona=settings.persona, level=settings.level)

    client = NvidiaClient(api_key=api_key, model=settings.model)
    started = time.perf_counter()
    # The request plus a thinking model's silent reasoning can run tens of
    # seconds before anything streams; keep a spinner up until the first chunk.
    shuffled = random.sample(_SPINNER_MESSAGES, len(_SPINNER_MESSAGES))
    with spinner(*shuffled):
        stream = client.prompt_stream(_to_messages(prompt))
        chunks = iter(stream)
        first = next(chunks, None)
    if first is not None:
        typer.echo(first, nl=False)
    for chunk in chunks:
        typer.echo(chunk, nl=False)
    typer.echo()
    latency_seconds = time.perf_counter() - started

    if stream.finish_reason == "length":
        typer.secho(
            "Warning: the response hit the completion-token limit; the roast may be incomplete.",
            err=True,
        )
    typer.secho(_summary_line(settings.model, stream.usage, latency_seconds), dim=True)


def _require_api_key() -> str:
    """Return the saved NVIDIA API key, failing fast before any slow work."""
    credentials = CredentialsStore(storage_dir()).load()
    if credentials.nvidia_api_key is None:
        raise AuthenticationError(
            "No NVIDIA API key configured. Run: resume-roast config credentials"
        )
    return credentials.nvidia_api_key


def _to_messages(prompt: Prompt) -> list[Message]:
    """Convert a built prompt into client messages.

    Lives here because prompts/ stays decoupled from integrations/.
    """
    messages = [Message(role="system", content=prompt.system)]
    if prompt.user is not None:
        messages.append(Message(role="user", content=prompt.user))
    return messages


def _summary_line(model: str, usage: Usage | None, latency_seconds: float) -> str:
    """Render the post-roast stats line, omitting whatever the API didn't report."""
    parts: list[str] = []
    if usage is not None:
        parts.append(f"{usage.prompt_tokens:,} in")
        parts.append(f"{usage.completion_tokens:,} out")
        cost = estimate_cost(usage, model)
        if cost is not None:
            parts.append(f"~${cost:.4f}")
    parts.append(f"{latency_seconds:.1f}s")
    return " · ".join(parts)
