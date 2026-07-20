"""Pure merge and selection logic for the config wizards (no I/O, no typer)."""

import dataclasses
from collections.abc import Mapping

from resume_roast.persistence.credentials.types import CREDENTIAL_SPECS, Credentials
from resume_roast.persistence.settings.types import Settings, SettingSpec


class InvalidSelectionError(ValueError):
    """A wizard entry that doesn't resolve to allowed choices."""


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


def parse_selection(spec: SettingSpec, entry: str) -> str | tuple[str, ...]:
    """Turn a numbered wizard entry into the setting's choice value(s).

    A single-valued setting takes one number ("2"); a multi-valued setting
    takes one or more comma-separated numbers ("1,3"), deduplicated in
    entry order.
    """
    parts = [part.strip() for part in entry.split(",")]
    if not spec.many and len(parts) != 1:
        raise InvalidSelectionError(f"{spec.label} takes exactly one selection")

    indexes: list[int] = []
    for part in parts:
        if not part.isdigit() or not 1 <= int(part) <= len(spec.choices):
            raise InvalidSelectionError(f"enter a number between 1 and {len(spec.choices)}")

        indexes.append(int(part))

    if spec.many:
        return tuple(spec.choices[index - 1] for index in dict.fromkeys(indexes))

    return spec.choices[indexes[0] - 1]


def apply_selections(
    existing: Settings, selections: Mapping[str, str | tuple[str, ...]]
) -> Settings:
    """Overwrite `existing` with parsed selections; absent fields keep their value."""
    return dataclasses.replace(existing, **selections)
