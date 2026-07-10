"""CLI entry point for resume-roast."""

from __future__ import annotations

import typer

from resume_roast.persistence.credentials_store import (
    CREDENTIAL_SPECS,
    Credentials,
    CredentialsStore,
    mask_secret,
)
from resume_roast.persistence.errors import PersistenceError
from resume_roast.persistence.paths import storage_dir

app = typer.Typer(no_args_is_help=True)
config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config", help="Manage settings and credentials.")


@config_app.command("credentials")
def credentials() -> None:
    """Select and save one of the supported API keys."""
    typer.echo("Select a credential to set:")
    for index, spec in enumerate(CREDENTIAL_SPECS, start=1):
        typer.echo(f"  {index}. {spec.label}")

    choice: int = typer.prompt("Enter a number", type=int)
    if choice < 1 or choice > len(CREDENTIAL_SPECS):
        typer.echo("Error: invalid selection", err=True)
        raise typer.Exit(1)
    spec = CREDENTIAL_SPECS[choice - 1]

    raw_value = typer.prompt(spec.label, hide_input=True, confirmation_prompt=True)
    value = raw_value.strip()
    if not value:
        typer.echo("Error: API key cannot be empty", err=True)
        raise typer.Exit(1)

    store = CredentialsStore(storage_dir())
    try:
        store.save(Credentials(**{spec.key: value}))
    except PersistenceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Saved {spec.label} {mask_secret(value)} to {store.path}")
