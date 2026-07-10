"""ShowHandler: commands under `resume-roast show`."""

import typer

from resume_roast.persistence.credentials_store import (
    CREDENTIAL_SPECS,
    CredentialsStore,
    mask_secret,
)
from resume_roast.persistence.paths import storage_dir

_NOT_SET = "(not set)"


class ShowHandler:
    def credentials(self) -> None:
        """List every registered credential, masked, or (not set)."""
        credentials = CredentialsStore(storage_dir()).load()
        for spec in CREDENTIAL_SPECS:
            value = getattr(credentials, spec.key, None) if credentials is not None else None
            shown = mask_secret(value) if value else _NOT_SET
            typer.echo(f"{spec.label}: {shown}")
