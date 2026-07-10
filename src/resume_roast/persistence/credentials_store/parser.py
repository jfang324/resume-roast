"""Loaded JSON to Credentials."""

from __future__ import annotations

from typing import Any

from resume_roast.persistence.credentials_store.models import CREDENTIAL_SPECS, Credentials
from resume_roast.persistence.errors import InvalidSchemaError


def parse_credentials(data: dict[str, Any]) -> Credentials:
    """Parse a loaded JSON object into Credentials.

    Every credential field is optional (unset means not yet configured), but
    when present it must be a non-blank string. Raises InvalidSchemaError
    otherwise.
    """
    values: dict[str, str] = {}
    for spec in CREDENTIAL_SPECS:
        raw = data.get(spec.key)
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw.strip():
            raise InvalidSchemaError(f"{spec.key} must be a non-blank string")
        values[spec.key] = raw

    return Credentials(**values)
