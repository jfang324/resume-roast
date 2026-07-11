"""`config` subcommand group: bare handler functions, wired by the registry."""

from pathlib import Path

import typer

from resume_roast.cli.config.logic import apply_entries
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import (
    CREDENTIAL_SPECS,
    Credentials,
    mask_secret,
)
from resume_roast.persistence.paths import storage_dir


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
