"""Prompt and confirmation helpers shared by the config wizards."""

from pathlib import Path

import typer

from resume_roast.cli.config.logic import InvalidSelectionError, parse_selection
from resume_roast.cli.utils import NOT_SET, display_value
from resume_roast.persistence.credentials.types import CREDENTIAL_SPECS, Credentials, mask_secret
from resume_roast.persistence.settings.types import SETTING_SPECS, Settings


def prompt_for_entries(existing: Credentials) -> dict[str, str]:
    """Ask for each registered provider's key, showing its masked current value."""
    entries: dict[str, str] = {}
    for spec in CREDENTIAL_SPECS:
        current = getattr(existing, spec.field)
        shown = mask_secret(current) if current else NOT_SET
        entries[spec.field] = typer.prompt(
            _with_current(spec.label, shown), hide_input=True, default="", show_default=False
        )

    return entries


def confirm_saved(saved: Credentials, path: Path) -> None:
    """Echo each provider's masked value, or "not set"."""
    for spec in CREDENTIAL_SPECS:
        value = getattr(saved, spec.field)
        if value is None:
            typer.echo(f"{spec.label}: {NOT_SET}")
        else:
            typer.echo(f"{spec.label}: saved ({mask_secret(value)}) to {path}")


def prompt_for_selections(existing: Settings) -> dict[str, str | tuple[str, ...]]:
    """Show each setting's numbered choices and collect valid selections."""
    selections: dict[str, str | tuple[str, ...]] = {}
    for spec in SETTING_SPECS:
        typer.echo(spec.label)
        for number, choice in enumerate(spec.choices, start=1):
            typer.echo(f"  {number}. {choice}")

        hint = "Selection(s), comma-separated" if spec.many else "Selection"
        current = display_value(getattr(existing, spec.field))
        while True:
            entry = typer.prompt(
                _with_current(hint, current), default="", show_default=False
            ).strip()
            if not entry:
                break

            try:
                selections[spec.field] = parse_selection(spec, entry)
                break
            except InvalidSelectionError as exc:
                typer.echo(f"Invalid selection: {exc}")

    return selections


def confirm_settings(saved: Settings, path: Path) -> None:
    """Echo each setting's saved value."""
    for spec in SETTING_SPECS:
        typer.echo(f"{spec.label}: {display_value(getattr(saved, spec.field))}")

    typer.echo(f"Saved to {path}")


def _with_current(prefix: str, current: str) -> str:
    """Format a prompt as ``<prefix> [current: <value>]``."""
    return f"{prefix} [current: {current}]"
