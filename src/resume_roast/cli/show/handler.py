"""Commands under `resume-roast show`."""

import typer

from resume_roast.persistence.config_store import SETTING_SPECS, ConfigStore
from resume_roast.persistence.credentials_store import (
    CREDENTIAL_SPECS,
    CredentialsStore,
    mask_secret,
)
from resume_roast.persistence.paths import storage_dir

_NOT_SET = "(not set)"

show_cli = typer.Typer(no_args_is_help=True)


@show_cli.command("credentials")
def credentials() -> None:
    """List every registered credential, masked, or (not set)."""
    stored = CredentialsStore(storage_dir()).load()
    for spec in CREDENTIAL_SPECS:
        value = getattr(stored, spec.key, None) if stored is not None else None
        shown = mask_secret(value) if value else _NOT_SET
        typer.echo(f"{spec.label}: {shown}")


@show_cli.command("settings")
def settings() -> None:
    """List every setting's saved value, or (not set)."""
    config = ConfigStore(storage_dir()).load()
    for spec in SETTING_SPECS:
        value = getattr(config, spec.key)
        if value is None:
            shown = _NOT_SET
        elif spec.multi:
            shown = f"[{', '.join(value)}]"
        else:
            shown = value
        typer.echo(f"{spec.label}: {shown}")
