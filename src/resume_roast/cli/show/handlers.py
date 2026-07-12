"""`show` subcommand group: bare handler functions, wired by the registry."""

import typer

from resume_roast.cli.utils import NOT_SET, display_value
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import CREDENTIAL_SPECS, mask_secret
from resume_roast.persistence.paths import storage_dir
from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.persistence.settings.types import SETTING_SPECS


def credentials() -> None:
    """Display every registered provider's saved API key, masked.

    Creates the credentials file if it doesn't exist yet.
    """
    saved = CredentialsStore(storage_dir()).load_or_create()
    for spec in CREDENTIAL_SPECS:
        value = getattr(saved, spec.field)
        shown = mask_secret(value) if value else NOT_SET
        typer.echo(f"{spec.label}: {shown}")


def settings() -> None:
    """Display every setting's current value.

    Creates the settings file with default values if it doesn't exist yet.
    """
    saved = SettingsStore(storage_dir()).load_or_create()
    for spec in SETTING_SPECS:
        typer.echo(f"{spec.label}: {display_value(getattr(saved, spec.field))}")
