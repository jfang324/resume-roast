"""CLI entry point for resume-roast."""

from __future__ import annotations

import typer

from resume_roast.persistence.credentials_store import Credentials, CredentialsStore, mask_secret
from resume_roast.persistence.errors import PersistenceError
from resume_roast.persistence.paths import storage_dir

app = typer.Typer(no_args_is_help=True)
config_app = typer.Typer(no_args_is_help=True)
app.add_typer(config_app, name="config", help="Manage settings and credentials.")


@config_app.command("credentials")
def credentials() -> None:
    """Prompt for and save the Anthropic API key."""
    raw_key = typer.prompt("Anthropic API key", hide_input=True, confirmation_prompt=True)
    key = raw_key.strip()
    if not key:
        typer.echo("Error: API key cannot be empty", err=True)
        raise typer.Exit(1)

    store = CredentialsStore(storage_dir())
    try:
        store.save(Credentials(anthropic_api_key=key))
    except PersistenceError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Saved Anthropic API key {mask_secret(key)} to {store.path}")
