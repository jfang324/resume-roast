"""`evaluate` command: bare handler function, wired by the registry."""

from pathlib import Path

import typer

from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.prompts.evaluate import build_evaluate_prompt
from resume_roast.utils.extraction.pdf_parser import PdfParser


def evaluate(path: Path) -> None:
    """Print the roast prompt built from a PDF resume.

    Temporary output: shows exactly what the model will receive, until the
    LLM integration lands and this command sends the prompt instead.
    """
    settings = SettingsStore(storage_dir()).load_or_create()
    parsed = PdfParser().parse(path)
    prompt = build_evaluate_prompt(parsed, persona=settings.persona, level=settings.level)
    typer.echo("=== system ===")
    typer.echo(prompt.system)
    typer.echo("=== user ===")
    typer.echo(prompt.user)
