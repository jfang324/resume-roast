"""Pure merge logic for the credentials wizard (no I/O, no typer)."""

import dataclasses
from collections.abc import Mapping

from resume_roast.persistence.credentials.types import CREDENTIAL_SPECS, Credentials


def apply_entries(existing: Credentials, entries: Mapping[str, str]) -> Credentials:
    """Merge freshly entered values into `existing`.

    A blank/whitespace-only entry (or a provider missing from `entries`)
    keeps the existing value for that field; a non-blank entry overwrites
    it (stripped). Fields outside CREDENTIAL_SPECS (e.g. `unrecognized`)
    pass through untouched.
    """
    values: dict[str, str | None] = {}
    for spec in CREDENTIAL_SPECS:
        entered = entries.get(spec.field, "")
        current = getattr(existing, spec.field)
        values[spec.field] = entered.strip() or current
    return dataclasses.replace(existing, **values)
