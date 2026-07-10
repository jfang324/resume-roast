"""Loaded JSON to Credentials."""

from __future__ import annotations

from typing import Any

from resume_roast.persistence.credentials_store.models import Credentials
from resume_roast.persistence.errors import InvalidSchemaError


def parse_credentials(data: dict[str, Any]) -> Credentials:
    """Parse a loaded JSON object into Credentials.

    Raises InvalidSchemaError when anthropic_api_key is missing, not a
    string, or blank after stripping.
    """
    key = data.get("anthropic_api_key")
    if not isinstance(key, str) or not key.strip():
        raise InvalidSchemaError("credentials file is missing a valid anthropic_api_key")

    return Credentials(anthropic_api_key=key)
