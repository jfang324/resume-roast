"""`config` subcommand group: bare handler functions, wired by the registry."""

from pathlib import Path

import typer

from resume_roast.cli.config.logic import (
    InvalidSelectionError,
    apply_entries,
    apply_selections,
    parse_selection,
)
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import (
    CREDENTIAL_SPECS,
    Credentials,
    mask_secret,
)
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.persistence.settings.types import SETTING_SPECS, Settings


def credentials() -> None:
    """Prompt for every registered provider's API key and save them.

    A blank entry keeps the existing value for that provider.
    """
    store = CredentialsStore(storage_dir())
    existing = store.load()
    updated = apply_entries(existing, _prompt_for_entries(existing))
    store.save(updated)
    _confirm_saved(updated, store.path)


def _prompt_for_entries(existing: Credentials) -> dict[str, str]:
    """Ask for each registered provider's key, showing its masked status."""
    entries: dict[str, str] = {}
    for spec in CREDENTIAL_SPECS:
        current = getattr(existing, spec.field)
        status = f"currently set, {mask_secret(current)}" if current else "not set"
        entries[spec.field] = typer.prompt(
            f"{spec.label} ({status})", hide_input=True, default="", show_default=False
        )
    return entries


def _confirm_saved(saved: Credentials, path: Path) -> None:
    """Echo each provider's masked value, or "not set"."""
    for spec in CREDENTIAL_SPECS:
        value = getattr(saved, spec.field)
        if value is None:
            typer.echo(f"{spec.label}: not set")
        else:
            typer.echo(f"{spec.label}: saved ({mask_secret(value)}) to {path}")


def settings() -> None:
    """Choose each setting from its allowed values and save them.

    A blank entry keeps the current value.
    """
    store = SettingsStore(storage_dir())
    existing = store.load()
    updated = apply_selections(existing, _prompt_for_selections(existing))
    store.save(updated)
    _confirm_settings(updated, store.path)


def _prompt_for_selections(existing: Settings) -> dict[str, str | tuple[str, ...]]:
    """Show each setting's numbered choices and collect valid selections."""
    selections: dict[str, str | tuple[str, ...]] = {}
    for spec in SETTING_SPECS:
        typer.echo(f"{spec.label} (currently: {_display(getattr(existing, spec.field))})")
        for number, choice in enumerate(spec.choices, start=1):
            typer.echo(f"  {number}. {choice}")
        hint = "Selection(s), comma-separated" if spec.many else "Selection"
        while True:
            entry = typer.prompt(
                f"{hint} (blank keeps current)", default="", show_default=False
            ).strip()
            if not entry:
                break
            try:
                selections[spec.field] = parse_selection(spec, entry)
                break
            except InvalidSelectionError as exc:
                typer.echo(f"Invalid selection: {exc}")
    return selections


def _display(value: str | tuple[str, ...]) -> str:
    """Render a setting value for prompts and confirmations."""
    return ", ".join(value) if isinstance(value, tuple) else value


def _confirm_settings(saved: Settings, path: Path) -> None:
    """Echo each setting's saved value."""
    for spec in SETTING_SPECS:
        typer.echo(f"{spec.label}: {_display(getattr(saved, spec.field))}")
    typer.echo(f"Saved to {path}")
